# -*- coding: utf-8 -*-

from openerp.osv import orm, fields


class sale_order(orm.Model):
    _inherit = 'sale.order'

    _columns = {
        # override only to change the 'string' argument
        # from 'Customer' to 'Requester'
        'partner_id': fields.many2one(
            'res.partner',
            'Requester',
            readonly=True,
            states={'draft': [('readonly', False)],
                    'sent': [('readonly', False)]},
            required=True,
            change_default=True,
            select=True,
            track_visibility='always'),
        'consignee_id': fields.many2one(
            'res.partner',
            string='Consignee',
            required=True),
    }
