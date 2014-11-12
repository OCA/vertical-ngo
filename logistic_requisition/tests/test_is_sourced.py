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
import time
from openerp.tests.common import TransactionCase
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as D_FMT


class TestIsSourced(TransactionCase):

    def test_warehouse_dispatch_is_always_sourced(self):
        self.source.procurement_method = 'wh_dispatch'
        self.assertEquals([], self.source._check_sourcing())

    def test_procurement_sourcing_without_pr_is_not_sourced(self):
        self.source.procurement_method = 'procurement'
        errors = self.source._check_sourcing()
        self.assertEquals(1, len(errors))
        self.assertIn('Missing Purchase Requisition', errors[0])

    def test_procurement_sourcing_with_draft_pr_is_not_sourced(self):
        self.source.procurement_method = 'procurement'
        self.source.po_requisition_id = self.PurcReq.new({'state': 'draft'})
        errors = self.source._check_sourcing()
        self.assertEquals(1, len(errors))
        self.assertIn('Purchase Requisition state should', errors[0])

    def test_procurement_sourcing_with_closed_pr_is_sourced(self):
        self.source.procurement_method = 'procurement'
        self.source.po_requisition_id = self.PurcReq.new({'state': 'closed'})
        self.assertEquals([], self.source._check_sourcing())

    def test_procurement_sourcing_with_done_pr_is_sourced(self):
        self.source.procurement_method = 'procurement'
        self.source.po_requisition_id = self.PurcReq.new({'state': 'done'})
        self.assertEquals([], self.source._check_sourcing())

    def test_other_sourcing_without_pr_is_not_sourced(self):
        self.source.procurement_method = 'other'
        errors = self.source._check_sourcing()
        self.assertEquals(1, len(errors))
        self.assertIn('Missing Purchase Requisition', errors[0])

    def setUp(self):
        """Setup a source.

        I use Model.new to get a model instance that is not saved to the
        database, but has working methods.

        """
        super(TestIsSourced, self).setUp()
        Source = self.env['logistic.requisition.source']
        self.PurcReq = self.env['purchase.requisition']
        self.source = Source.new()
