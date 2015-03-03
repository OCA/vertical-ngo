# -*- coding: utf-8 -*-
#
#
#    Author: Yannick Vaucher
#    Copyright 2014-2015 Camptocamp SA
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
#
from functools import partial

from openerp.tests.common import TransactionCase


def lrl_gen_donor_src(self):
    values = self._prepare_donor_source()
    LRS = self.env['logistic.requisition.source']
    new_lrs = LRS.new(values)
    if self.source_ids:
        self.source_ids |= new_lrs
    else:
        self.source_ids = new_lrs


class TestAutoCreateSources(TransactionCase):
    """Test that when confirming a Logistic Requisition in Donor Stock Dispatch
    that all the source lines are created correctly.

    """
    def test_create_source_for_no_location(self):
        self.lrl._generate_sources()
        sources = self.lrl.source_ids
        self.assertEquals(len(sources), 1)
        self.assertEquals(sources.sourcing_method, 'other')

    def test_create_source_for_single_location(self):
        """ Have product on a single location to check
        location is set
        """
        self.env['stock.quant'].create({
            'product_id': self.product_id,
            'owner_id': self.owner_id,
            'qty': 100,
            'location_id': self.ref('stock.stock_location_stock'),
        })
        self.lrl._generate_sources()
        sources = self.lrl.source_ids
        self.assertEquals(len(sources), 1)
        self.assertEquals(sources.sourcing_method, 'wh_dispatch')
        self.assertEquals(
            sources.dispatch_warehouse_id.lot_stock_id.id,
            self.ref('stock.stock_location_stock')
        )

    def test_create_source_for_multiple_location(self):
        Quant = self.env['stock.quant']
        Quant.create({
            'product_id': self.product_id,
            'owner_id': self.owner_id,
            'qty': 100,
            'location_id': self.ref('stock.stock_location_stock'),
        })
        Quant.create({
            'product_id': self.product_id,
            'owner_id': self.owner_id,
            'qty': 100,
            'location_id': self.ref('stock.stock_location_components'),
        })
        self.lrl._generate_sources()
        sources = self.lrl.source_ids
        self.assertEquals(len(sources), 1)
        self.assertEquals(sources.sourcing_method, 'wh_dispatch')
        self.assertFalse(sources.dispatch_location_id.id)

    def setUp(self):
        """Setup a logistic requisition line.

        """
        super(TestAutoCreateSources, self).setUp()
        self.owner_id = self.ref('base.res_partner_12')
        self.product_id = self.ref('product.product_product_12')
        lr = self.env['logistic.requisition'].new({
            'requisition_type': 'donor_stock',
            'partner_id': self.owner_id,
        })
        self.lrl = self.env['logistic.requisition.line'].new({
            'product_id': self.product_id,
            'requested_qty': 100,
            'requisition_id': lr,
        })
        lr.line_ids = self.lrl

        self.lrl._generate_donor_source = partial(lrl_gen_donor_src, self.lrl)
