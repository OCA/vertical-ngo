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

class stock_incoterms(orm.Model):
    _inherit = "stock.incoterms"
    
    def name_get(self, cr, user, ids, context=None):
        """
        Returns a list of tupples containing id, name.
        result format: {[(id, name), (id, name), ...]}

        @param cr: A database cursor
        @param user: ID of the user currently logged in
        @param ids: list of ids for which name should be read
        @param context: context arguments, like lang, time zone

        @return: Returns a list of tupples containing id, name 
                 composed by code + name
        """
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        result = self.browse(cr, user, ids, context=context)
        res = []
        for rs in result:
            name = "%s - (%s)" % (rs.code, rs.name)
            res += [(rs.id, name)]
        return res
