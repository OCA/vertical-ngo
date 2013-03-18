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

from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import netsvc
import logging
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

#####################################################################################################
# TODO : See if this is still useful !? Link PO to Logistic Request. I think it's more 
# linked to a line...
#####################################################################################################
# class purchase_order(osv.osv):
#     _inherit = "purchase.order"
#     # _name = "Cost Estimate"
#     _columns = {
#         'reject': fields.text('Rejection Reason', states={'cancel':[('readonly',True)]}),
#         'request_id' : fields.many2one('logistic.request','Logistic Request'),
#         'date_valid':fields.date('Validity Date', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)]}, select=True),
#         'partner_invoice_id': fields.many2one('res.partner.address', 'Invoice Address', help="Invoice address for current request if different."),
#     }
#     def wkf_confirm_order(self, cr, uid, ids, context=None):
#         res = super(purchase_order, self).wkf_confirm_order(cr, uid, ids, context=context)
#         proc_obj = self.pool.get('procurement.order')
#         for po in self.browse(cr, uid, ids, context=context):
#             if po.request_id and (po.request_id.exclusive=='exclusive'):
#                 for order in po.request_id.purchase_ids:
#                     if order.id<>po.id:
#                         proc_ids = proc_obj.search(cr, uid, [('purchase_id', '=', order.id)])
#                         if proc_ids and po.state=='confirmed':
#                             proc_obj.write(cr, uid, proc_ids, {'purchase_id': po.id})
#                         wf_service = netsvc.LocalService("workflow")
#                         wf_service.trg_validate(uid, 'purchase.order', order.id, 'purchase_cancel', cr)
#                     po.request_id.request_done(context=context)
#         return res
# 
#     def wkf_approve_order(self, cr, uid, ids, context=None):
#         for po in self.browse(cr, uid, ids, context=context):
#             if po.date_valid and datetime.today() >= datetime.strptime(po.date_valid, '%Y-%m-%d'):
#                 raise osv.except_osv(_('Error'), _('You cannot confirm this cost request after the validity date !'))
#         res = super(purchase_order,self).wkf_approve_order(cr, uid, ids)
#         return res
# 
# purchase_order()
#####################################################################################################


class LogisticRequest(osv.Model):
    _name = "logistic.request"
    _description="Logistic Request"
    _columns = {
        'name': fields.char(
            'Reference', size=32,required=True,
            readonly=True,
            states={
                'in_progress':[('readonly',True)], 
                'sent':[('readonly',True)], 
                'done':[('readonly',True)]
                }
        ),
        'origin': fields.char(
            'Origin', size=32, 
            states={
                'in_progress':[('readonly',True)], 
                'sent':[('readonly',True)],
                'done':[('readonly',True)]
            }
        ),
        'date_start': fields.date(
            'Request Date', 
            states={
                'in_progress':[('readonly',True)], 
                'sent':[('readonly',True)],
                'done':[('readonly',True)]
                },
            required=True
        ),
        'date_end': fields.date(
            'Desired Delivery Date', 
            states={
                'in_progress':[('readonly',True)],
                'sent':[('readonly',True)],
                'done':[('readonly',True)]
                },
            required=True
        ),
        'user_id': fields.many2one(
            'res.users', 'Request Responsible', required=True, 
            states={
                'in_progress':[('readonly',True)],
                'sent':[('readonly',True)],
                'done':[('readonly',True)]
                },
            help = "Mobilization Officer or Logistic Coordinator in charge of the Logistic Request"
        ),
        'requestor_id': fields.many2one(
            'res.users', 'Requestor', required=True,
            states={
                'in_progress':[('readonly',True)],
                'sent':[('readonly',True)],
                'done':[('readonly',True)]
            }
        ),
        'requestor_partner_id': fields.many2one(
            'res.partner', 'Requestor', required=True,
            states={
                'in_progress':[('readonly',True)],
                'sent':[('readonly',True)],
                'done':[('readonly',True)]
            }
        ),
        'country_id': fields.many2one('res.country', 'Country',
            states={
                'in_progress':[('readonly',True)],
                'sent':[('readonly',True)],
                'done':[('readonly',True)]
            }
        ),
        'company_id': fields.many2one(
            'res.company', 'Account N° / Company', required=True, 
            states={
                'in_progress':[('readonly',True)],
                'sent':[('readonly',True)],
                'done':[('readonly',True)]
            }
        ),
        'analytic_id':  fields.many2one('account.analytic.account', 'Project'),
        'activity_code': fields.char(
            'Activity Code', size=32,
            states={
                'in_progress':[('readonly',True)], 
                'sent':[('readonly',True)], 
                'done':[('readonly',True)]
                }
        ),
        'warehouse_id': fields.many2one(
            'stock.warehouse', 'Warehouse', 
            states={
                'in_progress':[('readonly',True)],
                'sent':[('readonly',True)],
                'done':[('readonly',True)]
            },
            required=True
        ),
        'address_id': fields.related('warehouse_id','partner_id', 
            type='many2one', readonly=True, relation='res.partner', 
            store=True, string='Address'
        ),
        'type' : fields.selection(
            [
                ('procurement','Procurement'),
                ('cost_estimate','Cost Estimate Only'),
                ('wh_dispatch','Warehouse Dispatch')],
            'Type of Request', 
            states={
                'in_progress':[('readonly',True)],
                'sent':[('readonly',True)],
                'done':[('readonly',True)]
            }
        ),
        'prefered_transport' : fields.selection(
            [
                ('land','Land'),
                ('sea','Sea'),
                ('air','Air')],
            'Prefered Transport', 
            states={
                'in_progress':[('readonly',True)],
                'sent':[('readonly',True)],
                'done':[('readonly',True)]
            }
        ),
        'description': fields.text('Remarks/Description'),
        'line_ids' : fields.one2many(
            'logistic.request.line',
            'request_id',
            'Products to Purchase',
            states={'done': [('readonly', True)]}
        ),
        'state': fields.selection([
                ('draft','Draft'),
                ('in_progress','Needs Confirmed'),
                ('sent','Quote Sent'),
                ('done','Done'),
                ('cancel','Cancelled'),
                ],
            'State', required=True
        ),
        'amount_total': fields.function(lambda self, *args, **kwargs:self._get_amount_all(*args,**kwargs), digits_compute=dp.get_precision('Account'), string='Total Budget',
            store={
                'logistic.request': (lambda self, cr, uid, ids, c=None: ids, ['line_ids'], 20),
                'logistic.request.line': (lambda self,*args,**kwargs:self._store__get_requests(*args,**kwargs), ['requested_qty','budget_unit_price','budget_tot_price','request_id'], 20),
            },
            multi='all'),
        #####################################################################################################
        # Todo : May be make a function field to show all lines related Offers
        # 'purchase_ids' : fields.one2many('purchase.order','request_id','Purchase Orders',states={'done': [('readonly', True)]}),
        #####################################################################################################
    }
    _defaults = {
        'date_start': time.strftime('%Y-%m-%d %H:%M:%S'),#FIX: TZ
        'state': 'draft',
        # 'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'logistic.request', context=c),
        'user_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).id ,
        'name': '/',
    }
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Logistic Request Reference must be unique !'),
    ]

    def _get_amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for request in self.browse(cr, uid, ids, context=context):
            res[request.id] = {
                'amount_total': 0.0
            }
            for line in request.line_ids:
                res[request.id]['amount_total'] += line.budget_tot_price
        return res

    def _do_cancel(self, cr, uid, ids, context=None):
        line_ids=reduce(lambda x,y:x+y,[x['line_ids'] for x in self.read(cr,uid,ids,['line_ids'],context=context,load='_classic_write')],[])
        line_ids and self.pool.get('logistic.request.line')._do_cancel(cr,uid,line_ids,context=context)
        self.write(cr, uid, ids, {'state': 'cancel'})
    def _do_confirm(self, cr, uid, ids, context=None):
        line_ids=reduce(lambda x,y:x+y,[x['line_ids'] for x in self.read(cr,uid,ids,['line_ids'],context=context,load='_classic_write')],[])
        line_ids and self.pool.get('logistic.request.line')._do_confirm(cr,uid,line_ids,context=context)
        self.write(cr, uid, ids, {'state':'in_progress'} ,context=context)
    def _do_draft(self, cr, uid, ids, context=None):
        line_ids=reduce(lambda x,y:x+y,[x['line_ids'] for x in self.read(cr,uid,ids,['line_ids'],context=context,load='_classic_write')],[])
        line_ids and self.pool.get('logistic.request.line')._do_draft(cr,uid,line_ids,context=context)
        self.write(cr, uid, ids, {'state': 'draft'})

    def create(self, cr, uid, vals, context=None):
        if vals.get('name','/')=='/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'logistic.request') or '/'
        return super(LogisticRequest, self).create(cr, uid, vals, context=context)
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'state':'draft',
            'name': self.pool.get('ir.sequence').get(cr, uid, 'logistic.request'),
        })
        return super(LogisticRequest, self).copy(cr, uid, id, default=default, context=context)

    def button_cancel(self, cr, uid, ids, context=None):
        #TODO: ask confirmation
        self._do_cancel(cr,uid,ids,context=context)
        return True
    def button_confirm(self, cr, uid, ids, context=None):
        self._do_confirm(cr,uid,ids,context=context)
        return True
    def button_reset(self, cr, uid, ids, context=None):
        self._do_draft(cr,uid,ids,context=context)
        return True
    def button_view_lines(self, cr, uid, ids, context=None):
        """
        This function returns an action that display related lines.
        """
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.get_object_reference(cr, uid, 'logistic_request', 'action_logistic_request_line')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        #compute the number of invoices to display
        inv_ids = []
        for lr in self.browse(cr, uid, ids, context=context):
            inv_ids += [line.id for line in lr.line_ids]
        if len(inv_ids)>1:
            result['domain'] = "[('id','in',["+','.join(map(str, inv_ids))+"])]"
        return result



    def request_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'done', 'date_end':time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)
        line_obj = self.pool.get('logistic.request.line')
        for line in self.browse(cr,uid,ids):
            line_obj.write(cr,uid,[line.id],{'state':'done'})
        return True

    def request_sent(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'sent'}, context=context)
        return True

    
    #####################################################################################################
    # TODO : Check if still necessary, depending on the way we'll create the quote to requestor...
    # 
    # def _planned_date(self, request, delay=0.0):
    #     company = request.company_id
    #     date_planned = False
    #     if request.date_start:
    #         date_planned = datetime.strptime(request.date_start, '%Y-%m-%d %H:%M:%S') - relativedelta(days=company.po_lead)
    #     else:
    #         date_planned = datetime.today() - relativedelta(days=company.po_lead)
    #     if delay:
    #         date_planned -= relativedelta(days=delay)
    #     return date_planned and date_planned.strftime('%Y-%m-%d %H:%M:%S') or False
    # 
    # def _seller_description(self, cr, uid, request_line, supplier, context=None):
    #     product_uom = self.pool.get('product.uom')
    #     pricelist = self.pool.get('product.pricelist')
    #     supplier_info = self.pool.get("product.supplierinfo")
    #     product = request_line.product_id
    #     default_uom_po_id = product.uom_po_id.id
    #     qty = product_uom._compute_qty(cr, uid, request_line.requested_uom_id.id, request_line.requested_qty, default_uom_po_id)
    #     seller_delay = 0.0
    #     seller_price = False
    #     seller_qty = False
    #     for product_supplier in product.seller_ids:
    #         if supplier.id ==  product_supplier.name.id and qty <= product_supplier.qty:
    #             seller_delay = product_supplier.delay
    #             seller_qty = product_supplier.qty
    #     supplier_pricelist = supplier.property_product_pricelist_purchase or False
    #     seller_price = pricelist.price_get(cr, uid, [supplier_pricelist.id], product.id, qty, False, {'uom': default_uom_po_id})[supplier_pricelist.id]
    #     if seller_qty:
    #         qty = max(qty,seller_qty)
    #     date_planned = self._planned_date(request_line.request_id, seller_delay)
    #     return seller_price, qty, default_uom_po_id, date_planned
    #####################################################################################################


class LogisticRequestLine(osv.osv):

    _name = "logistic.request.line"
    _description = "Logistic Request Line"
    _rec_name = "id"
    _order = "request_id asc"
    _inherit = ['mail.thread']
    _track =  {
        'state': {
            'logistic_request.mt_request_line_assigned': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'assigned',
            'logistic_request.mt_request_line_quoted': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'quoted',
        },
    }
    _columns = {
        'id': fields.integer('ID', required=True, readonly=True),
        'request_id' : fields.many2one('logistic.request','Request', ondelete='cascade'),
        'logistic_user_id': fields.many2one(
            'res.users', 'Logistic Specialist',
            help = "Logistic Specialist in charge of the Logistic Request Line",
            track_visibility='onchange',
        ),
        'procurement_user_id': fields.many2one(
            'res.users', 'Procurement Officer',
            help = "Assigned Procurement Officer in charge of the Logistic Request Line",
            track_visibility='onchange',
        ),
        #DEMAND
        'product_id': fields.many2one('product.product', 'Product'),
        'description': fields.char('Description', size=256, required=True, track_visibility='always'),
        'requested_qty': fields.float('Req. Qty', 
            digits_compute=dp.get_precision('Product UoM'), 
            track_visibility='always',),
        'requested_uom_id': fields.many2one('product.uom', 'Product UoM', required=True),
        'budget_tot_price': fields.float('Budget Total Price', digits_compute=dp.get_precision('Account')),
        # 'budget_unit_price': fields.float('Budget Unit Price', digits_compute=dp.get_precision('Account')),
        'budget_unit_price': fields.function(lambda self,*args,**kwargs:self._get_unit_amount_line(*args,**kwargs), string='Budget Unit Price', type="float",
            digits_compute=dp.get_precision('Account'), store=True),
        'requested_date': fields.related('request_id','date_end', string='Requested Date', 
            type='date', select=True, store = True),
        'country_id': fields.related('request_id','country_id', string='Country', 
            type='many2one',relation='res.country', select=True, store = True),
        'requested_type': fields.related('request_id','type', string='Requested Type', 
            type='selection', store=True,
            selection=[
                ('procurement','Procurement'),
                ('cost_estimate','Cost Estimate Only'),
                ('wh_dispatch','Warehouse Dispatch')]
            ),
        'transport_order_id': fields.many2one(
            'transport.order', 'Transport Order', 
            states={
                    'in_progress':[('readonly',True)],
                    'sent':[('readonly',True)],
                    'done':[('readonly',True)]
            },
        ),
        #PURCHASE REQUISITION
        'po_requisition_id': fields.many2one(
            'purchase.requisition', 'Purchase Requisition', 
            states={
                    'in_progress':[('readonly',True)],
                    'sent':[('readonly',True)],
                    'done':[('readonly',True)]
            },
        ),
        #PROPOSAL
        'confirmed_qty': fields.float('Prop. Qty', digits_compute=dp.get_precision('Product UoM')),
        # 'confirmed_uom_id': fields.many2one('product.uom', 'Product UoM', required=True),
        'confirmed_type': fields.selection([
            ('stock','Dispatch from Warehouse'),
            ('order','Purchase'),
            ],
            'Procurement Method',
        ),
        #'procure_supplier_id': fields.many2one('res.partner', 'Procured From'),
        'dispatch_location_id': fields.many2one('stock.location', 'Dispatch From'),
        'purchase_id': fields.many2one('purchase.order', 'Purchase Order'),
        'etd_date': fields.date('ETD', help="Estimated Date of Departure"), #NOTE: date that should be used for the stock move reservation
        'offer_ids': fields.one2many('sale.order.line','request_id','Sales Quotation Lines'),
        'estimated_goods_cost': fields.float('Goods Tot. Cost', digits_compute=dp.get_precision('Account')),
        'estimated_transportation_cost': fields.related('transport_order_id','transport_tot_cost',
            string='Transportation Cost', store=True, readonly=True),
        'estimated_tot_cost': fields.function(lambda self,*args,**kwargs:self._get_estimate_tot_cost(*args,**kwargs), string='Estimated Total Cost', type="float",
            digits_compute= dp.get_precision('Account'), store=True),
        # Do not remind what was this for...
        # 'company_id': fields.related('request_id','company_id',
        # type='many2one',relation='res.company',string='Company', store=True, readonly=True),
        'state': fields.selection([
                ('draft','Draft'),
                ('in_progress','Need Confirmed'),
                ('assigned','Assigned'),
                ('cost_estimated','Cost Estimated'),
                ('quoted','Quoted'),
                ('waiting','Waiting Approval'),
                ('done','Done'),
                ('refused','Refused'),
                ('cancel','Cancelled'),
            ], 
            'Status', required=True, track_visibility='onchange',
            help = "Draft: Created\n"
                   "Assigned: Line taken in charge by Logistic Officer\n"
                   "Quoted: Quotation made for the line\n"
                   "Waiting Approval: Wait on the requestor to approve the quote\n"
                   "Done: The line has been processed and quote was accepted\n"
                   "Refused: The line has been processed and quote was refused\n"
                   "Cancelled: The request has been cancelled"
        ),
        'status': fields.function(lambda self,*args,**kwargs:self._get_state(*args,**kwargs), string='Status', type="Selection", selection=[('draft','Draft'),
        ('in_progress','Need Confirmed'),
        ('assigned','Assigned'),
        ('cost_estimated','Cost Estimated'),
        ('quoted','Quoted'),
        ('waiting','Waiting Approval'),
        ('done','Done'),
        ('refused','Refused'),
        ('cancel','Cancelled'),
                    ],),
    }

    _defaults = {
        'state': 'draft',
        #####################################################################################################
        # Todo : See if we do need company ID on lines...
        # 'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'logistic.request.line', context=c),
        #####################################################################################################
    }

    # TODO: We could use the messageload method overriding to display in the LR line
    # some message that would have been sent on his parent LR:
    # Messages display management
    #     ++++++++++++++++++++++++++++
    # 
    #     By default, the mail_thread widget shows all messages related to the current document beside the document, 
    #     in the History and comments section. However, you may want to display other messages in the widget. 
    #     For example, the OpenChatter on res.users model shows
    # 
    #      - messages related to the user, as usual (messages with ``model = res.users, res_id = current_document_id``)
    #      - messages directly pushed to this user (containing @login)
    # 
    #     The best way to direct the messages that will be displayed in the OpenChatter widget is to override the ``message_load`` method. For example, the following method fetches messages as usual, but also fetches messages linked to the task project that contain the task name. Please refer to the API for more details about the arguments.
    # 
    #     ::
    # 
    #       def message_load(self, cr, uid, ids, limit=100, offset=0, domain=[], ascent=False, root_ids=[False], context=None):
    #         msg_obj = self.pool.get('mail.message')
    #         for my_task in self.browse(cr, uid, ids, context=context):
    #           # search as usual messages related to the current document
    #           msg_ids += msg_obj.search(cr, uid, ['|', '&', ('res_id', '=', my_task.id), ('model', '=', self._name),
    #             # add: search in the current task project messages
    #             '&', '&', ('res_id', '=', my_task.project_id.id), ('model', '=', 'project.project'),
    #             # ... containing the task name
    #             '|', ('body', 'like', '%s' % (my_task.name)), ('body_html', 'like', '%s' % (my_task.name))
    #             ] + domain, limit=limit, offset=offset, context=context)
    #         # if asked: add ancestor ids to have complete threads
    #         if (ascent): msg_ids = self._message_add_ancestor_ids(cr, uid, ids, msg_ids, root_ids, context=context)
    #         return msg_obj.read(cr, uid, msg_ids, context=context)
    #     

    def _do_confirm(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'in_progress'} ,context=context)
    def _do_cancel(self, cr, uid, ids, context=None):
        #TODO : cancel related documents if possible
        # purchase_order_obj = self.pool.get('purchase.order')
        # for purchase in self.browse(cr, uid, ids, context=context):
        #     for purchase_id in purchase.purchase_ids:
        #         if str(purchase_id.state) in('draft','wait'):
        #             purchase_order_obj.action_cancel(cr,uid,[purchase_id.id])
        self.write(cr, uid, ids, {'state':'cancel'} ,context=context)
    def _do_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'draft'} ,context=context)
    def _do_assign(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'assigned'} ,context=context)

    def _store__get_requests(self, cr, uid, ids, context=None):
        return [x['request_id'] for x in self.read(cr,uid,ids,['request_id'],context=context,load='_classic_write')]

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
            # TODO: origin is only 32 Char long !!! We override it for every line => we must
            # find a way to deal with that !
            origin = line.request_id.name + '/' + str(line.id)
            user_id = line.procurement_user_id and line.procurement_user_id.id
            if line.po_requisition_id:
                raise osv.except_osv(
                    _('Existing !'),
                    _('Your logistic request line is already linked to a Purchase Requisition.'))
            if not line.product_id:
                raise osv.except_osv(
                    _('Missing infos!'),
                    _('Your logistic request line do not have any product set, please choose one.'))
            if not company_id:
                company_id = line.request_id.company_id.id
            else:
                assert company_id == line.request_id.company_id.id, \
                    'You can only create a purchase requisition from line that belong to the same company.'
            if not warehouse_id:
                warehouse_id = line.request_id.warehouse_id.id
            else:
                assert warehouse_id == line.request_id.warehouse_id.id, \
                    'You can only create a purchase requisition from line that will be shipped to same warehouse.'
            # TODO: Make this more "factorized" by using _prepare method hook !!!
            lines.append({
                'product_id': line.product_id.id,
                'product_uom_id': line.requested_uom_id.id,
                'product_qty': line.requested_qty,
            })
        # TODO : make this looking like : vals = _prepare_po_requisition()
        rfq_id = rfq_obj.create(cr, uid, {
                        'origin': origin,
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
        """Take the shop that represent the location, or the Company one if not 
        found. In that case we are making a PO and we still need to handle that case."""
        warehouse_obj = self.pool.get('stock.warehouse')
        shop_obj = self.pool.get('sale.shop')
        shop_id = False
        if not location_id:
            return 1
        wareh_id = warehouse_obj.search(cr, uid, [('lot_stock_id','=',location_id)])
        if wareh_id:
            shop_id = shop_obj.search(cr, uid, [('warehouse_id','=',wareh_id)])
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
        assert len(product_id) == 1, "You can only have stock by location for one product"
        return {
            'name': _('Stock by Location'),
            'view_mode': 'tree',
            'res_model': 'stock.location',
            'target': 'current',
            'view_id': False,
            'context': {'product_id': product_id.pop()},
            'domain': [('usage','in',['internal'])],
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
        assert len(product_id) == 1, "You can only have price by location for one product"
        # import pdb;pdb.set_trace()
        ctx = {
            "search_default_name": line.product_id.name,
            }
        pricelist = line.dispatch_location_id and line.dispatch_location_id.name
        if pricelist:
            price_l_id = price_obj.search(cr, uid, [('name','like', pricelist)])
            # ctx['search_default_pricelist_id'] = price_l_id
            ctx['pricelist'] = price_l_id
            # ctx['default_pricelist_id'] = price_l_id
            
        return {
            'name': _('Prices for location'),
            'view_mode': 'tree',
            'res_model': 'product.product',
            'target': 'current',
            'view_id': False,
            'context': ctx,
            'domain': [('id','in',[line.product_id.id])],
            'type': 'ir.actions.act_window',
        }
    
    def button_make_so_quotation(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        sale_obj = self.pool.get('sale.order')
        sale_line_obj = self.pool.get('sale.order.line')
        origin = []
        sol = []
        partner_ids = set()
        location_ids = set()
        for line in self.browse(cr, uid, ids, context=context):
            line_vals = {
                'request_id': line.id,
                'product_id': line.product_id.id,
                'name': line.description,
                'type': line.confirmed_type=='stock' and 'make_to_stock' or 'make_to_order',
            }
            origin.append(self.name_get(cr, uid, [line.id])[0][1])
            partner_ids.add(line.request_id.requestor_partner_id.id)
            if line.dispatch_location_id:
                location_ids.add(line.dispatch_location_id.id)
            line_vals.update(
                sale_line_obj.product_id_change(
                        cr, 
                        uid, 
                        [], 
                        line.request_id.requestor_partner_id.property_product_pricelist.id, 
                        line.product_id.id,
                        partner_id=line.request_id.requestor_partner_id.id,
                        qty=line.requested_qty,
                        uom=line.requested_uom_id.id,
                ).get('value', {}),
            )
            
            sol.append(line_vals)
        assert len(partner_ids)==1, 'All request lines must belong to the same requestor'
        assert len(location_ids)<=1, 'All request lines must come from the same location or from purchase'
        partner_id=partner_ids.pop()
        if location_ids:
            location_id=location_ids.pop()
        else:
            location_id = None
        assert partner_id, 'Request must have a requestor partner'
        found_shop_id = self._get_shop_from_location(cr, uid, location_id, context=context)
        order_d={
            'partner_id': partner_id,
            'origin': ','.join(origin),
            'order_line': [(0,0,x) for x in sol],
            'shop_id': found_shop_id,
            }
        order_d.update(
            sale_obj.onchange_partner_id(cr, uid, ids, partner_id, context=context).get('value', {})
        )
        sale_id = sale_obj.create(cr, uid, order_d, context=context)
        self.write(cr, uid, ids, {'state':'quoted'}, context=context)
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
        
    def button_assign(self, cr, uid, ids, context=None):
        for line in self.read(cr,uid,ids,['logistic_user_id'],context=context):
            if not line['logistic_user_id']:
                raise osv.except_osv(_('Error'),_('Please first define the logistic specialist'))
        self._do_assign(cr,uid,ids,context=context)

    def _get_unit_amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        for line in self.browse(cr, uid, ids):
            price = line.budget_tot_price / line.requested_qty
            res[line.id] = price
        return res

    def _get_estimate_tot_cost(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        for line in self.browse(cr, uid, ids):
            price = line.estimated_goods_cost + line.estimated_transportation_cost
            res[line.id] = price
        return res

    def _get_state(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        for line in self.browse(cr, uid, ids):
            state = line.state
            res[line.id] = state
        return res

    
    # TODO : transport_order_id Must belong to same detsination and company !!!!
    # Make a _contraints [] !!!
    
    def copy_data(self, cr, uid, id, default=None, context=None):
        if not default:
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
        return super(LogisticRequestLine, self).copy_data(cr, uid, id, default=std_default, context=context)

    def _message_get_auto_subscribe_fields(self, cr, uid, updated_fields, auto_follow_fields=['user_id'], context=None):
        """ Returns the list of relational fields linking to res.users that should
            trigger an auto subscribe. The default list checks for the fields
            - called 'user_id'
            - linking to res.users
            - with track_visibility set
            We override it here to add logistic_user_id and procurement_user_id to the list
        """
        fields_to_follow = ['logistic_user_id','procurement_user_id']
        fields_to_follow.extend(auto_follow_fields)
        res = super(LogisticRequestLine, self)._message_get_auto_subscribe_fields(cr, uid, updated_fields, 
            auto_follow_fields = fields_to_follow,
            context=context)
        return res

    def _send_note_to_logistic_user(self, cr, uid, req_line, context=None):
        """Post a message to warn the logistic specialist that a new line has been associated."""
        subject = "Logistic Request Line %s Assigned" %(req_line.request_id.name+'/'+str(req_line.id))
        details = "This new request concerns %s and is due for %s" %(req_line.description,req_line.requested_date)
        # TODO: Posting the message here do not send it to the just added foloowers...
        # We need to find a way to propagate this properly.
        self.message_post(cr, uid, [req_line.id], body=details, subject=subject, context=context)
        
    def _manage_logistic_user_change(self, cr, uid, req_line, vals, context=None):
        """Set the state of the line as 'assigned' if actual state is draft or in_progress 
        and post    a message to let the logistic user about the new request line to be trated.
        
        :param object req_line: browse record of the request.line to process
        :param vals, dict of vals to give to write like: {'state':'assigned'}
        :return vals: dict of vals to give to write method like {'state':'assigned'}
        """
        self._send_note_to_logistic_user(cr, uid, req_line, context=context)
        if req_line.state == 'draft' or req_line.state == 'in_progress':
            vals['state'] = 'assigned'
        return vals

    def write(self, cr, uid, ids, vals, context=None):
        """ Call the _assign_logistic_user whenb changing it. This will also
        pass the state to 'assigned' if stil in draft.
        """
        for request_line in self.browse(cr, uid, ids, context):
            if 'logistic_user_id' in vals:
                # if request_line.logistic_user_id:
                #     self.message_unsubscribe_users(
                #         cr, uid, ids, 
                #         user_ids=[request_line.logistic_user_id.id],
                #         context=context)
                self._manage_logistic_user_change(cr, uid, request_line, vals, context=context)
            # elif 'procurement_user_id' in vals:
            #     if request_line.procurement_user_id:
            #         self.message_unsubscribe_users(
            #             cr, uid, ids, 
            #             user_ids=[request_line.procurement_user_id.id],
            #             context=context)
            #     self.message_subscribe_users(
            #         cr, uid, ids,
            #         user_ids=[vals['procurement_user_id']],
            #         context=context)
        return super(LogisticRequestLine, self).write(cr, uid, ids, vals, context=context)

    def onchange_product_id(self, cr, uid, ids, product_id, requested_uom_id, context=None):
        """ Changes UoM and name if product_id changes.
        @param name: Name of the field
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
        value = {'requested_uom_id': ''}
        if product_id:
            prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            value = {
                    'requested_uom_id': prod.uom_id.id,
                    # 'confirmed_uom_id': prod.uom_id.id,
                    'requested_qty': 1.0,
                    'description' : prod.name
                }
        return {'value': value}

    def line_assigned(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'assigned'}, context=context)
        return True        

    def line_estimated(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'cost_estimated'}, context=context)
        return True        

    def line_quoted(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'quoted'}, context=context)
        return True        

    def line_waiting(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'waiting'}, context=context)
        return True        

    def line_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'done'}, context=context)
        return True        

    def line_refused(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'refused'}, context=context)
        return True        

    #####################################################################################################
    # TODO : Originally made on logisitc request not line. See if we can re-use part of it
    #
    # def make_purchase_order(self, cr, uid, ids, partner_id, all_or_partial, context=None):
    #     """
    #     Create New RFQ for Supplier
    #     """
    #     if context is None:
    #         context = {}
    #     assert partner_id, 'Supplier should be specified'
    #     purchase_order = self.pool.get('purchase.order')
    #     purchase_order_line = self.pool.get('purchase.order.line')
    #     res_partner = self.pool.get('res.partner')
    #     fiscal_position = self.pool.get('account.fiscal.position')
    #     supplier = res_partner.browse(cr, uid, partner_id, context=context)
    #     delivery_address_id = res_partner.address_get(cr, uid, [supplier.id], ['delivery'])['delivery']
    #     supplier_pricelist = supplier.property_product_pricelist_purchase or False
    #     res = {}
    #     for request in self.browse(cr, uid, ids, context=context):
    #         if supplier.id in filter(lambda x: x, [rfq.state <> 'cancel' and rfq.partner_id.id or None for rfq in request.purchase_ids]):
    #              raise osv.except_osv(_('Warning'), _('You have already one %s purchase order for this partner, you must cancel this purchase order to create a new quotation.') % rfq.state)
    #         location_id = request.warehouse_id.lot_input_id.id
    #         purchase_id = purchase_order.create(cr, uid, {
    #                     'origin': request.name,
    #                     'partner_id': supplier.id,
    #                     'partner_address_id': delivery_address_id,
    #                     'partner_invoice_id': request.partner_invoice_id.id,
    #                     'pricelist_id': supplier_pricelist.id,
    #                     'location_id': location_id,
    #                     'company_id': request.company_id.id,
    #                     'fiscal_position': supplier.property_account_position and supplier.property_account_position.id or False,
    #                     'request_id':request.id,
    #                     'notes':request.description,
    #                     'warehouse_id':request.warehouse_id.id ,
    #         })
    #         res[request.id] = purchase_id
    #         for line in request.line_ids:
    #             product = line.product_id
    #             seller_price, qty, default_uom_po_id, date_planned = self._seller_description(cr, uid, line, supplier, context=context)
    #             if all_or_partial == 'difference':
    #                 # qty=self._count_remaining_product(product,request)
    #                 qty=round(qty/2,0)
    #             taxes_ids = product.supplier_taxes_id
    #             taxes = fiscal_position.map_tax(cr, uid, supplier.property_account_position, taxes_ids)
    #             purchase_order_line.create(cr, uid, {
    #                 'order_id': purchase_id,
    #                 'name': product.partner_ref,
    #                 'requested_qty': qty,
    #                 'product_id': product.id,
    #                 'product_uom': default_uom_po_id,
    #                 'price_unit': seller_price,
    #                 'date_planned': line.date_planned or date_planned,
    #                 'notes': product.description_purchase,
    #                 'taxes_id': [(6, 0, taxes)],
    #             }, context=context)
    #             
    #     return res
    #####################################################################################################
    

###################################################################################
#TODO : See if this is still useful !? Allow to create logistic request instead of "normal" PO when
# Order point are trigged
#####################################################################################################

# class product_product(osv.osv):
#     _inherit = 'product.product'
# 
#     _columns = {
#         'logistic_request': fields.boolean('Logistic Request', help="Check this box so that requests generates purchase requests instead of directly requests for quotations."),
#     }
#     _defaults = {
#         'logistic_request': False
#     }
# 
# product_product()

 
# class procurement_order(osv.osv):
# 
#     _inherit = 'procurement.order'
#     _columns = {
#         'request_id' : fields.many2one('logistic.request','Latest Request')
#     }
#     def make_po(self, cr, uid, ids, context=None):
#         sequence_obj = self.pool.get('ir.sequence')
#         res = super(procurement_order, self).make_po(cr, uid, ids, context=context)
#         for proc_id, po_id in res.items():
#             procurement = self.browse(cr, uid, proc_id, context=context)
#             request_id=False
#             if procurement.product_id.logistic_request:
#                 request_id=self.pool.get('logistic.request').create(cr, uid, {
#                     'name': sequence_obj.get(cr, uid, 'purchase.order.request'),
#                     'origin': procurement.origin,
#                     'date_end': procurement.date_planned,
#                     'warehouse_id':procurement.purchase_id and procurement.purchase_id.warehouse_id.id,
#                     'company_id':procurement.company_id.id,
#                     'line_ids': [(0,0,{
#                         'product_id': procurement.product_id.id,
#                         'requested_uom_id': procurement.product_uom.id,
#                         'requested_qty': procurement.requested_qty
# 
#                     })],
#                     'purchase_ids': [(6,0,[po_id])]
#                 })
#             self.write(cr,uid,proc_id,{'request_id':request_id})
#         return res
# 
# procurement_order()
#####################################################################################################


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
