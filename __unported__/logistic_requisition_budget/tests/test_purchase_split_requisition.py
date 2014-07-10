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
from openerp.osv import orm
import openerp.tests.common as common
from openerp import SUPERUSER_ID
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
        __, self.pricelist_sale = self.get_ref('product','list0')
        
        vals = {
            'partner_id': self.partner_4,
            'consignee_id': self.partner_3,
            'date_delivery': time.strftime(D_FMT),
            'user_id': self.user_demo,
            'pricelist_id': self.pricelist_sale,
        }
        line = {
            'product_id': self.product_7,
            'requested_qty': 100,
            'requested_uom_id': self.product_uom_pce,
            'date_delivery': time.strftime(D_FMT),
        }
        source = {
            'proposed_qty': 100,
            'proposed_product_id': self.product_7,
            'proposed_uom_id': self.product_uom_pce,
            'transport_applicable': 0,
            'procurement_method': 'procurement',
            'price_is': 'estimated',
        }
        self.requisition_id = logistic_requisition.create(self, vals)
        self.line_id = logistic_requisition.add_line(self, self.requisition_id,
                                                     line)
        self.source_id = logistic_requisition.add_source(self, self.line_id,
                                                         source)
        logistic_requisition.confirm(self, self.requisition_id)
        logistic_requisition.assign_lines(self, [self.line_id], self.user_demo)
        purch_req_id = logistic_requisition.create_purchase_requisition(
            self, self.source_id)
        purchase_requisition.confirm_call(self, purch_req_id)
        purch_req_model = self.registry('purchase.requisition')
        self.purchase_requisition = purch_req_model.browse(
            cr, uid, purch_req_id)
        dp_obj = self.registry('decimal.precision')
        self.uom_precision = dp_obj.precision_get(cr, SUPERUSER_ID,
                                                  'Product Unit of Measure')

    def test_split_too_many_products_selected_budget_exceeded(self):
        """ Create a call for bids from the logistic requisition, 2 po line choosed (budget exceeded)

        30 items in a first purchase order and 80 items in a second one,
        for a total of 110 items. That means 110 products have been ordered
        but 100 only have been ordered at the origin.

        The total cost is greater than the requested budget.
        We should not be able to propose more than requested financially.
        """
        # create a first draft bid and select a part of the line
        purchase1, bid_line1 = purchase_requisition.create_draft_purchase_order(
            self, self.purchase_requisition.id, self.partner_1)
        bid_line1.write({'price_unit': 15})
        purchase_order.select_line(self, bid_line1.id, 30)
        purchase_order.bid_encoded(self, purchase1.id)

        # create a second draft bid and select a part of the line
        purchase2, bid_line2 = purchase_requisition.create_draft_purchase_order(
            self, self.purchase_requisition.id, self.partner_12)
        bid_line2.write({'price_unit': 13})
        purchase_order.select_line(self, bid_line2.id, 80)
        purchase_order.bid_encoded(self, purchase2.id)

        # close the call for bids
        purchase_requisition.close_call(self, self.purchase_requisition.id)
        # selection of bids will trigger the split of lines
        # the generation of po fails because the budget is exceeded
        with self.assertRaises(orm.except_orm):
            purchase_requisition.bids_selected(self,
                                               self.purchase_requisition.id)
