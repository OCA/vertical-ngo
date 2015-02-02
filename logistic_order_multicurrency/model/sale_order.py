# -*- coding: utf-8 -*-
#
#
#    Copyright 2015 Camptocamp SA
#    Author: Yannick Vaucher
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
from openerp import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.one
    @api.depends('amount_total',
                 'currency_id',
                 'company_id.currency_id',
                 'date_order')
    def _compute_prices_in_company_currency(self):
        """ Compute amount_total in company currency

        Date for conversion is order date
        """
        if self.currency_id:
            from_curr = self.currency_id.with_context(date=self.date_order)
            to_curr = self.company_id.currency_id
            self.amount_total_co = from_curr.compute(self.amount_total,
                                                     to_curr, round=False)

    amount_total_co = fields.Float(
        compute='_compute_prices_in_company_currency',
        string="Total in Company currency",
        help="Total converted to company currency at today's rate."
        )

    company_currency_id = fields.Many2one(
        related='company_id.currency_id',
        comodel_name='res.currency',
        string='Currency')

    @api.one
    @api.depends('pricelist_id.currency_id')
    def _get_currency_id(self):
        self.stored_currency_id = self.pricelist_id.currency_id

    # define a dummy stored field for groupby
    # to be able to use new auto trigger store
    # and to avoid AssertionError: Fields in 'groupby' must be regular
    # database-persisted fields (no function or related fields), or function
    # fields with store=True
    stored_currency_id = fields.Many2one(
        related='pricelist_id.currency_id',
        comodel_name='res.currency',
        string='Currency',
        store=True)
