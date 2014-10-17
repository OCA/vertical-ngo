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


def add_line(test, requisition, vals):
    """ Create a logistic requisition line in an existing logistic
    requisition.

    :param test: instance of the running test
    :param requisition: recordset of the requisition
    :param vals: dict of values to create the requisition line
    :returns: id of the line
    """
    log_req_line_obj = test.env['logistic.requisition.line']
    vals = vals.copy()
    vals['requisition_id'] = requisition.id
    return log_req_line_obj.create(vals)


def add_source(test, requisition_line, vals):
    """ Create a logistic requisition source in an existing logistic
    requisition line.

    :param test: instance of the running test
    :param requisition_line: recordset of the requisition line
    :param vals: dict of values to create the requisition line
    :returns: id of the source line
    """
    log_req_source_obj = test.env['logistic.requisition.source']
    vals = vals.copy()
    vals['requisition_line_id'] = requisition_line.id
    return log_req_source_obj.create(vals)


def assign_lines(test, lines, user_id):
    """ Assign lines of a logistic requisition

    :param test: instance of the running test
    :param lines: recordset of the lines to assign
    :param user_id: user to assign on the lines
    """
    lines.write({'logistic_user_id': user_id})


def source_lines(test, lines):
    """ Source lines of a logistic requisition

    :param test: instance of the running test
    :param lines: recordset of the lines to assign
    """
    lines.button_sourced()


def check_line_unit_cost(test, lrs, bid_price, bid_pricelist):
    to_curr = lrs.requisition_id.currency_id
    from_curr = bid_pricelist.currency_id
    price = from_curr.compute(bid_price, to_curr, round=False)
    delta = abs(lrs.unit_cost - price)
    assert delta < 0.01, ("The unit cost of the LRS should be the selected bid"
                          " value converted regarding the different currency")


def create_quotation(test, requisition, lines):
    """ Create the quotation / cost estimate (sale.order)

    It also checks if a quotation line has been created for
    each line_ids. That means that you have to give only the
    line_ids which are valid for the creation of the quotation
    (sourced).

    :param test: instance of the running test
    :param requisition: recordset of the requisition
    :returns: tuple with (sale id, [sale line ids])
    """
    wizard_obj = test.env['logistic.requisition.cost.estimate']
    ctx = {'active_model': 'logistic.requisition.line',
           'active_ids': lines.ids}
    wizard = (wizard_obj
              .with_context(ctx)
              .create({'requisition_id': requisition.id}))
    res = wizard.cost_estimate()
    sale_id = res['res_id']
    sale = test.env['sale.order'].browse(sale_id)
    sale_lines = sale.order_line
    source_lines = [sl for line in lines for sl in line.source_ids]
    test.assertEquals(len(sale_lines),
                      len(source_lines),
                      "A sale line per logistic requisition "
                      "soucing line should have been created")
    # for sale_line in sale_lines:
    #     test.assertTrue(sale_line.logistic_requisition_source_id.id
    #                     in [sl.id for sl in source_lines])
    return sale, sale_lines


def create_purchase_requisition(test, source, pricelist=None):
    """ Create a purchase requisition for a logistic requisition line """
    purch_req_id = source._action_create_po_requisition(pricelist=pricelist)
    assert purch_req_id
    return purch_req_id
