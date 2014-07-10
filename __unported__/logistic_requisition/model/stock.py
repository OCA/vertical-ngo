# -*- coding: utf-8 -*-

from openerp.osv import orm


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
