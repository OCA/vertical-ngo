# -*- coding: utf-8 -*-

from openerp.osv import fields, orm


class sale_order_line(orm.Model):
    _inherit = "sale.order.line"
    _columns = {
        'requisition_id': fields.many2one('logistic.requisition.line',
                                          'Request Line',
                                          ondelete='restrict'),
    }
