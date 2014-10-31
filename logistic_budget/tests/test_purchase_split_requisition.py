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
from openerp import exceptions
import openerp.tests.common as common
from openerp.addons.logistic_requisition.tests import logistic_requisition
from openerp.addons.logistic_requisition.tests import purchase_requisition
from openerp.addons.logistic_requisition.tests import purchase_order


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

    def test_split_too_many_products_selected_budget_exceeded(self):
        """ Create a call for bids from the logistic requisition, 2 po line
        choosed (budget exceeded)

        30 items in a first purchase order and 80 items in a second one,
        for a total of 110 items. That means 110 products have been ordered
        but 100 only have been ordered at the origin.

        The total cost is greater than the requested budget.
        We should not be able to propose more than requested financially.
        """
        # create a first draft bid and select a part of the line
        draft_po = purchase_requisition.create_draft_purchase_order(
            self, self.purchase_requisition, self.partner_1.id)
        purchase1, bid_line1 = draft_po
        bid_line1.price_unit = 15
        purchase_order.select_line(self, bid_line1, 30)
        purchase_order.bid_encoded(self, purchase1)

        # create a second draft bid and select a part of the line
        draft_po = purchase_requisition.create_draft_purchase_order(
            self, self.purchase_requisition, self.partner_12.id)
        purchase2, bid_line2 = draft_po
        bid_line2.price_unit = 13
        purchase_order.select_line(self, bid_line2, 80)
        purchase_order.bid_encoded(self, purchase2)

        # close the call for bids
        purchase_requisition.close_call(self, self.purchase_requisition)
        # selection of bids will trigger the split of lines
        # the generation of po fails because the budget is exceeded
        with self.assertRaises(exceptions.ValidationError):
            purchase_requisition.bids_selected(self,
                                               self.purchase_requisition)
