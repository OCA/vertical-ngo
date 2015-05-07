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
import openerp.addons.decimal_precision as dp


class LogisticsRequisition(models.Model):
    _inherit = 'logistic.requisition'

    @api.one
    @api.depends('total_budget',
                 'currency_id',
                 'company_id.currency_id')
    def _compute_prices_in_company_currency(self):
        """ Compute total_budget in company currency

        Date for conversion is logistic requisition date
        """
        if self.currency_id:
            date = self.date or fields.Date.today()
            from_curr = self.currency_id.with_context(date=date)
            to_curr = self.company_id.currency_id
            self.total_budget_co = from_curr.compute(self.total_budget,
                                                     to_curr, round=False)

    company_currency_id = fields.Many2one(
        related='company_id.currency_id',
        comodel_name='res.currency',
        string='Currency',
        readonly=True,
    )

    total_budget_co = fields.Float(
        compute='_compute_prices_in_company_currency',
        string="Total Budget in company currency)",
        digits=dp.get_precision('Account'),
        help="Total budget converted at company currency using rates at "
             "requisition date."
    )
