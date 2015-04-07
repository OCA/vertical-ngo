# -*- coding: utf-8 -*-
#
#    Author: Alexandre Fayolle
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
from openerp import models, api, fields
from openerp.tools.translate import _


class SaleOrderLineBudgetUpdate(models.TransientModel):
    _name = 'sale.order.line.budget.update'

    @api.model
    def _default_budget(self):
        context = self.env.context
        if context.get('active_model') != "sale.order.line":
            return 0.
        so_line = self.env['sale.order.line'].browse(context['active_id'])
        return so_line.budget_tot_price

    new_budget = fields.Float('New Budget',
                              default=_default_budget)

    @api.multi
    def update_budget(self):
        context = self.env.context
        so_line = self.env['sale.order.line'].browse(context['active_id'])
        if self.new_budget != so_line.budget_tot_price:
            old_budget = so_line.budget_tot_price
            so_line.budget_tot_price = self.new_budget
            order = so_line.order_id
            msg = _('Budget for %(line)s updated from '
                    '%(old_budget)s to %(new_budget)s')
            vars = {'line': so_line.name,
                    'old_budget': old_budget,
                    'new_budget': self.new_budget,
                    }
            order.message_post(msg % vars)
