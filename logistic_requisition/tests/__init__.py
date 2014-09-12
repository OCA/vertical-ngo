# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
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
from . import test_purchase_split_requisition
from . import test_sale_order_from_lr_confirm
from . import test_mto_workflow
from . import test_mutlicurrency_update_po_line


fast_suite = [
]

checks = [
    test_purchase_split_requisition,
    test_sale_order_from_lr_confirm,
    test_mto_workflow,
    test_mutlicurrency_update_po_line,
]
