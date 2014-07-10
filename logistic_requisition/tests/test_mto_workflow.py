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

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as D_FMT
import openerp.tests.common as common
from openerp import netsvc
from . import logistic_requisition
from . import purchase_requisition
from . import purchase_order


class test_mto_workflow(common.TransactionCase):
    """ Test the workflows of MTO products accross the models
    logistic requisition, to purchase orders, to sale orders
    passing through stock pickings.

    We create a logistic requisition for 100 products A.
    From there, we create a purchase requisition for these products.
    From the purchase requisition, we create one or several bids. We
    select lines to keep in the bids.

    From the logistic requisition (now sourced), we create a sales
    order. This sales order is confirmed, and the full complexity
    appears now. At the moment when the sales order is confirmed,
    a purchase quotation is generated (using the selected bid lines).

    The sales order lines created in this way are MTO and direct
    delivery (dropshipping). The procurement generated for these lines
    should be linked to the purchase quotation created before and not
    generate a new one. The stock move (reservation) of the procurement
    should be the same than the stock move generated for the Incoming
    Shipment of the purchase order.

    Finally, when the Incoming Shipment of the purchase order is done,
    the sales orders should be "delivered" and the purchase order
    should be "received" as well.

    In order to achieve that, when the procurement of the sales order line
    is generated, we leave the procurement as draft, we link it with the PO
    and we leave the move_id empty. Only at the moment when the picking
    of the purchase order is generated, we link the procurement's move_id
    to the picking's move and confirm the procurement.
    """

    def setUp(self):
        super(test_mto_workflow, self).setUp()
        self.log_req_model = self.registry('logistic.requisition')
        self.log_req_line_model = self.registry('logistic.requisition.line')
        self.purchase_order_model = self.registry('purchase.order')
        self.purch_req_model = self.registry('purchase.requisition')
        self.sale_model = self.registry('sale.order')
        self.picking_in_model = self.registry('stock.picking.in')

        self.partner_1 = self.ref('base.res_partner_1')
        self.partner_3 = self.ref('base.res_partner_3')
        self.partner_4 = self.ref('base.res_partner_4')
        self.partner_12 = self.ref('base.res_partner_12')
        self.user_demo = self.ref('base.user_demo')
        self.product_7 = self.ref('product.product_product_7')
        self.browse_ref('product.product_product_7').write({'procure_method': 'make_to_order'})
        self.product_8 = self.ref('product.product_product_8')
        self.browse_ref('product.product_product_8').write({'procure_method': 'make_to_order'})
        self.product_uom_pce = self.ref('product.product_uom_unit')
        self.pricelist_sale = self.ref('product.list0')
        self.vals = {
            'partner_id': self.partner_4,
            'consignee_id': self.partner_3,
            'date_delivery': time.strftime(D_FMT),
            'user_id': self.user_demo,
            'pricelist_id' : self.pricelist_sale,
        }
        self.line = {
            'product_id': self.product_7,
            'requested_qty': 100,
            'requested_uom_id': self.product_uom_pce,
            'date_delivery': time.strftime(D_FMT),
            'account_code': 'a code',
            'source_ids': [{'proposed_qty': 100,
                            'proposed_product_id': self.product_7,
                            'proposed_uom_id': self.product_uom_pce,
                            'transport_applicable': 0,
                            'procurement_method': 'procurement',
                            'price_is': 'estimated'}],
        }

    def _setup_initial_data(self, lines_vals):
        """ Create objects and initialize the data for the tests

            - creates and confirm a logistic requisition
            - assign the lines
            - create a purchase requisition and bids for the lines
            - source the lines
            - Create a sales quotation
        """
        cr, uid = self.cr, self.uid
        # logistic requisition creation
        requisition_id = logistic_requisition.create(self, self.vals)
        line_ids = []
        for line_vals in lines_vals:
            source_vals = line_vals.pop('source_ids')
            line_id = logistic_requisition.add_line(
                self, requisition_id, line_vals)
            logistic_requisition.confirm(self, requisition_id)
            logistic_requisition.assign_lines(self, [line_id], self.user_demo)
            for src_vals in source_vals:
                source_id = logistic_requisition.add_source(
                    self, line_id, src_vals)

                # purchase requisition creation, bids selection
                purch_req_id = logistic_requisition.create_purchase_requisition(
                    self, source_id)
                purchase_requisition.confirm_call(self, purch_req_id)
                bid, bid_line = purchase_requisition.create_draft_purchase_order(
                    self, purch_req_id, self.partner_1)
                bid_line.write({'price_unit': 10})
                purchase_order.select_line(self, bid_line.id,
                                           src_vals['proposed_qty'])
                purchase_order.bid_encoded(self, bid.id)
                purchase_requisition.close_call(self, purch_req_id)
                purchase_requisition.bids_selected(self, purch_req_id)
            line_ids.append(line_id)

        # set lines as sourced
        logistic_requisition.source_lines(self, line_ids)

        # sales order creation
        sale_id, __ = logistic_requisition.create_quotation(
            self, requisition_id, line_ids)

        # the confirmation of the sale order generates the
        # purchase order of the purchase requisition
        self.sale_model.action_button_confirm(cr, uid, [sale_id])
        return requisition_id, line_ids, sale_id

    def _check_sale_line(self, sale_line):
        """ For a sales order lines, """
        cr, uid = self.cr, self.uid
        # check if the sale order line is linked with the purchase order
        # line
        self.assertTrue(sale_line.purchase_order_line_id)
        self.assertTrue(sale_line.purchase_order_id)

        # check if the procurement is linked with the correct purchase
        # order
        purchase = sale_line.purchase_order_id
        procurement = sale_line.procurement_id
        self.assertEquals(procurement.purchase_id, purchase,
                        "The purchase of the procurement should be "
                        "the same than the one generated by the purchase "
                        "requisition.")

        # confirm the purchase order
        self.assertEquals(purchase.state, 'draftpo')
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'purchase.order',
                                purchase.id, 'purchase_confirm', cr)
        purchase.refresh()
        self.assertEquals(purchase.state, 'approved')

        # the incoming shipment of the purchase order has been generated
        purchase.refresh()
        self.assertEquals(len(purchase.picking_ids), 1)
        picking = purchase.picking_ids[0]
        # receive it
        receive_obj = self.registry('stock.partial.picking')
        wizard_id = receive_obj.create(cr, uid, {},
                                       {'active_model': 'stock.picking.in',
                                        'active_id': picking.id,
                                        'active_ids': [picking.id]})
        receive_obj.do_partial(cr, uid, [wizard_id])
        picking.refresh()
        self.assertEquals(picking.state, 'done')

        # the purchase order should be received as we received the
        # picking
        purchase.refresh()
        self.assertTrue(purchase.shipped,
                        "The sales order should be considered as 'received' "
                        "because the picking 'in' has been received.")

    def test_workflow_with_1_line(self):
        """ Test the full workflow and check if sale and purchase are both delivered """
        cr, uid = self.cr, self.uid
        requisition_id, line_ids, sale_id = self._setup_initial_data([self.line])

        sale = self.sale_model.browse(cr, uid, sale_id)
        assert len(sale.order_line) == 1
        assert sale.order_line[0].type == 'make_to_order'
        self._check_sale_line(sale.order_line[0])

        # the sale order should be delivered as well
        sale.refresh()
        self.assertTrue(sale.shipped,
                        "The sales order should be considered as 'shipped' "
                        "because the procurement is the same than the one "
                        "of the purchase order.")

    def test_workflow_with_2_lines(self):
        """ Test the full workflow and check if sale and purchase are both delivered for 2 lines """
        cr, uid = self.cr, self.uid
        # add a line in the logistic requisition
        line2 = {
            'product_id': self.product_8,
            'requested_qty': 200,
            'requested_uom_id': self.product_uom_pce,
            'date_delivery': time.strftime(D_FMT),
            'account_code': 'a code',
            'source_ids': [{'proposed_qty': 200,
                            'proposed_product_id': self.product_8,
                            'proposed_uom_id': self.product_uom_pce,
                            'transport_applicable': 0,
                            'procurement_method': 'procurement',
                            'price_is': 'estimated'}],
        }
        lines = [self.line, line2]
        requisition_id, line_ids, sale_id = self._setup_initial_data(lines)

        # the confirmation of the sale order generates the
        # purchase order of the purchase requisition
        sale = self.sale_model.browse(cr, uid, sale_id)
        assert len(sale.order_line) == 2
        self._check_sale_line(sale.order_line[0])
        sale.refresh()
        self.assertFalse(sale.shipped,
                         "The sale is not shipped, not all lines "
                         "are delivered")
        self._check_sale_line(sale.order_line[1])

        # the sale order should be delivered as well
        sale.refresh()
        self.assertTrue(sale.shipped,
                        "The sales order should be 'shipped' "
                        "because the procurement is the same than the one "
                        "of the purchase order.")
