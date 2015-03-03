#    Author: Leonardo Pistone
#    Copyright 2014 Camptocamp SA
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
from openerp.tests.common import TransactionCase
from mock import Mock


class TestPropagateOwner(TransactionCase):
    def test_propagate_owner_to_cost_estimate(self):
        self.source.stock_owner_id = self.partner_1
        cel_data = self.wizard_model._prepare_cost_estimate_line(self.source)
        self.assertEqual(cel_data['stock_owner_id'], self.partner_1.id)

    def setUp(self):
        super(TestPropagateOwner, self).setUp()
        self.wizard_model = self.env['logistic.requisition.cost.estimate']
        self.partner_1 = self.env.ref('base.res_partner_1')
        partner_2 = self.env.ref('base.res_partner_2')
        self.source = Mock(
            spec_set=self.env['logistic.requisition.source'],
            dispatch_warehouse_id=False,
            sourcing_method='other',
            proposed_product_id=self.env['product.product'],
        )
        self.source.requisition_line_id.requisition_id.partner_id = partner_2
