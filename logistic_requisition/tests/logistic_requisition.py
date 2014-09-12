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

""" Helpers for the tests for the logistic requisition model
"""


def create(test, vals):
    """ Create a logistic requisition.

    :param test: instance of the running test
    :param vals: dict of values to create the requisition
    :returns: id of the logistic requisition
    """
    cr, uid = test.cr, test.uid
    log_req_obj = test.registry('logistic.requisition')
    vals = vals.copy()
    # Commented as the on_change method is in the IFRC specific
    # addons currently
    # vals.update(
    #     log_req_obj.onchange_requester_id(
    #         cr, uid, [], vals.get('partner_id'))['value']
    # )
    vals.update(
        log_req_obj.onchange_consignee_id(
            cr, uid, [], vals.get('consignee_id'))['value']
    )
    return log_req_obj.create(cr, uid, vals)


def add_line(test, requisition_id, vals):
    """ Create a logistic requisition line in an existing logistic
    requisition.

    :param test: instance of the running test
    :param requisition_id: ID of the requisition
    :param vals: dict of values to create the requisition line
    :returns: id of the line
    """
    cr, uid = test.cr, test.uid
    log_req_line_obj = test.registry('logistic.requisition.line')
    vals = vals.copy()
    vals['requisition_id'] = requisition_id
    vals.update(
        log_req_line_obj.onchange_product_id(
            cr, uid, [],
            vals.get('product_id'),
            vals.get('requested_uom_id'))['value']
    )
    return log_req_line_obj.create(cr, uid, vals)


def add_source(test, requisition_line_id, vals):
    """ Create a logistic requisition source in an existing logistic
    requisition line.

    :param test: instance of the running test
    :param requisition_line_id: ID of the requisition line
    :param vals: dict of values to create the requisition line
    :returns: id of the source line
    """
    cr, uid = test.cr, test.uid
    log_req_source_obj = test.registry('logistic.requisition.source')
    vals = vals.copy()
    vals['requisition_line_id'] = requisition_line_id
    vals.update(
        log_req_source_obj.onchange_transport_plan_id(
            cr, uid, [],
            vals.get('transport_plan_id'))['value']
    )
    return log_req_source_obj.create(cr, uid, vals)


def confirm(test, requisition_id):
    """ Confirm a logistic requisition

    :param test: instance of the running test
    :param requisition_id: id of the requisition
    """
    log_req_obj = test.registry('logistic.requisition')
    log_req_obj.button_confirm(test.cr, test.uid, [requisition_id])


def assign_lines(test, line_ids, user_id):
    """ Assign lines of a logistic requisition

    :param test: instance of the running test
    :param line_ids: ids of the lines to assign
    :param user_id: user to assign on the lines
    """
    log_req_line_obj = test.registry('logistic.requisition.line')
    log_req_line_obj.write(test.cr, test.uid, line_ids,
                           {'logistic_user_id': user_id})


def source_lines(test, line_ids):
    """ Source lines of a logistic requisition

    :param test: instance of the running test
    :param line_ids: ids of the lines to assign
    """
    log_req_line_obj = test.registry('logistic.requisition.line')
    log_req_line_obj.button_sourced(test.cr, test.uid, line_ids)


def check_line_unit_cost(test, line_id, bid_price, bid_pricelist):
    cr, uid = test.cr, test.uid
    log_req_source_obj = test.registry('logistic.requisition.source')
    pricelist_obj = test.registry('product.pricelist')
    currency_obj = test.registry('res.currency')
    lrs = log_req_source_obj.browse(cr, uid, line_id)
    pricelist = pricelist_obj.browse(cr, uid, bid_pricelist)
    to_curr = lrs.requisition_id.currency_id.id
    from_curr = pricelist.currency_id.id
    price = currency_obj.compute(cr, uid, from_curr, to_curr,
            bid_price, False)
    test.assertEquals(lrs.unit_cost,
                      price,
                      "The unit cost of the LRS should be the selected "
                      "bid value converted regarding the different currency")



def create_quotation(test, requisition_id, line_ids):
    """ Create the quotation / cost estimate (sale.order)

    It also checks if a quotation line has been created for
    each line_ids. That means that you have to give only the
    line_ids which are valid for the creation of the quotation
    (sourced).

    :param test: instance of the running test
    :param requisition_id: id of the requisition
    :returns: tuple with (sale id, [sale line ids])
    """
    cr, uid = test.cr, test.uid
    log_req_line_obj = test.registry('logistic.requisition.line')
    wizard_obj = test.registry('logistic.requisition.cost.estimate')
    sale_obj = test.registry('sale.order')
    ctx = {'active_model': 'logistic.requisition.line',
           'active_ids': line_ids}
    wizard_id = wizard_obj.create(cr, uid,
                                  {'requisition_id': requisition_id},
                                  context=ctx)
    res = wizard_obj.cost_estimate(cr, uid, wizard_id)
    sale_id = res['res_id']
    sale = sale_obj.browse(cr, uid, sale_id)
    sale_lines = sale.order_line
    lines = log_req_line_obj.browse(cr, uid, line_ids)
    source_lines = [sl for line in lines for sl in line.source_ids]
    test.assertEquals(len(sale_lines),
                      len(source_lines),
                      "A sale line per logistic requisition "
                      "soucing line should have been created")
    sale_line_ids = []
    for sale_line in sale_lines:
        test.assertTrue(sale_line.logistic_requisition_source_id.id
                        in [sl.id for sl in source_lines])
        sale_line_ids.append(sale_line.id)
    return sale_id, sale_line_ids


def create_purchase_requisition(test, source_id, pricelist=None):
    """ Create a purchase requisition for a logistic requisition line """
    log_req_source_obj = test.registry('logistic.requisition.source')
    purch_req_id = log_req_source_obj._action_create_po_requisition(
        test.cr, test.uid, [source_id], pricelist=pricelist)
    assert purch_req_id
    return purch_req_id
