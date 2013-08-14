# -*- coding: utf-8 -*-

from openerp.osv import fields, orm
from .logistic_requisition import logistic_requisition_line


class sale_order(orm.Model):
    _inherit = 'sale.order'
    _columns = {
        'requisition_id': fields.many2one('logistic.requisition',
                                          'Logistic Requisition',
                                          ondelete='restrict'),
    }


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
