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


def select_line(test, purchase_line, quantity):
    """ Select a quantity of products the BID """
    purchase_line.quantity_bid = quantity
    purchase_line.action_confirm()


def bid_encoded(test, purchase_order):
    """ Declare that BIDs are encoded for a purchase order """
    wizard_obj = test.env['purchase.action_modal.datetime']
    context = {'active_id': purchase_order.id,
               'active_ids': [purchase_order.id],
               'active_model': 'purchase.order'}
    res = purchase_order.bid_received()
    context.update(res['context'])
    wizard = wizard_obj.with_context(context).create({})
    res = wizard.action()
