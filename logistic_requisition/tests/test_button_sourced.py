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
from openerp import exceptions


class TestButtonSourced(TransactionCase):
    """Test that in a Logistic Requisition Line the Button sourced checks is
    all the source lines are sourced correctly.

    All cases are tested individually in TestCheckSourcing.

    """
    def test_line_with_procurement_sourcing_but_no_procurement_fails(self):
        self.lrl.source_ids = self.LRS.new({
            'procurement_method': 'procurement',
            'name': 'my source',
        })
        with self.assertRaises(exceptions.Warning) as cm:
            self.lrl.button_sourced()
        self.assertEqual("Incorrect Sourcing", cm.exception.args[0])
        self.assertIn("Missing Purchase Requisition", cm.exception.args[1])

    def test_line_with_no_sourcing_fails(self):
        with self.assertRaises(exceptions.Warning) as cm:
            self.lrl.button_sourced()
        self.assertEqual("Incorrect Sourcing", cm.exception.args[0])
        self.assertEqual("No Sourcing Lines", cm.exception.args[1])

    def test_it_can_pass(self):
        self.lrl.source_ids = self.LRS.new({
            'procurement_method': 'wh_dispatch',
        })
        self.lrl.button_sourced()
        self.assertEquals('sourced', self.lrl.state)

    def setUp(self):
        """Setup a logistic requisition line.

        """
        super(TestButtonSourced, self).setUp()
        LRL = self.env['logistic.requisition.line']
        self.LRS = self.env['logistic.requisition.source']
        self.lrl = LRL.new()
