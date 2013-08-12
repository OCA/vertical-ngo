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
