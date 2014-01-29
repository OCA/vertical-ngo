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

    def _map_source_to_po(self, cr, uid, line, po_pricelist, context=None):
        """Map source line to dict to be used by PO create defaults are optional

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

    def _map_source_to_po_line(self, cr, uid, po_id, line,
                               po_supplier, po_pricelist, context=None):
        """Map source line to dict to be used by PO line create
        Map source line to dict to be used by PO create
        defaults are optional

        :returns: data dict to be used by orm.Model.create

        """
        acc_pos_obj = self.pool['account.fiscal.position']
        pl_model = self.pool['product.pricelist']

        if line.framework_agreement_id:
            # currency = line.currency_id Joel TOFIX
            # price = line.framework_agreement_id.get_price(line.proposed_qty, currency=currency)
            # Joel to fix
            price = 9999.00
            lead_time = line.framework_agreement_id.delay
            supplier = line.framework_agreement_id.supplier_id
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
        data = {}
        data['order_id'] = po_id
        data['product_qty'] = line.proposed_qty
        data['product_id'] = line.proposed_product_id.id
        data['product_uom'] = line.proposed_uom_id.id
        data['lr_source_line_id']= line.id,
        data['product_lead_time'] = lead_time
        data['price_unit'] = price
        data['name'] = line.proposed_product_id.name
        data['date_planned'] = line.requisition_id.date_delivery
        data['taxes_id'] = [(6, 0, taxes)]
        return data

    def _make_po_from_source_lines(self, cr, uid, main_source, other_sources,
                                   pricelist, context=None):
        """adapt a source line to purchase order

        :returns: generated PO id

        """
        if context is None:
            context = {}
        context['draft_po'] = True
        po_obj = self.pool['purchase.order']
        po_l_obj = self.pool['purchase.order.line']

        supplier = main_source.framework_agreement_id.supplier_id
        po_vals = self._map_source_to_po(cr, uid, main_source,
                                         pricelist, context=context)
        po_id = po_obj.create(cr, uid, po_vals, context=context)
        other_sources = other_sources if other_sources else []
        for source in chain([main_source], other_sources):
            line_vals = self._map_source_to_po_line(cr, uid, po_id,
                                                    source, supplier,
                                                    pricelist, context=context)

            po_l_obj.create(cr, uid, line_vals, context=context)
        return po_id

    def make_purchase_order(self, cr, uid, ids, pricelist, context=None):
        """ adapt each source line to purchase order

        :returns: generated PO ids

        """
        po_ids = []
        sources = self.browse(cr, uid, ids, context=context)
        agreement_sources = []
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
        po_ids.append(po_id)
        return po_ids

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

    def get_agreement_price_from_po(self, cr, uid, source_id, context=None):
        """Get price from PO.

        The price is retreived on the po line generated by sourced line.

        :returns: price in float
        """
        if isinstance(source_id, (list, tuple)):
            assert len(source_id) == 1
            source_id = source_id[0]
        po_l_obj = self.pool['purchase.order.line']
        currency_obj = self.pool['res.currency']
        current = self.browse(cr, uid, source_id, context=context)
        agreement = current.framework_agreement_id

        if not agreement:
            raise ValueError('No framework agreement on source line %s' %
                             current.name)
        line_ids = po_l_obj.search(cr, uid,
                                   [('order_id.framework_agreement_id', '=', agreement.id),
                                    ('lr_source_line_id', '=', current.id),
                                    ('order_id.partner_id', '=', agreement.supplier_id.id)],
                                   context=context)
        price = 0.0
        lines = po_l_obj.browse(cr, uid, line_ids, context=context)
        if lines:
            price = sum(x.price_subtotal for x in lines) # To avoid rounding problems
            from_curr = lines[0].order_id.pricelist_id.currency_id.id
            to_curr = current.requisition_id.currency_id.id
            price = currency_obj.compute(cr, uid, from_curr, to_curr, price, False)
        return price

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
        return self.onchange_quantity_obs(cr, uid, source_id, qty, date,
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
        if (method != AGR_PROC or not proposed_product_id):
            return {}

        return self.onchange_sourcing_method(cr, uid, source_id, method, req_line_id,
                                             proposed_product_id,
                                             proposed_qty=proposed_qty,
                                             context=context)

    @id_boilerplate
    def onchange_agreement(self, cr, uid, ids, agreement_id, req_line_id, qty,
                           proposed_product_id, context=None):
        line_source = self.browse(cr, uid, ids, context=context)
        if not proposed_product_id or not pricelist_id or not agreement_id:
            return {}
        currency = line_source.currency_id
        date = self._get_date(cr, uid, req_line_id, context=context)
        return self.onchange_agreement_obs(cr, uid, source_id, agreement_id, qty,
                                           date, proposed_product_id,
                                           currency=currency, price_field='dummy')


class logistic_requisition_source_po_creator(orm.TransientModel):

    _name = 'logistic.requisition.source.create.agr.po'

    def action_create_agreement_po_requisition(self, cr, uid, ids, context=None):
        """ Implement buttons that create PO from selected source lines"""
        # We force empty context
        lr_model = self.pool['logistic.requisition.source']
        act_obj = self.pool['ir.actions.act_window']
        source_ids = context['active_ids']
        pricelist = None # place holder for Joel pl browse record
        po_ids = lr_model.make_purchase_order(cr, uid, source_ids,
                                              pricelist, context=context)
        # TODO : update LRS price from PO depending on the chosen currency
        res = act_obj.for_xml_id(cr, uid,
                                 'purchase', 'purchase_rfq', context=context)
        res.update({'domain': [('id', 'in', po_ids)],
                    'res_id': False,
                    'context': '{}',
                    })
        return res
