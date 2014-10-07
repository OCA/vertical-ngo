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
from openerp import models, fields, api
from openerp.exceptions import except_orm
from openerp.tools.translate import _


class LogisticRequisitionCostEstimate(models.TransientModel):
    _name = 'logistic.requisition.cost.estimate'
    _description = 'Create cost estimate of logistic requisition lines'

    requisition_id = fields.Many2one(
        'logistic.requisition',
        string='Logistic Requisition',
        readonly=True,
        required=True)
    line_ids = fields.Many2many(
        'logistic.requisition.line',
        'requisition_cost_estimate_sourced_line',
        'wizard_id',
        'line_id',
        string='Sourced Lines',
        readonly=True)
    skipped_line_ids = fields.Many2many(
        'logistic.requisition.line',
        'requisition_cost_estimate_skipped_line',
        'wizard_id',
        'line_id',
        string='Skipped Lines',
        readonly=True)

    @api.multi
    def _check_requisition_uniq(self):
        if any(line.requisition_id.id != self.requisition_id.id
               for line in self.line_ids):
            return False
        return True

    _constraints = [
        (_check_requisition_uniq,
         'All the lines should belong to the same requisition.',
         ['line_ids']),
    ]

    @api.model
    def _filter_cost_estimate_lines(self, lines):
        sourced = [line for line in lines
                   if line.state == 'sourced' and
                   not line.cost_estimate_id]
        skipped = [line for line in lines if line not in sourced]
        return sourced, skipped

    @api.model
    def default_get(self, fields_list):
        defaults = super(LogisticRequisitionCostEstimate, self
                         ).default_get(fields_list)
        req_obj = self.env['logistic.requisition']
        line_obj = self.env['logistic.requisition.line']
        line_ids = []
        if self.env.context['active_model'] == 'logistic.requisition':
            # when we create the cost estimate from the requisition,
            # we'll select all the lines
            req = req_obj.browse(self.env.context['active_ids']).ensure_one()
            lines = req.line_ids

        elif self.env.context['active_model'] == 'logistic.requisition.line':
            # we are coming from the selection of lines (ir.values)
            # or from the button on a line
            line_ids = self.env.context['active_ids']
            lines = line_obj.browse(line_ids)
            # take the first requisition found, constraint
            # will check afterwards if all the lines are linked to the same
            line = line_obj.browse(line_ids[0])
            req = line.requisition_id
        if lines:
            sourced, skipped = self._filter_cost_estimate_lines(lines)
            defaults['line_ids'] = [s_line.id for s_line in sourced]
            defaults['skipped_line_ids'] = [s_line.id for s_line in skipped]
        defaults['requisition_id'] = req.id
        return defaults

    @api.model
    def _get_route_drop_shipping(self):
        """ Return route_id of dropshipping route """
        ref = 'stock_drop_shipping'
        self.env['ir.model.data'].xmlid_to_res_id(ref)

    @api.model
    def _prepare_cost_estimate_line(self, sourcing):
        sale_line_obj = self.env['sale.order.line']
        vals = {'product_id': sourcing.proposed_product_id.id,
                'name': sourcing.requisition_line_id.description,
                'price_unit': sourcing.unit_cost,
                'price_is': sourcing.price_is,
                'product_uom_qty': sourcing.proposed_qty,
                'product_uom': sourcing.proposed_uom_id.id,
                'account_code': sourcing.requisition_line_id.account_code,
                # line must be sourced
                'manually_sourced': True,
                }
        if sourcing.dispatch_location_id:
            warehouse_id = self.env['stock.location'].get_warehouse(
                sourcing.dispatch_location_id)
            vals['warehouse_id'] = warehouse_id
        elif sourcing.procurement_method not in ('wh_dispatch'):
            vals['route_id'] = self._get_route_drop_shipping()

        requisition = sourcing.requisition_line_id.requisition_id
        onchange_vals = sale_line_obj.product_id_change(
            requisition.consignee_id.property_product_pricelist.id,
            sourcing.proposed_product_id.id,
            partner_id=requisition.consignee_id.id,
            qty=sourcing.proposed_qty,
            uom=sourcing.proposed_uom_id.id).get('value', {})
        #  price_unit and type of the requisition line must be kept
        if 'price_unit' in onchange_vals:
            del onchange_vals['price_unit']
        vals.update(onchange_vals)
        return vals

    @api.model
    def _check_requisition(self, requisition):
        """ Check the rules to create a cost estimate from the
        requisition

        :returns: list of tuples ('message, 'error_code')
        """
        errors = []
        return errors

    @api.model
    def _check_line(self, line):
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
            error = (_('Sourcing %s: no account code has been stored')
                     % line.name,
                     'NO_ACCOUNT_CODE')
            errors.append(error)
        return errors

    @api.model
    def _check_rules(self, requisition, source_lines):
        """ Check all the business rules which must be valid in order to
        create a cost estimate.

        A list of error codes is attached to the exception.
        Theses tests are used in the tests to know if the rules are applied
        correctly.
        """
        # each item of the error list contains the error message and an
        # error code
        errors = self._check_requisition(requisition)
        for line in source_lines:
            errors += self._check_line(line)
        if not errors:
            return
        msg = '\n\n'.join([' * %s' % error for error, __ in errors])
        codes = [code for __, code in errors]
        exception = except_orm(
            _('Cannot create a cost estimate because:'), msg)
        # attach a list of error codes so we can test them
        exception.error_codes = codes
        raise exception

    @api.model
    def _prepare_cost_estimate(self, requisition,
                               source_lines, estimate_lines):
        """ Prepare the values for the creation of a cost estimate
        from a selection of requisition lines.
        A cost estimate is a sale.order record.
        """
        sale_obj = self.env['sale.order']
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
                'project_id': requisition.analytic_id.id,
                }
        onchange_vals = (sale_obj.onchange_partner_id(partner_id)
                         .get('value', {}))
        vals.update(onchange_vals)
        vals.update({'pricelist_id': requisition.pricelist_id.id})
        return vals

    @api.multi
    def cost_estimate(self):
        self.ensure_one()
        sale_obj = self.env['sale.order']
        requisition = self.requisition_id
        lines = self.line_ids
        if not lines:
            raise except_orm(_('Error'),
                             _('The cost estimate cannot be created, '
                               'because no lines are sourced.'))
        source_lines = [source for line in lines for source in line.source_ids]
        self._check_rules(requisition, source_lines)
        estimate_lines = []
        for line in source_lines:
            vals = self._prepare_cost_estimate_line(line)
            estimate_lines.append(vals)
        order_vals = self._prepare_cost_estimate(requisition,
                                                 source_lines,
                                                 estimate_lines)
        sale_id = sale_obj.create(order_vals)
        for line in lines:
            line.cost_estimate_id = sale_id
        lines._do_quoted()
        return self._open_cost_estimate(sale_id)

    @api.model
    def _open_cost_estimate(self, estimate_id):
        return {
            'name': _('Cost Estimate'),
            'view_mode': 'form',
            'res_model': 'sale.order',
            'res_id': estimate_id.id,
            'target': 'current',
            'view_id': False,
            'context': {},
            'type': 'ir.actions.act_window',
        }
