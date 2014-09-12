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
import time

from openerp.osv import fields, orm
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT_FORMAT
import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class res_partner(orm.Model):
    _inherit = "res.partner"

    def _store_get_requisition_ids(self, cr, uid, ids, sfield, context=None):
        req_obj = self.pool.get('logistic.requisition')
        req_ids = req_obj.search(cr, uid, [(sfield, 'in', ids)], context=context)
        return req_ids


class logistic_requisition(orm.Model):
    _name = "logistic.requisition"
    _description = "Logistic Requisition"
    _inherit = ['mail.thread']
    _order = "name desc"

    REQ_STATES = {'confirmed': [('readonly', True)],
                  'done': [('readonly', True)]
                  }

    def get_partner_requisition(self, cr, uid, ids, context=None):
        model = self.pool['res.partner']
        return model._store_get_requisition_ids(cr, uid, ids, sfield='consignee_shipping_id', context=context)

    _columns = {
        'name': fields.char(
            'Reference',
            required=True,
            readonly=True),
        # Not intended to match OpenERP origin field convention.
        # Source comes from paper
        'source_document': fields.char(
            'Source Document',
            states=REQ_STATES,
        ),
        'date': fields.date(
            'Requisition Date',
            states=REQ_STATES,
            required=True
        ),
        'date_delivery': fields.date(
            'Desired Delivery Date',
            states=REQ_STATES,
            required=True
        ),
        'user_id': fields.many2one(
            'res.users', 'Business Unit Officer', required=True,
            states=REQ_STATES,
            help="Mobilization Officer or Logistic Coordinator "
                 "in charge of the Logistic Requisition"
        ),
        'partner_id': fields.many2one(
            'res.partner', 'Customer', required=True, domain=[('customer', '=', True)],
            states=REQ_STATES
        ),
        'consignee_id': fields.many2one(
            'res.partner', 'Consignee',
            states=REQ_STATES
        ),
        'consignee_shipping_id': fields.many2one(
            'res.partner', 'Delivery Address',
            states=REQ_STATES
        ),
        'country_id': fields.related(
            'consignee_shipping_id',
            'country_id',
            string='Country',
            type='many2one',
            relation='res.country',
            select=True,
            readonly=True,
            store={
                'logistic.requisition': (
                    lambda self, cr, uid, ids, c=None: ids,
                    ['consignee_shipping_id'], 10),
                'res.partner': (
                    get_partner_requisition,
                    ['country_id'], 10),
            }),
        'company_id': fields.many2one(
            'res.company',
            'Company',
            readonly=True,
        ),

        'analytic_id':  fields.many2one('account.analytic.account',
                                        'Project',
                                        states=REQ_STATES,
                                        ),
        'cost_estimate_only': fields.boolean(
            'Cost Estimate Only',
            states=REQ_STATES
        ),
        'preferred_transport': fields.many2one(
            'transport.mode',
            string='Preferred Transport',
            states=REQ_STATES
        ),
        'note': fields.text('Remarks/Description'),
        'shipping_note': fields.text('Delivery / Shipping Remarks'),
        'incoterm_id': fields.many2one(
            'stock.incoterms',
            'Incoterm',
            help="International Commercial Terms are a series of "
                 "predefined commercial terms used in international "
                 "transactions."),
        'incoterm_address': fields.char(
            'Incoterm Place',
            states=REQ_STATES,
            help="Incoterm Place of Delivery. "
                 "International Commercial Terms are a series of "
                 "predefined commercial terms used in "
                 "international transactions."),
        'line_ids': fields.one2many(
            'logistic.requisition.line',
            'requisition_id',
            'Products to Purchase',
            states={'done': [('readonly', True)]}
        ),
        'state': fields.selection(
            [('draft', 'Draft'),
             ('confirmed', 'Confirmed'),
             ('done', 'Done'),
             ('cancel', 'Cancelled'),
             ],
            string='State',
            readonly=True,
            required=True
        ),
        'sourced': fields.function(
            lambda self, *args, **kwargs: self._get_sourced(*args, **kwargs),
            string='Sourced',
            type='float'
        ),
        'pricelist_id': fields.many2one('product.pricelist',
            'Pricelist',
            required=True,
            states=REQ_STATES,
            help="Pricelist that represent the currency for current logistic request."),
        'currency_id': fields.related('pricelist_id',
                                      'currency_id',
                                      type='many2one',
                                      relation='res.currency',
                                      string='Currency',
                                      readonly=True),
        'cancel_reason_id': fields.many2one(
            'logistic.requisition.cancel.reason',
            string='Reason for Cancellation',
            ondelete='restrict',
            readonly=True),
    }

    _defaults = {
        'date': fields.date.context_today,
        'state': 'draft',
        'cost_estimate_only': False,
        'name': '/',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'logistic.request', context=c),
        'user_id': lambda self, cr, uid, ctx: uid,
    }

    _sql_constraints = [
        ('name_uniq',
         'unique(name)',
         'Logistic Requisition Reference must be unique!'),
    ]

    def _get_sourced(self, cr, uid, ids, name, args, context=None):
        res = {}
        for requisition in self.browse(cr, uid, ids, context=context):
            lines_len = sum(1 for req in requisition.line_ids
                            if req.state != 'cancel')
            sourced_len = sum(1 for req in requisition.line_ids
                              if req.state in ('sourced', 'quoted'))
            if lines_len == 0:
                percentage = 0.
            else:
                percentage = round(sourced_len / lines_len * 100, 2)
            res[requisition.id] = percentage
        return res

    def _store_get_requisition_line_ids(self, cr, uid, ids, context=None):
        req_line_obj = self.pool.get('logistic.requisition.line')
        line_ids = req_line_obj.search(cr, uid,
                                       [('requisition_id', 'in', ids)],
                                       context=context)
        return line_ids


    def _do_cancel(self, cr, uid, ids, reason_id, context=None):
        reqs = self.read(cr, uid, ids, ['line_ids'], context=context)
        line_ids = [lids for req in reqs for lids in req['line_ids']]
        if line_ids:
            line_obj = self.pool.get('logistic.requisition.line')
            line_obj._do_cancel(cr, uid, line_ids, context=context)
        vals = {'state': 'cancel',
                'cancel_reason_id': reason_id}
        self.write(cr, uid, ids, vals, context=context)

    def _do_confirm(self, cr, uid, ids, context=None):
        reqs = self.read(cr, uid, ids, ['line_ids'], context=context)
        line_ids = [lids for req in reqs for lids in req['line_ids']]
        if line_ids:
            line_obj = self.pool.get('logistic.requisition.line')
            line_obj._do_confirm(cr, uid, line_ids, context=context)
        self.write(cr, uid, ids, {'state': 'confirmed'}, context=context)

    def _do_draft(self, cr, uid, ids, context=None):
        reqs = self.read(cr, uid, ids, ['line_ids'], context=context)
        line_ids = [lids for req in reqs for lids in req['line_ids']]
        if line_ids:
            line_obj = self.pool.get('logistic.requisition.line')
            line_obj._do_draft(cr, uid, line_ids, context=context)
        vals = {'state': 'draft',
                'cancel_reason_id': False,
                }
        self.write(cr, uid, ids, vals, context=context)

    def _do_done(self, cr, uid, ids, context=None):
        done_ids = []
        for req in self.browse(cr, uid, ids, context=context):
            if all(line.state == 'quoted' for line in req.line_ids):
                done_ids.append(req.id)
        self.write(cr, uid, done_ids, {'state': 'done'}, context=context)

    def create(self, cr, uid, vals, context=None):
        if (vals.get('name') or '/') == '/':
            seq_obj = self.pool.get('ir.sequence')
            vals['name'] = seq_obj.get(cr, uid, 'logistic.requisition') or '/'
        return super(logistic_requisition, self).create(cr, uid, vals,
                                                        context=context)

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'state': 'draft',
            'name': '/',
        })
        return super(logistic_requisition, self).copy(cr, uid, id, default=default, context=context)

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        """We take the pricelist of the chosen partner"""
        values = {'pricelist_id': False}
        if not part:
            return {'value': values}

        part = self.pool.get('res.partner').browse(cr, uid, part,
                                                   context=context)
        pricelist = part.property_product_pricelist
        pricelist = pricelist.id if pricelist else False
        values = {}
        if pricelist:
            values['pricelist_id'] = pricelist
        return {'value': values}

    def onchange_consignee_id(self, cr, uid, ids, consignee_id, context=None):
        values = {'consignee_shipping_id': False}
        if not consignee_id:
            return {'value': values}

        partner_obj = self.pool.get('res.partner')
        partner = partner_obj.browse(cr, uid, consignee_id, context=context)
        addr = partner_obj.address_get(cr, uid,
                                       [partner.id], ['delivery'],
                                       context=context)
        values['consignee_shipping_id'] = addr['delivery']
        return {'value': values}

    def onchange_validate(self, cr, uid, ids, validate_id,
                          date_validate, date_field_name, context=None):
        values = {}
        if validate_id and not date_validate:
            values[date_field_name] = time.strftime(DT_FORMAT)
        return {'value': values}

    def button_confirm(self, cr, uid, ids, context=None):
        self._do_confirm(cr, uid, ids, context=context)
        return True

    def button_create_cost_estimate(self, cr, uid, ids, context=None):
        data_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        try:
            __, action_id = data_obj.get_object_reference(
                cr, uid, 'logistic_requisition',
                'action_logistic_requisition_cost_estimate')
        except ValueError:
            action_id = False
        return act_obj.read(cr, uid, action_id, context=context)

    def button_reset(self, cr, uid, ids, context=None):
        self._do_draft(cr, uid, ids, context=context)
        return True

    def button_view_lines(self, cr, uid, ids, context=None):
        """
        This function returns an action that display related lines.
        """
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        ref = mod_obj.get_object_reference(cr, uid, 'logistic_requisition',
                                           'action_logistic_requisition_line')
        action_id = ref[1] if ref else False
        action = act_obj.read(cr, uid, [action_id], context=context)[0]
        action['domain'] = str([('requisition_id', 'in', ids)])
        return action

    def button_view_source_lines(self, cr, uid, ids, context=None):
        """
        This function returns an action that display related sourcing lines.
        """
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        ref = mod_obj.get_object_reference(
            cr, uid, 'logistic_requisition',
            'action_logistic_requisition_source')
        action_id = ref[1] if ref else False
        action = act_obj.read(cr, uid, [action_id], context=context)[0]
        action['domain'] = str([('requisition_id', 'in', ids)])
        return action


class logistic_requisition_line(orm.Model):
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

    _columns = {
        'name': fields.char(u'Line N°', readonly=True),
        'requisition_id': fields.many2one(
            'logistic.requisition',
            'Requisition',
            readonly=True,
            required=True,
            ondelete='cascade'),
        'source_ids': fields.one2many(
            'logistic.requisition.source',
            'requisition_line_id',
            string='Source Lines',
            states={'sourced': [('readonly', True)],
                    'quoted': [('readonly', True)]}),
        'logistic_user_id': fields.many2one(
            'res.users',
            'Assigned To',
            states=REQUEST_STATES,
            # workaround for the following bug, preventing to
            # automatically subscribe the user to the line
            # https://bugs.launchpad.net/openobject-addons/+bug/1188538
            track_visibility='never',
            help="User in charge of the "
                 "Logistic Requisition Line"),
        'product_id': fields.many2one('product.product', 'Product',
                                      states=REQUEST_STATES),
        'description': fields.char('Description',
                                   states=REQUEST_STATES,
                                   required=True),
        'requested_qty': fields.float(
            'Quantity',
            states=REQUEST_STATES,
            digits_compute=dp.get_precision('Product UoM')),
        'requested_uom_id': fields.many2one('product.uom',
                                            'Product UoM',
                                            states=REQUEST_STATES,
                                            required=True),
        'amount_total': fields.function(
            lambda self, *args, **kwargs: self._get_total_cost(*args, **kwargs),
            string='Total Amount',
            type="float",
            digits_compute=dp.get_precision('Account'),
            store=True),
        'date_delivery': fields.date(
            'Desired Delivery Date',
            states=REQUEST_STATES,
            required=True
        ),
        'country_id': fields.related(
            'requisition_id',
            'country_id',
            string='Country',
            type='many2one',
            relation='res.country',
            readonly=True),
        'cost_estimate_only': fields.related(
            'requisition_id', 'cost_estimate_only',
            string='Cost Estimate Only',
            type='boolean',
            readonly=True,
            store={
                'logistic.requisition.line': (
                    lambda self, cr, uid, ids, c=None: ids,
                    ['requisition_id'], 10),
                'logistic.requisition': (
                    lambda self, *a, **kw: self._store_get_requisition_line_ids(*a, **kw),
                    ['cost_estimate_only'], 10),
                }
            ),
        'state': fields.selection(
            STATES,
            string='State',
            required=True,
            readonly=True,
            help="Draft: Created\n"
                 "Confirmed: Requisition has been confirmed\n"
                 "Assigned: Waiting the creation of a quote\n"
                 "Sourced: The line has been sourced from procurement or warehouse\n"
                 "Quoted: Quotation made for the line\n"
                 "Cancelled: The requisition has been cancelled"
        ),
        'currency_id': fields.related('requisition_id',
                                      'currency_id',
                                      type='many2one',
                                      relation='res.currency',
                                      string='Currency',
                                      readonly=True),
        'note': fields.text('Notes'),
        'activity_code': fields.char('Activity Code', size=32),
        'account_code': fields.char('Account Code', size=32),
        'account_id': fields.related(
            'product_id', 'property_account_income',
            string='Nominal Account',
            type='many2one',
            relation='account.account',
            readonly=True),
        'cost_estimate_id': fields.many2one(
            'sale.order',
            string='Cost Estimate',
            readonly=True),
    }

    _defaults = {
        'state': 'draft',
        'requested_qty': 1.0,
        'name': '/',
    }

    _sql_constraints = [
        ('name_uniq',
         'unique(name)',
         'Logistic Requisition Line number must be unique!'),
    ]

    def name_get(self, cr, user, ids, context=None):
        """
        Returns a list of tupples containing id, name.
        result format: {[(id, name), (id, name), ...]}
        """
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = []
        for line in self.browse(cr, user, ids, context=context):
            name = "%s - %s" % (line.requisition_id.name, line.name)
            res.append((line.id, name))
        return res

    def create(self, cr, uid, vals, context=None):
        if (vals.get('name') or '/') == '/':
            seq_obj = self.pool.get('ir.sequence')
            vals['name'] = seq_obj.get(cr, uid, 'logistic.requisition.line') or '/'
        return super(logistic_requisition_line, self).create(cr, uid, vals,
                                                             context=context)

    def _do_confirm(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'confirmed'}, context=context)

    def _do_cancel(self, cr, uid, ids, context=None):
        vals = {'state': 'cancel',
                'logistic_user_id': False}
        self.write(cr, uid, ids, vals, context=context)

    def _do_sourced(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            for source in line.source_ids:
                if not source._is_sourced():
                    raise orm.except_orm(_('line %s is not sourced') % source.name,
                                         _('Please create source ressource using'
                                           ' various source line actions'))
        self.write(cr, uid, ids, {'state': 'sourced'}, context=context)

    def _do_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'}, context=context)

    def _do_assign(self, cr, uid, ids, context=None):
        assigned_ids = []
        for line in self.browse(cr, uid, ids, context=context):
            if line.state == 'confirmed' and line.logistic_user_id:
                assigned_ids.append(line.id)
        if assigned_ids:
            self.write(cr, uid, assigned_ids,
                       {'state': 'assigned'},
                       context=context)

    def _do_quoted(self, cr, uid, ids, context=None):
        req_obj = self.pool.get('logistic.requisition')
        lines = self.browse(cr, uid, ids, context=context)
        req_ids = list(set(line.requisition_id.id for line in lines))
        self.write(cr, uid, ids, {'state': 'quoted'}, context=context)
        # When all lines of a requisition are 'quoted', it should be
        # done, so try to change the state
        req_obj._do_done(cr, uid, req_ids, context=context)

    def _store_get_requisition_ids(self, cr, uid, ids, context=None):
        reqs = self.read(cr, uid, ids, ['requisition_id'],
                         context=context, load='_classic_write')
        return list(set([x['requisition_id'] for x in reqs]))

    def _get_total_cost(self, cr, uid, ids, name, args, context=None):
        res = {}
        for i in ids:
            res[i] = 0.0
        for line in self.browse(cr, uid, ids, context=context):
            for source_line in line.source_ids:
                res[line.id] += source_line.total_cost
        return res

    def view_stock_by_location(self, cr, uid, ids, context=None):
        assert len(ids) == 1, "Expected only 1 ID"
        line = self.browse(cr, uid, ids[0], context=context)
        return {
            'name': _('Stock by Location'),
            'view_mode': 'tree',
            'res_model': 'stock.location',
            'target': 'current',
            'view_id': False,
            'context': {'product_id': line.product_id.id},
            'domain': [('usage', '=', 'internal')],
            'type': 'ir.actions.act_window',
        }

    def view_price_by_location(self, cr, uid, ids, context=None):
        assert len(ids) == 1, "Expected only 1 ID"
        price_obj = self.pool.get('product.pricelist')
        line = self.browse(cr, uid, ids[0], context=context)
        ctx = {"search_default_name": line.product_id.name}
        # if line.dispatch_location_id:
        #     price_l_id = price_obj.search(
        #         cr, uid,
        #         [('name', 'like', line.dispatch_location_id.name)],
        #         context=context)
        #     ctx['pricelist'] = price_l_id
        return {
            'name': _('Prices for location'),
            'view_mode': 'tree',
            'res_model': 'product.product',
            'target': 'current',
            'view_id': False,
            'context': ctx,
            'domain': [('id', '=', line.product_id.id)],
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
        return super(logistic_requisition_line, self).copy_data(
            cr, uid, id, default=std_default, context=context)

    def _message_get_auto_subscribe_fields(self, cr, uid, updated_fields,
                                           auto_follow_fields=['user_id'],
                                           context=None):
        """ Returns the list of relational fields linking to res.users that should
            trigger an auto subscribe. The default list checks for the fields
            - called 'user_id'
            - linking to res.users
            - with track_visibility set
            We override it here to add logistic_user_id to the list
        """
        fields_to_follow = ['logistic_user_id']
        fields_to_follow += auto_follow_fields
        return super(logistic_requisition_line, self)._message_get_auto_subscribe_fields(
            cr, uid, updated_fields,
            auto_follow_fields=fields_to_follow,
            context=context)

    def _send_note_to_logistic_user(self, cr, uid, ids, context=None):
        """Post a message to warn the user that a new
        line has been associated."""
        for line in self.browse(cr, uid, ids, context=context):
            subject = (_("Logistic Requisition Line %s Assigned") %
                       (line.requisition_id.name + '/' + str(line.id)))
            details = (_("This new requisition concerns %s "
                         "and is due for %s.") %
                       (line.description, line.date_delivery))
            self.message_post(cr, uid, [line.id], body=details,
                              subject=subject, subtype='mail.mt_comment',
                              context=context)

    def write(self, cr, uid, ids, vals, context=None):
        """ Send a message to the user when it is assigned
        and move the state's line to assigned.
        """
        res = super(logistic_requisition_line, self).write(cr, uid, ids,
                                                           vals,
                                                           context=context)
        assignee_changed = vals.get('logistic_user_id')
        state_changed = vals.get('state')
        if assignee_changed:
            self._send_note_to_logistic_user(cr, uid, ids, context=context)
        if assignee_changed or state_changed:
            # Retry to assign at each change of assignee or state
            # because we can assign someone when a line is in draft but
            # the state change only when the state is confirmed AND have
            # an assignee
            self._do_assign(cr, uid, ids, context=context)
        return res

    def onchange_product_id(self, cr, uid, ids, product_id, requested_uom_id, context=None):
        """ Changes UoM and name if product_id changes.
        @param name: Name of the field
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
        value = {'requested_uom_id': ''}
        if product_id:
            prod_obj = self.pool.get('product.product')
            prod = prod_obj.browse(cr, uid, product_id, context=context)
            value = {
                'requested_uom_id': prod.uom_id.id,
                'description': prod.name_get()[0][1]
            }
        return {'value': value}

    def button_create_cost_estimate(self, cr, uid, ids, context=None):
        data_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        try:
            __, action_id = data_obj.get_object_reference(
                cr, uid, 'logistic_requisition',
                'action_logistic_requisition_cost_estimate')
        except ValueError:
            action_id = False
        return act_obj.read(cr, uid, action_id, context=context)

    def button_sourced(self, cr, uid, ids, context=None):
        self._do_sourced(cr, uid, ids, context=context)
        return True

    def _open_cost_estimate(self, cr, uid, estimate_id, context=None):
        return {
            'name': _('Cost Estimate'),
            'view_mode': 'form',
            'res_model': 'sale.order',
            'res_id': estimate_id,
            'target': 'current',
            'view_id': False,
            'context': {},
            'type': 'ir.actions.act_window',
        }

    def button_open_cost_estimate(self, cr, uid, ids, context=None):
        assert len(ids) == 1, "Only 1 ID accepted"
        line = self.browse(cr, uid, ids[0], context=context)
        return self._open_cost_estimate(cr, uid,
                                        line.cost_estimate_id.id,
                                        context=context)

    def button_cancel(self, cr, uid, ids, context=None):
        self._do_cancel(cr, uid, ids, context=context)
        return True

    def button_reset(self, cr, uid, ids, context=None):
        self._do_confirm(cr, uid, ids, context=None)
        return True


class logistic_requisition_source(orm.Model):
    _name = "logistic.requisition.source"
    _description = "Logistic Requisition Source"
    _inherit = ['mail.thread']

    PRICE_IS_SELECTION = [('fixed', 'Fixed'),
                          ('estimated', 'Estimated'),
                          ]

    SOURCED_STATES = {'sourced': [('readonly', True)],
                      'quoted': [('readonly', True)]
                      }

    def _default_source_address(self, cr, uid, ids, field_name, arg, context=None):
        """Return the default source address depending of the procurment method"""
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = False
            if line.procurement_method == 'wh_dispatch':
                loc_id = line.location_partner_id.id if line.location_partner_id else False
                res[line.id] = loc_id
            else:
                sup_id = line.supplier_partner_id.id if line.supplier_partner_id else False
                res[line.id] = sup_id
            return res

    _columns = {
        'name': fields.char('Source Name', readonly=True),
        'requisition_line_id': fields.many2one(
            'logistic.requisition.line',
            string='Requisition Line',
            readonly=True,
            required=True,
            ondelete='cascade'),
        'requisition_id': fields.related(
            'requisition_line_id', 'requisition_id',
            type='many2one',
            relation='logistic.requisition',
            string='Logistic Requisition',
            store=True,
            readonly=True),
        'state': fields.related(
            'requisition_line_id', 'state',
            type='selection',
            selection=logistic_requisition_line.STATES,
            string='Line\'s State',
            readonly=True),
        'proposed_product_id': fields.many2one(
            'product.product',
            string='Proposed Product',
            states=SOURCED_STATES),
        'proposed_uom_id': fields.many2one(
            'product.uom',
            string='Proposed UoM',
            states=SOURCED_STATES),
        'proposed_qty': fields.float(
            'Proposed Qty',
            states=SOURCED_STATES,
            digits_compute=dp.get_precision('Product UoM')),
        'procurement_method': fields.selection(
            [('procurement', 'Procurement'),
             ('wh_dispatch', 'Warehouse Dispatch'),
             ('fw_agreement', 'Framework Agreement'),
             ('other', 'Other'),
             ],
            string='Procurement Method',
            required=True,
            states=SOURCED_STATES),
        'dispatch_location_id': fields.many2one(
            'stock.location',
            string='Dispatch From',
            states=SOURCED_STATES),
        'stock_owner': fields.related(
            'dispatch_location_id', 'owner_id',
            type='many2one',
            relation='res.partner',
            string='Stock Owner',
            readonly=True),
        # NOTE: date that should be used for the stock move reservation
        'date_etd': fields.related('transport_plan_id',
                                   'date_etd',
                                   readonly=True,
                                   type='date',
                                   string='ETD',
                                   help="Estimated Date of Departure"),
        'date_eta': fields.related('transport_plan_id',
                                   'date_eta',
                                   readonly=True,
                                   type='date',
                                   string='ETA',
                                   help="Estimated Date of Arrival"),
        'offer_ids': fields.one2many('sale.order.line',
                                     'logistic_requisition_source_id',
                                     'Sales Quotation Lines',
                                     readonly=True),
        'unit_cost': fields.float(
            'Unit Cost',
            states=SOURCED_STATES,
            digits_compute=dp.get_precision('Account')),
        'total_cost': fields.function(
            lambda self, *args, **kwargs: self._get_total_cost(*args, **kwargs),
            string='Total Cost',
            type='float',
            digits_compute=dp.get_precision('Account'),
            store=True),
        'currency_id': fields.related('requisition_id',
                                      'currency_id',
                                      type='many2one',
                                      relation='res.currency',
                                      string='Currency',
                                      readonly=True),
        'transport_applicable': fields.boolean(
            'Transport Applicable',
            states=SOURCED_STATES),
        'transport_plan_id': fields.many2one(
            'transport.plan',
            string='Transport Plan',
            states=SOURCED_STATES),
        'price_is': fields.selection(
            PRICE_IS_SELECTION,
            string='Price is',
            required=True,
            help="When the price is an estimation, the final price may change."
                 " I.e. it is not based on a request for quotation."),
        #
        'purchase_requisition_line_id': fields.many2one(
            'purchase.requisition.line',
            'Purchase Requisition Line',
            ondelete='set null',
            readonly=True),
        'po_requisition_id': fields.related(
            'purchase_requisition_line_id', 'requisition_id',
            type='many2one',
            relation='purchase.requisition',
            string='Purchase Requisition',
            readonly=True),
        # when filled, it means that it has been associated with a
        # bid order line during the split process
        'selected_bid_line_id': fields.many2one('purchase.order.line',  # one2one relation with lr_source_line_id
                                       'Purchase Order Line',
                                       readonly=True,
                                       ondelete='restrict'),
        'selected_bid_id': fields.related('selected_bid_line_id',
                                         'order_id',
                                         type='many2one',
                                         relation='purchase.order',
                                         string='Selected Bid',
                                         readonly=True),
        'purchase_line_id': fields.function(
            lambda self, *a, **kw: self._get_purchase_line_id(*a, **kw),
            type='many2one',
            relation='purchase.order.line',
            readonly=True,
            string='Purchase Order Line'),
        # needed to set the default destination address of the transport plan
        # when created from the lr line view
        'consignee_shipping_id': fields.related(
            'requisition_line_id', 'requisition_id', 'consignee_shipping_id',
            type='many2one', relation='res.partner',
            string='Delivery Address', readonly=True),
        # 2 fields below needed to set the default origin address
        # of the transport plan when created from the lr line view
        'supplier_partner_id': fields.related(
            'selected_bid_id', 'partner_id',
            type='many2one', relation='res.partner',
            string='Supplier Address', readonly=True),
        'location_partner_id': fields.related(
            'dispatch_location_id', 'partner_id',
            type='many2one', relation='res.partner',
            string='Location Address', readonly=True),
        'default_source_address': fields.function(_default_source_address,
                                                  type='many2one',
                                                  relation='res.partner',
                                                  string='Default source',
                                                  readonly=True)
    }
    _defaults = {
        'transport_applicable': False,
        'price_is': 'fixed',
        'name': '/',
        'procurement_method': 'other',
        'proposed_qty': 1
    }

    # TODO: The first 2 should be removed from this module !
    _constraints = [
        (lambda self, *a, **kw: self._check_transport_plan(*a, **kw),
         'Transport plan is mandatory for sourced requisition lines '
         'when the transport is applicable.',
         ['transport_plan_id']),
        (lambda self, *a, **kw: self._check_transport_plan_unique(*a, **kw),
         "A transport plan cannot be linked to lines of different "
         "logistic requisitions.",
         ['transport_plan_id', 'requisition_id']),
        (lambda self, *a, **kw: self._check_purchase_requisition_unique(*a, **kw),
         "A call for bids cannot be linked to lines of different "
         "logistics requisitions.",
         ['po_requisition_id', 'requisition_id']),
    ]

    def _is_sourced_procurement(self, cr, uid, source, context=None):
        """Predicate function to test if line on procurement
        method are sourced"""
        if (not source.po_requisition_id or
                source.po_requisition_id.state != 'closed'):
            return False
        return True

    def _is_sourced_other(self, cr, uid, source, context=None):
        """Predicate function to test if line on other
        method are sourced"""
        return self._is_sourced_procurement(cr, uid, source,
                                            context=context)

    def _is_sourced_wh_dispatch(self, cr, uid, source, context=None):
        """Predicate function to test if line on warehouse
        method are sourced"""
        return True

    def _is_sourced(self, cr, uid, source_id, context=None):
        """ check if line is source using predicate function
        that must be called _is_sourced_ + name of procurement.
        :returns: boolean True if sourced"""
        if isinstance(source_id, list):
            assert len(source_id) == 1
            source_id = source_id[0]
        source = self.browse(cr, uid, source_id, context=context)
        callable_name = "_is_sourced_%s" % source.procurement_method
        if not hasattr(self, callable_name):
            raise NotImplementedError(callable_name)
        callable_fun =  getattr(self, callable_name)
        return callable_fun(cr, uid, source, context=context)

    def _check_transport_plan(self, cr, uid, ids, context=None):
        lines = self.browse(cr, uid, ids, context=context)
        states = ('sourced', 'quoted')
        for line in lines:
            if (line.transport_applicable and
                    line.state in states and
                    not line.transport_plan_id):
                return False
        return True

    def _check_transport_plan_unique(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            if not line.transport_plan_id:
                continue
            plan = line.transport_plan_id
            if not plan.logistic_requisition_source_ids:
                continue
            first_source = plan.logistic_requisition_source_ids[0]
            requisition_id = first_source.requisition_line_id.requisition_id
            for oline in plan.logistic_requisition_source_ids:
                if oline.requisition_line_id.requisition_id != requisition_id:
                    return False
        return True

    def _check_purchase_requisition_unique(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            requisition_id = False
            if not line.po_requisition_id:
                continue
            for pr_line in line.po_requisition_id.line_ids:
                for source in pr_line.logistic_requisition_source_ids:
                    if not requisition_id:
                        requisition_id = source.requisition_line_id.requisition_id
                    elif requisition_id != source.requisition_line_id.requisition_id:
                        return False
        return True

    def _get_purchase_line_id(self, cr, uid, ids, field_name, arg, context=None):
        """ For each line, returns the generated purchase line from the
        purchase requisition.
        """
        result = {}
        po_line_model = self.pool['purchase.order.line']
        po_lines = None
        for line in self.browse(cr, uid, ids, context=context):
            result[line.id] = False
            if line.selected_bid_line_id:
                bid_line = line.selected_bid_line_id
                if not bid_line:
                    continue
                po_lines = [x.id for x in bid_line.po_line_from_bid_ids]
                if not po_lines:
                    continue
            else:
                po_lines = po_line_model.search(cr, uid,
                                                [('lr_source_line_id', '=', line.id),
                                                 ('state', '!=', 'cancel')],
                                                context=context)
            assert len(po_lines) == 1, (
                "We should not have several purchase order lines "
                "for a logistic requisition line")
            result[line.id] = po_lines[0] if po_lines else False

        return result

    def create(self, cr, uid, vals, context=None):
        if (vals.get('name') or '/') == '/':
            seq_obj = self.pool.get('ir.sequence')
            vals['name'] = seq_obj.get(cr, uid, 'logistic.requisition.source') or '/'
        return super(logistic_requisition_source, self).create(cr, uid, vals,
                                                               context=context)

    def _get_purchase_pricelist_from_currency(self, cr, uid, currency_id, context=None):
        """ This method will look for a pricelist of type 'purchase' using
        the same currency than than the given one.
        return : ID of product.pricelist type Integer
        """
        pricelist_obj = self.pool.get('product.pricelist')
        pricelist_id = pricelist_obj.search(cr, uid,
            [('currency_id','=',currency_id),('type','=','purchase')], limit=1)
        return pricelist_id[0]

    def _prepare_po_requisition(self, cr, uid, sources, purch_req_lines,
            pricelist=None, context=None):
        company_id = None
        user_id = None
        consignee_id = None
        dest_address_id = None
        origin = []
        for line in sources:
            origin.append(line.name)
            line_user_id = line.requisition_line_id.logistic_user_id.id
            if user_id is None:
                user_id = line_user_id
            elif user_id != line_user_id:
                raise orm.except_orm(
                    _('Error'),
                    _('The lines are not assigned to the same '
                      'User.'))
            line_company_id = line.requisition_id.company_id.id
            if company_id is None:
                company_id = line_company_id
            elif company_id != line_company_id:
                raise orm.except_orm(
                    _('Error'),
                    _('The sourcing lines do not belong to the same company.'))
            line_consignee_id = line.requisition_id.consignee_id.id
            if consignee_id is None:
                consignee_id = line_consignee_id
            elif consignee_id != line_consignee_id:
                raise orm.except_orm(
                    _('Error'),
                    _('The sourcing lines do not have the same consignee.'))
            line_dest_address_id = line.requisition_id.consignee_shipping_id.id
            if dest_address_id is None:
                dest_address_id = line_dest_address_id
            elif dest_address_id != line_dest_address_id:
                raise orm.except_orm(
                    _('Error'),
                    _('The sourcing lines do not have the '
                      'same delivery address.'))
            line_pricelist_id = self._get_purchase_pricelist_from_currency(
                cr,
                uid,
                line.requisition_id.pricelist_id.currency_id.id,
                context=context
                )
            if pricelist is None:
                pricelist = line_pricelist_id
        return {'user_id': user_id or uid,
                'company_id': company_id,
                'consignee_id': consignee_id,
                'dest_address_id': dest_address_id,
                'line_ids': [(0, 0, rline) for rline in purch_req_lines],
                'origin': ", ".join(origin),
                'req_incoterm_id': line.requisition_id.incoterm_id.id,
                'req_incoterm_address': line.requisition_id.incoterm_address,
                'pricelist_id': pricelist,
                'schedule_date': line.requisition_id.date_delivery,
                }

    def _prepare_po_requisition_line(self, cr, uid, line, context=None):
        if line.po_requisition_id:
            raise orm.except_orm(
                _('Existing'),
                _('The logistic requisition sourcing line %s is '
                  'already linked to a Purchase Requisition.') % line.name)
        if not line.proposed_product_id:
            raise orm.except_orm(
                _('Missing information'),
                _('The sourcing line %d '
                  'does not have any product defined, '
                  'please choose one.') % line.id)
        return {'product_id': line.proposed_product_id.id,
                'product_uom_id': line.proposed_uom_id.id,
                'product_qty': line.proposed_qty,
                'schedule_date': line.requisition_line_id.date_delivery,
                'logistic_requisition_source_ids': [(4, line.id)],
                }

    def _action_create_po_requisition(self, cr, uid, ids, pricelist=None, context=None):
        purch_req_obj = self.pool.get('purchase.requisition')
        purch_req_lines = []
        lines = self.browse(cr, uid, ids, context=context)
        if not next((x for x in lines
                     if x.procurement_method == 'procurement'), None):
            raise orm.except_orm(_('There should be at least one selected'
                                   ' line with procurement method Procurement'),
                                 _('Please correct selection'))
        for line in lines:
            if line.procurement_method not in ('other', 'procurement'):
                raise orm.except_orm(_('Selected line procurement method should'
                                       ' be procurement or other'),
                                     _('Please correct selection'))
            vals = self._prepare_po_requisition_line(cr, uid, line,
                                                     context=context)
            purch_req_lines.append(vals)
        vals = self._prepare_po_requisition(cr, uid,
                                            lines,
                                            purch_req_lines,
                                            pricelist=pricelist,
                                            context=context)
        purch_req_id = purch_req_obj.create(cr, uid, vals, context=context)
        self.write(cr, uid, ids,
                   {'po_requisition_id': purch_req_id},
                   context=context)
        return purch_req_id

    def action_create_po_requisition(self, cr, uid, ids,
            pricelist=None, context=None):
        self._action_create_po_requisition(cr, uid, ids,
                pricelist=pricelist, context=context)
        return self.action_open_po_requisition(cr, uid, ids, context=context)

    def action_open_po_requisition(self, cr, uid, ids, context=None):
        assert len(ids) == 1, "Only 1 ID expected, got: %r" % ids
        source = self.browse(cr, uid, ids[0], context=context)
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

    def _get_total_cost(self, cr, uid, ids, prop, unknow_none, unknow_dict, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.unit_cost * line.proposed_qty
        return res

    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        std_default = {
            'transport_plan_id': False,
            'date_etd': False,
            'date_eta': False,
            'purchase_requisition_line_id': False,
            'selected_bid_line_id': False,
            'name': False,
            'offer_ids': False,
        }
        std_default.update(default)
        return super(logistic_requisition_source, self).copy_data(
            cr, uid, id, default=std_default, context=context)

    def onchange_transport_plan_id(self, cr, uid, ids, transport_plan_id, context=None):
        # Even if date fields are related we want to have immediate visual feedback
        value = {'date_eta': False,
                 'date_etd': False}
        if transport_plan_id:
            plan_obj = self.pool.get('transport.plan')
            plan = plan_obj.browse(cr, uid, transport_plan_id, context=context)
            value['date_eta'] = plan.date_eta
            value['date_etd'] = plan.date_etd
        return {'value': value}

    def onchange_dispatch_location_id(self, cr, uid, ids, dispatch_location_id, context=None):
        """ Get the address of the location and write it in the
        location_partner_id field, this field is a related read-only, so
        this change will never be submitted to the server. But it is
        necessary to set the default "from address" of the transport
        plan in the context.
        """
        value = {'location_partner_id': False}
        if dispatch_location_id:
            location_obj = self.pool.get('stock.location')
            location = location_obj.browse(cr, uid, dispatch_location_id,
                                           context=context)
            value['location_partner_id'] = location.partner_id.id
        return {'value': value}

    def onchange_selected_bid_id(self, cr, uid, ids, selected_bid_id, context=None):
        #FIXME: don't understand
        """ Get the address of the supplier and write it in the
        supplier_partner_id field, this field is a related read-only, so
        this change will never be submitted to the server. But it is
        necessary to set the default "from address" of the transport
        plan in the context.
        """
        value = {'supplier_partner_id': False}
        if selected_bid_id:
            purchase_obj = self.pool.get('purchase.order')
            purchase = purchase_obj.browse(cr, uid, selected_bid_id,
                                           context=context)
            value['supplier_partner_id'] = purchase.partner_id.id
        return {'value': value}
