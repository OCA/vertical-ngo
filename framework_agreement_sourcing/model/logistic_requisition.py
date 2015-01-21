# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
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
##############################################################################
from openerp import models, api, exceptions


class LogisticsRequisitionLine(models.Model):

    """Override to enable generation of source line"""

    _inherit = "logistic.requisition.line"

    @api.multi
    def _prepare_agreement_source(self, agreement, qty=None):
        """Prepare data dict for source line creation. If an agreement
        is given, the sourcing_method will be an LTA ('fw_agreement').
        Otherwise, if it's a stockable product we'll go to tender
        by setting sourcing_method as 'procurement'. Finally marke the
        rest as 'other'. Those are default value that can be changed afterward
        by the user.

        :param agreement: browse record of origin agreement
        :param qty: quantity to be set on source line

        :returns: dict to be used by Model.create

        """

        if not agreement.product_id == self.product_id:
            raise exceptions.ValueError(
                "Product mismatch for agreement and requisition line")
        values = self._prepare_source(qty)
        values.update(
            framework_agreement_id=agreement.id,
            sourcing_method='fw_agreement',
            unit_cost=agreement.get_price(qty, self.currency_id),
        )
        return values

    # XXX to extract on agreement model
    def _sort_agreements(self, cr, uid, agreements, qty, currency=None,
                         context=None):
        """Sort agreements to be proposed

        Agreement with negociated currency will first be taken in account
        then they will be choosen by price converted in currency company

        :param agreements: list of agreements to be sorted
        :param currency: prefered currrency

        :returns: sorted agreements list

        """
        if not agreements:
            return agreements

        def _best_company_price(cr, uid, agreement, qty):
            """Returns the best price in company currency

            For given agreement and price

            """
            comp_id = self.pool['framework.agreement']._company_get(cr, uid)
            comp_obj = self.pool['res.company']
            currency_obj = self.pool['res.currency']
            comp_currency = comp_obj.browse(cr, uid, comp_id,
                                            context=context).currency_id
            prices = []
            for pl in agreement.framework_agreement_pricelist_ids:
                price = agreement.get_price(qty, currency=pl.currency_id)
                comp_price = currency_obj.compute(cr, uid,
                                                  pl.currency_id.id,
                                                  comp_currency.id,
                                                  price, False)
                prices.append(comp_price)
            return min(prices)

        firsts = []
        if currency:
            firsts = [x for x in agreements if x.has_currency(currency)]
            lasts = [x for x in agreements if not x.has_currency(currency)]
            firsts.sort(key=lambda x: x.get_price(qty, currency=currency))
            lasts.sort(key=lambda x: _best_company_price(cr, uid, x, qty))
            return firsts + lasts
        else:
            agreements.sort(key=lambda x: _best_company_price(cr, uid, x, qty))
            return agreements

    @api.multi
    def _generate_agreement_sources(self, agreements, currency=None):
        """Generate 1/n source line(s) for one requisition line.

        This is done using available agreements.
        We first look for cheapeast agreement.
        Then if no more quantity are available and there is still remaining
        needs we look for next cheapest agreement or return remaining qty.
        we prefer to use agreement with negociated currency first even
        if they are cheaper in other currences. Then it will choose remaining
        agreements ordered by price converted in company currency

        :param agreements: list of agreement which can be used
        :param currency: preferred currency for agreement sorting

        :returns: remaining quantity to source

        """
        qty = self.requested_qty
        if not agreements:
            return qty
        agreements = self._sort_agreements(agreements, qty,
                                           currency=currency)
        src_model = self.env['logistic.requisition.source']
        remaining_qty = qty
        while remaining_qty and agreements:
            current_agr = agreements.pop(0)
            avail = current_agr.available_quantity
            if not avail:
                continue
            avail_sold = avail - remaining_qty
            to_consume = remaining_qty if avail_sold >= 0 else avail
            remaining_qty -= to_consume

            values = self._prepare_agreement_source(current_agr,
                                                    qty=to_consume)
            src_model.create(values)

        return remaining_qty

    @api.multi
    def _generate_sources(self):
        """Generate one or n source line(s) per requisition line.

        Depending on the available resources. If there is framework
        agreement(s) running we generate one or n source line using agreements
        otherwise we generate one source line using tender process

        """
        self.ensure_one()
        if self.source_ids:
            return None
        Agreement = self.env['framework.agreement']
        date = self.requisition_id.date
        product_id = self.product_id.id
        agreements = Agreement.get_all_product_agreements(product_id, date)
        if agreements:
            currency = self.currency_id
            missing_qty = self._generate_agreement_sources(
                agreements, currency=currency)
            if missing_qty:
                self._generate_default_source(force_qty=missing_qty)
        super(LogisticsRequisitionLine, self)._generate_sources()
