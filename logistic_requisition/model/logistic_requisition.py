# -*- coding: utf-8 -*-
#
#
#    Author: Joël Grand-Guillaume, Jacques-Etienne Baudoux, Guewen Baconnier
#    Copyright 2013-2015 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
from __future__ import division

import logging

from openerp import models, fields, api, exceptions
from openerp.exceptions import except_orm
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.multi
    def _store_get_requisition_ids(self, sfield):
        env = self.env
        return env['logistic.requisition'].search([(sfield, 'in', env.ids)])


class LogisticsRequisition(models.Model):
    _name = "logistic.requisition"
    _description = "Logistics Requisition"
    _inherit = ['mail.thread']
    _order = "name desc"

    REQ_STATES = {'confirmed': [('readonly', True)],
                  'done': [('readonly', True)],
                  'cancel': [('readonly', True)]
                  }

    @api.model
    def get_requisition_type_selection(self):
        """ Extendable selection list """
        return [('standard', 'Standard'),
                ('cost_estimate_only', 'Cost Estimate Only')]

    @api.model
    def _get_requisition_type_selection(self):
        return self.get_requisition_type_selection()

    @api.multi
    def get_partner_requisition(self):
        return (self.env['res.partner']
                ._store_get_requisition_ids(sfield='consignee_shipping_id'))

    name = fields.Char(
        'Reference',
        required=True,
        readonly=True,
        default='/',
        copy=False)
    # Not intended to match OpenERP origin field convention.
    # Source comes from paper
    source_document = fields.Char(
        'Source Document',
        states=REQ_STATES)
    date = fields.Datetime(
        'Requisition Date',
        states=REQ_STATES,
        required=True,
        default=fields.Datetime.now)
    date_delivery = fields.Date(
        'Desired Delivery Date',
        states=REQ_STATES,
        required=True)
    user_id = fields.Many2one(
        'res.users',
        'Business Unit Officer',
        required=True,
        states=REQ_STATES,
        help="Mobilization Officer or Logistics Coordinator "
             "in charge of the Logistics Requisition",
        default=lambda self: self.env.uid)
    partner_id = fields.Many2one(
        'res.partner',
        'Requestor',
        required=True,
        domain=[('customer', '=', True)],
        states=REQ_STATES)
    consignee_id = fields.Many2one(
        'res.partner', 'Consignee',
        domain=[('is_consignee', '=', True)],
        states=REQ_STATES)
    consignee_shipping_id = fields.Many2one(
        'res.partner', 'Delivery Address',
        states=REQ_STATES)
    country_id = fields.Many2one(
        'res.country',
        string='Country',
        states=REQ_STATES,
        select=True)
    company_id = fields.Many2one(
        'res.company',
        'Company',
        readonly=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'logistic.request'))

    analytic_id = fields.Many2one(
        'account.analytic.account',
        'Project',
        states=REQ_STATES)
    requisition_type = fields.Selection(
        selection=_get_requisition_type_selection,
        string='Type',
        required=True,
        states=REQ_STATES,
        default='standard')
    note = fields.Text(
        'Remarks / Description',
        states=REQ_STATES)
    shipping_note = fields.Text(
        'Delivery / Shipping Remarks',
        states=REQ_STATES)
    incoterm_id = fields.Many2one(
        'stock.incoterms',
        'Incoterm',
        states=REQ_STATES,
        help="International Commercial Terms are a series of "
             "predefined commercial terms used in international "
             "transactions.")
    incoterm_address = fields.Char(
        'Incoterm Place',
        states=REQ_STATES,
        help="Incoterm Place of Delivery. "
             "International Commercial Terms are a series of "
             "predefined commercial terms used in "
             "international transactions.")
    line_ids = fields.One2many(
        'logistic.requisition.line',
        'requisition_id',
        string='Products to Purchase',
        states={'done': [('readonly', True)]},
        copy=True)
    state = fields.Selection(
        [('draft', 'Draft'),
         ('confirmed', 'Confirmed'),
         ('done', 'Done'),
         ('cancel', 'Cancelled'),
         ],
        string='State',
        readonly=True,
        required=True,
        default='draft',
        copy=False)
    sourced = fields.Float(
        compute='_get_sourced',
        string='Sourced')
    pricelist_id = fields.Many2one(
        'product.pricelist',
        'Pricelist',
        required=True,
        states=REQ_STATES,
        help="Pricelist that represents the currency for current logistics "
             "requisition.")
    # ValueError: Wrong value for logistic.requisition.currency_id:
    # res.currency() on create
    currency_id = fields.Many2one(
        related='pricelist_id.currency_id',
        comodel_name='res.currency',
        string='Currency',
        readonly=True,
        store=True)
    cancel_reason_id = fields.Many2one(
        'logistic.requisition.cancel.reason',
        string='Reason for Cancellation',
        ondelete='restrict',
        readonly=True,
        copy=False)
    ce_count = fields.Integer(compute='_count_cost_estimates',
                              string='CE count')
    po_count = fields.Integer(compute='_count_purchase_orders',
                              string='PO count')

    _sql_constraints = [
        ('name_uniq',
         'unique(name)',
         'Logistics Requisition Reference must be unique!'),
        ('check_date_delivery',
         'check(date::date <= date_delivery)',
         'Desired delivery date must be on or after Requisition date.'),
    ]

    @api.multi
    def _get_sourced(self):
        for requisition in self:
            lines_len = sum(1 for req in requisition.line_ids
                            if req.state != 'cancel')
            sourced_len = sum(1 for req in requisition.line_ids
                              if req.state in ('sourced', 'quoted'))
            if lines_len == 0:
                percentage = 0.
            else:
                percentage = round(sourced_len / lines_len * 100, 2)
            requisition.sourced = percentage

    @api.multi
    def _get_all_lines(self):
        """ return aggregated lines of multiple requisitions """
        line_ids = [line.id for req in self for line in req.line_ids]
        return self.env['logistic.requisition.line'].browse(line_ids)

    @api.multi
    def _do_cancel(self, reason_id):
        lines = self._get_all_lines()
        if lines:
            lines._do_cancel()
        vals = {'state': 'cancel',
                'cancel_reason_id': reason_id}
        self.write(vals)

    @api.multi
    def _do_confirm(self):
        lines = self._get_all_lines()
        if lines:
            lines._do_confirm()
        self.state = 'confirmed'

    @api.multi
    def _do_draft(self):
        lines = self._get_all_lines()
        if lines:
            lines._do_draft()
        vals = {'state': 'draft',
                'cancel_reason_id': False,
                }
        self.write(vals)

    @api.multi
    def _do_done(self):
        """ Set all Logistics Requisition to done if all lines are
        quoted or cancel and if at least one is quoted.

        Set Logistics Requisition to cancel if all lines are cancelled
        """
        to_dones = self.browse()
        to_cancels = self.browse()
        for req in self:
            if all(line.state == 'cancel' for line in req.line_ids):
                to_cancels |= req
            elif all(line.state in ['quoted', 'cancel']
                     for line in req.line_ids):
                to_dones |= req
        to_dones.write({'state': 'done'})
        to_cancels.write({'state': 'cancel'})

    @api.model
    def create(self, vals):
        if (vals.get('name') or '/') == '/':
            seq_obj = self.env['ir.sequence']
            vals['name'] = seq_obj.get('logistic.requisition') or '/'
        return super(LogisticsRequisition, self).create(vals)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """We take the pricelist of the chosen partner"""
        pricelist = False
        if self.partner_id:
            partner = self.partner_id
            pricelist = partner.property_product_pricelist
        self.pricelist_id = pricelist

    @api.onchange('consignee_id')
    def onchange_consignee_id_set_consignee_shipping_id(self):
        if not self.consignee_id:
            self.consignee_shipping_id = False
            return

        addr = self.consignee_id.address_get(['delivery'])
        self.consignee_shipping_id = addr['delivery']

    @api.onchange('consignee_id')
    def onchange_consignee_id_set_country_id(self):
        if not self.consignee_id:
            self.country_id = False
            return

        self.country_id = self.consignee_shipping_id.country_id

    @api.multi
    def button_confirm(self):
        self._do_confirm()
        return True

    @api.multi
    def button_create_cost_estimate(self):
        ref = 'logistic_requisition.action_logistic_requisition_cost_estimate'
        action = self.env['ir.model.data'].xmlid_to_object(ref)
        return action.read()[0]

    @api.multi
    def button_reset(self):
        self._do_draft()
        return True

    @api.multi
    def button_view_lines(self):
        """
        This function returns an action that display related lines.
        """
        ref = 'logistic_requisition.action_logistic_requisition_line'

        action = self.env['ir.model.data'].xmlid_to_object(ref)
        action_dict = action.read()[0]
        action_dict['domain'] = str([('requisition_id', 'in', self.ids)])
        return action_dict

    @api.multi
    def button_view_source_lines(self):
        """
        This function returns an action that display related sourcing lines.
        """
        ref = 'logistic_requisition.action_logistic_requisition_source'
        action = self.env['ir.model.data'].xmlid_to_object(ref)
        action_dict = action.read()[0]
        action_dict['domain'] = str([('requisition_id', 'in', self.ids)])
        return action_dict

    @api.multi
    def _get_relevant_purchases(self):
        sourced_lines = self.line_ids.filtered(
            lambda rec: rec.state in ('sourced', 'quoted')
            )
        purchases = sourced_lines.mapped(
            'source_ids.purchase_line_id.order_id'
            )

        unsourced_lines = self.env['logistic.requisition.line']
        for line in self.line_ids - sourced_lines:
            for method in line.mapped('source_ids.sourcing_method'):
                if method in ('procurement', 'reuse_bid'):
                    unsourced_lines |= line
                    break
        bids = unsourced_lines.mapped('source_ids.selected_bid_id')
        purchases |= bids
        return purchases

    @api.multi
    def action_open_lr_purchases(self):
        """ Open Bids and Purchase order sourcing this LR"""
        self.ensure_one()
        action_ref = 'purchase.purchase_form_action'
        action_dict = self.env.ref(action_ref).read()[0]
        purchases = self._get_relevant_purchases()
        action_dict['domain'] = [('id', 'in', purchases.ids)]
        del action_dict['help']

        return action_dict

    @api.one
    @api.depends('line_ids.source_ids.purchase_line_id.order_id',
                 'line_ids.source_ids.selected_bid_id')
    def _count_purchase_orders(self):
        """ Set lr_count field """
        self.po_count = len(self._get_relevant_purchases())

    @api.multi
    def _get_relevant_cost_estimates(self):
        return self.mapped('line_ids.cost_estimate_id')

    @api.multi
    def action_open_lr_cost_estimate(self):
        """ Open cost estimates generated from this LR """
        self.ensure_one()
        cost_estimates = self._get_relevant_cost_estimates()
        action_dict = {
            'name': _('Cost Estimate'),
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'target': 'current',
            'res_id': cost_estimates.ids[0] if cost_estimates else 1,
            'domain': [('id', 'in', cost_estimates.ids)],
            'view_id': False,
            'context': {},
            'type': 'ir.actions.act_window',
        }
        return action_dict

    @api.one
    @api.depends('line_ids.cost_estimate_id')
    def _count_cost_estimates(self):
        """ Set lr_count field """
        self.ce_count = len(self._get_relevant_cost_estimates())


class LogisticsRequisitionLine(models.Model):
    _name = "logistic.requisition.line"
    _description = "Logistics Requisition Line"
    _inherit = ['mail.thread']
    _order = "requisition_id desc, name desc"

    REQUEST_STATES = {'assigned': [('readonly', True)],
                      'sourced': [('readonly', True)],
                      'quoted': [('readonly', True)],
                      }
    STATES = [('draft', 'Draft'),
              ('confirmed', 'Confirmed'),
              ('assigned', 'Assigned'),
              ('sourced', 'Sourced'),
              ('quoted', 'Quoted'),
              ('cancel', 'Cancelled')
              ]

    name = fields.Char(
        u'Line No.',
        readonly=True,
        default='/',
        copy=False)
    requisition_id = fields.Many2one(
        'logistic.requisition',
        'Requisition',
        readonly=True,
        required=True,
        ondelete='cascade')
    source_ids = fields.One2many(
        'logistic.requisition.source',
        'requisition_line_id',
        string='Source Lines',
        states={'sourced': [('readonly', True)],
                'quoted': [('readonly', True)]})
    logistic_user_id = fields.Many2one(
        'res.users',
        'Assigned To',
        states=REQUEST_STATES,
        # workaround for the following bug, preventing to
        # automatically subscribe the user to the line
        # https://bugs.launchpad.net/openobject-addons/+bug/1188538
        track_visibility='never',
        help="User in charge of the "
             "Logistics Requisition Line")
    product_id = fields.Many2one('product.product', 'Product',
                                 states=REQUEST_STATES)
    description = fields.Text('Description',
                              states=REQUEST_STATES,
                              required=True)
    requested_qty = fields.Float(
        'Quantity',
        states=REQUEST_STATES,
        digits=dp.get_precision('Product UoM'),
        default=1.0)
    requested_uom_id = fields.Many2one('product.uom',
                                       'Product UoM',
                                       states=REQUEST_STATES,
                                       required=True)
    amount_total = fields.Float(
        compute='_get_total_cost',
        string='Total Amount',
        digits=dp.get_precision('Account'),
        store=True
    )
    date_delivery = fields.Date(
        'Desired Delivery Date',
        states=REQUEST_STATES,
        required=True
    )
    country_id = fields.Many2one(
        related='requisition_id.country_id',
        string='Country',
        comodel_name='res.country',
        readonly=True,
        store=True)
    requisition_type = fields.Selection(
        selection=LogisticsRequisition._get_requisition_type_selection,
        related='requisition_id.requisition_type',
        string='Requisition Type',
        readonly=True)
    state = fields.Selection(
        STATES,
        string='State',
        required=True,
        readonly=True,
        help="Draft: Created\n"
             "Confirmed: Requisition has been confirmed\n"
             "Assigned: Waiting the creation of a quote\n"
             "Sourced: The line has been sourced from procurement or warehouse"
             "\nQuoted: Quotation made for the line\n"
             "Cancelled: The requisition has been cancelled",
        default='draft',
        copy=False
    )
    currency_id = fields.Many2one(
        related='requisition_id.currency_id',
        comodel_name='res.currency',
        string='Currency',
        readonly=True,
        store=True)
    note = fields.Text('Remarks / Conditions')
    account_id = fields.Many2one(
        related='product_id.property_account_income',
        string='Nominal Account',
        comodel_name='account.account',
        readonly=True)
    cost_estimate_id = fields.Many2one(
        'sale.order',
        string='Cost Estimate',
        readonly=True,
        copy=False)

    stock_count = fields.Integer(compute='_stock_count')

    # related fields to requisition_id
    requestor_id = fields.Many2one(
        related='requisition_id.partner_id',
        co_model='res.partner',
        string='Requestor')
    consignee_id = fields.Many2one(
        related='requisition_id.consignee_id',
        co_model='res.partner',
        string='Consignee')
    consignee_shipping_id = fields.Many2one(
        related='requisition_id.consignee_shipping_id',
        co_model='res.partner',
        string='Delivery Address')
    incoterm_id = fields.Many2one(
        related='requisition_id.incoterm_id',
        co_model='stock.incoterms',
        string='Incoterm',
        help="International Commercial Terms are a series of "
             "predefined commercial terms used in international "
             "transactions.")
    incoterm_address = fields.Char(
        related='requisition_id.incoterm_address',
        string='Incoterm Place',
        help="Incoterm Place of Delivery. "
             "International Commercial Terms are a series of "
             "predefined commercial terms used in "
             "international transactions.")

    shipping_note = fields.Text(
        related='requisition_id.shipping_note',
        string='Delivery / Shipping Remarks')
    _sql_constraints = [
        ('name_uniq',
         'unique(name)',
         'Logistics Requisition Line number must be unique!'),
    ]

    @api.multi
    def name_get(self):
        """
        Returns a list of tupples containing id, name.
        result format: {[(id, name), (id, name), ...]}
        """
        res = []
        for line in self:
            name = "%s - %s" % (line.requisition_id.name, line.name)
            res.append((line.id, name))
        return res

    @api.model
    def create(self, vals):
        if (vals.get('name') or '/') == '/':
            seq_obj = self.env['ir.sequence']
            vals['name'] = seq_obj.get('logistic.requisition.line') or '/'
        return super(LogisticsRequisitionLine, self).create(vals)

    @api.multi
    def _prepare_source(self, qty=None):
        """Prepare data dict for source line creation.
        If it's a stockable product we'll go to tender
        by setting sourcing_method as 'procurement'.
        Finally mark the rest as 'other'.
        Those are default value that can be changed afterward
        by the user.

        :param self: record set of origin requistion.line
        :param qty: quantity to be set on source line

        :returns: dict to be used by Model.create

        """
        return {
            'proposed_product_id': self.product_id.id,
            'requisition_line_id': self.id,
            'proposed_uom_id': self.requested_uom_id.id,
            'unit_cost': 0.0,
            'proposed_qty': qty,
            'price_is': 'fixed',
        }

    @api.multi
    def _prepare_duplicated_bid_data(self):
        return {
            'dest_address_id': self.consignee_shipping_id.id,
            }

    @api.multi
    def _generate_default_source(self, force_qty=None):
        """Generate a source line from a requisition line, see
        _prepare_source for details.

        :param self: record set of origin requistion.line

        :param force_qty: if set this quantity will be used instead
        of requested quantity
        :returns: record set of generated source line

        """
        qty = force_qty if force_qty else self.requested_qty
        src_model = self.env['logistic.requisition.source']
        is_product = self.product_id.type == 'product'
        vals = self._prepare_source(qty=qty)

        sourcing_method = 'procurement' if is_product else 'other'
        vals['sourcing_method'] = sourcing_method

        return src_model.create(vals)

    @api.multi
    def _generate_sources(self):
        """Generate one or n source line(s) per requisition line.

        By default we generate only one source line using tender or other
        sourcing method.

        :param self: record set of origin requistion.line

        """
        self.ensure_one()
        if self.source_ids:
            return
        self._generate_default_source()

    @api.one
    def _do_confirm(self):
        self.state = 'confirmed'
        self._generate_sources()

    @api.multi
    def _do_cancel(self):
        vals = {'state': 'cancel',
                'logistic_user_id': False}
        self.write(vals)
        # When all lines of a requisition are 'quoted' or 'cancel',
        # it should be done, so try to change the state
        self.mapped('requisition_id')._do_done()

    @api.one
    def _do_sourced(self):
        errors = []
        if not self.source_ids:
            raise exceptions.Warning(_('Incorrect Sourcing'),
                                     _('No Sourcing Lines'))
        for source in self.source_ids:
            errors += source._check_sourcing()
        if errors:
            raise exceptions.Warning(_('Incorrect Sourcing'),
                                     '\n'.join(errors))
        self.state = 'sourced'

    @api.multi
    def _do_create_po_requisition(self):
        """ Create a single call for bid for all sourcing lines with
            sourcing_method = 'procurement' contained
            in the Line
        """
        sources = self.mapped('source_ids')
        pricelist = self[0].requisition_id.pricelist_id or None
        return sources._action_create_po_requisition(pricelist=pricelist)

    @api.one
    def _do_draft(self):
        self.state = 'draft'

    @api.multi
    def _do_assign(self):
        to_assigned = self.browse()
        for line in self:
            if line.state == 'confirmed' and line.logistic_user_id:
                to_assigned |= line
        for line in to_assigned:
            line.state = 'assigned'

    @api.multi
    def _do_quoted(self):
        self.write({'state': 'quoted'})
        # When all lines of a requisition are 'quoted' or 'cancel, it should be
        # done, so try to change the state
        self.mapped('requisition_id')._do_done()

    @api.multi
    def _store_get_requisition_ids(self):
        return list(set([line.requisition_id.id for line in self]))

    @api.multi
    @api.depends('requisition_id')
    def _get_display_requisition_id(self):
        """ Return the requisition if we are not creating a new
        requisition line in form view. Otherwise we let the field
        empty as NewId is not jsonisable
        """
        for line in self:

            if not isinstance(line.id, models.NewId):
                line.display_requisition_id = line.requisition_id

    @api.one
    @api.depends('source_ids.total_cost')
    def _get_total_cost(self):
        total_cost = 0.0
        for source_line in self.source_ids:
            total_cost += source_line.total_cost
        self.amount_total = total_cost

    @api.multi
    def _stock_count(self):
        self.stock_count = self.product_id.qty_available

    @api.model
    def _get_act_window_dict(self, name):
        mod_obj = self.env['ir.model.data']
        action = mod_obj.xmlid_to_object(name, raise_if_not_found=True)
        action_dict = action.read()[0]
        return action_dict

    @api.multi
    def action_view_stock(self):
        self.ensure_one()
        action_dict = self._get_act_window_dict('stock.product_open_quants')
        action_dict['domain'] = [('product_id', '=', self.product_id.id)]
        action_dict['context'] = {'search_default_locationgroup': 1,
                                  'search_default_ownergroup': 1,
                                  'search_default_internal_loc': 1}
        return action_dict

    @api.model
    def _message_get_auto_subscribe_fields(self, updated_fields,
                                           auto_follow_fields=None):
        """ Returns the list of relational fields linking to res.users that
            should trigger an auto subscribe. The default list checks for the
            fields
            - called 'user_id'
            - linking to res.users
            - with track_visibility set
            We override it here to add logistic_user_id to the list
        """
        if auto_follow_fields is None:
            auto_follow_fields = ['user_id']

        fields_to_follow = ['logistic_user_id']
        fields_to_follow += auto_follow_fields
        return super(LogisticsRequisitionLine, self
                     )._message_get_auto_subscribe_fields(
            updated_fields,
            auto_follow_fields=fields_to_follow
            )

    @api.multi
    def _send_note_to_logistic_user(self):
        """Post a message to warn the user that a new
        line has been associated."""
        for line in self:
            subject = (_("Logistics Requisition Line %s Assigned") %
                       (line.requisition_id.name + '/' + str(line.id)))
            details = (_("This new requisition concerns %s "
                         "and is due for %s.") %
                       (line.description, line.date_delivery))
            line.message_post(body=details,
                              subject=subject,
                              subtype='mail.mt_comment')

    @api.multi
    def write(self, vals):
        """ Send a message to the user when it is assigned
        and move the state's line to assigned.
        """
        res = super(LogisticsRequisitionLine, self).write(vals)
        assignee_changed = vals.get('logistic_user_id')
        state_changed = vals.get('state')
        if assignee_changed:
            self._send_note_to_logistic_user()
        if assignee_changed or state_changed:
            # Retry to assign at each change of assignee or state
            # because we can assign someone when a line is in draft but
            # the state change only when the state is confirmed AND have
            # an assignee
            self._do_assign()
        return res

    @api.onchange('product_id')
    def onchange_product_id(self):
        """ Changes UoM and name if product_id changes.
        @param name: Name of the field
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
        if self.product_id:
            self.requested_uom_id = self.product_id.uom_id
            self.description = self.product_id.name_get()[0][1]
        else:
            self.requested_uom_id = ''

    @api.multi
    def button_create_cost_estimate(self):
        ref = 'logistic_requisition.action_logistic_requisition_cost_estimate'
        action = self.env['ir.model.data'].xmlid_to_object(ref)
        return action.read()[0]

    @api.multi
    def button_sourced(self):
        self._do_sourced()
        return True

    @api.multi
    def button_create_po_requisition(self):
        """ Create a single purchase requisition for selected requisition lines
        Then open the created purchase requisition
        """
        purch_req = self._do_create_po_requisition()
        source_model = self.env['logistic.requisition.source']
        return source_model.open_po_requisition(purch_req)

    @api.model
    def _open_cost_estimate(self):
        return {
            'name': _('Cost Estimate'),
            'view_mode': 'form',
            'res_model': 'sale.order',
            'res_id': self.cost_estimate_id.id,
            'target': 'current',
            'view_id': False,
            'context': {},
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def button_open_cost_estimate(self):
        self.ensure_one()
        return self._open_cost_estimate()

    @api.multi
    def button_cancel(self):
        self._do_cancel()
        return True

    @api.multi
    def button_reset(self):
        self._do_confirm()
        return True


class LogisticsRequisitionSource(models.Model):
    _name = "logistic.requisition.source"
    _description = "Logistics Requisition Source"
    _inherit = ['mail.thread']

    PRICE_IS_SELECTION = [('fixed', 'Fixed'),
                          ('estimated', 'Estimated'),
                          ]

    SOURCED_STATES = {'sourced': [('readonly', True)],
                      'quoted': [('readonly', True)]
                      }

    @api.multi
    def _default_source_address(self):
        """Return the default source address
        depending of the procurment method

        """
        for line in self:
            address = False
            if line.sourcing_method == 'wh_dispatch':
                loc = line.location_partner_id
                if loc:
                    address = loc.id
            else:
                sup = line.supplier_partner_id
                if sup:
                    address = sup.id
            line.default_source_address = address

    @api.depends('po_requisition_id',
                 'proposed_product_id',
                 'sourcing_method')
    @api.one
    def _get_selectable_purchase_req_ids(self):
        purchase_reqs = False
        if (self.sourcing_method == 'reuse_bid' and self.proposed_product_id):
            domain = [('requisition_id.state', 'in', ('done', 'closed')),
                      ('product_id', '=', self.proposed_product_id.id)]
            p_req_lines = self.env['purchase.requisition.line'].search(domain)
            purchase_reqs = p_req_lines.mapped('requisition_id')
        self.selectable_purchase_req_ids = (purchase_reqs.ids if purchase_reqs
                                            else False)

    @api.depends('po_requisition_id',
                 'proposed_product_id',
                 'sourcing_method')
    @api.one
    def _get_selectable_bid_line_ids(self):
        bid_lines = False
        if (self.sourcing_method == 'reuse_bid' and self.po_requisition_id and
                self.proposed_product_id):
            domain = [
                ('order_id.requisition_id', '=', self.po_requisition_id.id),
                ('product_id', '=', self.proposed_product_id.id),
                ('order_id.state', '=', 'bid_selected'),
                ('order_id.dest_address_id', '=',
                 self.consignee_shipping_id.id),
            ]
            bid_lines = self.env['purchase.order.line'].search(domain)
        self.selectable_bid_line_ids = (bid_lines.ids if bid_lines
                                        else False)

    name = fields.Char(
        'Source Name',
        readonly=True,
        copy=False,
        default='/')
    requisition_line_id = fields.Many2one(
        'logistic.requisition.line',
        string='Requisition Line',
        readonly=True,
        required=True,
        ondelete='cascade')
    requisition_id = fields.Many2one(
        related='requisition_line_id.requisition_id',
        comodel_name='logistic.requisition',
        string='Logistics Requisition',
        store=True,
        readonly=True)
    state = fields.Selection(
        related='requisition_line_id.state',
        selection=LogisticsRequisitionLine.STATES,
        string='Line\'s State',
        readonly=True)
    proposed_product_id = fields.Many2one(
        'product.product',
        string='Proposed Product',
        states=SOURCED_STATES,
        required=True)
    proposed_uom_id = fields.Many2one(
        'product.uom',
        string='Proposed UoM',
        states=SOURCED_STATES)
    proposed_qty = fields.Float(
        'Proposed Qty',
        states=SOURCED_STATES,
        digits=dp.get_precision('Product UoM'),
        default=1)
    sourcing_method = fields.Selection(
        [('procurement', 'Go to Tender'),
         ('reuse_bid', 'Use Existing Bid'),
         ('wh_dispatch', 'Warehouse Dispatch'),
         ('fw_agreement', 'Framework Agreement'),
         ('other', 'Other'),
         ],
        string='Sourcing Method',
        required=True,
        states=SOURCED_STATES,
        default='other',
        oldname='procurement_method')
    dispatch_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Dispatch From',
        states=SOURCED_STATES)
    dispatch_location_id = fields.Many2one(
        related='dispatch_warehouse_id.lot_stock_id',
        comodel_name='stock.location',
        string='Dispatch Location',
        readonly=True,
        store=True)
    stock_owner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Stock owner')
    unit_cost = fields.Float(
        'Unit Cost',
        states=SOURCED_STATES,
        digits=dp.get_precision('Account'))
    total_cost = fields.Float(
        compute='_get_total_cost',
        string='Total Cost',
        digits=dp.get_precision('Account'),
        store=True)
    currency_id = fields.Many2one(
        related='requisition_line_id.requisition_id.currency_id',
        comodel_name='res.currency',
        string='Currency',
        readonly=True)
    price_is = fields.Selection(
        PRICE_IS_SELECTION,
        string='Price is',
        required=True,
        help="When the price is an estimation, the final price may change."
             " I.e. it is not based on a request for quotation.")
    #
    purchase_requisition_line_id = fields.Many2one(
        'purchase.requisition.line',
        'Purchase Requisition Line',
        ondelete='set null',
        readonly=True,
        copy=False)
    po_requisition_id = fields.Many2one(
        related='purchase_requisition_line_id.requisition_id',
        comodel_name='purchase.requisition',
        string='Purchase Requisition',
        readonly=True)
    # when filled, it means that it has been associated with a
    # bid order line during the split process
    selected_bid_line_id = fields.Many2one(
        'purchase.order.line',  # one2one relation with lr_source_line_id
        'Bid Selected Line',
        readonly=True,
        ondelete='restrict',
        copy=False)
    selected_bid_id = fields.Many2one(
        related='selected_bid_line_id.order_id',
        comodel_name='purchase.order',
        string='Selected Bid',
        readonly=True)
    purchase_line_id = fields.Many2one(
        compute='_get_purchase_line_id',
        comodel_name='purchase.order.line',
        readonly=True,
        string='Purchase Order Line')
    # needed to set the default destination address of the transport plan
    # when created from the lr line view
    consignee_shipping_id = fields.Many2one(
        related='requisition_line_id.requisition_id.consignee_shipping_id',
        comodel_name='res.partner',
        string='Delivery Address',
        readonly=True)
    # 2 fields below needed to set the default origin address
    # of the transport plan when created from the lr line view
    supplier_partner_id = fields.Many2one(
        related='selected_bid_line_id.order_id.partner_id',
        comodel_name='res.partner',
        string='Supplier Address',
        readonly=True)
    location_partner_id = fields.Many2one(
        related='dispatch_warehouse_id.partner_id',
        comodel_name='res.partner',
        string='Location Address',
        readonly=True)
    default_source_address = fields.Many2one(
        compute='_default_source_address',
        comodel_name='res.partner',
        string='Default source',
        readonly=True)

    # Procument Method = Other field
    origin = fields.Char("Origin")

    # domain limitation fields
    selectable_purchase_req_ids = fields.Many2many(
        comodel_name='purchase.order',
        compute='_get_selectable_purchase_req_ids',
    )
    selectable_bid_line_ids = fields.Many2many(
        comodel_name='purchase.requisition.line',
        compute='_get_selectable_bid_line_ids',
    )

    _constraints = [
        (lambda self, cr, uid, ids: self._check_purchase_requisition_unique(
            cr, uid, ids),
         "A call for bids cannot be linked to lines of different "
         "logistics requisitions.",
         ['po_requisition_id', 'requisition_id']),
    ]

    @api.multi
    def _check_sourcing_procurement(self):
        """Check sourcing for "procurement" method.

        :returns: list of error strings

        """
        if not self.po_requisition_id:
            return [_('{0}: Missing Purchase Requisition').format(self.name)]
        if self.po_requisition_id.state not in ['done', 'closed']:
            return [_('{0}: Purchase Requisition state should be '
                      '"Bids Selected" or "PO Created"').format(self.name)]
        return []

    @api.multi
    def _check_sourcing_reuse_bid(self):
        """Check sourcing for "reuse_bid" method.

        :returns: list of error strings

        """
        if not self.selected_bid_line_id:
            return [_('{0}: No bid line selected').format(self.name)]
        return []

    @api.multi
    def _check_sourcing_other(self):
        """Check sourcing for "other" method.

        :returns: list of error strings

        """
        return []

    @api.multi
    def _check_sourcing_wh_dispatch(self):
        """Check sourcing for "warehouse dispatch" method.

        :returns: list of error strings

        """
        return []

    @api.multi
    def _check_sourcing(self):
        """Check sourcing for all methods.

        Delegates to methods _check_sourcing_ + sourcing_method.

        :returns: list of error strings

        """
        self.ensure_one()
        if not self.proposed_qty:
            raise exceptions.Warning(_('Incorrect Sourcing'),
                                     _("Invalid source with a zero quantity."))
        if not self.unit_cost:
            raise exceptions.Warning(_('Incorrect Sourcing'),
                                     _("Invalid source with product cost at"
                                       " zero."))
        callable_name = "_check_sourcing_%s" % self.sourcing_method
        return getattr(self, callable_name)()

    @api.multi
    def _check_purchase_requisition_unique(self):
        for line in self:
            requisition_id = False
            if not line.po_requisition_id:
                continue
            for pr_line in line.po_requisition_id.line_ids:
                for source in pr_line.logistic_requisition_source_ids:
                    line = source.requisition_line_id
                    if not requisition_id:
                        requisition_id = line.requisition_id
                    elif requisition_id != line.requisition_id:
                        return False
        return True

    @api.multi
    def _get_purchase_line_id(self):
        """ For each line, returns the generated purchase line from the
        purchase requisition.
        """
        po_line_model = self.env['purchase.order.line']
        for line in self:
            po_line_id = False
            if line.selected_bid_line_id:
                bid_line = line.selected_bid_line_id
                if not bid_line:
                    continue
                po_line = bid_line.po_line_from_bid_ids
                if not po_line:
                    continue
            else:
                domain = [
                    ('lr_source_line_id', '=', line.id),
                    ('state', '!=', 'cancel')
                ]
                po_line = po_line_model.search(domain)
            # We should not have several purchase order lines "
            # for a logistic requisition line")
            if po_line:
                po_line.ensure_one()
                po_line_id = po_line.id
            line.purchase_line_id = po_line_id

    @api.model
    def create(self, vals):
        if (vals.get('name') or '/') == '/':
            seq_obj = self.env['ir.sequence']
            vals['name'] = seq_obj.get('logistic.requisition.source') or '/'
        return super(LogisticsRequisitionSource, self).create(vals)

    @api.model
    def _get_purchase_pricelist_from_currency(self, currency_id):
        """ This method will look for a pricelist of type 'purchase' using
        the same currency than than the given one.
        return : ID of product.pricelist type Integer
        """
        pricelist = self.env['product.pricelist'].search(
            [('currency_id', '=', currency_id),
             ('type', '=', 'purchase')],
            limit=1)
        return pricelist

    @api.multi
    def _prepare_po_requisition(self, purch_req_lines,
                                pricelist=None):
        company_id = None
        user_id = None
        consignee_id = None
        dest_address_id = None
        origin = []
        for line in self:
            origin.append(line.name)
            line_user_id = line.requisition_line_id.logistic_user_id.id
            if user_id is None:
                user_id = line_user_id
            elif user_id != line_user_id:
                raise except_orm(
                    _('Error'),
                    _('The lines are not assigned to the same '
                      'User.'))
            line_company_id = line.requisition_id.company_id.id
            if company_id is None:
                company_id = line_company_id
            elif company_id != line_company_id:
                raise except_orm(
                    _('Error'),
                    _('The sourcing lines do not belong to the same company.'))
            line_consignee_id = line.requisition_id.consignee_id.id
            if consignee_id is None:
                consignee_id = line_consignee_id
            elif consignee_id != line_consignee_id:
                raise except_orm(
                    _('Error'),
                    _('The sourcing lines do not have the same consignee.'))
            line_dest_address_id = line.requisition_id.consignee_shipping_id.id
            if dest_address_id is None:
                dest_address_id = line_dest_address_id
            elif dest_address_id != line_dest_address_id:
                raise except_orm(
                    _('Error'),
                    _('The sourcing lines do not have the '
                      'same delivery address.'))
            if pricelist is None:
                line_pricelist = self._get_purchase_pricelist_from_currency(
                    line.requisition_id.pricelist_id.currency_id.id)
                pricelist = line_pricelist
        return {'user_id': user_id or self.env.uid,
                'company_id': company_id,
                'consignee_id': consignee_id,
                'dest_address_id': dest_address_id,
                'line_ids': [(0, 0, rline) for rline in purch_req_lines],
                'origin': ", ".join(origin),
                'req_incoterm_id': line.requisition_id.incoterm_id.id,
                'req_incoterm_address': line.requisition_id.incoterm_address,
                'pricelist_id': pricelist.id,
                'schedule_date': line.requisition_id.date_delivery,
                }

    @api.multi
    def _prepare_po_requisition_line(self):
        """ Prepare values to create a purchase requisition line from
        a logistics requisition source """
        self.ensure_one()
        if self.po_requisition_id:
            raise except_orm(
                _('Existing'),
                _('The logistic requisition sourcing line %s is '
                  'already linked to a Purchase Requisition.') % self.name)
        if not self.proposed_product_id:
            raise except_orm(
                _('Missing information'),
                _('The sourcing line %d '
                  'does not have any product defined, '
                  'please choose one.') % self.id)
        return {'product_id': self.proposed_product_id.id,
                'product_uom_id': self.proposed_uom_id.id,
                'product_qty': self.proposed_qty,
                'schedule_date': self.requisition_line_id.date_delivery,
                'logistic_requisition_source_ids': [(4, self.id)],
                }

    @api.multi
    def _prepare_duplicated_bid_line_data(self, po_line):
        lrl = self.requisition_line_id
        data = {'date_planned': lrl.date_delivery}
        if self.proposed_product_id == po_line.product_id:
            data['product_qty'] = self.proposed_qty
        return data

    @api.multi
    def _action_create_po_requisition(self, pricelist=None):
        tender_sources = self.filtered(
            lambda s: s.sourcing_method == 'procurement'
        )
        if not tender_sources:
            raise except_orm(_('There should be at least one selected'
                               ' line with procurement method Procurement'),
                             _('Please correct selection'))
        tender_lines = [s._prepare_po_requisition_line()
                        for s in tender_sources]
        tender_vals = tender_sources._prepare_po_requisition(
            tender_lines, pricelist=pricelist)
        purch_req = self.env['purchase.requisition'].create(tender_vals)
        purch_req.onchange_dest_address_id()  # set the correct picking type
        tender_sources.write({'po_requisition_id': purch_req.id})
        return purch_req

    @api.multi
    def action_create_po_requisition(self):
        """ Create a single purchase requisition for selected requisition
        sources
        Then open the created purchase requisition
        """
        purch_req = self._action_create_po_requisition()
        return self.open_po_requisition(purch_req)

    @api.multi
    def open_po_requisition(self, purch_req=None):
        if not purch_req:
            purch_req = self.po_requisition_id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Requisition'),
            'res_model': 'purchase.requisition',
            'res_id': purch_req.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'nodestroy': True,
        }

    @api.multi
    def action_open_po_requisition(self):
        """Method called from view"""
        return self.open_po_requisition()

    @api.multi
    @api.depends('unit_cost', 'proposed_qty')
    def _get_total_cost(self):
        for line in self:
            line.total_cost = line.unit_cost * line.proposed_qty

    @api.onchange('dispatch_warehouse_id')
    def onchange_dispatch_warehouse_id(self):
        """ Get the address of the warehouse and write it in the
        location_partner_id field, this field is a related read-only, so
        this change will never be submitted to the server. But it is
        necessary to set the default "from address" of the transport
        plan in the context.
        """
        warehouse_partner_id = False
        if self.dispatch_warehouse_id:
            warehouse = self.dispatch_warehouse_id
            warehouse_partner_id = warehouse.partner_id.id
        self.location_partner_id = warehouse_partner_id

    @api.onchange('selected_bid_id')
    def onchange_selected_bid_id(self):
        # FIXME: don't understand
        """ Get the address of the supplier and write it in the
        supplier_partner_id field, this field is a related read-only, so
        this change will never be submitted to the server. But it is
        necessary to set the default "from address" of the transport
        plan in the context.
        """
        supplier_partner_id = False
        if self.selected_bid_id:
            purchase = self.selected_bid_id
            supplier_partner_id = purchase.partner_id.id
        self.supplier_partner_id = supplier_partner_id

    @api.onchange('sourcing_method')
    def onchange_sourcing_method(self):
        """ Set `price_is` to fixed when reusing a bid
        """
        self.price_is = ('fixed' if self.sourcing_method == 'reuse_bid'
                         else False)

    @api.onchange('po_requisition_id')
    def onchange_po_requisition_id(self):
        """ Empty selected_bid_line when po_requisition_id is manually changed
        """
        self.selected_bid_line_id = False

    @api.onchange('selected_bid_line_id')
    def onchange_selected_bid_line_id(self):
        """ Copy unit cost from bid line """
        unit_cost = 0.0
        to_curr = self.currency_id
        from_curr = self.selected_bid_line_id.order_id.pricelist_id.currency_id
        if from_curr:
            unit_cost = from_curr.compute(self.selected_bid_line_id.price_unit,
                                          to_curr, round=False)
        self.unit_cost = unit_cost
