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
        self.logistic_requisition_vals = {
            'partner_id': self.partner_4,
            'consignee_id': self.partner_3,
            'date_delivery': time.strftime(D_FMT),
            'user_id': self.user_demo,
            'budget_holder_id': self.user_demo,
            'finance_officer_id': self.user_demo,
        }

        self.logistic_requisition_line_vals = [{
            'product_id': self.product_7,
            'requested_qty': 100,
            'requested_uom_id': self.product_uom_pce,
            'date_delivery': time.strftime(D_FMT),
            'budget_tot_price': 1000,
            'transport_applicable': 0,
            'procurement_method': 'procurement',
            'price_is': 'estimated',
        }]
        self.requisition_id, self.line_ids = self._create_logistic_requisition()
        self.assertEquals(len(self.line_ids), 1)
        self._confirm_logistic_requisition()
        self._assign_logistic_req_lines()
        purch_req_id = self.log_req_line._action_create_po_requisition(
            cr, uid, self.line_ids)
        assert purch_req_id
        purch_req_model = self.registry('purchase.requisition')
        self.purchase_requisition = purch_req_model.browse(cr, uid, purch_req_id)

    def _create_logistic_requisition(self):
        """ Create a logistic requisition.

        :param requisition_vals: dict of values to create the requisition
        :param line_vals: list with a dict per line to create with their values
        :returns: a tuple with (id of the requisition created,
                                [ids of the lines])
        """
        requisition_vals = self.logistic_requisition_vals
        lines_vals = self.logistic_requisition_line_vals
        cr, uid = self.cr, self.uid

        requisition_vals.update(
            self.log_req.onchange_requester_id(
                cr, uid, [], requisition_vals.get('partner_id'))['value']
        )
        requisition_vals.update(
            self.log_req.onchange_consignee_id(
                cr, uid, [], requisition_vals.get('consignee_id'))['value']
        )
        requisition_vals.update(
            self.log_req.onchange_validate(
                cr, uid, [],
                requisition_vals.get('budget_holder_id'),
                False,
                'date_budget_holder')['value']
        )
        requisition_vals.update(
            self.log_req.onchange_validate(
                cr, uid, [],
                requisition_vals.get('finance_officer_id'),
                False,
                'date_finance_officer')['value']
        )
        requisition_id = self.log_req.create(cr, uid, requisition_vals)
        line_ids = []
        for row_vals in lines_vals:
            row_vals['requisition_id'] = requisition_id
            row_vals.update(
                self.log_req_line.onchange_product_id(
                    cr, uid, [],
                    row_vals.get('product_id'),
                    row_vals.get('requested_uom_id'))['value']
            )
            row_vals.update(
                self.log_req_line.onchange_transport_plan_id(
                    cr, uid, [],
                    row_vals.get('transport_plan_id'))['value']
            )
            line_id = self.log_req_line.create(cr, uid, row_vals)
            line_ids.append(line_id)
        return requisition_id, line_ids

    def _confirm_logistic_requisition(self):
        """ Helper to confirm a logistic requisition """
        cr, uid = self.cr, self.uid
        self.log_req.button_confirm(cr, uid, [self.requisition_id])

    def _assign_logistic_req_lines(self):
        """ Helper to assign a logistic requisition line """
        self.log_req_line.write(self.cr, self.uid, self.line_ids,
                                {'logistic_user_id': self.user_demo})

    def _make_po_draft(self, partner_id):
        cr, uid = self.cr, self.uid
        res = self.purchase_requisition.make_purchase_order(partner_id)
        purch_id = res[self.purchase_requisition.id]
        assert purch_id
        purchase = self.purchase_order.browse(cr, uid, purch_id)
        self.assertEquals(len(purchase.order_line), 1)
        purchase_line = purchase.order_line[0]
        return purchase_line

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
        purchase_line = self._make_po_draft(self.partner_1)
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
        purchase_line1 = self._make_po_draft(self.partner_1)
        # select the quantity and set a price
        purchase_line1.write({'price_unit': 15,
                              'quantity_bid': 30})
        purchase_line2 = self._make_po_draft(self.partner_12)
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
        purchase_line1 = self._make_po_draft(self.partner_1)
        # select the quantity and set a price
        purchase_line1.write({'price_unit': 15,
                              'quantity_bid': 30})
        purchase_line2 = self._make_po_draft(self.partner_12)
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
        purchase_line1 = self._make_po_draft(self.partner_1)
        # select the quantity and set a price
        purchase_line1.write({'price_unit': 15,
                              'quantity_bid': 30})
        purchase_line2 = self._make_po_draft(self.partner_12)
        purchase_line2.write({'price_unit': 13,
                              'quantity_bid': 50})
        purchase_line2.action_confirm()
        with self.assertRaises(AssertionError):
            self.purchase_requisition.generate_po()
