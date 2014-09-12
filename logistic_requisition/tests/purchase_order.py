# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
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
##############################################################################

""" Helpers for the tests for the purchase order model
"""

def select_line(test, purchase_line_id, quantity):
    """ Select a quantity of products the BID """
    cr, uid = test.cr, test.uid
    purch_line_obj = test.registry('purchase.order.line')
    purch_line_obj.write(cr, uid, [purchase_line_id],
                         {'quantity_bid': quantity})
    purch_line_obj.action_confirm(cr, uid, [purchase_line_id])


def bid_encoded(test, purchase_order_id):
    """ Declare that BIDs are encoded for a purchase order """
    cr, uid = test.cr, test.uid
    wizard_obj = test.registry('purchase.action_modal_datetime')
    purch_order_obj = test.registry('purchase.order')
    context = {'active_id': purchase_order_id,
               'active_ids': [purchase_order_id],
               'active_model': 'purchase.order'}
    res = purch_order_obj.bid_received(cr, uid, [purchase_order_id],
                                      context=context)
    context.update(res['context'])
    wizard_id = wizard_obj.create(cr, uid, {}, context=context)
    res = wizard_obj.action(cr, uid, [wizard_id], context=context)
