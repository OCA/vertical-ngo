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
import logging

from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class LogisticsRequisitionLine(models.Model):
    _inherit = 'logistic.requisition.line'

    @api.one
    @api.depends('amount_total',
                 'requisition_id.date',
                 'requisition_id.currency_id',
                 'requisition_id.company_id.currency_id')
    def _compute_prices_in_company_currency(self):
        """ Compute total_budget in company currency

        Date for conversion is logistic requisition date
        """
        requisition = self.requisition_id
        if requisition and requisition.currency_id:
            date = requisition.date
            from_curr = requisition.currency_id.with_context(date=date)
            to_curr = requisition.company_id.currency_id
            self.amount_total_co = from_curr.compute(self.amount_total,
                                                     to_curr,
                                                     round=False)
        elif not requisition:
            _logger.warning(
                "Total in currency not computed: requisition not passed "
                "to the onchange method. This can probably be avoided "
                "improving the view."
            )
        else:
            raise exceptions.Warning(
                _('You must set a pricelist on the Requisition, '
                  'or configure a default pricelist for this requestor.'))

    company_currency_id = fields.Many2one(
        related='requisition_id.company_id.currency_id',
        comodel_name='res.currency',
        string='Company currency',
        readonly=True
    )

    amount_total_co = fields.Float(
        compute='_compute_prices_in_company_currency',
        string='Tot. Amount in Company currency',
        digits=dp.get_precision('Account'),
        store=True,
        help="Total amount converted to company currency using rates at "
             "requisition date"
    )
