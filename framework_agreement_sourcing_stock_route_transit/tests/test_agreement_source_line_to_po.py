# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2013-2015 Camptocamp SA
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
import openerp.addons.framework_agreement_sourcing.tests as fa_sourcing_test

base_test = fa_sourcing_test.test_agreement_source_line_to_po


class TestSourceToPoTransit(base_test.TestSourceToPo):

    def setUp(self):
        # we generate a source line
        super(TestSourceToPoTransit, self).setUp()
        self.wh.write({'reception_steps': 'transit_three_steps',
                       'delivery_steps': 'pick_pack_ship_transit'})

    def test_01_transform_source_to_agreement_wh_dest(self):
        """Test transformation of an LRS sourced by FA to PO
        delivering to WH"""
        cr, uid = self.cr, self.uid

        # Set destination address
        partner_vals = {
            'name': 'Warehouse address',
            }
        partner_wh = self.env['res.partner'].create(partner_vals)
        self.wh.partner_id = partner_wh
        picking_type_wh = self.wh.transit_in_type_id
        self.agr_line.consignee_shipping_id = partner_wh

        self.assertTrue(self.lta_source, 'no lta source found')
        self.lta_source.refresh()
        active_ids = [x.id for x in self.source_lines]
        wiz_ctx = {'active_model': 'logistic.requisition.source',
                   'active_ids': active_ids}
        wiz_id = self.wiz_model.create(self.cr, self.uid, {},
                                       context=wiz_ctx)

        po_id = self.wiz_model.action_create_agreement_po_requisition(
            cr, uid, [wiz_id], context=wiz_ctx)['res_id']
        self.assertTrue(po_id, "no PO created")
        supplier = self.lta_source.framework_agreement_id.supplier_id
        add = self.lta_source.requisition_id.consignee_shipping_id
        consignee = self.lta_source.requisition_id.consignee_id
        po = self.registry('purchase.order').browse(cr, uid, po_id)
        date_order = self.lta_source.requisition_id.date
        date_delivery = self.lta_source.requisition_id.date_delivery
        self.assertEqual(po.partner_id, supplier)
        self.assertEqual(
            po.pricelist_id, supplier.property_product_pricelist_purchase)
        self.assertEqual(po.date_order, date_order)
        self.assertEqual(po.dest_address_id, add)
        self.assertEqual(po.picking_type_id.name, picking_type_wh.name)
        self.assertEqual(po.picking_type_id, picking_type_wh)
        self.assertEqual(po.consignee_id, consignee)
        self.assertEqual(po.state, 'draftpo')
        self.assertNotEqual(po.name, self.requisition.name)
        self.assertEqual(len(po.order_line), 2)
        self.assertEqual(po.location_id.name,
                         self.wh.wh_transit_in_loc_id.name)
        self.assertEqual(po.location_id, self.wh.wh_transit_in_loc_id)
        po_line = next(x for x in po.order_line
                       if x.product_id ==
                       self.lta_source.framework_agreement_id.product_id)
        self.assertEqual(po_line.product_qty, self.lta_source.proposed_qty)
        self.assertEqual(
            po_line.product_id, self.lta_source.proposed_product_id)
        self.assertEqual(po_line.product_qty, self.lta_source.proposed_qty)
        self.assertEqual(po_line.product_uom, self.lta_source.proposed_uom_id)
        self.assertAlmostEqual(po_line.price_unit, 50.0)
        self.assertEqual(po_line.lr_source_line_id, self.lta_source)
        self.assertEqual(po_line.date_planned, date_delivery)

        po_line = next(x for x in po.order_line
                       if x.product_id ==
                       self.other_source.proposed_product_id)
        self.assertEqual(po_line.product_qty, self.other_source.proposed_qty)
        self.assertEqual(
            po_line.product_id, self.other_source.proposed_product_id)
        self.assertEqual(po_line.product_qty, self.other_source.proposed_qty)
        self.assertEqual(
            po_line.product_uom, self.other_source.proposed_uom_id)
        self.assertAlmostEqual(po_line.price_unit, 1.0)
        self.assertEqual(po_line.lr_source_line_id, self.other_source)

    def test_02_transform_source_to_agreement_dropshipping(self):
        """Test transformation of an LRS sourced by FA to PO dropshipping"""
        cr, uid = self.cr, self.uid

        # Set destination address
        partner_dropship = self.ref('base.res_partner_12')
        self.agr_line.consignee_shipping_id = partner_dropship

        self.assertTrue(self.lta_source, 'no lta source found')
        self.lta_source.refresh()
        active_ids = [x.id for x in self.source_lines]
        wiz_ctx = {'active_model': 'logistic.requisition.source',
                   'active_ids': active_ids}
        wiz_id = self.wiz_model.create(self.cr, self.uid, {}, context=wiz_ctx)

        po_id = self.wiz_model.action_create_agreement_po_requisition(
            cr, uid, [wiz_id], context=wiz_ctx)['res_id']
        self.assertTrue(po_id, "no PO created")
        supplier = self.lta_source.framework_agreement_id.supplier_id
        add = self.lta_source.requisition_id.consignee_shipping_id
        consignee = self.lta_source.requisition_id.consignee_id
        po = self.registry('purchase.order').browse(cr, uid, po_id)
        date_order = self.lta_source.requisition_id.date
        date_delivery = self.lta_source.requisition_id.date_delivery
        self.assertEqual(po.partner_id, supplier)
        self.assertEqual(
            po.pricelist_id, supplier.property_product_pricelist_purchase)
        self.assertEqual(po.date_order, date_order)
        self.assertEqual(po.dest_address_id, add)
        self.assertEqual(po.picking_type_id.name, 'Dropship')
        self.assertEqual(po.location_id, self.wh.wh_transit_out_loc_id)
        self.assertEqual(po.consignee_id, consignee)
        self.assertEqual(po.state, 'draftpo')
        self.assertNotEqual(po.name, self.requisition.name)
        self.assertEqual(len(po.order_line), 2)

        po_line = next(x for x in po.order_line
                       if x.product_id ==
                       self.lta_source.framework_agreement_id.product_id)
        self.assertEqual(po_line.product_qty, self.lta_source.proposed_qty)
        self.assertEqual(
            po_line.product_id, self.lta_source.proposed_product_id)
        self.assertEqual(po_line.product_qty, self.lta_source.proposed_qty)
        self.assertEqual(po_line.product_uom, self.lta_source.proposed_uom_id)
        self.assertAlmostEqual(po_line.price_unit, 50.0)
        self.assertEqual(po_line.lr_source_line_id, self.lta_source)
        self.assertEqual(po_line.date_planned, date_delivery)

        po_line = next(x for x in po.order_line
                       if x.product_id ==
                       self.other_source.proposed_product_id)
        self.assertEqual(po_line.product_qty, self.other_source.proposed_qty)
        self.assertEqual(
            po_line.product_id, self.other_source.proposed_product_id)
        self.assertEqual(po_line.product_qty, self.other_source.proposed_qty)
        self.assertEqual(
            po_line.product_uom, self.other_source.proposed_uom_id)
        self.assertAlmostEqual(po_line.price_unit, 1.0)
        self.assertEqual(po_line.lr_source_line_id, self.other_source)
