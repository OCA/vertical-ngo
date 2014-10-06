# -*- coding: utf-8 -*-
#
#
#    Author: Joël Grand-Guillaume, Jacques-Etienne Baudoux, Guewen Baconnier
#    Copyright 2013-2014 Camptocamp SA
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
import logging

from openerp import models, fields, api
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


class LogisticRequisition(models.Model):
    _name = "logistic.requisition"
    _description = "Logistic Requisition"
    _inherit = ['mail.thread']
    _order = "name desc"

    REQ_STATES = {'confirmed': [('readonly', True)],
                  'done': [('readonly', True)]
                  }

    @api.multi
    def get_partner_requisition(self):
        return (self.env['res.partner']
                ._store_get_requisition_ids(sfield='consignee_shipping_id'))

    name = fields.Char(
        'Reference',
        required=True,
        readonly=True,
        default='/')
    # Not intended to match OpenERP origin field convention.
    # Source comes from paper
    source_document = fields.Char(
        'Source Document',
        states=REQ_STATES)
    date = fields.Date(
        'Requisition Date',
        states=REQ_STATES,
        required=True,
        default=fields.Date.context_today)
    date_delivery = fields.Date(
        'Desired Delivery Date',
        states=REQ_STATES,
        required=True)
    user_id = fields.Many2one(
        'res.users',
        'Business Unit Officer',
        required=True,
        states=REQ_STATES,
        help="Mobilization Officer or Logistic Coordinator "
             "in charge of the Logistic Requisition",
        default=lambda self: self.env.uid)
    partner_id = fields.Many2one(
        'res.partner',
        'Customer',
        required=True,
        domain=[('customer', '=', True)],
        states=REQ_STATES)
    consignee_id = fields.Many2one(
        'res.partner', 'Consignee',
        states=REQ_STATES)
    consignee_shipping_id = fields.Many2one(
        'res.partner', 'Delivery Address',
        states=REQ_STATES)
    country_id = fields.Many2one(
        related='consignee_shipping_id.country_id',
        comodel_name='res.country',
        string='Country',
        select=True,
        readonly=True,
        store=True)
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
    cost_estimate_only = fields.Boolean(
        'Cost Estimate Only',
        states=REQ_STATES,
        default=False)
    note = fields.Text('Remarks/Description')
    shipping_note = fields.Text('Delivery / Shipping Remarks')
    incoterm_id = fields.Many2one(
        'stock.incoterms',
        'Incoterm',
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
        states={'done': [('readonly', True)]})
    state = fields.Selection(
        [('draft', 'Draft'),
         ('confirmed', 'Confirmed'),
         ('done', 'Done'),
         ('cancel', 'Cancelled'),
         ],
        string='State',
        readonly=True,
        required=True,
        default='draft')
    sourced = fields.Float(
        compute='_get_sourced',
        string='Sourced')
    pricelist_id = fields.Many2one(
        'product.pricelist',
        'Pricelist',
        required=True,
        states=REQ_STATES,
        help="Pricelist that represent the currency for current logistic "
             "request.")
    # ValueError: Wrong value for logistic.requisition.currency_id:
    # res.currency() on create
    currency_id = fields.Many2one(
        related='pricelist_id.currency_id',
        comodel_name='res.currency',
        string='Currency',
        readonly=True)
    cancel_reason_id = fields.Many2one(
        'logistic.requisition.cancel.reason',
        string='Reason for Cancellation',
        ondelete='restrict',
        readonly=True)

    _sql_constraints = [
        ('name_uniq',
         'unique(name)',
         'Logistic Requisition Reference must be unique!'),
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
        to_dones = self.browse()
        for req in self:
            if all(line.state == 'quoted' for line in req.line_ids):
                to_dones |= req
        to_dones.state = 'done'

    @api.model
    def create(self, vals):
        if (vals.get('name') or '/') == '/':
            seq_obj = self.env['ir.sequence']
            vals['name'] = seq_obj.get('logistic.requisition') or '/'
        return super(LogisticRequisition, self).create(vals)

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'state': 'draft',
            'name': '/',
        })
        return super(LogisticRequisition, self
                     ).copy(cr, uid, id, default=default, context=context)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """We take the pricelist of the chosen partner"""
        pricelist = False
        if self.partner_id:
            partner = self.partner_id
            pricelist = partner.property_product_pricelist
        self.pricelist_id = pricelist

    @api.onchange('consignee_id')
    def onchange_consignee_id(self):
        if not self.consignee_id:
            self.consignee_shipping_id = False
            return

        addr = self.consignee_id.address_get(['delivery'])
        self.consignee_shipping_id = addr['delivery']

    @api.multi
    def button_confirm(self):
        self._do_confirm()
        return True

    @api.multi
    def button_create_cost_estimate(self):
        ref = 'logistic_requisition.action_logistic_requisition_cost_estimate'
        action = self.env['ir.model.data'].xmlid_to_object(ref)
        if action is None:
            action = self.env['ir.actions.act_window'].browse()
        return action.read()

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


class LogisticRequisitionLine(models.Model):
    _name = "logistic.requisition.line"
    _description = "Logistic Requisition Line"
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
        u'Line N°',
        readonly=True,
        default='/')
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
             "Logistic Requisition Line")
    product_id = fields.Many2one('product.product', 'Product',
                                 states=REQUEST_STATES)
    description = fields.Char('Description',
                              states=REQUEST_STATES,
                              required=True)
    requested_qty = fields.Float(
        'Quantity',
        states=REQUEST_STATES,
        digits_compute=dp.get_precision('Product UoM'),
        default=1.0)
    requested_uom_id = fields.Many2one('product.uom',
                                       'Product UoM',
                                       states=REQUEST_STATES,
                                       required=True)
    amount_total = fields.Float(
        compute='_get_total_cost',
        string='Total Amount',
        digits_compute=dp.get_precision('Account'),
        store=True)
    date_delivery = fields.Date(
        'Desired Delivery Date',
        states=REQUEST_STATES,
        required=True
    )
    country_id = fields.Many2one(
        related='requisition_id.country_id',
        string='Country',
        comodel_name='res.country',
        readonly=True)
    cost_estimate_only = fields.Boolean(
        related='requisition_id.cost_estimate_only',
        string='Cost Estimate Only',
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
        default='draft'
    )
    currency_id = fields.Many2one(
        related='requisition_id.currency_id',
        comodel_name='res.currency',
        string='Currency',
        readonly=True)
    note = fields.Text('Notes')
    activity_code = fields.Char('Activity Code', size=32)
    account_code = fields.Char('Account Code', size=32)
    account_id = fields.Many2one(
        related='product_id.property_account_income',
        string='Nominal Account',
        comodel_name='account.account',
        readonly=True)
    cost_estimate_id = fields.Many2one(
        'sale.order',
        string='Cost Estimate',
        readonly=True)

    _sql_constraints = [
        ('name_uniq',
         'unique(name)',
         'Logistic Requisition Line number must be unique!'),
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
        return super(LogisticRequisitionLine, self).create(vals)

    @api.one
    def _do_confirm(self):
        self.state = 'confirmed'

    @api.multi
    def _do_cancel(self):
        vals = {'state': 'cancel',
                'logistic_user_id': False}
        self.write(vals)

    @api.one
    def _do_sourced(self):
        for source in self.source_ids:
            if not source._is_sourced():
                raise except_orm(
                    _('line %s is not sourced') % source.name,
                    _('Please create source ressource using'
                      ' various source line actions'))
        self.state = 'sourced'

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
        req_ids = list(set(line.requisition_id.id for line in self))
        for line in self:
            line.state = 'quoted'
        # When all lines of a requisition are 'quoted', it should be
        # done, so try to change the state
        reqs = self.env['logistic.requisition'].browse(req_ids)
        reqs._do_done()

    @api.multi
    def _store_get_requisition_ids(self):
        return list(set([line.requisition_id.id for line in self]))

    @api.multi
    def _get_total_cost(self):
        for line in self:
            total_cost = 0.0
            for source_line in line.source_ids:
                total_cost += source_line.total_cost
            line.amount_total = total_cost

    @api.multi
    def view_stock_by_location(self):
        self.ensure_one()
        return {
            'name': _('Stock by Location'),
            'view_mode': 'tree',
            'res_model': 'stock.location',
            'target': 'current',
            'view_id': False,
            'context': {'product_id': self.product_id.id},
            'domain': [('usage', '=', 'internal')],
            'type': 'ir.actions.act_window',
        }

    @api.multi
    def view_price_by_location(self):
        self.ensure_one()
        # price_obj = self.env['product.pricelist']
        ctx = {"search_default_name": self.product_id.name}
        # if line.dispatch_location_id:
        #     price_l_id = price_obj.search(
        #         cr, uid,
        #         [('name', 'like', self.dispatch_location_id.name)],
        #         context=context)
        #     ctx['pricelist'] = price_l_id
        return {
            'name': _('Prices for location'),
            'view_mode': 'tree',
            'res_model': 'product.product',
            'target': 'current',
            'view_id': False,
            'context': ctx,
            'domain': [('id', '=', self.product_id.id)],
            'type': 'ir.actions.act_window',
        }

    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        std_default = {
            'logistic_user_id': False,
            'name': False,
            'cost_estimate_id': False,
            'source_ids': False,
        }
        std_default.update(default)
        return super(LogisticRequisitionLine, self).copy_data(
            cr, uid, id, default=std_default, context=context)

    @api.model
    def _message_get_auto_subscribe_fields(self, updated_fields,
                                           auto_follow_fields=['user_id']):
        """ Returns the list of relational fields linking to res.users that
            should trigger an auto subscribe. The default list checks for the
            fields
            - called 'user_id'
            - linking to res.users
            - with track_visibility set
            We override it here to add logistic_user_id to the list
        """
        fields_to_follow = ['logistic_user_id']
        fields_to_follow += auto_follow_fields
        return super(LogisticRequisitionLine, self
                     )._message_get_auto_subscribe_fields(
            updated_fields,
            auto_follow_fields=fields_to_follow
            )

    @api.multi
    def _send_note_to_logistic_user(self):
        """Post a message to warn the user that a new
        line has been associated."""
        for line in self:
            subject = (_("Logistic Requisition Line %s Assigned") %
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
        res = super(LogisticRequisitionLine, self).write(vals)
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
        if action is None:
            action = self.env['ir.actions.act_window'].browse()
        return action.read()

    @api.multi
    def button_sourced(self):
        self._do_sourced()
        return True

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


class LogisticRequisitionSource(models.Model):
    _name = "logistic.requisition.source"
    _description = "Logistic Requisition Source"
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
            if line.procurement_method == 'wh_dispatch':
                loc = line.location_partner_id
                if loc:
                    address = loc.id
            else:
                sup = line.supplier_partner_id
                if sup:
                    address = sup.id
            line.default_source_address = address

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
        string='Logistic Requisition',
        store=True,
        readonly=True)
    state = fields.Selection(
        related='requisition_line_id.state',
        selection=LogisticRequisitionLine.STATES,
        string='Line\'s State',
        readonly=True)
    proposed_product_id = fields.Many2one(
        'product.product',
        string='Proposed Product',
        states=SOURCED_STATES)
    proposed_uom_id = fields.Many2one(
        'product.uom',
        string='Proposed UoM',
        states=SOURCED_STATES)
    proposed_qty = fields.Float(
        'Proposed Qty',
        states=SOURCED_STATES,
        digits_compute=dp.get_precision('Product UoM'),
        default=1)
    procurement_method = fields.Selection(
        [('procurement', 'Procurement'),
         ('wh_dispatch', 'Warehouse Dispatch'),
         ('fw_agreement', 'Framework Agreement'),
         ('other', 'Other'),
         ],
        string='Procurement Method',
        required=True,
        states=SOURCED_STATES,
        default='other')
    dispatch_location_id = fields.Many2one(
        'stock.location',
        string='Dispatch From',
        states=SOURCED_STATES)
    stock_owner = fields.Many2one(
        related='dispatch_location_id.owner_id',
        relation='res.partner',
        string='Stock Owner',
        readonly=True)
    offer_ids = fields.One2many(
        'sale.order.line',
        'logistic_requisition_source_id',
        string='Sales Quotation Lines',
        readonly=True,
        copy=False)
    unit_cost = fields.Float(
        'Unit Cost',
        states=SOURCED_STATES,
        digits_compute=dp.get_precision('Account'))
    total_cost = fields.Float(
        compute='_get_total_cost',
        string='Total Cost',
        digits_compute=dp.get_precision('Account'),
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
             " I.e. it is not based on a request for quotation.",
        default='fixed')
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
        'Purchase Order Line',
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
        related='dispatch_location_id.partner_id',
        comodel_name='res.partner',
        string='Location Address',
        readonly=True)
    default_source_address = fields.Many2one(
        compute='_default_source_address',
        comodel_name='res.partner',
        string='Default source',
        readonly=True)

    _constraints = [
        (lambda self, cr, uid, ids: self._check_purchase_requisition_unique(
            cr, uid, ids),
         "A call for bids cannot be linked to lines of different "
         "logistics requisitions.",
         ['po_requisition_id', 'requisition_id']),
    ]

    def _is_sourced_procurement(self, source):
        """Predicate function to test if line on procurement
        method are sourced"""
        if (not source.po_requisition_id or
                source.po_requisition_id.state != 'closed'):
            return False
        return True

    @api.model
    def _is_sourced_other(self, source):
        """Predicate function to test if line on other
        method are sourced"""
        return self._is_sourced_procurement(source)

    @api.model
    def _is_sourced_wh_dispatch(self, source):
        """Predicate function to test if line on warehouse
        method are sourced"""
        return True

    @api.model
    def _is_sourced(self):
        """ check if line is source using predicate function
        that must be called _is_sourced_ + name of procurement.
        :returns: boolean True if sourced"""
        self.ensure_one()
        callable_name = "_is_sourced_%s" % self.procurement_method
        if not hasattr(self, callable_name):
            raise NotImplementedError(callable_name)
        callable_fun = getattr(self, callable_name)
        return callable_fun(self)

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
                po_lines = bid_line.po_line_from_bid_ids
                if not po_lines:
                    continue
            else:
                domain = [('lr_source_line_id', '=', line.id),
                          ('state', '!=', 'cancel')],
                po_line = po_line_model.search(domain)
            # We should not have several purchase order lines "
            # for a logistic requisition line")
            if po_line:
                po_line.ensure_one()
                po_line_id = po_line.id
            self.purchase_line_id = po_line_id

    @api.model
    def create(self, vals):
        if (vals.get('name') or '/') == '/':
            seq_obj = self.env['ir.sequence']
            vals['name'] = seq_obj.get('logistic.requisition.source') or '/'
        return super(LogisticRequisitionSource, self).create(vals)

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

    @api.model
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
    def _action_create_po_requisition(self, pricelist=None):
        purch_req_obj = self.env['purchase.requisition']
        purch_req_lines = []
        if not next((line for line in self
                     if line.procurement_method == 'procurement'), None):
            raise except_orm(_('There should be at least one selected'
                               ' line with procurement method Procurement'),
                             _('Please correct selection'))
        for line in self:
            if line.procurement_method not in ('other', 'procurement'):
                raise except_orm(_('Selected line procurement method should'
                                   ' be procurement or other'),
                                 _('Please correct selection'))
            line_vals = line._prepare_po_requisition_line()
            purch_req_lines.append(line_vals)
        vals = self._prepare_po_requisition(purch_req_lines,
                                            pricelist=pricelist)
        purch_req = purch_req_obj.create(vals)
        self.po_requisition_id = purch_req.id
        return purch_req

    @api.multi
    def action_create_po_requisition(self):
        self._action_create_po_requisition()
        return self.action_open_po_requisition()

    @api.multi
    def action_open_po_requisition(self):
        self.ensure_one()
        source = self
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Requisition'),
            'res_model': 'purchase.requisition',
            'res_id': source.po_requisition_id.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'nodestroy': True,
        }

    @api.multi
    def _get_total_cost(self):
        for line in self:
            line.total_cost = line.unit_cost * line.proposed_qty

    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        std_default = {
        }
        std_default.update(default)
        return super(LogisticRequisitionSource, self).copy_data(
            cr, uid, id, default=std_default, context=context)

    @api.onchange('dispatch_location_id')
    def onchange_dispatch_location_id(self):
        """ Get the address of the location and write it in the
        location_partner_id field, this field is a related read-only, so
        this change will never be submitted to the server. But it is
        necessary to set the default "from address" of the transport
        plan in the context.
        """
        location_partner_id = False
        if self.dispatch_location_id:
            location = self.dispatch_location_id
            location_partner_id = location.partner_id.id
        self.location_partner_id = location_partner_id

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
