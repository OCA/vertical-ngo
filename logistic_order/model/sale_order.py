# -*- coding: utf-8 -*-

from openerp.osv import orm, fields


class sale_order(orm.Model):
    _inherit = 'sale.order'

    _columns = {
        # override only to change the 'string' argument
        # from 'Customer' to 'Requesting Entity'
        'partner_id': fields.many2one(
            'res.partner',
            'Requesting Entity',
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
        'incoterm_address': fields.char(
            'Incoterm Place',
            help="Incoterm Place of Delivery. "
                 "International Commercial Terms are a series of "
                 "predefined commercial terms used in "
                 "international transactions."),
        'requested_by': fields.text('Requested By'),
    }
