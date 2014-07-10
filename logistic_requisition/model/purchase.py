# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier, Jacques-Etienne Baudoux
#    Copyright 2013 Camptocamp SA
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
##############################################################################

from openerp.osv import orm, fields
from openerp import netsvc
from openerp.tools.translate import _


class purchase_order(orm.Model):
    _inherit = 'purchase.order'

    def validate_service_product_procurement(self, cr, uid, ids, context=None):
        """ As action_picking_create only take care of non-service product
        by looping on the moves, we need then to pass through all line with
        product of type service and confirm them.
        This way all procurements will reach the done state once the picking
        related to the PO will be done and in the mean while the SO will be
        then marked as delivered.
        """
        wf_service = netsvc.LocalService("workflow")
        proc_obj = self.pool.get('procurement.order')
        # Proc product of type service should be confirm at this
        # stage, otherwise, when picking of related PO is created
        # then done, it stay blocked at running stage
        proc_ids = proc_obj.search(cr, uid, [('purchase_id', 'in', ids)],
                                   context=context)
        for proc in proc_obj.browse(cr, uid, proc_ids, context=context):
            if proc.product_id.type == 'service':
                wf_service.trg_validate(uid, 'procurement.order',
                                        proc.id, 'button_confirm', cr)
                wf_service.trg_validate(uid, 'procurement.order',
                                        proc.id, 'button_check', cr)
        return True

    def action_picking_create(self, cr, uid, ids, context=None):
        """ When the picking is created, we'll:

        Only for the sales order lines mto + drop shipping:
        Link the moves with the procurement of the sale order lines
        which generated the purchase and confirm the procurement.
        """
        assert len(ids) == 1, "Expected only 1 ID, got %r" % ids
        picking_id = super(purchase_order, self).action_picking_create(
            cr, uid, ids, context=context)
        if not picking_id:
            return picking_id
        wf_service = netsvc.LocalService("workflow")
        picking_obj = self.pool.get('stock.picking')
        picking = picking_obj.browse(cr, uid, picking_id, context=context)
        for move in picking.move_lines:
            purchase_line = move.purchase_line_id
            if not purchase_line:
                continue
            sale_line = purchase_line.sale_order_line_id
            if not sale_line:
                continue
            if not (sale_line.type == 'make_to_order'
                    and sale_line.sale_flow == 'direct_delivery'):
                continue
            procurement = sale_line.procurement_id
            if procurement and not procurement.move_id:
                # the procurement for the sales and purchase is the same!
                # So when the move will be done, the sales order and the
                # purchase order will be shipped at the same time
                procurement.write({'move_id': move.id})
                wf_service.trg_validate(uid, 'procurement.order',
                                        procurement.id, 'button_confirm', cr)
                if purchase_line is not None:
                    wf_service.trg_validate(uid, 'procurement.order',
                                            procurement.id, 'button_check', cr)
        self.validate_service_product_procurement(cr, uid, ids, context)
        return picking_id


class purchase_order_line(orm.Model):
    _inherit = 'purchase.order.line'

    _columns = {
        'lr_source_line_id': fields.many2one(  # one2one relation with selected_bid_line_id
            'logistic.requisition.source',
            'Logistic Requisition Source',
            readonly=True,
            ondelete='restrict'),
        'from_bid_line_id': fields.many2one(
            'purchase.order.line',
            'Generated from bid',
            readonly=True),
        'po_line_from_bid_ids': fields.one2many(
            'purchase.order.line',
            'from_bid_line_id',
            'Lines generated by the bid',
            readonly=True),
    }

    def _prepare_lrs_update_from_po_line(self, cr, uid, vals,
            po_line, context=None):
        """ Take the vals dict from po line and return a vals dict for LRS

        :param dict vals: value of to be written in new po line
        :param browse_record po_line: purchase.order.line
        :returns dict : vals to be written on logistic.requisition.source

        """
        lrs_vals = {}
        if vals.get('product_qty'):
            lrs_vals['proposed_qty'] = vals.get('product_qty')
        if vals.get('product_id'):
            lrs_vals['proposed_product_id'] = vals.get('product_id')
        if vals.get('product_uom'):
            lrs_vals['proposed_uom_id'] = vals.get('product_uom')
        if vals.get('price_unit'):
            currency_obj = self.pool['res.currency']
            to_curr = po_line.lr_source_line_id.requisition_id.currency_id.id
            from_curr = po_line.order_id.pricelist_id.currency_id.id
            price = currency_obj.compute(cr, uid, from_curr, to_curr,
                    vals.get('price_unit'), False)
            lrs_vals['unit_cost'] = price
        if vals.get('date_planned'):
            if po_line.lr_source_line_id.transport_applicable:
                if pr_bid_line.order_id.transport == 'included':
                    lrs_vals['date_etd'] = False
                    lrs_vals['date_eta'] = vals.get('date_planned')

                else:
                    lrs_vals['date_etd'] = vals.get('date_planned')
                    lrs_vals['date_eta'] = False
            else:
                lrs_vals['date_etd'] = vals.get('date_planned')
                lrs_vals['date_eta'] = vals.get('date_planned')
        return lrs_vals

    def write(self, cr, uid, ids, vals, context=None):
        """ Here we implement something to allow the update of LRS when some
        information are changed in PO line. It should be possible to do it when :
        PO is still in draft
        LRL is not marked as sourced
        Once done, nobody should be able to change the PO line infos
        """
        if context is None:
            context = {}
        if not ids:
            return True
        #We have to enforce list as it is called by function_inv
        if not isinstance(ids, list):
            ids = [ids]
        if (vals.get('product_qty') or vals.get('product_id')
                                    or vals.get('product_uom')
                                    or vals.get('price_unit')
                                    or vals.get('date_planned')):
            lrs_obj = self.pool.get('logistic.requisition.source')
            for line in self.browse(cr, uid, ids, context=context):
                if line.lr_source_line_id:
                    if (line.lr_source_line_id.requisition_line_id in
                                                ('sourced', 'quoted')):
                        raise osv.except_osv(
                            _('UserError'),
                            _(
                                "You cannot change the informations because this PO line "
                                "is already linked to a Logistic Requsition Line %s marked "
                                "as sourced or quoted." % (line.lr_source_line_id.name)
                            )
                    )
                    else:
                        lrs_vals = self._prepare_lrs_update_from_po_line(cr,
                            uid, vals, line, context=context)
                        lrs_obj.write(cr, uid, [line.lr_source_line_id.id],
                            lrs_vals, context=context)
        return super(purchase_order_line, self).write(cr, uid, ids, vals,
                                                      context=context)
    def unlink(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            if line.lr_source_line_id:
                if (line.lr_source_line_id.requisition_line_id in
                                            ('sourced', 'quoted')):
                    raise osv.except_osv(
                        _('UserError'),
                        _(
                            "You cannot delete this PO line because it is "
                            "already linked to a Logistic Requsition Line %s marked "
                            "as sourced or quoted." % (line.lr_source_line_id.name)
                        )
                )
        return super(purchase_order_line, self).unlink(cr, uid, ids, context=context)
