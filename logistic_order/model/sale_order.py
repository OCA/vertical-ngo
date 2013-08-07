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
         'state': fields.selection([
            ('draft', 'Draft Cost Estimate'),
            ('sent', 'Cost Estimate Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Logistic Order'),
            ('manual', 'Logistic Order to Invoice'),
            ('shipping_except', 'Shipping Exception'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ], 'Status', readonly=True, track_visibility='onchange',
            help="Gives the status of the cost estimate or logistic order. \nThe exception status is automatically set when a cancel operation occurs in the processing of a document linked to the logistic order. \nThe 'Waiting Schedule' status is set when the invoice is confirmed but waiting for the scheduler to run on the order date.", select=True),

    }
