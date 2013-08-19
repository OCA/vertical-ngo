# -*- coding: utf-8 -*-

from itertools import groupby
from openerp.osv import orm, fields
from openerp import netsvc
from .logistic_requisition import logistic_requisition_line


class sale_order(orm.Model):
    _inherit = 'sale.order'
    _columns = {
        'requisition_id': fields.many2one('logistic.requisition',
                                          'Logistic Requisition',
                                          ondelete='restrict'),
    }

    def _create_procurements_direct_mto(self, cr, uid, order, order_lines,
                                        context=None):
        """ Create procurement for the direct MTO lines.

        No picking or move is created for those lines because the
        delivery will be handled by the 'Incoming Shipment' from the
        purchase order.

        We reconnect the procurement to the existing purchase order if
        it has already be created from the logistic requisition.

        The purchase order has to be handled like a drop shipping for
        the procurements, so we change the sale flow of the purchase
        to 'direct_delivery'. We also link the purchase with the sale
        and sale lines because this is how the ``sale_dropshipping``
        does.
        """
        purchase_ids = set()
        for line in order_lines:
            log_req_line = line.requisition_line_id
            if log_req_line and log_req_line.purchase_line_id:
                purchase_ids.add(log_req_line.purchase_line_id.order_id.id)

        purchase_obj = self.pool.get('purchase.order')
        purchase_obj.write(cr, uid, list(purchase_ids),
                           {'invoice_method': 'order',
                            'sale_flow': 'direct_delivery',
                            'sale_id': order.id},
                           context=context)

        proc_obj = self.pool.get('procurement.order')
        wf_service = netsvc.LocalService("workflow")
        for sale_line in order_lines:
            purchase_line = None
            logistic_req_line = sale_line.requisition_line_id
            if logistic_req_line and logistic_req_line.purchase_line_id:
                purchase_line = logistic_req_line.purchase_line_id
                # reconnect with the purchase line created previously
                # by the purchase requisition
                # as needed by the sale_dropshipping module
                purchase_line.write({'sale_order_line_id': sale_line.id,
                                     'sale_flow': 'direct_delivery'})

            date_planned = self._get_date_planned(cr, uid, order, sale_line,
                                                  order.date_order,
                                                  context=context)

            vals = self._prepare_order_line_procurement(cr, uid, order,
                                                        sale_line, False,
                                                        date_planned,
                                                        context=context)
            vals['sale_order_line_id'] = sale_line.id
            if purchase_line is not None:
                # the purchase order for this procurement as already
                # been created from the purchase requisition, reconnect
                # with it
                vals['purchase_id'] = purchase_line.order_id.id

            proc_id = proc_obj.create(cr, uid, vals, context=context)
            sale_line.write({'procurement_id': proc_id})
            wf_service.trg_validate(uid, 'procurement.order',
                                    proc_id, 'button_confirm', cr)
            if purchase_line is not None:
                proc_obj.write(cr, uid, proc_id,
                               {'state': 'running'},
                               context=context)

    def _create_pickings_and_procurements(self, cr, uid, order, order_lines,
                                          picking_id=False, context=None):
        """ Instead of creating 1 picking for all the sale order lines, it creates:

        * 1 delivery order per different source location (each line has its own)

        At end, only the MTS / not drop shipping lines will be part
        of the delivery orders, because the sale_dropshipping module
        will take care of the drop shipping lines (create only
        procurement.order for them and exclude them from the
        picking).

        :param browse_record order: sales order to which the order lines belong
        :param list(browse_record) order_lines: sales order line records to procure
        :param int picking_id: optional ID of a stock picking to which the created stock moves
                               will be added. A new picking will be created if ommitted.
        :return: True
        """

        direct_mto_lines = []
        other_lines = []
        for line in order_lines:
            if (line.type == 'make_to_order' and
                    line.sale_flow == 'direct_delivery'):
                direct_mto_lines.append(line)
            else:
                other_lines.append(line)

        self._create_procurements_direct_mto(cr, uid, order, direct_mto_lines,
                                             context=context)

        def get_location_address(line):
            if line.location_id and line.location_id.partner_id:
                return line.location_id.partner_id.id

        # group the lines by address of source location and create
        # a different picking for each address
        sorted_lines = sorted(other_lines, key=get_location_address)
        for _unused_location, lines in groupby(sorted_lines,
                                               key=get_location_address):
            super(sale_order, self)._create_pickings_and_procurements(
                cr, uid, order, list(lines), picking_id=False, context=context)
        return True


class sale_order_line(orm.Model):
    _inherit = "sale.order.line"
    _columns = {
        'requisition_line_id': fields.many2one('logistic.requisition.line',
                                               'Requisition Line',
                                               ondelete='restrict'),
        'price_is': fields.selection(
            logistic_requisition_line.PRICE_IS_SELECTION,
            string='Price is',
            help="When the price is an estimation, the final price may change. "
                 "I.e. it is not based on a request for quotation.")
    }

    _defaults = {
        'price_is': 'fixed',
    }

    def button_confirm(self, cr, uid, ids, context=None):
        """ When a sale order is confirmed, we'll also generate the
        purchase order on the purchase requisition of the logistic
        requisition which has created the sales order lines.

        E.g.
        I create a logistic requisition with 2 lines.
        On each line, I create a purchase requisition, I select the
        purchase lines and confirm the selection.
        Then, a sales order is generated from the logistic requisition, a line
        is created for each logistic requisition line.
        When this sale order is confirmed, for each line, I have to go
        back to the logistic requisition line, and generate the purchase
        order for the purchase requisition.
        """
        result = super(sale_order_line, self).button_confirm(cr, uid, ids, context=context)
        for line in self.browse(cr, uid, ids, context=context):
            if not line.requisition_line_id:
                continue
            purchase_req = line.requisition_line_id.po_requisition_id
            if not purchase_req:
                continue
            purchase_req.generate_po()
        return result
