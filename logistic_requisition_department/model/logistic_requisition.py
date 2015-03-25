# -*- coding: utf-8 -*-
# Author: Leonardo Pistone
# Copyright 2014-2015 Camptocamp SA (http://www.camptocamp.com)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public Lice
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from openerp import models, fields, api
from openerp import exceptions

from openerp.addons.logistic_requisition.model.logistic_requisition import (
    LogisticsRequisition as base_requisition
)


class LogisticRequisition(models.Model):
    _inherit = 'logistic.requisition'

    def _get_my_department(self):
        employees = self.env.user.employee_ids
        return (employees and employees[0].department_id or
                self.env['hr.department'])

    department_id = fields.Many2one('hr.department', 'Department',
                                    states=base_requisition.REQ_STATES,
                                    default=_get_my_department)


class LogisticRequisitionLine(models.Model):
    _inherit = 'logistic.requisition.line'

    department_id = fields.Many2one(related='requisition_id.department_id',
                                    readonly=True,
                                    store=True)


class LogisticRequisitionSource(models.Model):
    _inherit = 'logistic.requisition.source'

    department_id = fields.Many2one(
        related='requisition_line_id.requisition_id.department_id',
        readonly=True,
        store=True)

    @api.multi
    def _prepare_po_requisition(self, purch_req_lines, pricelist=None):
        res = super(LogisticRequisitionSource, self)._prepare_po_requisition(
            purch_req_lines, pricelist)
        departments = self.mapped('department_id')
        if len(departments) > 1:
            raise exceptions.Warning(
                'Cannot generate Purchase Order: '
                'the sourcing lines are from '
                'different departments.')
        res['department_id'] = departments.id
        return res
