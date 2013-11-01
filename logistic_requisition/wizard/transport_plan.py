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


class logistic_requisition_source_transport_plan(orm.TransientModel):
    _name = 'logistic.requisition.source.transport.plan'
    _description = 'Create a transport plan for logistic requisition source lines'

    _columns = {
        'date_eta': fields.date(
            'ETA',
            required=True,
            help="Estimated Date of Arrival"
                 " if not set requisition ETA will be used"
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

    def _get_default_lines(self, cr, uid, context=None):
        active_ids = context.get('active_ids')
        if not active_ids:
            return []
        req_source_obj = self.pool['logistic.requisition.source']
        lines = req_source_obj.browse(cr, uid, active_ids, context=context)
        return lines

    def _get_default_transport_mode(self, cr, uid, context=None):
        """ Set the default value for transport mode using
        preffered LR mode, if lines came from differents
        requisitions nothing is set"""
        if context is None:
            return False
        lines = self._get_default_lines(cr, uid, context=context)
        if any(lines[0].requisition_id != x.requisition_id for x in lines):
            return False
        return lines[0].requisition_id.preferred_transport.id

    def _get_default_date_eta_from_lines(self, cr, uid, context=None):
        """ Set the default eta_date value"""
        if context is None:
            return False
        lines = self._get_default_lines(cr, uid, context=context)
        if any(lines[0].requisition_line_id != x.requisition_line_id for x in lines):
            return False
        return lines[0].requisition_line_id.date_delivery

    def _get_default_from_address(self, cr, uid, context=None):
        """ Set the default source address,
        if lines came from differents
        requisitions nothing is set"""
        if context is None:
            return False
        lines = self._get_default_lines(cr, uid, context=context)
        if any(lines[0].requisition_id != x.requisition_id for x in lines):
            return False
        if any(lines[0].default_source_address != x.default_source_address
                for x in lines):
            return False
        return lines[0].default_source_address.id

    def _get_default_to_address(self, cr, uid, context=None):
        """ Set the default destination address,
        if lines came from differents
        requisitions nothing is set"""
        if context is None:
            return False
        lines = self._get_default_lines(cr, uid, context=context)
        if any(lines[0].requisition_id != x.requisition_id for x in lines):
            return False
        return lines[0].requisition_id.consignee_shipping_id.id

    _defaults = {'transport_mode_id': _get_default_transport_mode,
                 'date_eta': _get_default_date_eta_from_lines,
                 'from_address_id': _get_default_from_address,
                 'to_address_id': _get_default_to_address}

    def _prepare_transport_plan(self, cr, uid, form,
                                line_brs, context=None):
        """ Prepare the values for the creation of a transport plan
        from a selection of requisition lines.
        """
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
        source_ids = context.get('active_ids')
        if not source_ids:
            return
        assert len(ids) == 1, "One ID expected"
        form = self.browse(cr, uid, ids[0], context=context)
        transport_obj = self.pool.get('transport.plan')
        source_obj = self.pool.get('logistic.requisition.source')
        lines = source_obj.browse(cr, uid, source_ids, context=context)
        vals = self._prepare_transport_plan(cr, uid, form, lines, context=context)
        transport_id = transport_obj.create(cr, uid, vals, context=context)
        source_obj.write(cr, uid, source_ids,
                         {'transport_plan_id': transport_id,
                          'transport_applicable': True},
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
