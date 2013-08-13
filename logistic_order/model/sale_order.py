# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from itertools import groupby
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
        'delivery_time': fields.char('Delivery time'),
        'state': fields.selection([
            ('draft', 'Draft Cost Estimate'),
            ('sent', 'Cost Estimate Sent'),
            ('cancel', 'Cancelled'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Logistic Order'),
            ('manual', 'Logistic Order to Invoice'),
            ('shipping_except', 'Shipping Exception'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done')],
            'Status',
            readonly=True,
            track_visibility='onchange',
            help="Gives the status of the cost estimate or logistic order.\n"
                 "The exception status is automatically set when a cancel"
                 " operation occurs in the processing of a document linked to the logistic order.\n"
                 "The 'Waiting Schedule' status is set when the invoice is"
                 " confirmed but waiting for the scheduler to run on the order date.",
            select=True),
    }

    def _create_pickings_and_procurements(self, cr, uid, order, order_lines,
                                          picking_id=False, context=None):
        """ Instead of creating 1 picking for all the sale order lines, it creates:

        * 1 delivery order per different source location (each line has its own)

        At end, only the MTS / not drop shipping lines will be part
        of the delivery orders, because the sale_dropshipping module
        will take care of the drop shipping lines (create
        procurement.order for them and exclude them from the
        picking).

        :param browse_record order: sales order to which the order lines belong
        :param list(browse_record) order_lines: sales order line records to procure
        :param int picking_id: optional ID of a stock picking to which the created stock moves
                               will be added. A new picking will be created if ommitted.
        :return: True
        """
        def get_location_address(line):
            if line.location_id and line.location_id.partner_id:
                return line.location_id.partner_id.id

        sorted_lines = sorted(order_lines, key=get_location_address)
        for _unused_location, lines in groupby(sorted_lines, key=get_location_address):
            super(sale_order, self)._create_pickings_and_procurements(
                cr, uid, order, list(lines), picking_id=False, context=context)
        return True
