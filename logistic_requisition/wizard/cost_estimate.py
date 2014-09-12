# -*- coding: utf-8 -*-
#
#
#    Author:  Joël Grand-Guillaume
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
from openerp.osv import fields, orm
from openerp.tools.translate import _


class logistic_requisition_cost_estimate(orm.TransientModel):
    _name = 'logistic.requisition.cost.estimate'
    _description = 'Create cost estimate of logistic requisition lines'

    _columns = {
        'requisition_id': fields.many2one('logistic.requisition',
                                          string='Logistic Requisition',
                                          readonly=True,
                                          required=True),
        'line_ids': fields.many2many(
            'logistic.requisition.line',
            'requisition_cost_estimate_sourced_line',
            'wizard_id',
            'line_id',
            string='Sourced Lines',
            readonly=True),
        'skipped_line_ids': fields.many2many(
            'logistic.requisition.line',
            'requisition_cost_estimate_skipped_line',
            'wizard_id',
            'line_id',
            string='Skipped Lines',
            readonly=True),
    }

    def _check_requisition_uniq(self, cr, uid, ids, context=None):
        form = self.browse(cr, uid, ids[0], context=context)
        if any(line.requisition_id != form.requisition_id
               for line in form.line_ids):
            return False
        return True

    _constraints = [
        (_check_requisition_uniq,
         'All the lines should belong to the same requisition.',
         ['line_ids']),
    ]

    def _filter_cost_estimate_lines(self, cr, uid, lines, context=None):
        sourced = [line for line in lines
                   if line.state == 'sourced' and
                   not line.cost_estimate_id]
        skipped = [line for line in lines if line not in sourced]
        return sourced, skipped

    def default_get(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        defaults = super(logistic_requisition_cost_estimate, self).\
            default_get(cr, uid, fields_list, context=context)
        req_obj = self.pool.get('logistic.requisition')
        line_obj = self.pool.get('logistic.requisition.line')
        req_id = False
        line_ids = []
        if context['active_model'] == 'logistic.requisition':
            # when we create the cost estimate from the requisition,
            # we'll select all the lines
            assert len(context['active_ids']) == 1, "Only 1 ID accepted"
            req_id = context['active_ids'][0]
            line_ids = req_obj.read(cr, uid, req_id,
                                    ['line_ids'], context=context)['line_ids']

        elif context['active_model'] == 'logistic.requisition.line':
            # we are coming from the selection of lines (ir.values)
            # or from the button on a line
            line_ids = context['active_ids']
            # take the first requisition found, constraint
            # will check afterwards if all the lines are linked to the same
            line = line_obj.browse(cr, uid, line_ids[0], context=context)
            req_id = line.requisition_id.id
        if line_ids:
            lines = line_obj.browse(cr, uid, line_ids, context=context)
            sourced, skipped = self._filter_cost_estimate_lines(
                cr, uid, lines, context=context)
            defaults['line_ids'] = [s_line.id for s_line in sourced]
            defaults['skipped_line_ids'] = [s_line.id for s_line in skipped]
        defaults['requisition_id'] = req_id
        return defaults

    def _get_name_transport_line(self, cr, uid, transport_plan, context=None):
        name = _('Transport from %s to %s by %s (Ref. %s)') % (
            transport_plan.from_address_id.name,
            transport_plan.to_address_id.name,
            transport_plan.transport_mode_id.name,
            transport_plan.name
        )
        return name

    def _prepare_transport_line(self, cr, uid, transport_plan, context=None):
        """ Prepare the values to write the transport plan lines.

        One ``sale.order.line`` is created for each transport plan
        used in the requisition lines.

        :param transport_plan: transport plan for the lines
        """
        sale_line_obj = self.pool.get('sale.order.line')
        requisition = transport_plan.logistic_requisition_id
        vals = sale_line_obj.product_id_change(
            cr, uid, [],
            requisition.consignee_id.property_product_pricelist.id,
            transport_plan.product_id.id,
            partner_id=requisition.consignee_id.id,
            qty=1).get('value', {})
        vals.update({
            'product_id': transport_plan.product_id.id,
            'price_unit': transport_plan.transport_estimated_cost,
            'name': self._get_name_transport_line(cr, uid,
                                                  transport_plan,
                                                  context=context
                                                  )
        })
        return vals

    def _prepare_cost_estimate_line(self, cr, uid, sourcing, context=None):
        sale_line_obj = self.pool.get('sale.order.line')
        vals = {'logistic_requisition_source_id': sourcing.id,
                'product_id': sourcing.proposed_product_id.id,
                'name': sourcing.requisition_line_id.description,
                'price_unit': sourcing.unit_cost,
                'price_is': sourcing.price_is,
                'product_uom_qty': sourcing.proposed_qty,
                'product_uom': sourcing.proposed_uom_id.id,
                'account_code': sourcing.requisition_line_id.account_code,
                }
        if sourcing.dispatch_location_id:
            vals['location_id'] = sourcing.dispatch_location_id.id
        if sourcing.procurement_method in ('wh_dispatch'):
            vals['type'] = 'make_to_stock'
        else:
            vals['type'] = sourcing.proposed_product_id.procure_method
            vals['sale_flow'] = 'direct_delivery'

        requisition = sourcing.requisition_line_id.requisition_id
        onchange_vals = sale_line_obj.product_id_change(
            cr, uid, [],
            requisition.consignee_id.property_product_pricelist.id,
            sourcing.proposed_product_id.id,
            partner_id=requisition.consignee_id.id,
            qty=sourcing.proposed_qty,
            uom=sourcing.proposed_uom_id.id).get('value', {})
        #  price_unit and type of the requisition line must be kept
        if 'price_unit' in onchange_vals:
            del onchange_vals['price_unit']
        if 'type' in onchange_vals:
            del onchange_vals['type']
        vals.update(onchange_vals)
        return vals

    def _check_requisition(self, cr, uid, requisition, context=None):
        """ Check the rules to create a cost estimate from the
        requisition

        :returns: list of tuples ('message, 'error_code')
        """
        errors = []
        return errors

    def _check_line(self, cr, uid, line, context=None):
        """ Check the rules to create a cost estimate from the
        requisition line

        :returns: list of tuples ('message, 'error_code')
        """
        errors = []
        if not line.proposed_qty:
            error = (_('Sourcing %s: '
                       'no quantity has been proposed') % line.name,
                     'NO_QTY')
            errors.append(error)
        if not line.requisition_line_id.account_code:
            error = (_('Sourcing %s: no account code has been stored') % line.name,
                     'NO_ACCOUNT_CODE')
            errors.append(error)
        return errors

    def _check_rules(self, cr, uid, requisition, source_lines, context=None):
        """ Check all the business rules which must be valid in order to
        create a cost estimate.

        A list of error codes is attached to the exception.
        Theses tests are used in the tests to know if the rules are applied
        correctly.
        """
        # each item of the error list contains the error message and an
        # error code
        errors = self._check_requisition(cr, uid, requisition, context=context)
        for line in source_lines:
            errors += self._check_line(cr, uid, line, context=context)
        if not errors:
            return
        msg = '\n\n'.join([' * %s' % error for error, __ in errors])
        codes = [code for __, code in errors]
        exception = orm.except_orm(
            _('Cannot create a cost estimate because:'), msg)
        # attach a list of error codes so we can test them
        exception.error_codes = codes
        raise exception

    def _prepare_cost_estimate(self, cr, uid, requisition,
                               source_lines, estimate_lines,
                               context=None):
        """ Prepare the values for the creation of a cost estimate
        from a selection of requisition lines.
        A cost estimate is a sale.order record.
        """
        sale_obj = self.pool.get('sale.order')
        partner_id = requisition.partner_id.id
        vals = {'partner_id': partner_id,
                'partner_invoice_id': partner_id,
                'partner_shipping_id': requisition.consignee_shipping_id.id,
                'consignee_id': requisition.consignee_id.id,
                'order_line': [(0, 0, x) for x in estimate_lines],
                'incoterm': requisition.incoterm_id.id,
                'incoterm_address': requisition.incoterm_address,
                'requisition_id': requisition.id,
                'origin': requisition.name,
                'project_id': requisition.analytic_id.id if requisition.analytic_id else False,
                }
        onchange_vals = sale_obj.onchange_partner_id(
            cr, uid, [], partner_id, context=context).get('value', {})
        vals.update(onchange_vals)
        vals.update({'pricelist_id':requisition.pricelist_id.id})
        return vals

    def cost_estimate(self, cr, uid, ids, context=None):
        if isinstance(ids, (tuple, list)):
            assert len(ids) == 1, "Only 1 ID accepted"
            ids = ids[0]
        line_obj = self.pool.get('logistic.requisition.line')
        source_obj = self.pool.get('logistic.requisition.source')
        sale_obj = self.pool.get('sale.order')
        form = self.browse(cr, uid, ids, context=context)
        requisition = form.requisition_id
        lines = form.line_ids
        if not lines:
            raise orm.except_orm(_('Error'),
                                 _('The cost estimate cannot be created, '
                                   'because no lines are sourced.'))
        source_lines = [source for line in lines for source in line.source_ids]
        self._check_rules(cr, uid, requisition, source_lines, context=context)
        estimate_lines = []
        transport_plans = set()
        for line in source_lines:
            if line.transport_applicable and line.transport_plan_id:
                transport_plans.add(line.transport_plan_id)
            vals = self._prepare_cost_estimate_line(cr, uid, line,
                                                    context=context)
            estimate_lines.append(vals)
        for transport_plan in transport_plans:
            vals = self._prepare_transport_line(cr, uid, transport_plan,
                                                context=context)
            estimate_lines.append(vals)
        order_id = self._prepare_cost_estimate(cr, uid,
                                               requisition,
                                               source_lines,
                                               estimate_lines,
                                               context=context)
        sale_id = sale_obj.create(cr, uid, order_id, context=context)
        line_ids = [line.id for line in lines]
        line_obj.write(cr, uid, line_ids,
                       {'cost_estimate_id': sale_id},
                       context=context)
        line_obj._do_quoted(cr, uid, line_ids, context=context)
        return self._open_cost_estimate(cr, uid, sale_id, context=context)

    def _open_cost_estimate(self, cr, uid, estimate_id, context=None):
        return {
            'name': _('Cost Estimate'),
            'view_mode': 'form',
            'res_model': 'sale.order',
            'res_id': estimate_id,
            'target': 'current',
            'view_id': False,
            'context': {},
            'type': 'ir.actions.act_window',
        }
