#    Author: Alexandre Fayolle, Leonardo Pistone
#    Copyright 2014-2015 Camptocamp SA
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
from openerp.tests.common import TransactionCase


class TestShipAddresses(TransactionCase):

    def test_ship_addresses(self):
        so = self.env.ref('logistic_order_donation.donation_1')
        out_transit_loc = self.env.ref('stock_route_transit.transit_outgoing')
        customers_loc = self.env.ref('stock.stock_location_customers')

        # if sale_exception is installed, ignore exceptions because they are
        # irrelevant to this test. If not, assigning a missing field is no_op
        so.ignore_exceptions = True

        so.signal_workflow('order_confirm')
        self.env['procurement.order'].run_scheduler()
        self.assertEqual(2, len(so.picking_ids))
        for picking in so.picking_ids:
            moves = picking.move_lines
            self.assertEqual(2, len(moves))
            for move in moves:
                self.assertEqual(move.ship_from_address_id, so.partner_id)
                self.assertEqual(move.ship_to_address_id,
                                 so.partner_shipping_id)

            if picking.location_dest_id == customers_loc:
                self.assertEqual(picking.location_id, out_transit_loc)
                for move in moves:
                    self.assertEqual(move.location_id, out_transit_loc)
            else:
                self.assertEqual(picking.location_dest_id,
                                 out_transit_loc)
                for move in moves:
                    self.assertEqual(move.location_dest_id, out_transit_loc)
