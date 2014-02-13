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
from itertools import chain
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.addons.framework_agreement.model.framework_agreement import\
    FrameworkAgreementObservable
from openerp.addons.framework_agreement.utils import id_boilerplate


AGR_PROC = 'fw_agreement'


class logistic_requisition_source(orm.Model, FrameworkAgreementObservable):
    """Adds support of framework agreement to source line"""

    _inherit = "logistic.requisition.source"

    _columns = {'framework_agreement_id': fields.many2one('framework.agreement',
                                                          'Agreement'),
                'framework_agreement_po_id': fields.many2one('purchase.order',
                                                             'Agreement Purchase'),
                'supplier_id': fields.related('framework_agreement_id', 'supplier_id',
                                              type='many2one',  relation='res.partner',
                                              string='Agreement Supplier')}

    def _get_procur_method_hook(self, cr, uid, context=None):
        """Adds framework agreement as a procurement method in selection field"""
        res = super(logistic_requisition_source, self)._get_procur_method_hook(cr, uid,
                                                                               context=context)
        res.append((AGR_PROC, 'Framework agreement'))
        return res

    def _get_purchase_line_id(self, cr, uid, ids, field_name, arg, context=None):
        """For each source line, get the related purchase order line

        For more detail please refer to function fields documentation

        """
        po_line_model = self.pool['purchase.order.line']
        res = super(logistic_requisition_source, self)._get_purchase_line_id(cr, uid, ids,
                                                                             field_name,
                                                                             arg,
                                                                             context=context)
        for line in self.browse(cr, uid, ids, context=context):
            if line.procurement_method == AGR_PROC:
                po_l_ids = po_line_model.search(cr, uid,
                                                [('lr_source_line_id', '=', line.id),
                                                 ('state', '!=', 'cancel')],
                                                context=context)
                if po_l_ids:
                    if len(po_l_ids) > 1:
                        raise orm.except_orm(_('Many Purchase order lines found for %s') % line.name,
                                             _('Please cancel uneeded one'))
                    res[line.id] = po_l_ids[0]
                else:
                    res[line.id] = False
        return res

    #------------------ adapting source line to po -----------------------------
    def _company(self, cr, uid, context):
        """Return company id

        :returns: company id

        """
        return self.pool['res.company']._company_default_get(cr, uid, self._name,
                                                             context=context)

    def _prepare_purchase_order(self, cr, uid, line, po_pricelist, context=None):
        """Prepare the dict of values to create the PO from a
           source line.

        :param browse_record line: logistic.requisition.source
        :param browse_record pricelist: product.pricelist
        :returns: data dict to be used by orm.Model.create

        """
        supplier = line.framework_agreement_id.supplier_id
        add = line.requisition_id.consignee_shipping_id
        term = supplier.property_supplier_payment_term
        term = term.id if term else False
        position = supplier.property_account_position
        position = position.id if position else False
        requisition = line.requisition_id
        data = {}
        data['framework_agreement_id'] = line.framework_agreement_id.id
        data['partner_id'] = supplier.id
        data['company_id'] = self._company(cr, uid, context)
        data['pricelist_id'] = po_pricelist.id
        data['dest_address_id'] = add.id
        data['location_id'] = add.property_stock_customer.id
        data['payment_term_id'] = term
        data['fiscal_position'] = position
        data['origin'] = requisition.name
        data['date_order'] = requisition.date
        # data['name'] = requisition.name
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
            price = line.framework_agreement_id.get_price(line.proposed_qty, currency=currency)
            lead_time = line.framework_agreement_id.delay
            supplier = line.framework_agreement_id.supplier_id
            data['framework_agreement_id'] = line.framework_agreement_id.id
        else:
            supplier = po_supplier
            lead_time = 0
            price = 0.0
            if po_pricelist:
                price = pl_model.price_get(cr, uid,
                                           [po_pricelist.id],
                                           line.proposed_product_id.id,
                                           line.proposed_qty or 1.0,
                                           po_supplier.id,
                                           {'uom': line.proposed_uom_id.id})[po_pricelist.id]

        if not price:
            price = line.proposed_product_id.standard_price or 1.00
        taxes_ids = line.proposed_product_id.supplier_taxes_id
        taxes = acc_pos_obj.map_tax(cr, uid, supplier.property_account_position,
                                    taxes_ids)

        data['order_id'] = po_id
        data['product_qty'] = line.proposed_qty
        data['product_id'] = line.proposed_product_id.id
        data['product_uom'] = line.proposed_uom_id.id
        data['lr_source_line_id']= line.id
        data['product_lead_time'] = lead_time
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
                                                    pricelist, context=context)
            po_l_obj.create(cr, uid, line_vals, context=context)
            # TODO: Update LRS unit_cost from po line, with currency conversion
            from_curr = source.requisition_id.currency_id.id
            # Compute from bid currency to LRS currency
            price = currency_obj.compute(cr, uid, from_curr, to_curr,
                    line_vals['price_unit'], False)
            source.write({'framework_agreement_po_id': po_id, 'unit_cost':price})
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
        other_sources =  []
        for source in sources:
            if source.procurement_method == AGR_PROC:
                agreement_sources.append(source)
            elif source.procurement_method == 'other':
                other_sources.append(source)
            else:
                raise orm.except_orm(_('Source line must be of type other or agreement'),
                                     _('Please correct selection'))

        main_source = agreement_sources[0] if agreement_sources else False
        if len(agreement_sources) > 1:
            raise orm.except_orm(_('There should be only one agreement line'),
                                 _('Please correct selection'))
        if not main_source:
            raise orm.except_orm(_('There should be at least one agreement line'),
                                 _('Please correct selection'))
        fback = main_source.framework_agreement_id.supplier_id.property_product_pricelist_purchase
        pricelist = pricelist if pricelist else fback
        po_id = self._make_po_from_source_lines(cr, uid, main_source,
                                                other_sources, pricelist, context=None)
        return po_id

    def _is_sourced_other(self, cr, uid, source, context=None):
        """Predicate function to test if line on other
        method are sourced"""
        tender_ok = self._is_sourced_procurement(cr, uid, source,
                                                 context=context)
        agr_ok = self._is_sourced_fw_agreement(cr, uid, source,
                                                 context=context)
        return (tender_ok or agr_ok)

    def _is_sourced_fw_agreement(self, cr, uid, source, context=None):
        """Predicate that tells if source line of type agreement are sourced

        :retuns: boolean True if sourced

        """
        po_line_obj = self.pool['purchase.order.line']
        sources_ids = po_line_obj.search(cr, uid,
                                         [('lr_source_line_id', '=', source.id)],
                                         context=context)
        # predicate
        return bool(sources_ids)

    #---------------OpenERP tedious onchange management ------------------------

    def _get_date(self, cr, uid, requision_line_id, context=None):
        """helper to retrive date to be used by framework agreement
        when in source line context

        :param source_id: requisition.line.source id that should
            provide date

        :returns: date/datetime string

        """
        req_obj = self.pool['logistic.requisition.line']
        current = req_obj.browse(cr, uid, requision_line_id, context=context)
        now = fields.datetime.now()
        return current.requisition_id.date or now

    @id_boilerplate
    def onchange_sourcing_method(self, cr, uid, ids, method, req_line_id, proposed_product_id,
                                 proposed_qty=0, context=None):
        """
        Called when source method is set on a source line.

        If sourcing method is framework agreement
        it will set price, agreement and supplier if possible
        and raise quantity warning.

        """
        line_source = self.browse(cr, uid, ids, context=context)
        res = {'value': {'framework_agreement_id': False}}
        if (method != AGR_PROC or not proposed_product_id):
            return res
        currency = line_source.currency_id
        agreement_obj = self.pool['framework.agreement']
        date = self._get_date(cr, uid, req_line_id, context=context)
        agreement, enough_qty = agreement_obj.get_cheapest_agreement_for_qty(cr, uid,
                                                                             proposed_product_id,
                                                                             date,
                                                                             proposed_qty,
                                                                             currency=currency,
                                                                             context=context)
        if not agreement:
            return res
        price = agreement.get_price(proposed_qty, currency=currency)
        res['value'] = {'framework_agreement_id': agreement.id,
                        'unit_cost': price,
                        'total_cost': price * proposed_qty,
                        'supplier_id': agreement.supplier_id.id}
        if not enough_qty:
            msg = _("You have ask for a quantity of %s \n"
                    " but there is only %s available"
                    " for current agreement") % (proposed_qty,
                                                 agreement.available_quantity)
            res['warning'] = msg
        return res

    @id_boilerplate
    def onchange_quantity(self, cr, uid, ids, method, req_line_id, qty,
                          proposed_product_id, context=None):
        """Raise a warning if agreed qty is not sufficient"""
        line_source = self.browse(cr, uid, ids, context=context)
        if (method != AGR_PROC or not proposed_product_id):
            return {}
        currency = line_source.currency_id
        date = self._get_date(cr, uid, req_line_id, context=context)
        return self.onchange_quantity_obs(cr, uid, ids, qty, date,
                                          proposed_product_id,
                                          currency=currency,
                                          price_field='dummy',
                                          context=context)

    @id_boilerplate
    def onchange_product_id(self, cr, uid, ids, method, req_line_id,
                            proposed_product_id, proposed_qty,
                            context=None):
        """Call when product is set on a source line.

        If sourcing method is framework agreement
        it will set price, agreement and supplier if possible
        and raise quantity warning.

        """
        if method != AGR_PROC:
            if proposed_product_id:
                value = {'proposed_uom_id': ''}
                if proposed_product_id:
                    prod_obj = self.pool.get('product.product')
                    prod = prod_obj.browse(cr, uid, proposed_product_id, context=context)
                    value = {
                        'proposed_uom_id': prod.uom_id.id,
                    }
                return {'value': value}
            return {}

        return self.onchange_sourcing_method(cr, uid, ids, method, req_line_id,
                                             proposed_product_id,
                                             proposed_qty=proposed_qty,
                                             context=context)

    @id_boilerplate
    def onchange_agreement(self, cr, uid, ids, agreement_id, req_line_id, qty,
                           proposed_product_id, context=None):
        line_source = self.browse(cr, uid, ids, context=context)
        if not proposed_product_id or not agreement_id:
            return {}
        currency = line_source.currency_id
        date = self._get_date(cr, uid, req_line_id, context=context)
        return self.onchange_agreement_obs(cr, uid, ids, agreement_id, qty,
                                           date, proposed_product_id,
                                           currency=currency, price_field='dummy')
