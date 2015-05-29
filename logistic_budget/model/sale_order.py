# -*- coding: utf-8 -*-
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
from openerp import models, fields, api
from openerp.addons.logistic_order.model.sale_order import (
    SaleOrder as base_logistics_order
)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    requester_validator_id = fields.Many2one(
        'res.partner',
        string='Requester',
        states=base_logistics_order.LO_STATES,
        copy=False)
    date_requester_validation = fields.Datetime(
        'Requester Validation Date',
        states=base_logistics_order.LO_STATES,
        copy=False)
    requester_remark = fields.Text(
        'Requester Remark',
        states=base_logistics_order.LO_STATES,
        copy=False)
    budget_holder_id = fields.Many2one(
        'res.users',
        string='Budget Holder',
        states=base_logistics_order.LO_STATES,
        copy=False)
    date_budget_holder = fields.Datetime(
        'Budget Holder Validation Date',
        states=base_logistics_order.LO_STATES,
        copy=False)
    budget_holder_remark = fields.Text(
        'Budget Holder Remark',
        states=base_logistics_order.LO_STATES,
        copy=False)
    finance_officer_id = fields.Many2one(
        'res.users',
        string='Finance Officer',
        states=base_logistics_order.LO_STATES,
        copy=False)
    date_finance_officer = fields.Datetime(
        'Finance Officer Validation Date',
        states=base_logistics_order.LO_STATES,
        copy=False)
    finance_officer_remark = fields.Text(
        'Finance Officer Remark',
        states=base_logistics_order.LO_STATES,
        copy=False)
    total_budget = fields.Float("Total Budget", compute='_total_budget',
                                store=True)

    @api.one
    @api.depends('order_line.budget_tot_price')
    def _total_budget(self):
        self.total_budget = sum([l.budget_tot_price for l in self.order_line])

    @api.onchange('requester_validator_id')
    def onchange_set_date_requester_validation(self):
        self.date_requester_validation = fields.Datetime.now()

    @api.onchange('budget_holder_id')
    def onchange_set_date_budget_holder(self):
        self.date_budget_holder = fields.Datetime.now()

    @api.onchange('finance_officer_id')
    def onchange_set_date_finance_officer(self):
        self.date_finance_officer = fields.Datetime.now()

    @api.multi
    def over_budget(self):
        self.ensure_one()
        return self.amount_total > self.total_budget

    @api.multi
    def has_budget_holder(self):
        self.ensure_one()
        return bool(self.budget_holder_id)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    budget_tot_price = fields.Float("Budget Amount", copy=False)
