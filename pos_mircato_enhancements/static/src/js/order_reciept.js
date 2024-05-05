/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Order } from "@point_of_sale/app/store/models";

patch(Order.prototype, {
    export_for_printing() {
        // add total quantity in pos order reciept
         var orders = super.export_for_printing(...arguments);
         var total_qty = 0
         for (let i = 0; i < orders['orderlines'].length; i++) {
            total_qty += parseFloat(orders['orderlines'][i].qty)
        }
        orders['total_qty'] = total_qty
        return orders;
     }
 });
 