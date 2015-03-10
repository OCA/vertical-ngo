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


class TestCheckSourcing(TransactionCase):
    """Check the _check_sourcing method of the source. """

    def test_agreement_sourcing_without_agreement_is_not_sourced(self):
        self.source.sourcing_method = 'fw_agreement'
        errors = self.source._check_sourcing()
        self.assertEquals(1, len(errors))
        self.assertIn('No Framework Agreement', errors[0])

    def test_agreement_sourcing_with_running_agreement_is_sourced(self):
        self.source.sourcing_method = 'fw_agreement'
        self.source.framework_agreement_id = self.Agreement.new({
            'state': 'running',
        })
        self.source.framework_agreement_id.available_quantity = 20
        self.assertEquals([], self.source._check_sourcing())

    def test_other_sourcing_is_always_sourced(self):
        self.source.sourcing_method = 'other'
        self.assertEquals([], self.source._check_sourcing())

    def setUp(self):
        """Setup a source.

        I use Model.new to get a model instance that is not saved to the
        database, but has working methods.

        """
        super(TestCheckSourcing, self).setUp()
        Source = self.env['logistic.requisition.source']
        self.Agreement = self.env['framework.agreement']
        self.source = Source.new({'proposed_qty': 1, 'unit_cost': 1})
