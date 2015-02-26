#    Author: Leonardo Pistone
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
from openerp.tests.common import TransactionCase
from mock import Mock


class TestPropagateBudget(TransactionCase):
    def test_propagate_budget_to_cost_estimate(self):
        cel_data = self.wizard_model._prepare_cost_estimate_line(self.source)
        self.assertEqual(cel_data['budget_tot_price'], 120.0)
        for key in cel_data:
            self.assertIn(key, dir(self.env['sale.order.line']))

    def test_propagate_budget_to_cost_estimate_2_sources(self):
        source2 = Mock(
            spec_set=self.env['logistic.requisition.source'],
            dispatch_warehouse_id=False,
            sourcing_method='other',
            proposed_product_id=self.env['product.product'],
            proposed_qty=80,
            requisition_line_id=self.line,
        )
        self.line.requested_qty = 100
        cel_data1 = self.wizard_model._prepare_cost_estimate_line(self.source)
        cel_data2 = self.wizard_model._prepare_cost_estimate_line(source2)
        self.assertEqual(cel_data1['budget_tot_price'] +
                         cel_data2['budget_tot_price'], 120.0)
        # 20% of 120 = 24
        self.assertEqual(cel_data1['budget_tot_price'], 24.0)
        # 80% of 120 = 96
        self.assertEqual(cel_data2['budget_tot_price'], 96.0)

    def test_propagate_holder_to_cost_estimate(self):
        ce_data = self.wizard_model._prepare_cost_estimate(
            requisition=self.request,
            source_lines=None,
            estimate_lines=[],
        )
        self.assertEqual(1, ce_data['budget_holder_id'], 1)
        self.assertEqual(2, ce_data['finance_officer_id'], 2)
        self.assertEqual('LGTM', ce_data['budget_holder_remark'])
        self.assertEqual('not bad', ce_data['finance_officer_remark'])
        self.assertEqual('2001-01-01 00:00:00', ce_data['date_budget_holder'])
        self.assertEqual('2002-02-02 00:00:00',
                         ce_data['date_finance_officer'])
        for key in ce_data:
            self.assertIn(key, dir(self.env['sale.order']))

    def setUp(self):
        super(TestPropagateBudget, self).setUp()
        self.wizard_model = self.env['logistic.requisition.cost.estimate']
        self.partner1 = self.env.ref('base.res_partner_1')
        self.source = Mock(
            spec_set=self.env['logistic.requisition.source'],
            dispatch_warehouse_id=False,
            sourcing_method='other',
            proposed_product_id=self.env['product.product'],
            proposed_qty=20,
        )
        self.request = self.env['logistic.requisition'].new({
            'budget_holder_id': 1,
            'finance_officer_id': 2,
            'date_budget_holder': '2001-01-01 00:00:00',
            'date_finance_officer': '2002-02-02 00:00:00',
            'budget_holder_remark': 'LGTM',
            'finance_officer_remark': 'not bad',
        })
        self.line = self.env['logistic.requisition.line'].new({
            'requisition_id': self.request,
            'requested_qty': 20,
            'budget_tot_price': 120.0,
        })
        self.source.requisition_line_id = self.line
        self.line.requisition_id.partner_id = self.partner1
