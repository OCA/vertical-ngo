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


class TestItBlocks(TransactionCase):
    """Integration tests on the budget check.

    These check that our exceptions are wired correctly, the estimate is not
    confirmed and an error message is returned.

    """
    def test_it_can_block(self):
        self.order.order_line.budget_tot_price = 80.0
        self.order.order_line.price_unit = 100.0

        result = self.order.action_button_confirm()

        self.assertEqual('draft', self.order.state)
        exceptions = self.wizard_model.browse(result['res_id']).exception_ids
        self.assertEqual(2, len(exceptions))
        self.assertIn("is over the total budget", exceptions[0].description)
        self.assertIn("has not validated", exceptions[1].description)

    def test_it_can_pass(self):
        self.order.order_line.budget_tot_price = 500.0
        self.order.order_line.price_unit = 100.0
        self.order.budget_holder_id = self.env['res.users'].browse(
            self.env.uid)

        self.order.action_button_confirm()

        self.assertEqual('manual', self.order.state)

    def setUp(self):
        super(TestItBlocks, self).setUp()
        data_model = self.env['ir.model.data']
        self.wizard_model = self.env['sale.exception.confirm']

        self.order = self.env['sale.order'].create({
            'partner_id': data_model.xmlid_to_res_id('base.res_partner_1'),
            'consignee_id': data_model.xmlid_to_res_id('base.res_partner_1'),
        })
        self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'name': 'my line name',
        })
