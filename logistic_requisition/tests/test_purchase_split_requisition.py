# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
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

import time
import unittest2
from functools import partial

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as D_FMT
import openerp.tests.common as common
from .logistic_requisition import create, confirm, assign_lines
from .purchase_requisition import create_draft_purchase_order


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
        cr, uid = self.cr, self.uid
        self.ir_model_data = self.registry('ir.model.data')
        self.log_req = self.registry('logistic.requisition')
        self.log_req_line = self.registry('logistic.requisition.line')
        self.purchase_order = self.registry('purchase.order')
        self.get_ref = partial(self.ir_model_data.get_object_reference,
                               self.cr, self.uid)

        __, self.partner_1 = self.get_ref('base', 'res_partner_1')
        __, self.partner_3 = self.get_ref('base', 'res_partner_3')
        __, self.partner_4 = self.get_ref('base', 'res_partner_4')
        __, self.partner_12 = self.get_ref('base', 'res_partner_12')
        __, self.user_demo = self.get_ref('base', 'user_demo')
        __, self.product_7 = self.get_ref('product', 'product_product_7')
        __, self.product_uom_pce = self.get_ref('product', 'product_uom_unit')
        self.vals = {
            'partner_id': self.partner_4,
            'consignee_id': self.partner_3,
            'date_delivery': time.strftime(D_FMT),
            'user_id': self.user_demo,
            'budget_holder_id': self.user_demo,
            'finance_officer_id': self.user_demo,
        }

        self.lines = [{
            'product_id': self.product_7,
            'requested_qty': 100,
            'requested_uom_id': self.product_uom_pce,
            'date_delivery': time.strftime(D_FMT),
            'budget_tot_price': 1000,
            'transport_applicable': 0,
            'procurement_method': 'procurement',
            'price_is': 'estimated',
        }]
        self.requisition_id, self.line_ids = create(self, self.vals, self.lines)
        self.assertEquals(len(self.line_ids), 1)
        confirm(self, self.requisition_id)
        assign_lines(self, self.line_ids, self.user_demo)
        purch_req_id = self.log_req_line._action_create_po_requisition(
            cr, uid, self.line_ids)
        assert purch_req_id
        purch_req_model = self.registry('purchase.requisition')
        self.purchase_requisition = purch_req_model.browse(cr, uid, purch_req_id)

    def assertPurchaseToRequisitionLines(self, purchase_lines):
        """ assert that the lines of a logistic requisition are correct
        after the generation of the purchase order """
        requisition = self.log_req.browse(self.cr, self.uid,
                                          self.requisition_id)
        self.assertEquals(len(requisition.line_ids),
                          len(purchase_lines),
                          "We should have the same count of requisition "
                          "lines and purchase order lines. ")
        self.assertEquals(sorted([pline.id for pline in purchase_lines]),
                          sorted([rline.purchase_line_id.id for rline in
                                  requisition.line_ids]),
                          "The requisition lines should be linked with the "
                          "purchase lines.")
        for rline in requisition.line_ids:
            purchase_line = rline.purchase_line_id
            self.assertEquals(rline.price_is,
                              'fixed',
                              "The requisition line price should be fixed. ")
            self.assertEquals(rline.proposed_qty,
                              purchase_line.quantity_bid,
                              "The requisition line quantity should be "
                              "the same than the bid quantity. ")
            self.assertEquals(rline.unit_cost,
                              purchase_line.price_unit,
                              "The requisition line should have the price "
                              "proposed on the purchase order line. ")

    def test_create_call_for_bid_1_line(self):
        """ Create a call for bids from the logistic requisition, 1 po line choosed """
        cr, uid = self.cr, self.uid
        __, purchase_line = create_draft_purchase_order(
            self, self.purchase_requisition.id, self.partner_1)
        # select the quantity and set a price
        purchase_line.write({'price_unit': 12,
                             'quantity_bid': 100})
        purchase_line.action_confirm()
        self.purchase_requisition.generate_po()
        purchase_line.refresh()
        self.assertPurchaseToRequisitionLines([purchase_line])

    def test_create_call_for_bid_2_line(self):
        """ Create a call for bids from the logistic requisition, 2 po line choosed

        30 items in a first purchase order and 70 items in a second one,
        for a total of 100 items.
        """
        __, purchase_line1 = create_draft_purchase_order(
            self, self.purchase_requisition.id, self.partner_1)
        # select the quantity and set a price
        purchase_line1.write({'price_unit': 15,
                              'quantity_bid': 30})
        __, purchase_line2 = create_draft_purchase_order(
            self, self.purchase_requisition.id, self.partner_12)
        purchase_line2.write({'price_unit': 13,
                              'quantity_bid': 70})
        purchase_line2.action_confirm()
        self.purchase_requisition.generate_po()
        purchase_line1.refresh()
        purchase_line2.refresh()
        self.assertPurchaseToRequisitionLines([purchase_line1,
                                               purchase_line2])

    def test_create_call_for_bid_too_many_products(self):
        """ Create a call for bids from the logistic requisition, 2 po line choosed (too many)

        30 items in a first purchase order and 80 items in a second one,
        for a total of 110 items. That means 110 products have been ordered
        but 100 only have been ordered at the origin.
        """
        __, purchase_line1 = create_draft_purchase_order(
            self, self.purchase_requisition.id, self.partner_1)
        # select the quantity and set a price
        purchase_line1.write({'price_unit': 15,
                              'quantity_bid': 30})
        __, purchase_line2 = create_draft_purchase_order(
            self, self.purchase_requisition.id, self.partner_12)
        purchase_line2.write({'price_unit': 13,
                              'quantity_bid': 80})
        purchase_line2.action_confirm()
        self.purchase_requisition.generate_po()
        purchase_line1.refresh()
        purchase_line2.refresh()
        self.assertPurchaseToRequisitionLines([purchase_line1,
                                               purchase_line2])

    def test_create_call_for_bid_too_few_products(self):
        """ Create a call for bids from the logistic requisition, 2 po line choosed (too few)

        30 items in a first purchase order and 50 items in a second one,
        for a total of 80 items. That means 80 products have been ordered
        but 100 have been ordered at the origin.

        It fails because not all the quantities have been purchased.
        """
        __, purchase_line1 = create_draft_purchase_order(
            self, self.purchase_requisition.id, self.partner_1)
        # select the quantity and set a price
        purchase_line1.write({'price_unit': 15,
                              'quantity_bid': 30})
        __, purchase_line2 = create_draft_purchase_order(
            self, self.purchase_requisition.id, self.partner_12)
        purchase_line2.write({'price_unit': 13,
                              'quantity_bid': 50})
        purchase_line2.action_confirm()
        with self.assertRaises(AssertionError):
            self.purchase_requisition.generate_po()
