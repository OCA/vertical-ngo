# -*- coding: utf-8 -*-
#
#
#    Author: Jacques-Etienne Baudoux, Guewen Baconnier
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
#
from openerp import models, fields, api


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    # TODO : Remove transport plan things (ETA, ETD)
    # CAlled by the "Chose products" buton in the call for bid process
    @api.multi
    def _split_requisition_sources(self):
        """ Effectively split the logistic requisition sources.
        For each selected bid line, we ensure there is a corresponding source
        (one2one relation) and we update the source data with the bid line
        data.
        """
        self.ensure_one()
        for pr_line in self.line_ids:
            if not pr_line.logistic_requisition_source_ids:
                # this call for bid line has been added manually
                continue
            source = pr_line.logistic_requisition_source_ids[0]
            has_requisition = source.requisition_id
            if not has_requisition:
                continue
            to_curr = source.requisition_id.currency_id
            set_sources = set()
            # Look for po lines of this purchase_requisition line
            for pr_bid_line in pr_line.purchase_line_ids:
                # Compute from bid currency to LRS currency
                from_curr = pr_bid_line.order_id.pricelist_id.currency_id
                price = from_curr.compute(pr_bid_line.price_unit, to_curr,
                                          round=False)
                vals = {
                    'price_is': 'fixed',
                    'proposed_qty': pr_bid_line.quantity_bid,
                    'proposed_product_id': pr_bid_line.product_id.id,
                    'proposed_uom_id': pr_bid_line.product_uom.id,
                    'selected_bid_line_id': pr_bid_line.id,
                    'unit_cost': price,
                    #FIXME: we need to take care of the scheduled date
                    # set eta or etd depending if transport is included
                    }
                if source.transport_applicable:
                    if pr_bid_line.order_id.transport == 'included':
                        vals.update({'date_etd': False,
                                     'date_eta': pr_bid_line.date_planned,
                                     })
                    else:
                        vals.update({'date_etd': pr_bid_line.date_planned,
                                     'date_eta': False,
                                     })
                else:
                    vals.update({'date_etd': pr_bid_line.date_planned,
                                 'date_eta': pr_bid_line.date_planned,
                                 })
                if not pr_bid_line.lr_source_line_id:
                    if (not pr_bid_line.quantity_bid
                            or pr_bid_line.state not in ('confirmed', 'done')):
                        # this bid line is not selected
                        continue
                    # We need to set the quantity on the LR source line and
                    # create the one2one link with this bid line
                    if (not source.selected_bid_line_id
                            and source.id not in set_sources):
                        pr_line.logistic_requisition_source_ids[0].write(vals)
                        pr_bid_line.write({'lr_source_line_id': source.id})
                        set_sources.add(source.id)
                    else:
                        # create a new source line
                        vals.update({
                            'purchase_requisition_line_id': pr_line.id})
                        new_id = source.copy(default=vals)
                        pr_bid_line.lr_source_line_id = new_id
                else:
                    if (not pr_bid_line.quantity_bid
                            or pr_bid_line.state not in ('confirmed', 'done')):
                        # this bid line is not anymore selected
                        pr_bid_line.lr_source_line_id.proposed_qty = 0
                    else:
                        # update source line
                        pr_bid_line.lr_source_line_id.write(vals)
        return

    @api.multi
    def close_callforbids_ok(self):
        """ We have to split the logistic requisition lines according to
        the selected lines after the selection of the lines, when we
        click on the 'Confirm selection of lines'.
        """
        result = super(PurchaseRequisition, self).close_callforbids_ok()
        self._split_requisition_sources()
        return result

    @api.model
    def _prepare_po_line_from_tender(self, tender, line, purchase_id):
        """ Prepare the values to write in the purchase order line
        created for a line of the tender.

        :param tender: the source tender from which we generate a purchase
                       order
        :param line: the source tender's line from which we generate a line
        :param purchase_id: the id of the new purchase
        """
        vals = super(PurchaseRequisition, self
                     )._prepare_po_line_from_tender(tender, line, purchase_id)
        vals['from_bid_line_id'] = line.id
        return vals


class PurchaseRequisition_Line(models.Model):
    _inherit = 'purchase.requisition.line'

    logistic_requisition_source_ids = fields.One2many(
        'logistic.requisition.source',
        'purchase_requisition_line_id',
        string='Logistic Requisition Source Lines',
        readonly=True)
