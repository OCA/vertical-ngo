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
from itertools import groupby

from openerp import models, fields, api
from openerp.exceptions import except_orm
from openerp.tools.translate import _
from .logistic_requisition import LogisticRequisitionSource


# TODO: We want to deconnect the SO from the LR and LRS. The goal would be
# to be able to create manually a SO (cost estimate) withou using the wizard
# from an LRL. So, if I provide all the needed infos and link to other documents
# it should work.

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    requisition_id = fields.Many2one('logistic.requisition',
                                     'Logistic Requisition',
                                     ondelete='restrict',
                                     copy=False)

    # TODO: 
    # sale_dropshipping allow to link the procurement created from a SO to 
    # a purchase order. That means, we have a purchase_line_id on SO line 
    # completed once the procurement is reunning.
    # In our context, as we already have generated the PO, this method recreate 
    # the link sale_dropshipping should have made.
    # In version 8, it'll e different because of Routes but we'll STILL HAVE 
    # ALREADY GENERATED THE PO => We want to be able to link the PO line
    # manually with the SO Line.
    @api.model
    def _create_procurements_direct_mto(self, order, order_lines):
        """ Create procurement for the direct MTO lines.

        No picking or move is created for those lines because the
        delivery will be handled by the 'Incoming Shipment' from the
        purchase order.

        We reconnect the procurement to the existing purchase order if
        it has already be created from the logistic requisition.

        The purchase order has to be handled like a drop shipping for
        the procurements, so we change the sale flow of the purchase
        to 'direct_delivery'. We also link the purchase with the sale
        and sale lines because this is how the ``sale_dropshipping``
        does.
        """
        proc_obj = self.env['procurement.order']
        purchases = self.env['purchase.order'].browse()
        for sale_line in order_lines:
            purchase_line = None
            logistic_req_source = sale_line.logistic_requisition_source_id
            if logistic_req_source:
                if not logistic_req_source.purchase_line_id:
                    raise except_orm(
                        _('Error'),
                        _('The logistic requisition line %s has no '
                          'purchase order line.') % logistic_req_source.name)
                purchase_line = logistic_req_source.purchase_line_id
                purchases |= purchase_line.order_id

            else:  # no logistic requisition line
                # The sales line has been created manually as a mto and
                # dropshipping, pass it to the normal flow
                super(SaleOrder, self
                      )._create_procurements_direct_mto(order, [sale_line])
                continue

            # reconnect with the purchase line created previously
            # by the purchase requisition
            # as needed by the sale_dropshipping module
            purchase_line.write({'sale_order_line_id': sale_line.id})

            date_planned = self._get_date_planned(order, sale_line,
                                                  order.date_order)
            vals = self._prepare_order_line_procurement(order,
                                                        sale_line, False,
                                                        date_planned)
            vals['sale_order_line_id'] = sale_line.id
            # the purchase order for this procurement as already
            # been created from the purchase requisition, reconnect
            # with it
            vals['purchase_id'] = purchase_line.order_id.id
            proc_id = proc_obj.create(vals)
            sale_line.procurement_id = proc_id
            # We do not confirm the procurement. It will stay in 'draft'
            # without reservation move. At the moment when the picking
            # (in) of the purchase order will be created, we'll write
            # the id of the picking's move in this procurement and
            # confirm the procurement
            # (see in purchase_order.action_picking_create())
            # In there, we'll also take care and confirm all procurements
            # with product of type service.

        # set the purchases to direct delivery
        purchases.write({'invoice_method': 'order',
                         'sale_flow': 'direct_delivery',
                         'sale_id': order.id})

    # TODO: I think we have in v 8.0 the procurement group that may help
    # to split the deliveries properly. Try to use them.
    @api.model
    def _create_pickings_and_procurements(self, order, order_lines,
                                          picking_id=False):
        """ Instead of creating 1 picking for all the sale order lines, it
        creates:

        * 1 delivery order per different source location (each line has its
        own)

        At end, only the MTS / not drop shipping lines will be part
        of the delivery orders, because the sale_dropshipping module
        will take care of the drop shipping lines (create only
        procurement.order for them and exclude them from the
        picking).

        :param browse_record order: sales order to which the order lines belong
        :param list(browse_record) order_lines: sales order line records to
                                                procure
        :param int picking_id: optional ID of a stock picking to which the
                               created stock moves will be added. A new
                               picking will be created if ommitted.
        :return: True
        """

        direct_mto_lines = []
        other_lines = []
        for line in order_lines:
            if (line.type == 'make_to_order' and
                    line.sale_flow == 'direct_delivery'):
                direct_mto_lines.append(line)
            else:
                other_lines.append(line)

        self._create_procurements_direct_mto(order, direct_mto_lines)

        def get_location_address(line):
            if line.location_id and line.location_id.partner_id:
                return line.location_id.partner_id.id

        # group the lines by address of source location and create
        # a different picking for each address
        sorted_lines = sorted(other_lines, key=get_location_address)
        for _unused_location, lines in groupby(sorted_lines,
                                               key=get_location_address):
            super(SaleOrder, self
                  )._create_pickings_and_procurements(order,
                                                      list(lines),
                                                      picking_id=False)
        return True

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default['invoice_ids'] = False
        return super(SaleOrder, self
                     ).copy(cr, uid, id, default=default, context=context)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    logistic_requisition_source_id = fields.Many2one(
        'logistic.requisition.source',
        'Requisition Source',
        ondelete='restrict')
    price_is = fields.Selection(
        LogisticRequisitionSource.PRICE_IS_SELECTION,
        string='Price is',
        help="When the price is an estimation, the final price may change. "
             "I.e. it is not based on a request for quotation.",
        default='fixed')
    account_code = fields.Char('Account Code', size=32)

    # TODO: The purchase_requisition from where to generate
    # the draft PO should in v8 be taken from a link on the SO line.
    # We should not get back to the LRS for that.
    @api.multi
    def button_confirm(self):
        """ When a sale order is confirmed, we'll also generate the
        purchase order on the purchase requisition of the logistic
        requisition which has created the sales order lines.

        E.g.
        I create a logistic requisition with 2 lines.
        On each line, I create a purchase requisition, I select the
        purchase lines and confirm the selection.
        Then, a sales order is generated from the logistic requisition, a line
        is created for each logistic requisition line.
        When this sale order is confirmed, for each line, I have to go
        back to the logistic requisition line, and generate the purchase
        order for the purchase requisition.
        """
        result = super(SaleOrderLine, self).button_confirm()
        purchase_requisitions = set()
        for line in self:
            source = line.logistic_requisition_source_id
            if not source:
                continue
            # TODO : Take that link from SO Line
            purchase_req = source.po_requisition_id
            if purchase_req:
                purchase_requisitions.add(purchase_req)
        # Beware! generate_po() accepts a list of ids, but discards the
        # ids > 1.
        # We can't call it 2 times on a purchase_requisition,
        # and 2 lines may have the same one.
        for purchase_requisition in purchase_requisitions:
            purchase_requisition.generate_po()
        return result
