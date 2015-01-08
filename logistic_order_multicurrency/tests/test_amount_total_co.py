# -*- coding: utf-8 -*-
#
#
#    Author: Yannick Vaucher
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
#
#
from openerp import fields
import openerp.tests.common as common


class test_total_amount_co(common.TransactionCase):
    """ Test the confirmation of a sale order created by a logistic
    requisition.

    According to the type of products (make to stock, make to order),
    the behavior when confirming a sale order line is different.
    """

    def setUp(self):
        super(test_total_amount_co, self).setUp()
        Sale = self.env['sale.order']

        self.now = fields.Datetime.now()

        self.pricelist_sale = self.env.ref('product.list0')
        sale_data = {
            'date_order': self.now,
            'pricelist_id': self.pricelist_sale.id,
            'company_id': self.env.ref('base.main_company').id,
            'amount_total': 1000,
        }
        self.sale = Sale.new(sale_data)

    def test_amount_same_currency(self):
        """Test amount in company currency if it same as amount
        when currency is the same on order and on company
        """
        self.sale._compute_prices_in_company_currency()
        self.assertEquals(self.sale.amount_total, self.sale.amount_total_co)

    def test_amount_other_currency(self):
        """Test amount in company currency converted from order currency
        """
        currency_data = {'name': 'dataries',
                         'rate': 10.0}
        currency = self.env['res.currency'].create(currency_data)
        currency_rate_data = {'name': self.now,
                              'rate': 10.0,
                              'currency_id': currency.id}
        self.env['res.currency.rate'].create(currency_rate_data)
        self.sale.currency_id = currency
        self.sale._compute_prices_in_company_currency()
        self.assertEquals(100.0, self.sale.amount_total_co)
