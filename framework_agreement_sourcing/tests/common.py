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
import openerp.tests.common as test_common
from openerp.addons.logistic_requisition.tests import logistic_requisition
from openerp.addons.framework_agreement.tests.common \
    import BaseAgreementTestMixin


class CommonSourcingSetUp(test_common.TransactionCase, BaseAgreementTestMixin):

    def setUp(self):
        super(CommonSourcingSetUp, self).setUp()
        self.commonsetUp()

        # new API
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
        Portfolio = self.env['framework.agreement.portfolio']
        start_date = date.today() + timedelta(days=10)
        end_date = date.today() + timedelta(days=20)

        # Agreement 1
        agr = self.agreement_model.create({
            'portfolio_id': self.portfolio.id,
            'product_id': self.product.id,
            'start_date': fields.Date.to_string(start_date),
            'end_date': fields.Date.to_string(end_date),
            'draft': False,
            'delay': 5,
            'quantity': 2000,
        })

        pl = self.agreement_pl_model.create({
            'framework_agreement_id': agr.id,
            'currency_id': self.ref('base.EUR')
        })

        self.agreement_line_model.create({
            'framework_agreement_pricelist_id': pl.id,
            'quantity': 0,
            'price': 77.0,
        })

        self.agreement_line_model.create({
            'framework_agreement_pricelist_id': pl.id,
            'quantity': 1000,
            'price': 30.0,
        })

        self.cheap_on_high_agreement = agr

        self.portfolio_2 = Portfolio.create({
            'name': '/',
            'supplier_id': self.ref('base.res_partner_3'),
        })

        # Agreement 2
        agr = self.agreement_model.create({
            'portfolio_id': self.portfolio_2.id,
            'product_id': self.product.id,
            'start_date': fields.Date.to_string(start_date),
            'end_date': fields.Date.to_string(end_date),
            'draft': False,
            'delay': 5,
            'quantity': 1200,
        })

        pl = self.agreement_pl_model.create({
            'framework_agreement_id': agr.id,
            'currency_id': self.ref('base.EUR'),
        })

        self.agreement_line_model.create({
            'framework_agreement_pricelist_id': pl.id,
            'quantity': 0,
            'price': 50.0,
        })

        self.agreement_line_model.create({
            'framework_agreement_pricelist_id': pl.id,
            'quantity': 1000,
            'price': 45.0,
        })

        self.cheap_on_low_agreement = agr
