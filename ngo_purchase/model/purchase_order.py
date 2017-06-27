# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields


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
