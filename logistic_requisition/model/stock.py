# -*- coding: utf-8 -*-

from openerp.osv import orm


class stock_location(orm.Model):
    _inherit = "stock.location"

    def _get_shop_from_location(self, cr, uid, location_id, context=None):
        """ Returns the sale.shop for a location.

        Returns None if no shop exist for a location.
        """
        if isinstance(location_id, (tuple, list)):
            assert len(location_id) == 1, "Only 1 ID accepted"
            location_id = location_id[0]
        warehouse_obj = self.pool.get('stock.warehouse')
        shop_obj = self.pool.get('sale.shop')
        warehouse_ids = warehouse_obj.search(
            cr, uid,
            [('lot_stock_id', '=', location_id)],
            context=context)
        if not warehouse_ids:
            return None
        shop_ids = shop_obj.search(cr, uid,
                                   [('warehouse_id', 'in', warehouse_ids)],
                                   context=context)
        if not shop_ids:
            return None
        assert len(shop_ids) == 1, (
            "Several shops found for location with id %s" % location_id)
        return shop_ids[0]
