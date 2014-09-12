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
from openerp import netsvc


def confirm_call(test, purchase_requisition_id):
    """ Confirm the call for bids """
    wf_service = netsvc.LocalService("workflow")
    wf_service.trg_validate(test.uid, 'purchase.requisition',
                            purchase_requisition_id, 'sent_suppliers', test.cr)


def close_call(test, purchase_requisition_id):
    """ Confirm the call for bids, next step is selection of lines """
    wf_service = netsvc.LocalService("workflow")
    wf_service.trg_validate(test.uid, 'purchase.requisition',
                            purchase_requisition_id, 'open_bid', test.cr)


def bids_selected(test, purchase_requisition_id):
    """ Close the purchase requisition, after selection of purchase lines """
    purch_req_obj = test.registry('purchase.requisition')
    purch_req_obj.close_callforbids_ok(test.cr, test.uid,
                                       [purchase_requisition_id])

def change_pricelist(test, purchase_requisition_id, pricelist_id):
    """ Change the pricelist """
    purch_req_obj = test.registry('purchase.requisition')
    purch_req_obj.write(test.cr, test.uid, [purchase_requisition_id],
        {'pricelist_id': pricelist_id})


def create_draft_purchase_order(test, purchase_requisition_id, partner_id):
    """ Create a draft purchase order for a purchase requisition.

    Returns the purchase order created with the line.
    A logistic requisition create always only 1 line in a purchase order.

    :param test: instance of the running test
    :param purchase_requisition_id: id of the purchase requisition
    :param partner_id: id of the supplier of the purchase order
    :returns: a tuple with (browse record the purchase order created,
                            browse record of the line)
    """
    cr, uid = test.cr, test.uid
    purch_req_obj = test.registry('purchase.requisition')
    purch_order_obj = test.registry('purchase.order')
    context = {'draft_bid': True}
    res = purch_req_obj.make_purchase_order(cr, uid,
                                            [purchase_requisition_id],
                                            partner_id,
                                            context=context)
    po_id = res[purchase_requisition_id]
    assert po_id
    purchase = purch_order_obj.browse(cr, uid, po_id)
    test.assertEquals(len(purchase.order_line), 1,
                      "We should always have 1 line in a purchase order "
                      "created from a logistic requisition line.")
    return purchase, purchase.order_line[0]
