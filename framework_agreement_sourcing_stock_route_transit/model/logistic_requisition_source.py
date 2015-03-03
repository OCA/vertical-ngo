# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2013-2015 Camptocamp SA
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
import logging

from openerp.osv import orm


class LogisticRequisitionSource(orm.Model):
    _inherit = "logistic.requisition.source"

    def _prepare_purchase_order(self, cr, uid,
                                line, po_pricelist, context=None):
        """change the destination location of the generated purchase order

        In case the PO delivers to a warehouse, use the incoming transit
        location, if it is dropshipping, use the outgoing transit location.
        """
        IrModelData = self.pool['ir.model.data']

        def ref(xmlid):
            return IrModelData.xmlid_to_res_id(cr, uid, xmlid)

        _super = super(LogisticRequisitionSource, self)
        res = _super._prepare_purchase_order(cr, uid,
                                             line, po_pricelist,
                                             context=context)
        xmlid_dropship = 'stock_dropshipping.picking_type_dropship'
        if res.get('picking_type_id') == ref(xmlid_dropship):
            transit_location_id = ref('stock_route_transit.transit_outgoing')
        elif 'picking_type_id' in res:
            PickType = self.pool['stock.picking.type']
            picking_type = PickType.browse(cr, uid,
                                           res['picking_type_id'],
                                           context=context)
            transit_location_id = picking_type.default_location_dest_id.id
        else:
            # ouch: we get not picking type if it is not delivered to a
            # customer or a warehouse
            logger = logging.getLogger(__name__)
            logger.warning('unable to figure out the picking_type, '
                           'likely because the consignee is not '
                           'a customer or a warehouse')
            transit_location_id = res.get('location_id', False)
        res['location_id'] = transit_location_id
        return res
