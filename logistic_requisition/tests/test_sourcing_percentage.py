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


class TestSourcingPercentage(TransactionCase):
    def test_one_sourced_out_of_two_is_50_percent(self):
        self.lr = self.LR.new({
            'line_ids': (
                self.LRL.new({'state': 'draft'}) |
                self.LRL.new({'state': 'sourced'})
            )
        })
        self.assertAlmostEqual(50.0, self.lr.sourced)

    def setUp(self):
        super(TestSourcingPercentage, self).setUp()
        self.LR = self.env['logistic.requisition']
        self.LRL = self.env['logistic.requisition.line']
