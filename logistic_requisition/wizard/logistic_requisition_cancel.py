# -*- coding: utf-8 -*-
#
#
#    Author: Guewen Baconnier
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


class LogisticRequisitionCancel(models.TransientModel):
    """ Ask a reason for the logistic requisition cancellation."""
    _name = 'logistic.requisition.cancel'
    _description = __doc__

    reason_id = fields.Many2one('logistic.requisition.cancel.reason',
                                string='Reason',
                                required=True)

    @api.multi
    def confirm_cancel(self):
        self.ensure_one()
        act_close = {'type': 'ir.actions.act_window_close'}
        requisition_ids = self.env.context.get('active_ids')
        if requisition_ids is None:
            return act_close
        reqs = self.env['logistic.requisition'].browse(requisition_ids)
        reqs._do_cancel(self.reason_id.id)
        return act_close
