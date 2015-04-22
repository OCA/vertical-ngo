#    Author: Nicolas Bessi, Leonardo Pistone
#    Copyright 2013-2015 Camptocamp SA
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

from datetime import timedelta, date
from openerp import fields
from openerp.addons.logistic_requisition.tests import logistic_requisition
from openerp.addons.framework_agreement.tests.common \
    import AgreementTransactionCase


class CommonSourcingSetUp(AgreementTransactionCase):

    def setUp(self):
        super(CommonSourcingSetUp, self).setUp()

        self.Requisition = self.env['logistic.requisition']

        self.make_common_agreements()
        self.make_common_requisition()

    def make_common_requisition(self):
        """Create a standard logistic requisition"""
        start_date = date.today() + timedelta(days=12)
        req = {
            'partner_id': self.ref('base.res_partner_1'),
            'consignee_id': self.ref('base.res_partner_3'),
            'date_delivery': fields.Date.to_string(start_date),
            'date': fields.Date.to_string(start_date),
            'user_id': self.uid,
            'pricelist_id': self.ref('product.list0'),
        }
        agr_line = {
            'product_id': self.product.id,
            'requested_qty': 100,
            'requested_uom_id': self.ref('product.product_uom_unit'),
            'date_delivery': fields.Date.today(),
            'description': '/',
        }
        product_line = {
            'product_id': self.ref('product.product_product_7'),
            'requested_qty': 10,
            'requested_uom_id': self.ref('product.product_uom_unit'),
            'date_delivery': fields.Date.today(),
            'description': '/',
        }

        other_line = {
            'product_id': self.ref('logistic_requisition.product_transport'),
            'requested_qty': 1,
            'requested_uom_id': self.ref('product.product_uom_unit'),
            'date_delivery': fields.Date.today(),
            'description': '/',
        }

        self.requisition = self.Requisition.create(req)
        self.requisition.onchange_consignee_id_set_country_id()
        self.requisition.onchange_consignee_id_set_consignee_shipping_id()
        logistic_requisition.add_line(self, self.requisition, agr_line)
        logistic_requisition.add_line(self, self.requisition, product_line)
        logistic_requisition.add_line(self, self.requisition, other_line)

    def make_common_agreements(self):
        """Create two default agreements.

        We have two agreement for same product but using
        different suppliers

        One supplier has a better price for lower qty the other
        has better price for higher qty

        We also create one requisition with one line of agreement product
        And one line of other product

        """

        self.agreement.partnerinfo_ids.write({
            'min_quantity': 0.,
            'price': 77.0,
        })

        self.agreement.partnerinfo_ids.copy({
            'min_quantity': 1000.,
            'price': 30.0,
        })

        self.portfolio_2 = self.Portfolio.create({
            'name': 'second portfolio',
            'supplier_id': self.ref('base.res_partner_3'),
            'start_date': fields.Date.to_string(self.start_date),
            'end_date': fields.Date.to_string(self.end_date),
            'line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1200.,
            })],
        })

        self.portfolio_2.create_new_agreement()
        self.agreement_2 = self.portfolio_2.pricelist_ids

        self.agreement_2.partnerinfo_ids.write({
            'min_quantity': 0.,
            'price': 50.0,
        })

        self.agreement_2.partnerinfo_ids.copy({
            'min_quantity': 1000.,
            'price': 45.0,
        })
