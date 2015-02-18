# -*- coding: utf-8 -*-
#
#
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
#
from openerp import api
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

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """
        Allows to search incoterms by code

        Show results by code on top as they are more accurate.
        """
        if args is None:
            args = []
        results = []
        if name:
            recs = self.search([('code', operator, name)], limit=limit)
            results = recs.name_get()
            limit -= len(results)
            # Do not search for same records
            args.insert(0, ('id', 'not in', recs.ids))

        results.extend(super(stock_incoterms, self).name_search(
            name, args=args, operator=operator, limit=limit))
        return results
