# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2013 Camptocamp SA
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


def create(test, vals, lines):
    """ Create a logistic requisition.

    :param test: instance of the running test
    :param vals: dict of values to create the requisition
    :param lines: list with a dict per line to create with their values
    :returns: a tuple with (id of the requisition created,
                            [ids of the lines])
    """
    cr, uid = test.cr, test.uid
    log_req_obj = test.registry('logistic.requisition')
    log_req_line_obj = test.registry('logistic.requisition.line')
    vals.update(
        log_req_obj.onchange_requester_id(
            cr, uid, [], vals.get('partner_id'))['value']
    )
    vals.update(
        log_req_obj.onchange_consignee_id(
            cr, uid, [], vals.get('consignee_id'))['value']
    )
    vals.update(
        log_req_obj.onchange_validate(
            cr, uid, [],
            vals.get('budget_holder_id'),
            False,
            'date_budget_holder')['value']
    )
    vals.update(
        log_req_obj.onchange_validate(
            cr, uid, [],
            vals.get('finance_officer_id'),
            False,
            'date_finance_officer')['value']
    )
    requisition_id = log_req_obj.create(cr, uid, vals)
    line_ids = []
    for row_vals in lines:
        row_vals['requisition_id'] = requisition_id
        row_vals.update(
            log_req_line_obj.onchange_product_id(
                cr, uid, [],
                row_vals.get('product_id'),
                row_vals.get('requested_uom_id'))['value']
        )
        row_vals.update(
            log_req_line_obj.onchange_transport_plan_id(
                cr, uid, [],
                row_vals.get('transport_plan_id'))['value']
        )
        line_id = log_req_line_obj.create(cr, uid, row_vals)
        line_ids.append(line_id)
    return requisition_id, line_ids


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
    log_req_obj = test.registry('logistic.requisition')
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
    test.assertEquals(len(sale_lines),
                      len(line_ids),
                      "A sale line per logistic requisition "
                      "line should have been created")
    sale_line_ids = []
    for sale_line in sale_lines:
        test.assertTrue(sale_line.requisition_line_id.id in line_ids)
        sale_line_ids.append(sale_line.id)
    return sale_id, sale_line_ids


def create_purchase_requisition(test, logistic_line_id):
    """ Create a purchase requisition for a logistic requisition line """
    log_req_line_obj = test.registry('logistic.requisition.line')
    purch_req_id = log_req_line_obj._action_create_po_requisition(
        test.cr, test.uid, [logistic_line_id])
    assert purch_req_id
    return purch_req_id
