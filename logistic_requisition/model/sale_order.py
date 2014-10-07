# -*- coding: utf-8 -*-
#
#
#    Copyright 2013-2014 Camptocamp SA
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
from openerp import models, fields
from .logistic_requisition import LogisticRequisitionSource


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    requisition_id = fields.Many2one('logistic.requisition',
                                     'Logistic Requisition',
                                     ondelete='restrict',
                                     copy=False)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    price_is = fields.Selection(
        LogisticRequisitionSource.PRICE_IS_SELECTION,
        string='Price is',
        help="When the price is an estimation, the final price may change. "
             "I.e. it is not based on a request for quotation.",
        default='fixed')
    account_code = fields.Char('Account Code', size=32)
