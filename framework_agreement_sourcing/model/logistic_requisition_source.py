# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Leonardo Pistone
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
from itertools import chain

from openerp import fields, api, osv
from openerp.osv import orm
from openerp.tools.translate import _


class logistic_requisition_source(orm.Model):

    """Adds support of framework agreement to source line"""

    _inherit = "logistic.requisition.source"

    _columns = {
        'portfolio_id': osv.fields.many2one('framework.agreement.portfolio',
                                            'Agreement Portfolio'),
        'framework_agreement_id': osv.fields.many2one('framework.agreement',
                                                      'Agreement'),
        'framework_agreement_po_id': osv.fields.many2one(
            'purchase.order',
            'Agreement Purchase'),
        'supplier_id': osv.fields.related(
            'framework_agreement_id', 'supplier_id',
            type='many2one',  relation='res.partner',
            string='Agreement Supplier')}

    # ----------------- adapting source line to po --------------------------
    def _company(self, cr, uid, context):
        """Return company id

        :returns: company id

        """
        return self.pool['res.company']._company_default_get(
            cr, uid, self._name, context=context)

    @api.model
    def _get_po_picking_type_id(self, dest_address):
        if not dest_address:
            return False
        PickType = self.env['stock.picking.type']
        types = PickType.search([
            ('warehouse_id.partner_id', '=', dest_address.id),
            ('code', '=', 'incoming')])

        picking_type_id = False
        if types:
            picking_type_id = types[0].id
        elif dest_address.customer:
            # if destination is not for a warehouse address,
            # we set dropshipping picking type
            ref = 'stock_dropshipping.picking_type_dropship'
            picking_type_id = self.env['ir.model.data'].xmlid_to_res_id(ref)
        return picking_type_id

    def _prepare_purchase_order(self, cr, uid, line, po_pricelist,
                                context=None):
        """Prepare the dict of values to create the PO from a
           source line.

        :param browse_record line: logistic.requisition.source
        :param browse_record pricelist: product.pricelist
        :returns: data dict to be used by orm.Model.create

        """
        supplier = line.framework_agreement_id.supplier_id
        add = line.requisition_id.consignee_shipping_id
        pick_type_id = self._get_po_picking_type_id(
            cr, uid, add, context=context)
        term = supplier.property_supplier_payment_term
        term = term.id if term else False
        position = supplier.property_account_position
        position = position.id if position else False
        requisition = line.requisition_id
        data = {}
        data['portfolio_id'] = line.portfolio_id.id
        data['partner_id'] = supplier.id
        data['company_id'] = self._company(cr, uid, context)
        data['pricelist_id'] = po_pricelist.id
        data['dest_address_id'] = add.id
        if pick_type_id:
            data['picking_type_id'] = pick_type_id
        data['location_id'] = add.property_stock_customer.id
        data['payment_term_id'] = term
        data['fiscal_position'] = position
        data['origin'] = requisition.name
        data['date_order'] = requisition.date
        data['consignee_id'] = requisition.consignee_id.id
        data['incoterm_id'] = requisition.incoterm_id.id
        data['incoterm_address'] = requisition.incoterm_address
        data['type'] = 'purchase'
        return data

    def _prepare_purchase_order_line(self, cr, uid, po_id, line,
                                     po_supplier, po_pricelist, context=None):
        """Prepare the dict of values to create the PO Line from args.

        :param integer po_id: ids of purchase.order
        :param browse_record line: logistic.requisition.source
        :param browse_record po_supplier: res.partner
        :param browse_record po_pricelist: product.pricelist
        :returns: data dict to be used by orm.Model.create

        """
        data = {}
        acc_pos_obj = self.pool['account.fiscal.position']
        pl_model = self.pool['product.pricelist']
        currency = po_pricelist.currency_id

        if line.framework_agreement_id:
            price = line.framework_agreement_id.get_price(
                line.proposed_qty, currency=currency)
            supplier = line.framework_agreement_id.supplier_id
            data['framework_agreement_id'] = line.framework_agreement_id.id
        else:
            supplier = po_supplier
            price = 0.0
            if po_pricelist:
                price = pl_model.price_get(
                    cr, uid,
                    [po_pricelist.id],
                    line.proposed_product_id.id,
                    line.proposed_qty or 1.0,
                    po_supplier.id,
                    {'uom': line.proposed_uom_id.id})[po_pricelist.id]

        if not price:
            price = line.proposed_product_id.standard_price or 1.00
        taxes_ids = line.proposed_product_id.supplier_taxes_id
        taxes = acc_pos_obj.map_tax(
            cr, uid, supplier.property_account_position, taxes_ids)

        data['order_id'] = po_id
        data['product_qty'] = line.proposed_qty
        data['product_id'] = line.proposed_product_id.id
        data['product_uom'] = line.proposed_uom_id.id
        data['lr_source_line_id'] = line.id
        data['framework_agreement_id'] = line.framework_agreement_id.id
        data['price_unit'] = price
        data['name'] = line.proposed_product_id.name
        data['date_planned'] = line.requisition_id.date_delivery
        data['taxes_id'] = [(6, 0, taxes)]
        return data

    def _make_po_from_source_lines(self, cr, uid, main_source, other_sources,
                                   pricelist, context=None):
        """Create a purchase order from a source line. After creating it,
        it'll update the unit_cost of the source line accoring to the PO
        price. We do this because the currency of the PO may not be the same
        than the LRS so it may happends that value vary because of exchange
        rate.

        :param browse_record main_source: logistic.requisition.source of
            type LTA from which you want to generate to PO
        :param browse_record other_sources: logistic.requisition.source of
            type other to indlue in the PO
        :param browse_record pricelist: product.pricelist to be used in PO to
            know the currency mainly (as the prices will be computed from LTA)
        :returns integer : generated PO id

        """
        if context is None:
            context = {}
        fa_po = main_source.framework_agreement_po_id
        if fa_po and fa_po.state != 'cancel':
            raise orm.except_orm(_('Agreement Purchase Order already exists.'),
                                 _('If you want to create a new Purchase '
                                   'Order, please cancel Purchase %s')
                                 % fa_po.name)
        context['draft_po'] = True
        currency_obj = self.pool['res.currency']
        po_obj = self.pool['purchase.order']
        po_l_obj = self.pool['purchase.order.line']
        supplier = main_source.framework_agreement_id.supplier_id
        to_curr = pricelist.currency_id.id
        po_vals = self._prepare_purchase_order(cr, uid, main_source,
                                               pricelist, context=context)
        po_id = po_obj.create(cr, uid, po_vals, context=context)
        other_sources = other_sources if other_sources else []
        for source in chain([main_source], other_sources):
            line_vals = self._prepare_purchase_order_line(cr, uid, po_id,
                                                          source, supplier,
                                                          pricelist,
                                                          context=context)
            po_l_obj.create(cr, uid, line_vals, context=context)
            # TODO: Update LRS unit_cost from po line, with currency conversion
            from_curr = source.requisition_id.currency_id.id
            # Compute from bid currency to LRS currency
            price = currency_obj.compute(cr, uid, from_curr, to_curr,
                                         line_vals['price_unit'], False)
            source.write(
                {'framework_agreement_po_id': po_id, 'unit_cost': price})
        return po_id

    def make_purchase_order(self, cr, uid, ids, pricelist, context=None):
        """Create a purchase order from the LRS ids list. This method will
        create one PO with all lines. Between them, you'll have line of type
        LTA (framewrok agreement) and line of type other.
        Currently, only one line of type LTA is accepted at a time.

        We'll raise an error if other types are selected here.
        We accept line of type other here to include products not included
        in the LTA for example : you order Product A under LTA + the transport
        as a LRS of type other.

        :param integer list ids: ids of logistic.requisition.source
        :param browse_record pricelist: product.pricelist
        :returns integer : generated PO id

        """
        sources = self.browse(cr, uid, ids, context=context)
        # LRS of type LTA (framework agreement)
        agreement_sources = []
        # LRS of type other
        other_sources = []
        for source in sources:
            if source.sourcing_method == 'fw_agreement':
                agreement_sources.append(source)
            elif source.sourcing_method == 'other':
                other_sources.append(source)
            else:
                raise orm.except_orm(
                    _('Source line must be of type other or agreement'),
                    _('Please correct selection'))

        main_source = agreement_sources[0] if agreement_sources else False
        if len(agreement_sources) > 1:
            raise orm.except_orm(_('There should be only one agreement line'),
                                 _('Please correct selection'))
        if not main_source:
            raise orm.except_orm(
                _('There should be at least one agreement line'),
                _('Please correct selection'))

        supplier = main_source.framework_agreement_id.supplier_id
        fback = supplier.property_product_pricelist_purchase
        pricelist = pricelist if pricelist else fback
        po_id = self._make_po_from_source_lines(
            cr, uid, main_source, other_sources, pricelist, context=None)
        return po_id

    @api.multi
    def _check_sourcing_fw_agreement(self):
        """Check sourcing for "fw_agreement" method.

        Check if assigned Framework Agreement is running and if it has enough
        remaining quantity

        :returns: list of error strings

        """
        if self.framework_agreement_po_id:
            return []
        agreement = self.framework_agreement_id
        if not agreement:
            return ['{0}: No Framework Agreement associated with this '
                    'source'.format(self.name)]
        if agreement.state != 'running':
            return ['{0}: Selected Framework Agreement is {1} for this source,'
                    ' it must be Running'.format(self.name, agreement.state)]
        if agreement.available_quantity < self.proposed_qty:
            return ['{0}: Selected Framework Agreement available quantity is '
                    'only {1} and this source proposed quantity is {2}. You '
                    'need to:'
                    '\n * Reduce proposed quantity of this source'
                    '\n * Fill remaining quantity with aditional(s) source(s)'
                    .format(self.name, agreement.available_quantity,
                            self.proposed_qty)]
        return []

    # ---------------Odoo onchange management ----------------------

    @api.model
    def _get_date(self):
        """helper to retrive date to be used by framework agreement
        when in source line context

        :param requisition_line_id: requisition.line id that should
            provide date

        :returns: date/datetime string

        """
        now = fields.datetime.now()
        return self.requisition_id.date or now

    @api.multi
    def _check_enought_qty(self, agreement):
        """ Raise a warning if quantity is not enough
        to fullfil completely the sourcing

        :returns: dict with warning message

        """
        if self.proposed_qty > agreement.available_quantity:
            msg = _("You have asked for a quantity of %s \n"
                    " but there is only %s available"
                    " for current agreement") % (self.proposed_qty,
                                                 agreement.available_quantity)

            return {'warning': {'message': msg}}

    @api.onchange('sourcing_method', 'portfolio_id', 'proposed_qty',
                  'proposed_product_id')
    def update_agreement(self):
        """Update the choice of agreement depending on other fields.

        Like in the purchase order with framework_agreement 2.0, we do not
        choose automatically the cheapest agreement, except when there is only
        one that is suitable.

        If the current choice is suitable, keep it.

        """
        if (self.sourcing_method != 'fw_agreement' or
                not self.proposed_product_id):
            self.framework_agreement_id = False
            return
        Agreement = self.env['framework.agreement']
        ag_domain = Agreement.get_agreement_domain(
            self.proposed_product_id.id,
            self.proposed_qty,
            self.portfolio_id.id,
            self.requisition_id.date,
            self.requisition_id.incoterm_id.id,
            self.requisition_id.incoterm_address,
        )

        good_agreements = Agreement.search(ag_domain)
        if self.framework_agreement_id in good_agreements:
            agreement = self.framework_agreement_id
        else:
            if len(good_agreements) == 1:
                agreement = good_agreements
            else:
                agreement = Agreement

        if agreement:
            self.unit_cost = agreement.get_price(self.proposed_qty,
                                                 self.currency_id)
        else:
            self.unit_cost = 0.0

        self.framework_agreement_id = agreement.id

        self.total_cost = self.unit_cost * self.proposed_qty
        self.price_is = 'fixed'
        self._check_enought_qty(agreement)

        return {'domain': {'framework_agreement_id': ag_domain}}
