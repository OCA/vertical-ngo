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
from openerp import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # override only to change the 'string' argument
    # from 'Customer' to 'Requesting Entity'
    partner_id = fields.Many2one(
        'res.partner',
        'Requesting Entity',
        readonly=True,
        states={'draft': [('readonly', False)],
                'sent': [('readonly', False)]},
        required=True,
        change_default=True,
        select=True,
        track_visibility='always')
    consignee_id = fields.Many2one(
        'res.partner',
        string='Consignee',
        required=True)
    incoterm_address = fields.Char(
        'Incoterm Place',
        help="Incoterm Place of Delivery. "
             "International Commercial Terms are a series of "
             "predefined commercial terms used in "
             "international transactions.")
    delivery_time = fields.Char('Delivery time')
    # TODO Move this in translation, as all others stuff like it !
    state = fields.Selection([
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
             "The exception status is automatically set when a cancel "
             "operation occurs in the processing of a document linked to the "
             "logistic order.\nThe 'Waiting Schedule' status is set when the "
             "invoice is confirmed but waiting for the scheduler to run on the"
             "order date.",
        select=True)
