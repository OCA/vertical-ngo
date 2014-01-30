# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
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
from collections import namedtuple
from openerp.tools.translate import _
from openerp.osv import orm
from .logistic_requisition_source import AGR_PROC


class logistic_requisition_line(orm.Model):
    """Override to enable generation of source line"""

    _inherit = "logistic.requisition.line"

    def _map_agr_requisiton_to_source(self, cr, uid, line,
                                      qty=0, agreement=None,
                                      context=None):
        """Prepare data dict for source line using agreement as source

        :params line: browse record of origin requistion.line
        :params agreement: browse record of origin agreement
        :params qty: quantity to be set on source line

        :returns: dict to be used by Model.create

        """
        res = {}
        res['proposed_product_id'] = line.product_id.id
        res['requisition_line_id'] = line.id
        res['proposed_uom_id'] = line.requested_uom_id.id

        if not agreement:
            raise ValueError("Missing agreement")
        if not agreement.product_id.id == line.product_id.id:
            raise ValueError("Product mismatch for agreement and requisition line")
        res['unit_cost'] = 0.0
        res['proposed_qty'] = qty
        res['framework_agreement_id'] = agreement.id
        res['procurement_method'] = AGR_PROC
        return res

    def _map_requisition_to_source(self, cr, uid, line,
                                   qty=0,
                                   context=None):
        """Prepare data dict to generate source line using requisition as source

        :params line: browse record of origin requistion.line
        :params qty: quantity to be set on source line

        :returns: dict to be used by Model.create

        """
        res = {}
        res['proposed_product_id'] = line.product_id.id
        res['requisition_line_id'] = line.id
        res['proposed_uom_id'] = line.requested_uom_id.id
        res['unit_cost'] = 0.0
        res['proposed_qty'] = qty
        res['framework_agreement_id'] = False
        if line.product_id.type == 'product':
            res['procurement_method'] = 'procurement'
        else:
            res['procurement_method'] = 'other'
        return res

    def _generate_lines_from_agreements(self, cr, uid, container, line,
                                        agreements, qty, currency=None, context=None):
        """Generate 1/n source line(s) for one requisition line.

        This is done using available agreements.
        We first look for cheapeast agreement.
        Then if no more quantity are available and there is still remaining needs
        we look for next cheapest agreement or return remaining qty

        :param container: list of agreements browse
        :param qty: quantity to be sourced
        :param line: origin requisition line

        :returns: remaining quantity to source

        """
        agreements = agreements if agreements is not None else []
        if currency:
            agreements = [x for x in agreements if x.has_currency(currency)]
        if not agreements:
            return qty
        agreements.sort(key=lambda x: x.get_price(qty, currency=currency))
        current_agr = agreements.pop(0)
        avail = current_agr.available_quantity
        if not avail:
            return qty
        avail_sold = avail - qty
        to_consume = qty if avail_sold >= 0 else avail

        source_id = self.make_source_line(cr, uid, line, force_qty=to_consume,
                                          agreement=current_agr, context=context)
        container.append(source_id)
        difference = qty - to_consume
        if difference:
            return self._generate_lines_from_agreements(cr, uid, container, line,
                                                        agreements, difference, context=context)
        else:
            return 0

    def _source_lines_for_agreements(self, cr, uid, line, agreements, currency=None, context=None):
        """Generate 1/n source line(s) for one requisition line

        This is done using available agreements.
        We first look for cheapeast agreement.
        Then if no more quantity are available and there is still remaining needs
        we look for next cheapest agreement or we create a tender source line

        :param line: requisition line browse record
        :returns: (generated line ids, remaining qty not covered by agreement)

        """
        Sourced = namedtuple('Sourced', ['generated', 'remaining'])
        qty = line.requested_qty
        generated = []
        remaining_qty = self._generate_lines_from_agreements(cr, uid, generated,
                                                             line, agreements, qty,
                                                             currency=currency, context=context)
        return Sourced(generated, remaining_qty)

    def make_source_line(self, cr, uid, line, force_qty=None, agreement=None, context=None):
        """Generate a source line for a tender from a requisition line

        :param line: browse record of origin logistic.request
        :param force_qty: if set this quantity will be used instead
        of requested quantity
        :returns: id of generated source line

        """
        qty = force_qty if force_qty else line.requested_qty
        src_obj = self.pool['logistic.requisition.source']
        if agreement:
            vals = self._map_agr_requisiton_to_source(cr, uid, line,
                                                      qty=force_qty,
                                                      agreement=agreement,
                                                      context=None)
        else:
             vals = self._map_requisition_to_source(cr, uid, line,
                                                    qty=force_qty,
                                                    context=None)

        return src_obj.create(cr, uid, vals, context=context)

    def _generate_source_line(self, cr, uid, line, context=None):
        """Generate one or n source line(s) per requisition line.

        Depending on the available resources. If there is framework agreement(s)
        running we generate one or n source line using agreements otherwise we generate one
        source line using tender process

        :param line: browse record of origin logistic.request

        :returns: list of generated source line ids

        """
        if line.source_ids:
            return None
        agr_obj = self.pool['framework.agreement']
        date = line.requisition_id.date
        currency = line.currency_id
        product_id = line.product_id.id
        agreements = agr_obj.get_all_product_agreements(cr, uid, product_id, date,
                                                        context=context)
        generated_lines = []
        if agreements:
            line_ids, missing_qty = self._source_lines_for_agreements(cr, uid, line,
                                                                      agreements, currency=currency)
            generated_lines.extend(line_ids)
            if missing_qty:
                generated_lines.append(self.make_source_line(cr, uid, line,
                                                             force_qty=missing_qty))
        else:
            generated_lines.append(self.make_source_line(cr, uid, line))

        return generated_lines

    def _do_confirm(self, cr, uid, ids, context=None):
        """Override to generate source lines from requision line.

        Please refer to _generate_source_line documentation

        """
        # TODO refactor
        # this should probably be in logistic_requisition module
        # providing a mechanism to allow each type of sourcing method
        # to generate source line
        res = super(logistic_requisition_line, self)._do_confirm(cr, uid, ids,
                                                                 context=context)
        for line_br in self.browse(cr, uid, ids, context=context):
            self._generate_source_line(cr, uid, line_br, context=context)
        return res


# Removed cuause we use here currency, no more pricelist


# class logistic_requisition(orm.Model):
#     """Add get pricelist function"""

#     _inherit = "logistic.requisition"

#     def get_pricelist(self, cr, uid, requisition_id, context=None):
#         """Retrive pricelist id to use in sourcing by agreement process

#         :returns: pricelist record

#         """
#         if isinstance(requisition_id, (list, tuple)):
#             assert len(requisition_id) == 1
#             requisition_id = requisition_id[0]
#         requisiton = self.browse(cr, uid, requisition_id, context=context)
#         plist = requisiton.partner_id.property_product_pricelist
#         if not plist:
#             raise orm.except_orm(_('No price list on customer'),
#                                  _('Please set sale price list on %s partner') %
#                                  requisiton.partner_id.name)
#         return plist
