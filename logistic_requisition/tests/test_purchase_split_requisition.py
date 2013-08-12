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
        self.purchase_requisition = self.registry('purchase.requisition')
        self.get_ref = partial(self.ir_model_data.get_object_reference,
                               self.cr, self.uid)

        __, self.partner_3 = self.get_ref('base', 'res_partner_3')
        __, self.partner_4 = self.get_ref('base', 'res_partner_4')
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

        self.logistic_requisition_line_vals = {
            'product_id': self.product_7,
            'requested_qty': 100,
            'requested_uom_id': self.product_uom_pce,
            'date_delivery': time.strftime(D_FMT),
            'budget_tot_price': 1000,
            'transport_applicable': 0,
            'procurement_method': 'procurement',
            'price_is': 'estimated',
        }

    def _create_logistic_requisition(self, requisition_vals=None,
                                     lines_vals=None):
        """ Helper for creation of a logistic requisition.

        :param requisition_vals: dict of values to create the requisition
        :param line_vals: list with a dict per line to create with their values
        :returns: a tuple with (id of the requisition created,
                                [ids of the lines])
        """
        if requisition_vals is None:
            requisition_vals = self.logistic_requisition_vals
        if lines_vals is None:
            lines_vals = [self.logistic_requisition_line_vals]
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

    def _confirm_logistic_requisition(self, requisition_id):
        """ Helper to confirm a logistic requisition """
        cr, uid = self.cr, self.uid
        self.log_req.button_confirm(cr, uid, [requisition_id])

    def _assign_logistic_req_lines(self, line_ids):
        """ Helper to assign a logistic requisition line """
        self.log_req_line.write(self.cr, self.uid, line_ids,
                                {'logistic_user_id': self.user_demo})

    def test_create_call_for_bid(self):
        """ Create a call for bids from the logistic requisition """
        cr, uid = self.cr, self.uid
        requisition_id, line_ids = self._create_logistic_requisition()
        assert len(line_ids) == 1
        self._confirm_logistic_requisition(requisition_id)
        self._assign_logistic_req_lines(line_ids)
        rfq_id = self.log_req_line._action_create_po_requisition(cr, uid, line_ids)
        assert rfq_id
