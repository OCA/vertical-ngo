# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2013-2014 Camptocamp SA
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

import time

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as D_FMT
import openerp.tests.common as common
from . import logistic_requisition
from . import purchase_requisition
from . import purchase_order


class test_sale_order_from_lr_confirm(common.TransactionCase):
    """ Test the confirmation of a sale order created by a logistic
    requisition.

    According to the type of products (make to stock, make to order),
    the behavior when confirming a sale order line is different.
    """

    def setUp(self):
        super(test_sale_order_from_lr_confirm, self).setUp()
        self.log_req_model = self.env['logistic.requisition']
        self.partner_1 = self.env.ref('base.res_partner_1')
        self.partner_3 = self.env.ref('base.res_partner_3')
        partner_4 = self.env.ref('base.res_partner_4')
        self.user_demo = self.env.ref('base.user_demo')
        # Computer Case: make_to_order
        product_16 = self.env.ref('product.product_product_16')
        product_uom_pce = self.env.ref('product.product_uom_unit')
        pricelist_sale = self.env.ref('product.list0')
        self.vals = {
            'partner_id': partner_4.id,
            'consignee_id': self.partner_3.id,
            'date': time.strftime(D_FMT),
            'date_delivery': time.strftime(D_FMT),
            'user_id': self.user_demo.id,
            'pricelist_id': pricelist_sale.id,
        }

        self.line1 = {
            'product_id': product_16.id,  # MTO
            'description': "[C-Case] Computer Case",
            'requested_qty': 100,
            'requested_uom_id': product_uom_pce.id,
            'date_delivery': time.strftime(D_FMT),
        }
        self.source1 = {
            'proposed_qty': 100,
            'proposed_product_id': product_16.id,
            'proposed_uom_id': product_uom_pce.id,
            'unit_cost': 10,
            'sourcing_method': 'procurement',
            'price_is': 'estimated',
        }

    def test_mto_generate_po(self):
        """ The purchase requisition must generate the purchase orders on
        confirmation of sale order.

        When a logistic requisition creates a sale order with MTO lines,
        the confirmation of the lines should generates the purchase
        orders on the purchase requisition linked to the logistic
        requisition lines.
        """
        requisition = self.log_req_model.create(self.vals)
        line = logistic_requisition.add_line(self, requisition, self.line1)
        source = logistic_requisition.add_source(self, line, self.source1)
        requisition.button_confirm()
        logistic_requisition.assign_lines(self, line, self.user_demo.id)
        purch_req = logistic_requisition.create_purchase_requisition(
            self, source)
        purchase_requisition.confirm_call(self, purch_req)
        bid, bid_line = purchase_requisition.create_draft_purchase_order(
            self, purch_req, self.partner_1.id)
        bid_line.price_unit = 10
        purchase_order.select_line(self, bid_line, 100)
        purchase_order.bid_encoded(self, bid)
        purchase_requisition.close_call(self, purch_req)
        purchase_requisition.bids_selected(self, purch_req)
        logistic_requisition.source_lines(self, line)
        sale, __ = logistic_requisition.create_quotation(
            self, requisition, line)
        # when accepting the cost estimate it should generate the
        # purchase order of the purchase requisition
        sale.signal_workflow('accepted')
        self.assertEquals(purch_req.state,
                          'done',
                          "The purchase requisition should be in 'done' "
                          "state.")
        self.assertEquals(len(purch_req.generated_order_ids), 1,
                          "We should have only 1 purchase order.")
        self.assertEquals(purch_req.generated_order_ids.state, "draftpo",
                          "The purchase order should be in state draftpo.")
        # Purchase order line must have been set in sourced_by field
        # on sale.order.line
        self.assertIsNotNone(sale.order_line.sourced_by)
        self.assertEquals(sale.order_line.sourced_by,
                          purch_req.generated_order_ids.order_line)

    def test_mto_sales_order_line_per_source_line(self):
        """ 1 sales order line is generated for each source line """
        requisition = self.log_req_model.create(self.vals)
        line = logistic_requisition.add_line(self, requisition, self.line1)
        source = logistic_requisition.add_source(self, line, self.source1)
        requisition.button_confirm()
        logistic_requisition.assign_lines(self, line, self.user_demo.id)
        purch_req = logistic_requisition.create_purchase_requisition(
            self, source)
        purchase_requisition.confirm_call(self, purch_req)
        # create 2 purchase requisitions
        bid1, bid_line1 = purchase_requisition.create_draft_purchase_order(
            self, purch_req, self.partner_1.id)
        bid_line1.price_unit = 10
        purchase_order.select_line(self, bid_line1, 60)
        purchase_order.bid_encoded(self, bid1)

        bid2, bid_line2 = purchase_requisition.create_draft_purchase_order(
            self, purch_req, self.partner_3.id)
        bid_line2.price_unit = 10
        purchase_order.select_line(self, bid_line2, 40)
        purchase_order.bid_encoded(self, bid2)

        purchase_requisition.close_call(self, purch_req)
        purchase_requisition.bids_selected(self, purch_req)
        logistic_requisition.source_lines(self, line)
        sale, sale_lines = logistic_requisition.create_quotation(
            self, requisition, line)
        self.assertEquals(len(sale_lines), 2,
                          "We should have one sales order line per "
                          "logistic requisition source")
        self.assertEquals(len(line.source_ids), 2)
        self.assertEquals(sorted([line.source_ids[0].id,
                          line.source_ids[1].id]),
                          sorted([sl.lr_source_id.id for sl
                                  in sale_lines]))
