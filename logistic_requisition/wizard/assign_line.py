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
from openerp import models, fields, api


class LogisticsRequisitionLineAssign(models.TransientModel):
    _name = 'logistic.requisition.line.assign'
    _description = 'Assign a logistic requisition line'

    logistic_user_id = fields.Many2one(
        'res.users',
        'Logistics Specialist',
        required=True,
        help="Logistics Specialist in charge of the "
             "Logistics Requisition Line")

    @api.multi
    def assign(self):
        line_ids = self.env.context.get('active_ids')
        if not line_ids:
            return
        lines = self.env['logistic.requisition.line'].browse(line_ids)
        lines.write({'logistic_user_id': self.logistic_user_id.id})
        return {'type': 'ir.actions.act_window_close'}
