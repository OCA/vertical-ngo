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
from openerp.osv import fields, orm
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT_FORMAT
import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class logistic_requisition(orm.Model):
    _name = "logistic.requisition"
    _description = "Logistic Requisition"

    REQ_STATES = {'confirmed': [('readonly', True)],
                  'done': [('readonly', True)]
                  }

    SELECTION_TYPE = [('cost_estimate', 'Cost Estimate Only'),
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

        'analytic_id':  fields.many2one('account.analytic.account',
                                        'Project',
                                        readonly=True,
                                        states=REQ_STATES,
                                        ),
        'type': fields.selection(
            SELECTION_TYPE,
            string='Type of Requisition',
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
            readonly=True,
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
                              if req.state in ('sourced', 'quoted'))
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

    def _do_done(self, cr, uid, ids, context=None):
        done_ids = []
        for req in self.browse(cr, uid, ids, context=context):
            if all(line.state == 'quoted' for line in req.line_ids):
                done_ids.append(req.id)
        self.write(cr, uid, done_ids, {'state': 'done'}, context=context)

    @staticmethod
    def _validation_dates(vals):
        res = {}
        if vals.get('budget_holder_id'):
            res['date_budget_holder'] = time.strftime(DT_FORMAT)
        if vals.get('finance_officer_id'):
            res['date_finance_officer'] = time.strftime(DT_FORMAT)
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

    _order = "requisition_id asc"

    REQUEST_STATES = {'assigned': [('readonly', True)],
                      'sourced': [('readonly', True)],
                      'quoted': [('readonly', True)],
                      }

    SOURCED_STATES = {'sourced': [('readonly', True)],
                      'quoted': [('readonly', True)]
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

    def _get_name(self, cr, uid, ids, field_names, arg=None, context=None):
        return dict((line_id, line_id) for line_id in ids)

    _columns = {
        'name': fields.function(_get_name,
                                string='Line N°',
                                type='char',
                                readonly=True,
                                store=True),
        'requisition_id': fields.many2one(
            'logistic.requisition',
            'Requisition',
            readonly=True,
            ondelete='cascade'),
        'logistic_user_id': fields.many2one(
            'res.users',
            'Logistic Specialist',
            readonly=True,
            # workaround for the following bug, preventing to
            # automatically subscribe the user to the line
            # https://bugs.launchpad.net/openobject-addons/+bug/1188538
            track_visibility='never',
            help="Logistic Specialist in charge of the "
                 "Logistic Requisition Line"),
        'product_id': fields.many2one('product.product', 'Product',
                                      states=SOURCED_STATES,),
        'description': fields.char('Description',
                                   states=REQUEST_STATES,
                                   required=True),
        'requested_qty': fields.float(
            'Req. Qty',
            states=REQUEST_STATES,
            digits_compute=dp.get_precision('Product UoM')),
        'requested_uom_id': fields.many2one('product.uom',
                                            'Product UoM',
                                            states=REQUEST_STATES,
                                            required=True),
        'budget_tot_price': fields.float(
            'Budget Total Price',
            states=REQUEST_STATES,
            digits_compute=dp.get_precision('Account')),
        'budget_unit_price': fields.function(
            lambda self, *args, **kwargs: self._get_unit_amount_line(*args, **kwargs),
            string='Budget Unit Price',
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
            readonly=True,
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
        'po_requisition_id': fields.many2one(
            'purchase.requisition', 'Request for Tender',
            states=SOURCED_STATES),
        'proposed_qty': fields.float(
            'Proposed Qty',
            states=SOURCED_STATES,
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
            states=SOURCED_STATES),
        'dispatch_location_id': fields.many2one(
            'stock.location',
            string='Dispatch From',
            states=SOURCED_STATES),
        'stock_type': fields.selection(
            [('ifrc', 'IFRC'),
             ('vci', 'VCI'),
             ('pns', 'PNS'),
             ('program', 'Program')],
            string='Stock Type',
            states=SOURCED_STATES),
        'stock_owner': fields.many2one(
            'res.partner',
            string='Stock Owner',
            states=SOURCED_STATES),
        'purchase_id': fields.many2one('purchase.order', 'Purchase Order'),
        # NOTE: date that should be used for the stock move reservation
        'date_etd': fields.date('ETD',
                                states=SOURCED_STATES,
                                help="Estimated Date of Departure"),
        'date_eta': fields.date('ETA',
                                states=SOURCED_STATES,
                                help="Estimated Date of Arrival"),
        'offer_ids': fields.one2many('sale.order.line',
                                     'requisition_id',
                                     'Sales Quotation Lines'),
        'unit_cost': fields.float(
            'Unit Cost',
            states=SOURCED_STATES,
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
             ('sourced', 'Sourced'),
             ('quoted', 'Quoted'),
             ('cancel', 'Cancelled')],
            string='State',
            required=True,
            readonly=True,
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
        'cost_estimate_id': fields.many2one(
            'sale.order',
            string='Cost Estimate',
            readonly=True),
        'transport_plan_id': fields.many2one(
            'transport.plan',
            string='Transport Plan',
            states=SOURCED_STATES),
        'selected_bid': fields.many2one('purchase.order',
                                        string='Selected BID',
                                        states=SOURCED_STATES),
    }

    _defaults = {
        'state': 'draft',
        'requested_qty': 1.0,
    }

    def _do_confirm(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'confirmed'}, context=context)

    def _do_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)

    def _do_sourced(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'sourced'}, context=context)

    def _do_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'}, context=context)

    def _do_assign(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            if line.state == 'confirmed' and line.logistic_user_id:
                self.write(cr, uid, ids,
                           {'state': 'assigned'},
                           context=context)

    def _do_quoted(self, cr, uid, ids, context=None):
        req_obj = self.pool.get('logistic.requisition')
        req_ids = list(set(line.requisition_id.id for line
                           in self.browse(cr, uid, ids, context=context)))
        self.write(cr, uid, ids, {'state': 'quoted'}, context=context)
        # When all lines of a requisition are 'quoted', it should be
        # done, so try to change the state
        req_obj._do_done(cr, uid, req_ids, context=context)

    def _store__get_requisitions(self, cr, uid, ids, context=None):
        # _classic_write returns only the m2o id and not the name_get's tuple
        reqs = self.read(cr, uid, ids, ['requisition_id'],
                         context=context, load='_classic_write')
        return [x['requisition_id'] for x in reqs]

    def _prepare_po_requisition(self, cr, uid, lines, rfq_lines, context=None):
        company_id = None
        user_id = None
        consignee_id = None
        dest_address_id = None
        warehouse_id = False  # TODO: always empty, where does it comes from?
        origin = []
        for line in lines:
            origin.append(line.name)
            line_user_id = line.logistic_user_id.id
            if user_id is None:
                user_id = line_user_id
            elif user_id != line_user_id:
                raise orm.except_orm(
                    _('Error'),
                    _('The lines are not assigned to the same '
                      'Logistic Specialist.'))
            line_company_id = line.requisition_id.company_id.id
            if company_id is None:
                company_id = line_company_id
            elif company_id != line_company_id:
                raise orm.except_orm(
                    _('Error'),
                    _('The lines do not belong to the same company.'))
            line_consignee_id = line.requisition_id.consignee_id.id
            if consignee_id is None:
                consignee_id = line_consignee_id
            elif consignee_id != line_consignee_id:
                raise orm.except_orm(
                    _('Error'),
                    _('The lines do not have the same consignee.'))
            line_dest_address_id = line.requisition_id.consignee_shipping_id.id
            if dest_address_id is None:
                dest_address_id = line_dest_address_id
            elif dest_address_id != line_dest_address_id:
                raise orm.except_orm(
                    _('Error'),
                    _('The lines do not have the same delivery address.'))
        return {'user_id': user_id or uid,
                'company_id': company_id,
                'consignee_id': consignee_id,
                'dest_address_id': dest_address_id,
                'warehouse_id': warehouse_id,
                'line_ids': [(0, 0, line) for line in rfq_lines],
                'origin': ", ".join(origin),
                }

    def _prepare_po_requisition_line(self, cr, uid, line, context=None):
        if line.po_requisition_id:
            raise orm.except_orm(
                _('Existing'),
                _('The logistic requisition line %d is '
                  'already linked to a Request for Tender.') % line.id)
        if not line.product_id:
            raise orm.except_orm(
                _('Missing information'),
                _('The logistic requisition line %d '
                  'does not have any product defined, '
                  'please choose one.') % line.id)
        return {'product_id': line.product_id.id,
                'product_uom_id': line.requested_uom_id.id,
                'product_qty': line.requested_qty,
                'schedule_date': line.date_delivery,
                }

    def _action_create_po_requisition(self, cr, uid, ids, context=None):
        rfq_obj = self.pool.get('purchase.requisition')
        rfq_lines = []
        lines = self.browse(cr, uid, ids, context=context)
        for line in lines:
            vals = self._prepare_po_requisition_line(cr, uid, line,
                                                     context=context)
            rfq_lines.append(vals)
        vals = self._prepare_po_requisition(cr, uid,
                                            lines,
                                            rfq_lines,
                                            context=context)
        rfq_id = rfq_obj.create(cr, uid, vals, context=context)
        self.write(cr, uid, ids,
                   {'po_requisition_id': rfq_id},
                   context=context)
        return rfq_id

    def _get_shop_from_location(self, cr, uid, location_id, context=None):
        """ Returns the sale.shop for a location.

        Returns None if no shop exist for a location.
        """
        warehouse_obj = self.pool.get('stock.warehouse')
        shop_obj = self.pool.get('sale.shop')
        warehouse_ids = warehouse_obj.search(
            cr, uid,
            [('lot_stock_id', '=', location_id)],
            context=context)
        if not warehouse_ids:
            return None
        shop_ids = shop_obj.search(cr, uid,
                                   [('warehouse_id', 'in', warehouse_ids)],
                                   context=context)
        if not shop_ids:
            return None
        assert len(shop_ids) == 1, (
            "Several shops found for location with id %s" % location_id)
        return shop_ids[0]

    def action_create_po_requisition(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        rfq_id = self._action_create_po_requisition(cr, uid, ids, context=context)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Request for Tender'),
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
            'domain': [('id', '=', line.product_id.id)],
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
        """Post a message to warn the logistic specialist that a new
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
        """ Send a message to the logistic user when it is assigned
        and move the state's line to assigned.
        """
        res = super(logistic_requisition_line, self).write(cr, uid, ids,
                                                           vals,
                                                           context=context)
        assignee_changed = vals.get('logistic_user_id')
        if assignee_changed:
            self._send_note_to_logistic_user(cr, uid, ids,
                                             context=context)
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
                'description': prod.name
            }
        return {'value': value}

    def onchange_transport_plan_id(self, cr, uid, ids, transport_plan_id, context=None):
        value = {'date_eta': False,
                 'date_etd': False}
        if transport_plan_id:
            plan_obj = self.pool.get('transport.plan')
            plan = plan_obj.browse(cr, uid, transport_plan_id, context=context)
            value['date_eta'] = plan.date_eta
            value['date_etd'] = plan.date_etd
        return {'value': value}

    def _prepare_cost_estimate_line(self, cr, uid, line, context=None):
        sale_line_obj = self.pool.get('sale.order.line')
        make_type = ('make_to_stock' if line.procurement_method == 'wh_dispatch'
                     else 'make_to_order')
        vals = {'requisition_id': line.id,
                'product_id': line.product_id.id,
                'name': line.description,
                'type': make_type,
                'price_unit': line.unit_cost,
                }
        onchange_vals = sale_line_obj.product_id_change(
            cr, uid, [],
            line.requisition_id.consignee_id.property_product_pricelist.id,
            line.product_id.id,
            partner_id=line.requisition_id.consignee_id.id,
            qty=line.proposed_qty,
            uom=line.proposed_uom_id.id).get('value', {})
        #  price_unit to keep from LR Line unit_cost
        if 'price_unit' in onchange_vals:
            del onchange_vals['price_unit']
        vals.update(onchange_vals)
        return vals

    def _prepare_cost_estimate(self, cr, uid, lines, estimate_lines, context=None):
        sale_obj = self.pool.get('sale.order')
        requester_ids = set()
        consignee_ids = set()
        shipping_ids = set()
        location_ids = set()
        for line in lines:
            requester_ids.add(line.requisition_id.requester_id.id)
            consignee_ids.add(line.requisition_id.consignee_id.id)
            if line.dispatch_location_id:
                location_ids.add(line.dispatch_location_id.id)
            shipping_ids.add(line.requisition_id.consignee_shipping_id.id)

        if len(requester_ids) > 1:
            raise orm.except_orm(
                _('Error'),
                _('All requisition lines must belong to the same requester.'))
        if len(consignee_ids) > 1:
            raise orm.except_orm(
                _('Error'),
                _('All requisition lines must belong to the same consignee.'))
        if len(shipping_ids) > 1:
            raise orm.except_orm(
                _('Error'),
                _('All requisition lines must be delivered in the same place.'))
        if len(location_ids) > 1:
            raise orm.except_orm(
                _('Error'),
                _('All requisition lines must come from the same location '
                  'or from purchase.'))

        requester_id = requester_ids.pop()
        consignee_id = consignee_ids.pop()
        shipping_id = shipping_ids.pop()
        try:
            location_id = location_ids.pop()
        except KeyError:
            shop_id = 1  # FIXME
        else:
            shop_id = self._get_shop_from_location(cr, uid, location_id,
                                                   context=context)
            assert shop_id, "No shop found with the given location"

        vals = {'partner_id': requester_id,
                'partner_invoice_id': requester_id,
                'partner_shipping_id': shipping_id,
                'consignee_id': consignee_id,
                'order_line': [(0, 0, x) for x in estimate_lines],
                'shop_id': shop_id,
                }

        onchange_vals = sale_obj.onchange_partner_id(
            cr, uid, [], requester_id, context=context).get('value', {})
        vals.update(onchange_vals)
        return vals

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

    def _filter_cost_estimate_lines(self, cr, uid, lines, context=None):
        return [line for line in lines
                if line.state == 'sourced' and
                not line.cost_estimate_id]

    def button_create_cost_estimate(self, cr, uid, ids, context=None):
        sale_obj = self.pool.get('sale.order')
        estimate_lines = []
        lines = self.browse(cr, uid, ids, context=context)
        lines = self._filter_cost_estimate_lines(cr, uid, lines,
                                                 context=context)
        if not lines:
            return False
        for line in lines:
            vals = self._prepare_cost_estimate_line(cr, uid, line,
                                                    context=context)
            estimate_lines.append(vals)
        order_d = self._prepare_cost_estimate(cr, uid,
                                              lines,
                                              estimate_lines,
                                              context=context)
        sale_id = sale_obj.create(cr, uid, order_d, context=context)
        self.write(cr, uid, ids,
                   {'cost_estimate_id': sale_id},
                   context=context)
        self._do_quoted(cr, uid, [line.id for line in lines], context=context)
        return self._open_cost_estimate(cr, uid, sale_id, context=context)

    def button_sourced(self, cr, uid, ids, context=None):
        self._do_sourced(cr, uid, ids, context=context)
        return True

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
