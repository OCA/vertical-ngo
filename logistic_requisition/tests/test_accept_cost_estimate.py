# -*- coding: utf-8 -*-
#
#
#    Author: Yannick Vaucher
#    Copyright 2015 Camptocamp SA
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
#
import openerp.tests.common as common
from openerp import fields


class test_accept_cost_estimate(common.TransactionCase):
    """ Test generation of PO when pushing "Accept Cost Estimate"
    button.
    """

    def setUp(self):
        super(test_accept_cost_estimate, self).setUp()

        self.partner_12 = self.env.ref('base.res_partner_12')
        self.pricelist = self.partner_12.property_product_pricelist_purchase
        self.product_32 = self.env.ref('product.product_product_32')

    def test_ce_reuse_bid(self):
        """ Test a Cost Estimate with a line having 'Use existing Bid' sourcing
        method

        This should duplicate the exsisting selected bid in a new draft PO.
        Sale order line must be sourced by the new purchase order line.

        """
        winning_bid = self.env['purchase.order'].create(
            {'name': '/',
             'partner_id': self.partner_12.id,
             'pricelist_id': self.pricelist.id,
             'location_id': self.ref('stock.stock_location_stock'),
             'state': 'bid_selected',
             })
        po_line = self.env['purchase.order.line'].create(
            {'order_id': winning_bid.id,
             'name': '/',
             'product_id': self.product_32.id,
             'date_planned': fields.Datetime.now(),
             'price_unit': 10.0})

        source = self.env['logistic.requisition.source'].new(
            {'sourcing_method': 'reuse_bid',
             'selected_bid_line_id': po_line
             })

        self.cost_estimate = self.env['sale.order'].new({
            'state': 'draft'})
        so_line = self.env['sale.order.line'].new({
            'order_id': self.cost_estimate,
            'lr_source_id': source})
        self.cost_estimate.order_line = so_line
        self.cost_estimate.action_accepted()

        self.assertEqual(po_line.product_id,
                         so_line.sourced_by.product_id)
        self.assertTrue(so_line.sourced_by)
        self.assertNotEqual(po_line,
                            so_line.sourced_by)
        self.assertEqual(so_line.sourced_by.order_id.state, 'draft')
        self.assertNotEqual(po_line.order_id,
                            so_line.sourced_by.order_id)
