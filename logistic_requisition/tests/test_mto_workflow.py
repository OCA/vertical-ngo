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
        self.log_req_model = self.env['logistic.requisition']
        self.log_req_line_model = self.env['logistic.requisition.line']
        self.purchase_order_model = self.env['purchase.order']
        self.purch_req_model = self.env['purchase.requisition']
        self.sale_model = self.env['sale.order']
        self.picking_in_model = self.env['stock.picking']

        data_model = self.env['ir.model.data']
        self.partner_1 = data_model.xmlid_to_object('base.res_partner_1')
        self.partner_3 = data_model.xmlid_to_object('base.res_partner_3')
        self.partner_4 = data_model.xmlid_to_object('base.res_partner_4')
        self.partner_12 = data_model.xmlid_to_object('base.res_partner_12')
        self.user_demo = data_model.xmlid_to_object('base.user_demo')
        route_mto_id = self.ref('stock.route_warehouse0_mto')
        self.product_32 = data_model.xmlid_to_object(
            'product.product_product_32')
        self.browse_ref('product.product_product_32').write(
            {'route_ids': [(6, 0, [route_mto_id])]})
        self.product_25 = data_model.xmlid_to_object(
            'product.product_product_25')
        self.browse_ref('product.product_product_25').write(
            {'route_ids': [(6, 0, [route_mto_id])]})
        self.product_uom_pce = data_model.xmlid_to_object(
            'product.product_uom_unit')
        self.pricelist_sale = data_model.xmlid_to_object('product.list0')
        self.vals = {
            'partner_id': self.partner_4.id,
            'consignee_id': self.partner_3.id,
            'date_delivery': time.strftime(D_FMT),
            'user_id': self.user_demo.id,
            'pricelist_id': self.pricelist_sale.id,
        }
        self.line_vals = {
            'product_id': self.product_32.id,
            'description': "[HEAD] Headset standard",
            'requested_qty': 100,
            'requested_uom_id': self.product_uom_pce.id,
            'date_delivery': time.strftime(D_FMT),
            'account_code': 'a code',
            'source_ids': [{'proposed_qty': 100,
                            'proposed_product_id': self.product_32.id,
                            'proposed_uom_id': self.product_uom_pce.id,
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
        # logistic requisition creation
        requisition = self.log_req_model.create(self.vals)
        lines = self.log_req_line_model.browse()
        purchase_orders = []
        for line_vals in lines_vals:
            source_vals = line_vals.pop('source_ids')
            line = logistic_requisition.add_line(
                self, requisition, line_vals)
            requisition.button_confirm()
            logistic_requisition.assign_lines(self, line, self.user_demo.id)
            for src_vals in source_vals:
                source = logistic_requisition.add_source(
                    self, line, src_vals)

                # purchase requisition creation, bids selection
                purch_req = logistic_requisition.create_purchase_requisition(
                    self, source)
                purchase_requisition.confirm_call(self, purch_req)
                draft_po = purchase_requisition.create_draft_purchase_order(
                    self, purch_req, self.partner_1.id)
                bid, bid_line = draft_po
                bid_line.write({'price_unit': 10})
                purchase_order.select_line(self, bid_line,
                                           src_vals['proposed_qty'])
                purchase_order.bid_encoded(self, bid)
                purchase_requisition.close_call(self, purch_req)
                purchase_requisition.bids_selected(self, purch_req)
                purch_req.generate_po()
                po = self.env['purchase.order'].search(
                    [('requisition_id', '=', purch_req.id),
                     ('type', '=', 'purchase'),
                     ('state', 'in', ['approved'])])
                purchase_orders.append(po)

            lines |= line

        # set lines as sourced
        logistic_requisition.source_lines(self, lines)

        # sales order creation
        sale, __ = logistic_requisition.create_quotation(
            self, requisition, lines)

        for line in sale.order_line:
            for po in purchase_orders:
                po.order_line.ensure_one()
                if line.product_id == po.order_line.product_id:
                    line.sourced_by = po.order_line.id
                    break
        # the confirmation of the sale order link the
        # purchase order on the purchase requisition
        sale.signal_workflow('order_confirm')
        sale.action_ship_create()
        return requisition, lines, sale

    def _check_sale_line(self, sale_line):
        """ For a sales order lines, """
        # check if the sale order line is linked with the purchase order
        # line
        assert sale_line.sourced_by
        self.assertTrue(sale_line.manually_sourced,
                        "The sale order line should be set as manually "
                        "sourced")

        # check if the procurement is linked with the correct purchase
        # order
        purchase = sale_line.sourced_by.order_id
        # proc = sale_line.procurement_group_id.procurement_ids
        # XXX procurement isn't linked to a PO yet ???
        # self.assertEquals(proc.purchase_id, purchase,
        #                 "The purchase of the procurement should be "
        #                 "the same than the one generated by the purchase "
        #                 "requisition.")

        self.assertEquals(purchase.state, 'approved')

        # the incoming shipment of the purchase order has been generated
        purchase.refresh()
        self.assertEquals(len(purchase.picking_ids), 1)
        picking = purchase.picking_ids[0]
        # receive it
        picking.do_transfer()
        self.assertEquals(picking.state, 'done')

        # the purchase order should be received as we received the
        # picking
        self.assertTrue(purchase.shipped,
                        "The sales order should be considered as 'received' "
                        "because the picking 'in' has been received.")

    def test_workflow_with_1_line(self):
        """ Test the full workflow and check if sale and purchase are both
        delivered

        """
        requisition, lines, sale = self._setup_initial_data([self.line_vals])

        assert len(sale.order_line) == 1
        self._check_sale_line(sale.order_line[0])

        # the sale order should be delivered as well
        # XXX sale procurement is in exception
        # self.assertTrue(sale.shipped,
        #                 "The sales order should be considered as 'shipped' "
        #                 "because the procurement is the same than the one "
        #                 "of the purchase order.")

    def test_workflow_with_2_lines(self):
        """ Test the full workflow and check if sale and purchase are both
        delivered for 2 lines

        """
        # add a line in the logistic requisition
        line2 = {
            'product_id': self.product_25.id,
            'description': "[LAP-E5] Laptop E5023",
            'requested_qty': 200,
            'requested_uom_id': self.product_uom_pce.id,
            'date_delivery': time.strftime(D_FMT),
            'account_code': 'a code',
            'source_ids': [{'proposed_qty': 200,
                            'proposed_product_id': self.product_25.id,
                            'proposed_uom_id': self.product_uom_pce.id,
                            'procurement_method': 'procurement',
                            'price_is': 'estimated'}],
        }
        lines = [self.line_vals, line2]
        requisition, lines, sale = self._setup_initial_data(lines)

        # the confirmation of the sale order generates the
        # purchase order of the purchase requisition
        assert len(sale.order_line) == 2
        self._check_sale_line(sale.order_line[0])

        self.assertFalse(sale.shipped,
                         "The sale is not shipped, not all lines "
                         "are delivered")
        self._check_sale_line(sale.order_line[1])

        # the sale order should be delivered as well
        # XXX sale procurement is in exception
        # self.assertTrue(sale.shipped,
        #                 "The sales order should be 'shipped' "
        #                 "because the procurement is the same than the one "
        #                 "of the purchase order.")
