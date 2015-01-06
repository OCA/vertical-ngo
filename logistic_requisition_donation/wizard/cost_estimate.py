# -*- coding: utf-8 -*-
#
#
#    Author: Yannick Vaucher
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
#
#
from openerp import models, api


class LogisticsRequisitionCostEstimate(models.TransientModel):
    _inherit = 'logistic.requisition.cost.estimate'

    @api.model
    def _prepare_cost_estimate(self, requisition,
                               source_lines, estimate_lines):
        """ Ensure we propagate cost_estimate_only

        However, a dispatch from donor stock should create a standard
        cost estimate.
        """
        _super = super(LogisticsRequisitionCostEstimate, self)
        vals = _super._prepare_cost_estimate(
            requisition, source_lines, estimate_lines)
        if requisition.requisition_type == 'donor_stock':
            vals['order_type'] = 'standard'
        return vals
