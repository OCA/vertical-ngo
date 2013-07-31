# -*- coding: utf-8 -*-
##############################################################################
#
#    Author:  Joël Grand-Guillaume
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more description.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import fields, orm
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class logistic_requisition_line_transport_plan(orm.TransientModel):
    _name = 'logistic.requisition.line.transport.plan'
    _description = 'Create a transport plan for logistic requisition lines'

    _columns = {
        'date_eta': fields.date(
            'ETA',
            required=True,
            help="Estimated Date of Arrival"
        ),
        'date_etd': fields.date(
            'ETD',
            help="Estimated Date of Departure"
        ),
        'from_address_id': fields.many2one(
            'res.partner', 'From Address',
            required=True
        ),
        'to_address_id': fields.many2one(
            'res.partner', 'To Address',
            required=True
        ),
        'transport_estimated_cost': fields.float(
            'Transportation Estimated Costs',
            digits_compute=dp.get_precision('Account'),
        ),
        'transport_mode_id': fields.many2one(
            'transport.mode',
            string='Transport by',
        ),
        'note': fields.text('Remarks/Description'),
    }

    def _prepare_transport_plan(self, cr, uid, form,
                               context=None):
        """ Prepare the values for the creation of a transport plan
        from a selection of requisition lines.
        """
        transport_obj = self.pool.get('transport.plan')
        vals = {'date_eta': form.date_eta,
                'date_etd': form.date_etd,
                'from_address_id': form.from_address_id.id,
                'to_address_id': form.to_address_id.id,
                'transport_estimated_cost': form.transport_estimated_cost,
                'transport_mode_id': form.transport_mode_id.id,
                'note': form.note,
                }
        return vals

    def create_and_affect(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        line_ids = context.get('active_ids')
        if not line_ids:
            return
        form = self.browse(cr, uid, ids[0], context=context)
        transport_obj = self.pool.get('transport.plan')
        line_obj = self.pool.get('logistic.requisition.line')
        vals = self._prepare_transport_plan(cr, uid, form, context=context)
        transport_id = transport_obj.create(cr, uid, vals, context=context)
        line_obj.write(cr, uid, line_ids,
                       {'transport_plan_id': transport_id},
                       context=context)
        return self._open_transport_plan(cr, uid, transport_id, context=context)

    def _open_transport_plan(self, cr, uid, transport_id, context=None):
        return {
            'name': _('Transport Plan'),
            'view_mode': 'form',
            'res_model': 'transport.plan',
            'res_id': transport_id,
            'target': 'current',
            'view_id': False,
            'context': {},
            'type': 'ir.actions.act_window',
        }
