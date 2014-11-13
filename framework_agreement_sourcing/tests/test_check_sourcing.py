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


class TestCheckSourcing(TransactionCase):
    """Check the _check_sourcing method of the source. """

    def test_agreement_sourcing_without_po_is_not_sourced(self):
        self.source.procurement_method = 'fw_agreement'
        errors = self.source._check_sourcing()
        self.assertEquals(1, len(errors))
        self.assertIn('No Purchase Order Lines', errors[0])

    def test_agreement_sourcing_with_po_is_sourced(self):
        self.source.procurement_method = 'fw_agreement'
        self.source._get_purchase_order_lines = lambda: self.PO.new()
        self.assertEquals([], self.source._check_sourcing())

    def test_other_sourcing_without_pr_nor_pol_is_not_sourced(self):
        self.source.procurement_method = 'other'
        errors = self.source._check_sourcing()
        self.assertEquals(1, len(errors))
        self.assertIn('Sourcing errors', errors[0])

    def test_other_sourcing_with_pr_without_pol_is_sourced(self):
        self.source.procurement_method = 'other'
        self.source.po_requisition_id = self.PurcReq.new({'state': 'closed'})
        self.assertEquals([], self.source._check_sourcing())

    def test_other_sourcing_without_pr_with_pol_is_sourced(self):
        self.source.procurement_method = 'other'
        self.source._get_purchase_order_lines = lambda: self.PO.new()
        self.assertEquals([], self.source._check_sourcing())

    def test_other_sourcing_with_pr_and_pol_is_sourced(self):
        self.source.procurement_method = 'other'
        self.source.po_requisition_id = self.PurcReq.new({'state': 'closed'})
        self.source._get_purchase_order_lines = lambda: self.PO.new()
        self.assertEquals([], self.source._check_sourcing())

    def setUp(self):
        """Setup a source.

        I use Model.new to get a model instance that is not saved to the
        database, but has working methods.

        """
        super(TestCheckSourcing, self).setUp()
        Source = self.env['logistic.requisition.source']
        self.PO = self.env['purchase.order']
        self.PurcReq = self.env['purchase.requisition']
        self.source = Source.new()
