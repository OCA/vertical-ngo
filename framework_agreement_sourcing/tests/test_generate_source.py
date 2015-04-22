#    Author: Leonardo Pistone
#    Copyright 2015 Camptocamp SA
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

from .common import CommonSourcingSetUp


class TestGenerateSource(CommonSourcingSetUp):

    def test_if_there_are_agreements_source_by_agreement(self):
        """We choose an existing lrl for a product that has an agreement"""
        lrl = next(line for line in self.requisition.line_ids
                   if line.product_id == self.product)

        source = lrl._generate_default_source()
        self.assertEqual('fw_agreement', source.sourcing_method)

    def test_if_no_agreements_dont_source_by_agreement(self):
        """We choose an existing lrl for a product that has an agreement"""
        product_without_agreement = self.env.ref('product.product_product_7')

        lrl = next(line for line in self.requisition.line_ids
                   if line.product_id == product_without_agreement)
        source = lrl._generate_default_source()
        self.assertNotEqual('fw_agreement', source.sourcing_method)
