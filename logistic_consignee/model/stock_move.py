# -*- coding: utf-8 -*-
#
#
#    Author: Yannick Vaucher
#    Copyright 2014 Camptocamp SA
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
from openerp import models, api


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.cr_uid_ids_context
    def _picking_assign(self, cr, uid, move_ids, procurement_group,
                        location_from, location_to, context=None):
        res = super(StockMove, self
                    )._picking_assign(cr, uid, move_ids, procurement_group,
                                      location_from, location_to,
                                      context=context)
        pick_ids = self.pool['stock.picking'].search(
            cr, uid, [
                ('group_id', '=', procurement_group),
                ('location_id', '=', location_from),
                ('location_dest_id', '=', location_to),
                ('state', 'in', ['draft', 'confirmed', 'waiting'])])
        if pick_ids:
            pick_id = pick_ids[0]
            pick = self.pool['stock.picking'].browse(cr, uid, pick_id,
                                                     context=context)
            if pick.sale_id and not pick.consignee_id:
                pick.write({'consignee_id': pick.sale_id.consignee_id.id})
        return res
