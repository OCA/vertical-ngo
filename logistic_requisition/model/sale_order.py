# -*- coding: utf-8 -*-

from openerp.osv import fields, orm


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
        'requisition_id': fields.many2one('logistic.requisition.line',
                                          'Requisition Line',
                                           ondelete='restrict'),
        'cost_estimated': fields.boolean(
            'Price is estimated',
            readonly=True,
            help="The unit price is an estimation, "
                 "the final price may change.")
    }
