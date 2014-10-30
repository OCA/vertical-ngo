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


""" Helpers for the tests for the purchase requisition model
"""


def confirm_call(test, purchase_requisition):
    """ Confirm the call for bids """
    purchase_requisition.signal_workflow('sent_suppliers')


def close_call(test, purchase_requisition):
    """ Confirm the call for bids, next step is selection of lines """
    purchase_requisition.signal_workflow('open_bid')


def bids_selected(test, purchase_requisition):
    """ Close the purchase requisition, after selection of purchase lines """
    purchase_requisition.close_callforbids_ok()


def create_draft_purchase_order(test, purchase_requisition, partner_id):
    """ Create a draft purchase order for a purchase requisition.

    Returns the purchase order created with the line.
    A logistic requisition create always only 1 line in a purchase order.

    :param test: instance of the running test
    :param purchase_requisition: recordset of the purchase requisition
    :param partner_id: id of the supplier of the purchase order
    :returns: a tuple with (browse record the purchase order created,
                            browse record of the line)
    """
    context = {'draft_bid': True}
    res = (purchase_requisition
           .with_context(context)
           .make_purchase_order(partner_id))
    po_id = res[purchase_requisition.id]
    assert po_id
    purchase = test.env['purchase.order'].browse(po_id)
    test.assertEquals(len(purchase.order_line), 1,
                      "We should always have 1 line in a purchase order "
                      "created from a logistic requisition line.")
    return purchase, purchase.order_line[0]
