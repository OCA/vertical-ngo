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


class test_purchase_split_requisition(common.TransactionCase):
    """ Test the split of the logistics requisition lines
    according to the purchase order lines choosed during the
    purchase requisition process.

    A bit of context:

    We create a logistics requisition with several lines.
    For each line, we create a purchase requisition.
    During the purchase requisition process, we'll send requests
    for quotations to several suppliers. Once the call is closed,
    we'll have a few RfQ with different amounts. We'll choose
    which lines we want to confirm.
    A purchase order will be generated with the final choice, at this
    point, for 1 logistics requisition line, we may have several
    purchase order line. We have to split the logistics requisition
    lines in order to have the same quantities than the purchase lines.

    The purpose of the tests here is to check if the split is done
    correctly.
    """

    def setUp(self):
        super(test_purchase_split_requisition, self).setUp()
        self.ir_model_data = self.env['ir.model.data']
        self.log_req = self.env['logistic.requisition']
        self.log_req_line = self.env['logistic.requisition.line']
        self.purchase_order = self.env['purchase.order']

        data_model = self.env['ir.model.data']
        self.partner_1 = data_model.xmlid_to_object('base.res_partner_1')
        self.partner_3 = data_model.xmlid_to_object('base.res_partner_3')
        self.partner_4 = data_model.xmlid_to_object('base.res_partner_4')
        self.partner_12 = data_model.xmlid_to_object('base.res_partner_12')
        self.user_demo = data_model.xmlid_to_object('base.user_demo')
        self.product_32 = data_model.xmlid_to_object(
            'product.product_product_32')
        self.product_uom_pce = data_model.xmlid_to_object(
            'product.product_uom_unit')
        self.pricelist_sale = data_model.xmlid_to_object('product.list0')

        vals = {
            'partner_id': self.partner_4.id,
            'consignee_id': self.partner_3.id,
            'date_delivery': time.strftime(D_FMT),
            'user_id': self.user_demo.id,
            'pricelist_id': self.pricelist_sale.id,
        }
        line = {
            'product_id': self.product_32.id,
            'description': "[HEAD] Headset standard",
            'requested_qty': 100,
            'requested_uom_id': self.product_uom_pce.id,
            'date_delivery': time.strftime(D_FMT),
        }
        source = {
            'proposed_qty': 100,
            'proposed_product_id': self.product_32.id,
            'proposed_uom_id': self.product_uom_pce.id,
            'procurement_method': 'procurement',
            'price_is': 'estimated',
        }
        self.requisition = self.log_req.create(vals)
        self.line = logistic_requisition.add_line(self, self.requisition,
                                                  line)
        self.source = logistic_requisition.add_source(self, self.line,
                                                      source)
        self.requisition.button_confirm()
        logistic_requisition.assign_lines(self, self.line, self.user_demo.id)
        purch_req = logistic_requisition.create_purchase_requisition(
            self, self.source)
        purchase_requisition.confirm_call(self, purch_req)
        self.purchase_requisition = purch_req
        dp_obj = self.env['decimal.precision']
        self.uom_precision = (dp_obj
                              .sudo()
                              .precision_get('Product Unit of Measure'))

    def assertPurchaseToRequisitionLines(self, bid_lines):
        """ assert that the lines of a logistic requisition are correct
        after the generation of the purchase order.

        Checks only the lines linked with purchase lines.
        If new lines are created without being linked to a purchase line
        (remaining), they should be tested apart.
        """
        req_line = self.line
        bid_line_ids = [line.id for line in bid_lines]
        sources = [source for source in req_line.source_ids
                   if source.selected_bid_line_id.id in bid_line_ids]
        self.assertEquals(len(sources),
                          len(bid_lines),
                          "The requisition lines should be linked with the "
                          "purchase lines.")
        for source in sources:
            bid_line = source.selected_bid_line_id
            self.assertEquals(source.price_is,
                              'fixed',
                              "The requisition line price should be fixed. ")
            self.assertAlmostEquals(source.proposed_qty,
                                    bid_line.quantity_bid,
                                    places=self.uom_precision,
                                    msg="The requisition line quantity "
                                        "should be the same than the bid "
                                        "quantity. ")
            self.assertEquals(source.unit_cost,
                              bid_line.price_unit,
                              "The requisition line should have the price "
                              "proposed on the purchase order line as long as "
                              "their currency are the same ")

    def test_split_1_line_selected(self):
        """ Create a call for bids from the logistic requisition, 1 po line
        choosed

        """
        # create a first draft bid and select completely the line
        purchase, bid_line = purchase_requisition.create_draft_purchase_order(
            self, self.purchase_requisition, self.partner_1.id)
        bid_line.price_unit = 10
        purchase_order.select_line(self, bid_line, 100)
        purchase_order.bid_encoded(self, purchase)

        # close the call for bids
        purchase_requisition.close_call(self, self.purchase_requisition)
        # selection of bids will trigger the split of lines
        purchase_requisition.bids_selected(self, self.purchase_requisition)

        bid_line.refresh()

        # check if the lines are split correctly
        self.assertPurchaseToRequisitionLines([bid_line])

        req_line = self.line
        self.assertEquals(sum(source.proposed_qty for source
                              in req_line.source_ids),
                          100,
                          "The total quantity of the split lines should "
                          "be the same than requested.")
        sources = req_line.source_ids
        self.assertEquals(len(sources), 1,
                          "We should have 0 line linked with the purchase "
                          "line and no remaining line.")

    def test_split_bid_2_line_selected(self):
        """ Create a call for bids from the logistic requisition, 2 po line
        choosed

        30 items in a first purchase order and 70 items in a second one,
        for a total of 100 items.
        """
        # create a first draft bid and select a part of the line
        draft_po = purchase_requisition.create_draft_purchase_order(
            self, self.purchase_requisition, self.partner_1.id)
        purchase1, bid_line1 = draft_po
        bid_line1.price_unit = 10
        purchase_order.select_line(self, bid_line1, 30)
        purchase_order.bid_encoded(self, purchase1)

        # create a second draft bid and select a part of the line
        draft_po = purchase_requisition.create_draft_purchase_order(
            self, self.purchase_requisition, self.partner_12.id)
        purchase2, bid_line2 = draft_po
        bid_line2.price_unit = 9.5
        purchase_order.select_line(self, bid_line2, 70)
        purchase_order.bid_encoded(self, purchase2)

        # close the call for bids
        purchase_requisition.close_call(self, self.purchase_requisition)
        # selection of bids will trigger the split of lines
        purchase_requisition.bids_selected(self, self.purchase_requisition)

        bid_line1.refresh()
        bid_line2.refresh()

        # check if the lines are split correctly
        self.assertPurchaseToRequisitionLines([bid_line1, bid_line2])
        req_line = self.line
        self.assertEquals(sum(source.proposed_qty for source
                              in req_line.source_ids),
                          100,
                          "The total quantity of the split lines should "
                          "be the same than requested.")
        sources = req_line.source_ids
        self.assertEquals(len(sources), 2,
                          "We should have 2 lines linked with the purchase "
                          "lines and no remaining line.")

    def test_split_too_many_products_selected(self):
        """ Create a call for bids from the logistic requisition, 2 po line
        choosed (too many)

        30 items in a first purchase order and 80 items in a second one,
        for a total of 110 items. That means 110 products have been ordered
        but 100 only have been ordered at the origin.

        As far as the total cost is less than the requested budget, we are
        allowed to order more products than requested. In that case,
        we increase the quantity of products in the line.
        """
        # create a first draft bid and select a part of the line
        draft_po = purchase_requisition.create_draft_purchase_order(
            self, self.purchase_requisition, self.partner_1.id)
        purchase1, bid_line1 = draft_po
        bid_line1.price_unit = 10
        purchase_order.select_line(self, bid_line1, 30)
        purchase_order.bid_encoded(self, purchase1)

        # create a second draft bid and select a part of the line
        draft_po = purchase_requisition.create_draft_purchase_order(
            self, self.purchase_requisition, self.partner_12.id)
        purchase2, bid_line2 = draft_po
        bid_line2.price_unit = 7
        purchase_order.select_line(self, bid_line2, 80)
        purchase_order.bid_encoded(self, purchase2)

        # close the call for bids
        purchase_requisition.close_call(self, self.purchase_requisition)
        # selection of bids will trigger the split of lines
        purchase_requisition.bids_selected(self, self.purchase_requisition)

        bid_line1.refresh()
        bid_line2.refresh()

        # check if the lines are split correctly
        self.assertPurchaseToRequisitionLines([bid_line1, bid_line2])
        req_line = self.line
        self.assertEquals(sum(source.proposed_qty for source
                              in req_line.source_ids),
                          110,
                          "The total quantity should extend to the "
                          "quantity of the bid lines.")
        sources = req_line.source_ids
        self.assertEquals(len(sources), 2,
                          "We should have 2 lines linked with the purchase "
                          "lines and no remaining line.")

    def test_split_too_few_products_selected(self):
        """ Create a call for bids from the logistic requisition, 2 po line
        choosed (too few)

        30 items in a first purchase order and 50 items in a second one,
        for a total of 80 items. That means 80 products have been ordered
        but 100 have been ordered at the origin.

        A logistic requisition line should be created for the rest of
        the lines.
        """
        # create a first draft bid and select a part of the line
        draft_po = purchase_requisition.create_draft_purchase_order(
            self, self.purchase_requisition, self.partner_1.id)
        purchase1, bid_line1 = draft_po
        bid_line1.price_unit = 10
        purchase_order.select_line(self, bid_line1, 30)
        purchase_order.bid_encoded(self, purchase1)

        # create a second draft bid and select a part of the line
        draft_po = purchase_requisition.create_draft_purchase_order(
            self, self.purchase_requisition, self.partner_12.id)
        purchase2, bid_line2 = draft_po
        bid_line2.price_unit = 10
        purchase_order.select_line(self, bid_line2, 50)
        purchase_order.bid_encoded(self, purchase2)

        # close the call for bids
        purchase_requisition.close_call(self, self.purchase_requisition)
        # selection of bids will trigger the split of lines
        purchase_requisition.bids_selected(self, self.purchase_requisition)

        bid_line1.refresh()
        bid_line2.refresh()

        # check if the lines are split correctly
        self.assertPurchaseToRequisitionLines([bid_line1, bid_line2])

        req_line = self.line
        self.assertEquals(sum(source.proposed_qty for source
                              in req_line.source_ids),
                          80,
                          "The total quantity of the split lines should "
                          "be the same than the selected bid lines.")
        # one extra line without relation to a purchase line should have
        # been created for the rest
        sources = req_line.source_ids
        self.assertEquals(len(sources), 2,
                          "We should have 2 lines linked with the purchase "
                          "lines and no remaining line.")
