# -*- coding: utf-8 -*-

from osv import fields, osv
from tools.translate import _
from openerp import SUPERUSER_ID

class sale_order_line(osv.osv):
    _inherit = "sale.order.line"
    _columns = {
        'request_id':fields.many2one('logistic.request.line', 'Request Line', ondelete='restrict'),
    }
