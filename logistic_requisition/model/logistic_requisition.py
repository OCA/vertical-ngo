# -*- coding: utf-8 -*-
##############################################################################
#
#    Author:  Joël Grand-Guillaume
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more description.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from __future__ import division
import logging
import time
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
                           DEFAULT_SERVER_DATETIME_FORMAT)
import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

# shortcuts
DATE_FORMAT = DEFAULT_SERVER_DATE_FORMAT
DATETIME_FORMAT = DEFAULT_SERVER_DATETIME_FORMAT


class logistic_requisition(orm.Model):
    _name = "logistic.requisition"
    _description = "Logistic Requisition"

    REQ_STATES = {'confirmed': [('readonly', True)],
                  'done': [('readonly', True)]
                  }

    SELECTION_TYPE =[('cost_estimate', 'Cost Estimate Only'),
                     ('donation', 'Donation')]

    def _get_from_partner(self, cr, uid, ids, context=None):
        req_obj = self.pool.get('logistic.requisition')
        req_ids = req_obj.search(cr, uid,
                                 [('consignee_shipping_id', 'in', ids)],
                                context=context)
        return req_ids

    _columns = {
        'name': fields.char(
            'Reference',
            required=True,
            readonly=True,
            states=REQ_STATES),
        'consignee_reference': fields.char(
            'Consignee Reference',
            states=REQ_STATES),
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
            'res.users', 'Responsible', required=True,
            states=REQ_STATES,
            help="Mobilization Officer or Logistic Coordinator "
                 "in charge of the Logistic Requisition"
        ),
        'requester_id': fields.many2one(
            'res.partner', 'Requester', required=True,
            states=REQ_STATES
        ),
        'consignee_id': fields.many2one(
            'res.partner', 'Consignee', required=True,
            states=REQ_STATES
        ),
        'consignee_shipping_id': fields.many2one(
            'res.partner', 'Delivery Address', required=True,
            states=REQ_STATES
        ),
        'donor_affiliate_id': fields.many2one(
            'res.partner', 'Donor Affiliate',
            states=REQ_STATES
        ),
        'preferred_sourcing': fields.selection(
            [('procurement', 'Procurement'),
             ('wh_dispatch', 'Warehouse Dispatch')],
            string='Preferred Sourcing'
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
                'logistic.requisition': (lambda self, cr, uid, ids, c=None: ids,
                                         ['consignee_shipping_id'],
                                         10),
                'res.partner': (_get_from_partner, ['country_id'], 10),
            }),
        'company_id': fields.many2one(
            'res.company',
            'Company',
            readonly=True,
        ),
        'analytic_id':  fields.many2one('account.analytic.account', 'Project'),
        'type': fields.selection(
            SELECTION_TYPE,
            string='Type of Requisition',
            states=REQ_STATES
        ),
        'preferred_transport': fields.selection(
            [('land', 'Land'),
             ('sea', 'Sea'),
             ('air', 'Air')],
            string='Preferred Transport',
            states=REQ_STATES
        ),
        'note': fields.text('Remarks/Description'),
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
            required=True
        ),
        'amount_total': fields.function(
            lambda self, *args, **kwargs: self._get_amount(*args, **kwargs),
            digits_compute=dp.get_precision('Account'),
            string='Total Budget',
            store={
                'logistic.requisition': (lambda self, cr, uid, ids, c=None: ids,
                                         ['line_ids'], 20),
                'logistic.requisition.line': (lambda self, *args, **kwargs: self._store__get_requisitions(*args, **kwargs),
                                              ['requested_qty',
                                               'budget_unit_price',
                                               'budget_tot_price',
                                               'requisition_id'],
                                              20),
            }),
        'sourced': fields.function(
            lambda self, *args, **kwargs: self._get_sourced(*args, **kwargs),
            string='Sourced',
            type='float'
            ),
        'm_code': fields.char('M-Code', size=32),
        'allowed_budget': fields.boolean('Allowed Budget'),
        'currency_id': fields.related('company_id',
                                      'currency_id',
                                      type='many2one',
                                      relation='res.currency',
                                      string='Currency',
                                      readonly=True),
        'budget_holder_id': fields.many2one(
            'res.users',
            string='Budget Holder'),
        'date_budget_holder': fields.datetime(
            'Budget Holder Validation Date',
            readonly=True),
        'finance_officer_id': fields.many2one(
            'res.users',
            string='Finance Officer'),
        'date_finance_officer': fields.datetime(
            'Finance Officer Validation Date',
            readonly=True),
    }

    _defaults = {
        'date': fields.date.context_today,
        'state': 'draft',
        'user_id': lambda self, cr, uid, c: uid,
        'name': '/',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'logistic.request', context=c),
    }

    _sql_constraints = [
        ('name_uniq',
         'unique(name)',
         'Logistic Requisition Reference must be unique!'),
    ]

    def _get_amount(self, cr, uid, ids, name, args, context=None):
        res = {}
        for requisition in self.browse(cr, uid, ids, context=context):
            res[requisition.id] = sum(line.budget_tot_price for line
                                      in requisition.line_ids)
        return res

    def _get_sourced(self, cr, uid, ids, name, args, context=None):
        res = {}
        for requisition in self.browse(cr, uid, ids, context=context):
            lines_len = sum(1 for req in requisition.line_ids
                            if req.state != 'cancel')
            sourced_len = sum(1 for req in requisition.line_ids
                              if req.state in ('quoted', 'done'))
            if lines_len == 0:
                percentage = 0.
            else:
                percentage = round(sourced_len / lines_len * 100, 2)
            res[requisition.id] = percentage
        return res

    def _do_cancel(self, cr, uid, ids, context=None):
        reqs = self.read(cr, uid, ids, ['line_ids'], context=context)
        line_ids = [lids for req in reqs for lids in req['line_ids']]
        if line_ids:
            line_obj = self.pool.get('logistic.requisition.line')
            line_obj._do_cancel(cr, uid, line_ids, context=context)
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)

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
        self.write(cr, uid, ids, {'state': 'draft'}, context=context)

    @staticmethod
    def _validation_dates(vals):
        res = {}
        if vals.get('budget_holder_id'):
            res['date_budget_holder'] = time.strftime(DATETIME_FORMAT)
        if vals.get('finance_officer_id'):
            res['date_finance_officer'] = time.strftime(DATETIME_FORMAT)
        return res

    def create(self, cr, uid, vals, context=None):
        if vals.get('name', '/') == '/':
            seq_obj = self.pool.get('ir.sequence')
            vals['name'] = seq_obj.get(cr, uid, 'logistic.requisition') or '/'
        vals.update(self._validation_dates(vals))
        return super(logistic_requisition, self).create(cr, uid, vals,
                                                        context=context)

    def write(self, cr, uid, ids, vals, context=None):
        vals.update(self._validation_dates(vals))
        return super(logistic_requisition, self).write(cr, uid, ids, vals,
                                                       context=context)

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'state': 'draft',
            'name': '/',
            'budget_holder_id': False,
            'date_budget_holder': False,
            'finance_officer_id': False,
            'date_finance_officer': False,
        })
        return super(logistic_requisition, self).copy(cr, uid, id, default=default, context=context)

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

    def button_cancel(self, cr, uid, ids, context=None):
        #TODO: ask confirmation
        self._do_cancel(cr, uid, ids, context=context)
        return True

    def button_confirm(self, cr, uid, ids, context=None):
        self._do_confirm(cr, uid, ids, context=context)
        return True

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
        line_ids = []
        for lr in self.browse(cr, uid, ids, context=context):
            line_ids += [line.id for line in lr.line_ids]
        action['domain'] = str([('id', 'in', line_ids)])
        return action


class logistic_requisition_line(orm.Model):
    _name = "logistic.requisition.line"
    _description = "Logistic Requisition Line"
    _inherit = ['mail.thread']

    _rec_name = "id"
    _order = "requisition_id asc"

    _track = {
        'state': {
            'logistic_requisition.mt_requisition_line_assigned':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'assigned',
            'logistic_requisition.mt_requisition_line_quoted':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'quoted',
        },
    }

    def _get_from_partner(self, cr, uid, ids, context=None):
        req_obj = self.pool.get('logistic.requisition')
        req_line_obj = self.pool.get('logistic.requisition.line')
        req_ids = req_obj.search(cr, uid,
                                 [('consignee_shipping_id', 'in', ids)],
                                context=context)
        return req_line_obj._get_from_requisition(cr, uid, req_ids,
                                                  context=context)

    def _get_from_requisition(self, cr, uid, ids, context=None):
        req_line_obj = self.pool.get('logistic.requisition.line')
        line_ids = req_line_obj.search(cr, uid,
                                       [('requisition_id', 'in', ids)],
                                       context=context)
        return line_ids

    _columns = {
        'requisition_id': fields.many2one(
            'logistic.requisition',
            'Requisition',
            ondelete='cascade'),
        'logistic_user_id': fields.many2one(
            'res.users',
            'Logistic Specialist',
            help="Logistic Specialist in charge of the "
                 "Logistic Requisition Line",
            track_visibility='onchange',
        ),
        'procurement_user_id': fields.many2one(
            'res.users',
            'Procurement Officer',
            help="Assigned Procurement Officer in charge of "
                 "the Logistic Requisition Line",
            track_visibility='onchange',
        ),
        #DEMAND
        'product_id': fields.many2one('product.product', 'Product'),
        'description': fields.char('Description',
                                   required=True,
                                   track_visibility='always'),
        'requested_qty': fields.float(
            'Req. Qty',
            digits_compute=dp.get_precision('Product UoM'),
            track_visibility='always'),
        'requested_uom_id': fields.many2one('product.uom',
                                            'Product UoM',
                                            required=True),
        'budget_tot_price': fields.float(
            'Budget Total Price',
            digits_compute=dp.get_precision('Account')),
        'budget_unit_price': fields.function(
            lambda self, *args, **kwargs: self._get_unit_amount_line(*args, **kwargs), string='Budget Unit Price', type="float",
            digits_compute=dp.get_precision('Account'),
            store=True),
        'requested_date': fields.related('requisition_id', 'date_delivery',
                                         string='Requested Date',
                                         type='date',
                                         select=True),
        'country_id': fields.related(
            'requisition_id',
            'country_id',
            string='Country',
            type='many2one',
            relation='res.country',
            store={
                'logistic.requisition.line': (lambda self, cr, uid, ids, c=None: ids,
                                              ['requisition_id'],
                                              10),
                'logistic.requisition': (_get_from_requisition,
                                         ['consignee_shipping_id'],
                                         10),
                'res.partner': (_get_from_partner, ['country_id'], 10),
            }),
        'requested_type': fields.related(
            'requisition_id', 'type',
            string='Requested Type',
            type='selection',
            selection=logistic_requisition.SELECTION_TYPE,
            readonly=True,
            store=True),
        #PURCHASE REQUISITION
        'po_requisition_id': fields.many2one(
            'purchase.requisition', 'Purchase Requisition',
            states={'in_progress': [('readonly', True)],
                    'sent': [('readonly', True)],
                    'done': [('readonly', True)]}),
        #PROPOSAL
        'proposed_qty': fields.float(
            'Proposed Qty',
            digits_compute=dp.get_precision('Product UoM')),
        # to be able to display the UOM 2 times
        'proposed_uom_id': fields.related('requested_uom_id',
                                          string='Proposed UoM',
                                          type='many2one',
                                          relation='product.uom',
                                          readonly=True),
        'procurement_method': fields.selection(
            [('procurement', 'Procurement'),
             ('wh_dispatch', 'Warehouse Dispatch'),
             ('fw_agreement', 'Framework Agreement'),
             ],
            string='Procurement Method',
        ),
        'dispatch_location_id': fields.many2one(
            'stock.location',
            string='Dispatch From'),
        'stock_type': fields.selection(
            [('ifrc', 'IFRC'),
             ('vci', 'VCI'),
             ('pns', 'PNS'),
             ('program', 'Program')],
            string='Stock Type'),
        'stock_owner': fields.many2one(
            'res.partner',
            string='Stock Owner'),
        'purchase_id': fields.many2one('purchase.order', 'Purchase Order'),
        # NOTE: date that should be used for the stock move reservation
        'date_etd': fields.date('ETD', help="Estimated Date of Departure"),
        'date_eta': fields.date('ETA', help="Estimated Date of Arrival"),
        'offer_ids': fields.one2many('sale.order.line',
                                     'requisition_id',
                                     'Sales Quotation Lines'),
        'unit_cost': fields.float(
            'Unit Cost',
            digits_compute=dp.get_precision('Account')),
        'total_cost': fields.function(
            lambda self, *args, **kwargs: self._get_total_cost(*args,**kwargs),
            string='Total Cost',
            type='float',
            digits_compute=dp.get_precision('Account'),
            store=True),
        'state': fields.selection(
            [('draft', 'Draft'),
             ('confirmed', 'Confirmed'),
             ('assigned', 'Assigned'),
             ('quoted', 'Quoted'),
             ('cancel', 'Cancelled')],
            string='State',
            required=True,
            track_visibility='onchange',
            help="Draft: Created\n"
                 "Confirmed: Requisition has been confirmed\n"
                 "Assigned: Waiting the creation of a quote\n"
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
        'account_id': fields.related(
            'product_id', 'property_account_income',
            string='Account Code',
            type='many2one',
            relation='account.account',
            readonly=True),
    }

    _defaults = {
        'state': 'draft',
    }

    def _do_confirm(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'confirmed'}, context=context)

    def _do_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)

    def _do_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'}, context=context)

    def _do_assign(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'assigned'}, context=context)

    def _do_quoted(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'quoted'}, context=context)

    def _store__get_requisitions(self, cr, uid, ids, context=None):
        # _classic_write returns only the m2o id and not the name_get's tuple
        reqs = self.read(cr, uid, ids, ['requisition_id'],
                         context=context, load='_classic_write')
        return [x['requisition_id'] for x in reqs]

    def _prepare_po_requisition(self, cr, uid, ids, context=None):
        # TODO : Make the prepare for the lines
        return

    def _action_create_po_requisition(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        rfq_obj = self.pool.get('purchase.requisition')
        rfq_line_obj = self.pool.get('purchase.requisition.line')
        lines = []
        company_id = False
        warehouse_id = False
        for line in self.browse(cr, uid, ids, context=context):
            user_id = line.procurement_user_id and line.procurement_user_id.id
            if line.po_requisition_id:
                raise osv.except_osv(
                    _('Existing !'),
                    _('Your logistic requisition line is already linked to a Purchase Requisition.'))
            if not line.product_id:
                raise osv.except_osv(
                    _('Missing infos!'),
                    _('Your logistic requisition line do not have any product set, please choose one.'))
            if not company_id:
                company_id = line.requisition_id.company_id.id
            else:
                assert company_id == line.requisition_id.company_id.id, \
                    'You can only create a purchase requisition from line that belong to the same company.'
            # TODO: Make this more "factorized" by using _prepare method hook !!!
            lines.append({
                'product_id': line.product_id.id,
                'product_uom_id': line.requested_uom_id.id,
                'product_qty': line.requested_qty,
            })
        # TODO : make this looking like : vals = _prepare_po_requisition()
        rfq_id = rfq_obj.create(cr, uid, {
                        'user_id': user_id,
                        'company_id': company_id,
                        'warehouse_id': warehouse_id,
                        }, context=context)
        # TODO: Make this more "factorized" by using _prepare method hook !!!
        for rfq_line in lines:
            rfq_line_obj.create(cr, uid, {
                'product_id': rfq_line['product_id'],
                'product_uom_id': rfq_line['product_uom_id'],
                'product_qty': rfq_line['product_qty'],
                'requisition_id': rfq_id,
            }, context=context)
        for line in self.browse(cr, uid, ids, context=context):
            self.write(cr, uid, [line.id], {'po_requisition_id': rfq_id}, context=context)
        return rfq_id

    def _get_shop_from_location(self, cr, uid, location_id, context=None):
        """Take the shop that represent the location, or the Company one
        if not found. In that case we are making a PO and we still need
        to handle that case."""
        warehouse_obj = self.pool.get('stock.warehouse')
        shop_obj = self.pool.get('sale.shop')
        shop_id = False
        if not location_id:
            return 1
        wareh_id = warehouse_obj.search(cr, uid,
                                        [('lot_stock_id', '=', location_id)],
                                        context=context)
        if wareh_id:
            shop_id = shop_obj.search(cr, uid,
                                      [('warehouse_id', '=', wareh_id)],
                                      context=context)
            assert shop_id, "No Shop found with the given location"
        return shop_id[0]

    def action_create_po_requisition(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        rfq_id = self._action_create_po_requisition(cr, uid, ids, context=context)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Requisition'),
            'res_model': 'purchase.requisition',
            'res_id': rfq_id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'nodestroy': True,
        }

    def view_stock_by_location(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        product_id = set()
        for line in self.browse(cr, uid, ids, context=context):
            if line.product_id:
                product_id.add(line.product_id.id)
        assert len(product_id) == 1, (
            "You can only have stock by location for one product")
        return {
            'name': _('Stock by Location'),
            'view_mode': 'tree',
            'res_model': 'stock.location',
            'target': 'current',
            'view_id': False,
            'context': {'product_id': product_id.pop()},
            'domain': [('usage', '=', 'internal')],
            'type': 'ir.actions.act_window',
        }

    def view_price_by_location(self, cr, uid, ids, context=None):
        price_obj = self.pool.get('product.pricelist')
        if context is None:
            context = {}
        product_id = set()
        for line in self.browse(cr, uid, ids, context=context):
            if line.product_id:
                product_id.add(line.product_id.id)
        assert len(product_id) == 1, (
            "You can only have price by location for one product")
        ctx = {"search_default_name": line.product_id.name}
        pricelist = line.dispatch_location_id and line.dispatch_location_id.name
        if pricelist:
            price_l_id = price_obj.search(cr, uid,
                                          [('name', 'like', pricelist)],
                                          context=context)
            ctx['pricelist'] = price_l_id
        return {
            'name': _('Prices for location'),
            'view_mode': 'tree',
            'res_model': 'product.product',
            'target': 'current',
            'view_id': False,
            'context': ctx,
            'domain': [('id', 'in', [line.product_id.id])],
            'type': 'ir.actions.act_window',
        }

    def button_create_cost_estimate(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        sale_obj = self.pool.get('sale.order')
        sale_line_obj = self.pool.get('sale.order.line')
        sol = []
        partner_ids = set()
        location_ids = set()
        for line in self.browse(cr, uid, ids, context=context):
            make_type = 'make_to_order'
            if line.procurement_method == 'wh_dispatch':
                make_type = 'make_to_stock'
            line_vals = {
                'requisition_id': line.id,
                'product_id': line.product_id.id,
                'name': line.description,
                'type': make_type,
            }
            partner_ids.add(line.requisition_id.consignee_id.id)
            if line.dispatch_location_id:
                location_ids.add(line.dispatch_location_id.id)
            line_vals.update(
                sale_line_obj.product_id_change(
                    cr, uid, [],
                    line.requisition_id.consignee_id.property_product_pricelist.id,
                    line.product_id.id,
                    partner_id=line.requisition_id.consignee_id.id,
                    qty=line.requested_qty,
                    uom=line.requested_uom_id.id,
                ).get('value', {}))

            sol.append(line_vals)
        assert len(partner_ids) == 1, (
            'All requisition lines must belong to the same requestor')
        assert len(location_ids) <= 1, (
            'All requisition lines must come from the same location '
            'or from purchase')
        partner_id = partner_ids.pop()
        if location_ids:
            location_id = location_ids.pop()
        else:
            location_id = None
        assert partner_id, 'Requisitions must have a requestor partner'
        found_shop_id = self._get_shop_from_location(
            cr, uid, location_id, context=context)
        order_d = {
            'partner_id': partner_id,
            'order_line': [(0, 0, x) for x in sol],
            'shop_id': found_shop_id,
        }
        order_d.update(
            sale_obj.onchange_partner_id(
                cr, uid, ids, partner_id, context=context).get('value', {})
        )
        sale_id = sale_obj.create(cr, uid, order_d, context=context)
        self.write(cr, uid, ids, {'state': 'quoted'}, context=context)
        return {
            'name': _('Quotation'),
            'view_mode': 'form',
            'res_model': 'sale.order',
            'res_id': sale_id,
            'target': 'current',
            'view_id': False,
            'context': {},
            'type': 'ir.actions.act_window',
        }

    def _get_unit_amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            price = line.budget_tot_price / line.requested_qty
            res[line.id] = price
        return res

    def _get_total_cost(self, cr, uid, ids, prop, unknow_none, unknow_dict, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.unit_cost * line.proposed_qty
        return res

    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        std_default = {
            'logistic_user_id': False,
            'procurement_user_id': False,
            # TODO: Not sure it's mandatory, but seems to be needed otherwise
            # Messages are copied... strange...
            # 'message_ids' : [],
            # 'message_follower_ids' : [],
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
            We override it here to add logistic_user_id and procurement_user_id to the list
        """
        fields_to_follow = ['logistic_user_id', 'procurement_user_id']
        fields_to_follow.extend(auto_follow_fields)
        return super(logistic_requisition_line, self)._message_get_auto_subscribe_fields(
            cr, uid, updated_fields,
            auto_follow_fields=fields_to_follow,
            context=context)

    def _send_note_to_logistic_user(self, cr, uid, req_line, context=None):
        """Post a message to warn the logistic specialist that a new
        line has been associated."""
        subject = ("Logistic Requisition Line %s Assigned" %
                   (req_line.requisition_id.name + '/' + str(req_line.id)))
        details = ("This new requisition concerns %s and is due for %s" %
                   (req_line.description, req_line.requested_date))
        # TODO: Posting the message here do not send it to the just added foloowers...
        # We need to find a way to propagate this properly.
        self.message_post(cr, uid, [req_line.id], body=details,
                          subject=subject, context=context)

    def _manage_logistic_user_change(self, cr, uid, req_line, vals, context=None):
        """Set the state of the line as 'assigned' if actual state is
        draft or in_progress and post    a message to let the logistic
        user about the new requisition line to be trated.

        :param object req_line: browse record of the requisition.line to process
        :param vals, dict of vals to give to write like: {'state':'assigned'}
        :return: dict of vals to give to write method like {'state':'assigned'}
        """
        self._send_note_to_logistic_user(cr, uid, req_line, context=context)
        if req_line.state == 'draft':
            vals['state'] = 'assigned'
        return vals

    def write(self, cr, uid, ids, vals, context=None):
        """ Call the _assign_logistic_user when changing it. This will also
        pass the state to 'assigned' if still in draft.
        """
        for requisition_line in self.browse(cr, uid, ids, context=context):
            if 'logistic_user_id' in vals:
                self._manage_logistic_user_change(cr, uid,
                                                  requisition_line,
                                                  vals,
                                                  context=context)
        return super(logistic_requisition_line, self).write(cr, uid, ids,
                                                            vals,
                                                            context=context)

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
                'requested_qty': 1.0,
                'description': prod.name
            }
        return {'value': value}

    def button_assign(self, cr, uid, ids, context=None):
        # TODO: open a popup asking who to assign
        lines = self.read(cr, uid, ids, ['logistic_user_id'], context=context)
        for line in lines:
            if not line['logistic_user_id']:
                raise osv.except_osv(
                    _('Error'),
                    _('Please first define the logistic specialist.'))
        self._do_assign(cr, uid, ids, context=context)
        return True

    def button_create_cost_estimate(self, cr, uid, ids, context=None):
        # TODO create cost estimate
        self._do_quoted(cr, uid, ids, context=context)
        return True

    def button_open_cost_estimate(self, cr, uid, ids, context=None):
        # TODO
        return True

    def button_cancel(self, cr, uid, ids, context=None):
        self._do_cancel(cr, uid, ids, context=context)
        return True

    def button_reset(self, cr, uid, ids, context=None):
        self._do_confirm(cr, uid, ids, context=None)
        return True
