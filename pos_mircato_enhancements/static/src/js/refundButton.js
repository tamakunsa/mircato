/** @odoo-module */

import { RefundButton } from "@point_of_sale/app/screens/product_screen/control_buttons/refund_button/refund_button";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { patch } from "@web/core/utils/patch";

patch(RefundButton.prototype, {
    click() {
        // employee cannot open refund orders unless the employee has the access rights
        if (!this.pos.get_cashier().allow_refund){
            this.pos.env.services.popup.add(ErrorPopup, {
                'title':"Access Right Error",
                'body':  "Employee must have 'allow refund' access right",
            });
            return;
        }
        super.click();

    }
});
