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


class TestPropagateBudget(TransactionCase):
    def test_propagate_budget_to_cost_estimate(self):
        self.source.requisition_line_id.budget_tot_price = 120.0
        cel_data = self.wizard_model._prepare_cost_estimate_line(self.source)
        self.assertEqual(cel_data['budget_tot_price'], 120.0)
        for key in cel_data:
            self.assertIn(key, dir(self.env['sale.order.line']))

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
        partner1_id = self.env['ir.model.data'].xmlid_to_res_id(
            'base.res_partner_1')
        self.source = Mock(
            spec_set=self.env['logistic.requisition.source'],
            dispatch_location_id=False,
            procurement_method='other',
            proposed_product_id=self.env['product.product'],
        )
        self.source.requisition_line_id.requisition_id.partner_id.id = \
            partner1_id
        self.request = self.env['logistic.requisition'].new({
            'budget_holder_id': 1,
            'finance_officer_id': 2,
            'date_budget_holder': '2001-01-01 00:00:00',
            'date_finance_officer': '2002-02-02 00:00:00',
            'budget_holder_remark': 'LGTM',
            'finance_officer_remark': 'not bad',
        })
