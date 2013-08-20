<html>
<head>
    <style type="text/css">
        ${css}

.list_sale_table {
    border:thin solid #E3E4EA;
    text-align:center;
    border-collapse: collapse;
}
.list_sale_table th {
    background-color: #EEEEEE;
    border: thin solid #000000;
    text-align:center;
    font-size:12;
    font-weight:bold;
    padding-right:3px;
    padding-left:3px;
}
.list_sale_table td {
    border-top: thin solid #EEEEEE;
    text-align:left;
    font-size:12;
    padding-right:3px;
    padding-left:3px;
    padding-top:3px;
    padding-bottom:3px;
}
.list_sale_table thead {
    display:table-header-group;
}

td.formatted_note {
    text-align:left;
    border-right:thin solid #EEEEEE;
    border-left:thin solid #EEEEEE;
    border-top:thin solid #EEEEEE;
    padding-left:10px;
    font-size:11;
}



.no_bloc {
    border-top: thin solid  #ffffff ;
}

.right_table {
    right: 4cm;
    width:"100%";
}

.std_text {
    font-size:12;
}

tfoot.totals tr:first-child td{
    padding-top: 15px;
}


td.amount, th.amount {
    text-align: right;
    white-space: nowrap;
}


.address .recipient .shipping .invoice {
    font-size: 12px;
}

    </style>
</head>
<body>
    <%page expression_filter="entity"/>
    <%
    def carriage_returns(text):
        return text.replace('\n', '<br />')

    %>
    %for order in objects:
    <% setLang(order.partner_id.lang) %>
    <%
      l_order = order.state in ['progress', 'manual', 'done']
    %>
    <div class="address">
        <table class="recipient">
            %if order.partner_id.parent_id:
            <tr><td class="name">${order.partner_id.parent_id.name or ''}</td></tr>
            <tr><td>${order.partner_id.title and order.partner_id.title.name or ''} ${order.partner_id.name }</td></tr>
            <% address_lines = order.partner_id.contact_address.split("\n")[1:] %>
            %else:
            <tr><td class="name">${order.partner_id.title and order.partner_id.title.name or ''} ${order.partner_id.name }</td></tr>
            <% address_lines = order.partner_id.contact_address.split("\n") %>
            %endif
            %for part in address_lines:
                %if part:
                <tr><td>${part}</td></tr>
                %endif
            %endfor
        </table>

        <table class="shipping">
            <tr><td class="address_title">${_("Shipping address:")}</td></tr>
            %if order.partner_shipping_id.parent_id:
            <tr><td>${order.partner_shipping_id.parent_id.name or ''}</td></tr>
            <tr><td>${order.partner_shipping_id.title and order.partner_shipping_id.title.name or ''} ${order.partner_shipping_id.name }</td></tr>
            <% address_lines = order.partner_shipping_id.contact_address.split("\n")[1:] %>
            %else:
            <tr><td>${order.partner_shipping_id.title and order.partner_shipping_id.title.name or ''} ${order.partner_shipping_id.name }</td></tr>
            <% address_lines = order.partner_shipping_id.contact_address.split("\n") %>
            %endif
            %for part in address_lines:
                %if part:
                <tr><td>${part}</td></tr>
                %endif
            %endfor
        </table>

        <table class="invoice">
            <tr><td class="address_title">${_("Consignee address:")}</td></tr>
            %if order.consignee_id.parent_id:
            <tr><td>${order.consignee_id.parent_id.name or ''}</td></tr>
            <tr><td>${order.consignee_id.title and order.consignee_id.title.name or ''} ${order.consignee_id.name }</td></tr>
            <% address_lines = order.consignee_id.contact_address.split("\n")[1:] %>
            %else:
            <tr><td>${order.consignee_id.title and order.consignee_id.title.name or ''} ${order.consignee_id.name }</td></tr>
            <% address_lines = order.consignee_id.contact_address.split("\n") %>
            %endif
            %for part in address_lines:
                %if part:
                <tr><td>${part}</td></tr>
                %endif
            %endfor
        </table>
    </div>

    % if l_order:
    <h1 style="clear:both;">${_('Logistic order')} ${order.name}</h1>
    % else:
    <h1 style="clear:both;">${_('Cost estimate')} ${order.name}</h1>
    %endif
    <table class="basic_table" width="100%">
        <tr>
            <td style="font-weight:bold;">${l_order and _("Order Date") or _("Date")}</td>
            <td style="font-weight:bold;width:30%">${_("Your Reference")}</td>
            <td style="font-weight:bold;">${_("Validity")}</td>
        </tr>
        <tr>
            <td>${formatLang(order.date_order, date=True)}</td>
            <td>${order.client_order_ref or ''}</td>
            %if order.date_validity.val:
            <td>${_('The pricing indications in this estimate are valid till:')}<br/>
                ${formatLang(order.date_validity, date=True)}</td>
            %else:
               <td></td>
            %endif
        </tr>
    </table>

    <div>
    %if order.note1:
        <p class="std_text"> ${order.note1| n} </p>
    %endif
    </div>

    <table class="list_sale_table" width="100%" style="margin-top: 20px;">
        <thead>
            <tr>
                <th>${_("Description")}</th>
                <th class="amount">${_("Quantity")}</th>
                <th class="amount">${_("UoM")}</th>
                <th class="amount">${_("Unit Price")}</th>
                <th>${_("VAT")}</th>
                <th class="amount">${_("Disc.(%)")}</th>
                <th class="amount">${_("Price")}</th>
            </tr>
        </thead>
        <tbody>
        %for line in order.order_line:
            <tr class="line">
                <td style="text-align:left; " >${ line.name }</td>
                <td class="amount" width="7.5%">${ formatLang(line.product_uos and line.product_uos_qty or line.product_uom_qty) }</td>
                <td style="text-align:center;">${ line.product_uos and line.product_uos.name or line.product_uom.name }</td>
                <td class="amount" width="8%">${formatLang(line.price_unit)}</td>
                <td style="font-style:italic; font-size: 10;">${ ', '.join([tax.description or tax.name for tax in line.tax_id]) }</td>
                <td class="amount" width="10%">${line.discount and formatLang(line.discount, digits=get_digits(dp='Sale Price')) or ''} ${line.discount and '%' or ''}</td>
                <td class="amount" width="13%">${formatLang(line.price_subtotal, digits=get_digits(dp='Sale Price'))}&nbsp;${order.pricelist_id.currency_id.symbol}</td>
            </tr>
            %if line.formatted_note:
            <tr>
              <td class="formatted_note" colspan="7">
                ${line.formatted_note| n}
              </td>
            </tr>
            %endif
        %endfor
        </tbody>
        <tfoot class="totals">
            <tr>
                <td colspan="5" style="border-style:none"/>
                <td style="border-style:none"><b>${_("Net Total:")}</b></td>
                <td class="amount" style="border-style:none">${formatLang(order.amount_untaxed, get_digits(dp='Sale Price'))} ${order.pricelist_id.currency_id.symbol}</td>
            </tr>
            <tr>
                <td colspan="5" style="border-style:none"/>
                <td style="border-style:none" ><b>${_("Taxes:")}</b></td>
                <td class="amount"style="border-style:none" >${formatLang(order.amount_tax, get_digits(dp='Sale Price'))} ${order.pricelist_id.currency_id.symbol}</td>
            </tr>
            <tr>
                <td colspan="5" style="border-style:none"/>
                <td style="border-style:none"><b>${_("Total:")}</b></td>
                <td class="amount" style="border-style:none">${formatLang(order.amount_total, get_digits(dp='Sale Price'))} ${order.pricelist_id.currency_id.symbol}</td>
            </tr>
        </tfoot>
    </table>
    <br/>
    <br/>
    <table class="basic_table" width="100%">
        <tr>
            <td style="font-weight:bold;">${_("Delivery time")}</td>
            <td style="font-weight:bold;">${_("Payment term")}</td>
            <td style="font-weight:bold;">${_("Incoterm/Incoterm Place")}</td>
        </tr>
        <tr>
            <td>${_('Item subjet to supplier availability.')}<br/>
                ${_('Transit Time')} ${order.delivery_time or _('N/A')| carriage_returns}</td>
            <td>${order.payment_term and order.payment_term.note or ''}</td>
            %if order.incoterm or order.incoterm_address:
              <td>${order.incoterm.name if order.incoterm else ''} ${order.incoterm_address or ''} INCOTERMS 2010</td>
            %else:
              <td></td>
            %endif
        </tr>
    </table>
    %if order.note :
        <p class="std_text">${order.note | carriage_returns}</p>
    %endif
    %if order.note2:
        <p class="std_text">${order.note2 | n}</p>
    %endif

    <p style="page-break-after: always"/>
    <br/>
    %endfor
</body>
</html>
