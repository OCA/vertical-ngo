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
    %for requisition in objects:
    <% setLang(requisition.partner_id.lang) %>

    <div class="address">
        <table class="recipient">
            %if requisition.partner_id.parent_id:
            <tr><td class="name">${requisition.partner_id.parent_id.name or ''}</td></tr>
            <tr><td>${requisition.partner_id.title.name if requisition.partner_id.title else ''} ${requisition.partner_id.name }</td></tr>
            <% address_lines = requisition.partner_id.contact_address.split("\n")[1:] %>
            %else:
            <tr><td class="name">${requisition.partner_id.title.name if requisition.partner_id.title else ''} ${requisition.partner_id.name }</td></tr>
            <% address_lines = requisition.partner_id.contact_address.split("\n") %>
            %endif
            %for part in address_lines:
                %if part:
                <tr><td>${part}</td></tr>
                %endif
            %endfor
        </table>

        <table class="shipping">
            <tr><td class="address_title">${_("Shipping address:")}</td></tr>
            %if requisition.consignee_shipping_id.parent_id:
            <tr><td>${requisition.consignee_shipping_id.parent_id.name or ''}</td></tr>
            <tr><td>${requisition.consignee_shipping_id.title.name if requisition.consignee_shipping_id.title else ''} ${requisition.consignee_shipping_id.name }</td></tr>
            <% address_lines = requisition.consignee_shipping_id.contact_address.split("\n")[1:] %>
            %else:
            <tr><td>${requisition.consignee_shipping_id.title and requisition.consignee_shipping_id.title.name or ''} ${requisition.consignee_shipping_id.name }</td></tr>
            <% address_lines = requisition.consignee_shipping_id.contact_address.split("\n") %>
            %endif
            %for part in address_lines:
                %if part:
                <tr><td>${part}</td></tr>
                %endif
            %endfor
        </table>

        <table class="invoice">
            <tr><td class="address_title">${_("Consignee address:")}</td></tr>
            %if requisition.consignee_id.parent_id:
            <tr><td>${requisition.consignee_id.parent_id.name or ''}</td></tr>
            <tr><td>${requisition.consignee_id.title.name if requisition.consignee_id.title else ''} ${requisition.consignee_id.name }</td></tr>
            <% address_lines = requisition.consignee_id.contact_address.split("\n")[1:] %>
            %else:
            <tr><td>${requisition.consignee_id.title.name if requisition.consignee_id.title else ''} ${requisition.consignee_id.name }</td></tr>
            <% address_lines = requisition.consignee_id.contact_address.split("\n") %>
            %endif
            %for part in address_lines:
                %if part:
                <tr><td>${part}</td></tr>
                %endif
            %endfor
        </table>
    </div>

    <h1 style="clear:both;">${_('Logistic requisition')} ${requisition.name}</h1>
    <table class="basic_table" width="100%">
        <tr>
            <td style="font-weight:bold;">${_("Desired delivery date")}</td>
            <td style="font-weight:bold;">${_("Preferred transport")}</td>
            <td style="font-weight:bold;">${_("Cost estimate only")}</td>
            <td style="font-weight:bold;">${_("Project")}</td>
            <td style="font-weight:bold;">${_("Country")}</td>
            <td style="font-weight:bold;">${_("Requisition Date")}</td>
        </tr>
        <tr>
            <td>${formatLang(requisition.date_delivery, date=True)}</td>
            <td>${requisition.preferred_transport.name if requisition.preferred_transport else ''}</td>
            <td>${_("Yes") if requisition.cost_estimate_only else _("No")}</td>
            <td>${requisition.analytic_id.name if requisition.analytic_id else ''}</td>
            <td>${requisition.country_id.name}</td>
            <td>${formatLang(requisition.date, date=True)}</td>
        </tr>
    </table>
    <br/>

    <table class="list_sale_table" width="100%" style="margin-top: 20px;">
        <thead>
            <tr>
                <th>${_("Number")}</th>
                <th>${_("Description")}</th>
                <th class="amount">${_("Quantity")}</th>
                <th class="amount">${_("UoM")}</th>
            </tr>
        </thead>
        <tbody>
        %for line in requisition.line_ids:
            <tr class="line">
                <td style="text-align:left; " >${line.name}</td>
                <td style="text-align:left; " >${(line.product_id.code or '') if line.product_id else ''} ${line.product_id.name if line.product_id else ''}</td>

                <td class="amount" width="15%">${formatLang(line.requested_qty)}</td>
                <td style="text-align:center;">${line.requested_uom_id.category_id.name}</td>
        %endfor
        </tbody>
    </table>
    %if requisition.shipping_note :
    <p><b>${_('Delivery Remarks')}</b></p>
        <p class="std_text">${requisition.note | carriage_returns}</p>
    %endif
    %if requisition.note :
    <p><b>${_("General Remarks")}</b></p>
        <p class="std_text">${requisition.note | carriage_returns}</p>
    %endif
    <br/>
    <br/>
    <p><b>${_("Approval")}</b></p>
    <table class="basic_table" width="100%">
        <tr>
            <td style="font-weight:bold;width:40%">${_("Requesting entity")}</td>
            <td style="font-weight:bold;width:30%">${_("Requested date")}</td>
            <td style="font-weight:bold;">${_("Signature")}</td>
        </tr>
        <tr>
            <td>${requisition.partner_id.name}</td>
            <td>${requisition.date or 'N/A'}</td>
            <td>&nbsp;</td>
        </tr>
    </table>
    <p style="page-break-after: always"/>
    %endfor
</body>
</html>
