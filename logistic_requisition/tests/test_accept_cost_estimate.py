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

        self.user_demo = self.env.ref('base.user_demo')
        self.partner_3 = self.env.ref('base.res_partner_3')
        self.partner_4 = self.env.ref('base.res_partner_4')
        self.partner_12 = self.env.ref('base.res_partner_12')
        self.pricelist = self.partner_12.property_product_pricelist_purchase
        self.pricelist_sale = self.env.ref('product.list0')
        self.product_32 = self.env.ref('product.product_product_32')
        self.product_uom_pce = self.env.ref('product.product_uom_unit')

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

        lr = self.env['logistic.requisition'].create({
            'partner_id': self.partner_4.id,
            'consignee_id': self.partner_3.id,
            'date': fields.Datetime.now(),
            'date_delivery': fields.Datetime.now(),
            'user_id': self.user_demo.id,
            'pricelist_id': self.pricelist_sale.id,
            })
        lrl = self.env['logistic.requisition.line'].create({
            'requisition_id': lr.id,
            'product_id': self.product_32.id,
            'description': "[HEAD] Headset standard",
            'requested_qty': 100,
            'requested_uom_id': self.product_uom_pce.id,
            'date_delivery': fields.Datetime.now(),
            })
        source = self.env['logistic.requisition.source'].create(
            {'requisition_line_id': lrl.id,
             'proposed_product_id': self.product_32.id,
             'proposed_qty': 100,
             'sourcing_method': 'reuse_bid',
             'selected_bid_line_id': po_line.id,
             'proposed_uom_id': self.product_uom_pce.id,
             'price_is': 'fixed',
             })

        self.cost_estimate = self.env['sale.order'].create({
            'partner_id': self.partner_4.id,
            'consignee_id': self.partner_3.id,
            'state': 'draft'})
        so_line = self.env['sale.order.line'].create({
            'order_id': self.cost_estimate.id,
            'lr_source_id': source.id,
            'product_id': self.product_32.id,
            'product_uom_qty': 100,
            'product_uom': self.product_uom_pce.id,
            })
        self.cost_estimate.action_accepted()

        self.assertEqual(po_line.product_id,
                         so_line.sourced_by.product_id)
        self.assertTrue(so_line.sourced_by)
        self.assertNotEqual(po_line,
                            so_line.sourced_by)
        self.assertEqual(so_line.sourced_by.order_id.state, 'draftpo')
        self.assertNotEqual(po_line.order_id,
                            so_line.sourced_by.order_id)

        # Check info have been copied from LR and LRS
        self.assertEqual(source.requisition_id.consignee_shipping_id,
                         so_line.sourced_by.order_id.dest_address_id)
        self.assertEqual(source.requisition_line_id.requested_qty,
                         so_line.sourced_by.product_qty)
        self.assertEqual(source.requisition_line_id.date_delivery,
                         so_line.sourced_by.date_planned)
