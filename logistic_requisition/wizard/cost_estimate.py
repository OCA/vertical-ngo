# -*- coding: utf-8 -*-

from openerp.osv import fields, orm
from openerp.tools.translate import _


class logistic_requisition_cost_estimate(orm.TransientModel):
    _name = 'logistic.requisition.cost.estimate'
    _description = 'Create cost estimate of logistic requisition lines'

    def _get_requisition_id(self, cr, uid, context=None):
        if context is None:
            context = {}

    _columns = {
        'requisition_id': fields.many2one('logistic.requisition',
                                          string='Logistic Requisition',
                                          readonly=True,
                                          required=True),
        'sourced_line_ids': fields.many2many(
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
               for line in form.sourced_line_ids):
            return False
        return True

    _constraints = [
        (_check_requisition_uniq,
         'All the lines should belong to the same requisition.',
         ['sourced_line_ids']),
    ]

    def _filter_cost_estimate_lines(self, cr, uid, lines, context=None):
        sourced = [line for line in lines
                   if line.state == 'sourced' and
                   not line.cost_estimate_id]
        skipped = [line for line in lines if line not in sourced]
        return sourced, skipped

    def default_get(self, cr, uid, fields_list, context=None):
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
            defaults['sourced_line_ids'] = [line.id for line in sourced]
            defaults['skipped_line_ids'] = [line.id for line in skipped]
        defaults['requisition_id'] = req_id
        return defaults

    def _prepare_cost_estimate_line(self, cr, uid, line, context=None):
        sale_line_obj = self.pool.get('sale.order.line')
        make_type = ('make_to_stock'
                     if line.procurement_method == 'wh_dispatch'
                     else 'make_to_order')
        vals = {'requisition_id': line.id,
                'product_id': line.product_id.id,
                'name': line.description,
                'type': make_type,
                'price_unit': line.unit_cost,
                }
        onchange_vals = sale_line_obj.product_id_change(
            cr, uid, [],
            line.requisition_id.consignee_id.property_product_pricelist.id,
            line.product_id.id,
            partner_id=line.requisition_id.consignee_id.id,
            qty=line.proposed_qty,
            uom=line.proposed_uom_id.id).get('value', {})
        #  price_unit of the requisition line must be kept
        if 'price_unit' in onchange_vals:
            del onchange_vals['price_unit']
        vals.update(onchange_vals)
        return vals

    def _prepare_cost_estimate(self, cr, uid, requisition,
                               sourced_lines, estimate_lines, context=None):
        """ Prepare the values for the creation of a cost estimate
        from a selection of requisition lines.
        A cost estimate is a sale.order record.
        """
        sale_obj = self.pool.get('sale.order')
        location_obj = self.pool.get('stock.location')
        location_ids = set()
        for line in sourced_lines:
            if line.dispatch_location_id:
                location_ids.add(line.dispatch_location_id.id)
        if len(location_ids) > 1:
            raise orm.except_orm(
                _('Error'),
                _('All requisition lines must come from the same location '
                  'or from purchase.'))
        try:
            location_id = location_ids.pop()
        except KeyError:
            data_obj = self.pool.get('ir.model.data')
            __, shop_id = data_obj.get_object_reference(
                cr, uid, 'sale', 'sale_shop_1')
        else:
            shop_id = location_obj._get_shop_from_location(cr, uid,
                                                           location_id,
                                                           context=context)
            if not shop_id:
                location = location_obj.browse(cr, uid, location_id,
                                               context=context)
                raise orm.except_orm(
                    _('Error'),
                    _('No shop is associated with the location %s') %
                    location.name)

        requester_id = requisition.requester_id.id
        vals = {'partner_id': requester_id,
                'partner_invoice_id': requester_id,
                'partner_shipping_id': requisition.consignee_shipping_id.id,
                'consignee_id': requisition.consignee_id.id,
                'order_line': [(0, 0, x) for x in estimate_lines],
                'shop_id': shop_id,
                'incoterm': requisition.incoterm_id.id,
                'incoterm_address': requisition.incoterm_address,
                }

        onchange_vals = sale_obj.onchange_partner_id(
            cr, uid, [], requester_id, context=context).get('value', {})
        vals.update(onchange_vals)
        return vals

    def cost_estimate(self, cr, uid, ids, context=None):
        if isinstance(ids, (tuple, list)):
            assert len(ids) == 1, "Only 1 ID accepted"
            ids = ids[0]
        line_obj = self.pool.get('logistic.requisition.line')
        sale_obj = self.pool.get('sale.order')
        form = self.browse(cr, uid, ids, context=context)
        requisition = form.requisition_id
        sourced_lines = form.sourced_line_ids
        if not sourced_lines:
            raise orm.except_orm(_('Error'),
                                 _('The cost estimate cannot be created, '
                                   'because no lines are sourced.'))
        estimate_lines = []
        for line in sourced_lines:
            vals = self._prepare_cost_estimate_line(cr, uid, line,
                                                    context=context)
            estimate_lines.append(vals)
        order_d = self._prepare_cost_estimate(cr, uid,
                                              requisition,
                                              sourced_lines,
                                              estimate_lines,
                                              context=context)
        sale_id = sale_obj.create(cr, uid, order_d, context=context)
        line_obj.write(cr, uid, ids,
                       {'cost_estimate_id': sale_id},
                       context=context)
        line_obj._do_quoted(cr, uid,
                            [line.id for line in sourced_lines],
                            context=context)
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
