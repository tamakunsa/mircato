/** @odoo-module **/

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

// pos order inherit
patch(Order.prototype, {
   export_for_printing() {
        var orders = super.export_for_printing(...arguments);
        var canvas = document.createElement('canvas');
        JsBarcode(canvas, orders['name']);
        console.log('ooooooooooooooooo',orders['name'])
        orders['barcode'] = canvas.toDataURL("image/png");
        return orders;
    }
});
