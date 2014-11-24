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


class TestUnitCheck(TransactionCase):
    """Unit tests on the budget check."""

    def test_over_budget(self):
        order = self.env['sale.order'].new({
            'total_budget': 80.0,
            'amount_total': 100.0,
        })
        self.assertIs(True, order.over_budget())

    def test_not_over_budget(self):
        order = self.env['sale.order'].new({
            'total_budget': 80.0,
            'amount_total': 30.0,
        })
        self.assertIs(False, order.over_budget())

    def test_has_no_budget_holder(self):
        order = self.env['sale.order'].new({})
        self.assertIs(False, order.has_budget_holder())

    def test_has_budget_holder(self):
        order = self.env['sale.order'].new({
            'budget_holder_id': self.env['res.users'].browse(self.env.uid),
        })
        self.assertIs(True, order.has_budget_holder())
