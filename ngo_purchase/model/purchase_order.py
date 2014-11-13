# -*- coding: utf-8 -*-
#
#
#    Author: Yannick Vaucher
#    Copyright 2014 Camptocamp SA
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
from openerp import models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    req_bid_tendering_mode = fields.Selection(
        related='requisition_id.bid_tendering_mode',
        selection=[('open', 'Open'),
                   ('restricted', 'Restricted')],
        string='Call for Bids Mode',
        readonly=True,
        help="Call for Bids mode of the requisition from which this RFQ was "
             "generated\n- Restricted: Only the Tender's creator can select "
             "bidders and generate a RFQ for each of those.\n"
             "- Open : anybody can bid.")
    req_date_end = fields.Datetime(
        related='requisition_id.date_end',
        string="Bid Submission Deadline",
        readonly=True)
