# -*- coding: utf-8 -*-
#
#    Author: Joël Grand-Guillaume, Leonardo Pistone
#    Copyright 2013, 2014 Camptocamp SA
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
from openerp import models, api


class LogisticRequisitionCostEstimate(models.TransientModel):
    _inherit = 'logistic.requisition.cost.estimate'

    @api.model
    def _prepare_cost_estimate(self, requisition, source_lines,
                               estimate_lines):
        vals = super(
            LogisticRequisitionCostEstimate,
            self
        )._prepare_cost_estimate(requisition, source_lines, estimate_lines)
        vals['budget_holder_id'] = requisition.budget_holder_id.id
        vals['finance_officer_id'] = requisition.finance_officer_id.id
        vals['budget_holder_remark'] = requisition.budget_holder_remark
        vals['finance_officer_remark'] = requisition.finance_officer_remark
        vals['date_budget_holder'] = requisition.date_budget_holder
        vals['date_finance_officer'] = requisition.date_finance_officer

        return vals

    @api.model
    def _prepare_cost_estimate_line(self, source):
        vals = super(
            LogisticRequisitionCostEstimate,
            self
        )._prepare_cost_estimate_line(source)
        req_line = source.requisition_line_id
        if req_line.requested_qty:
            # Compute the part of budget it consumes on pro-rata
            budget_portion = source.proposed_qty / req_line.requested_qty
            budget_tot_price = budget_portion * req_line.budget_tot_price
            vals['budget_tot_price'] = budget_tot_price
        return vals
