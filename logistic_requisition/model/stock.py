# -*- coding: utf-8 -*-

from openerp.osv import orm


class stock_location(orm.Model):
    _inherit = "stock.location"

    def name_get(self, cr, uid, ids, context=None):
        # always return the full hierarchical name
        res = self._complete_name(cr, uid, ids,
                                  'complete_name',
                                  None,
                                  context=context)
        return res.items()

    def _complete_name(self, cr, uid, ids, name, args, context=None):
        """ Forms complete name of location from parent location to
        child location.

        :returns: Dictionary of values
        """
        res = {}
        # TODO
        for m in self.browse(cr, uid, ids, context=context):
            res[m.id] = m.name
        return res
