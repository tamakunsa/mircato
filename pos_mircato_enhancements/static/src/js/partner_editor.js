/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PartnerDetailsEdit } from "@point_of_sale/app/screens/partner_list/partner_editor/partner_editor";
import { useEffect, useRef } from "@odoo/owl";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";

// pos order inherit
patch(PartnerDetailsEdit.prototype, {
    setup(){
        this.phoneInput = useRef("Phone");
        useEffect(
            () => {
                if(!this.changes.phone){
                    console.log(this.phoneInput)
                    this.phoneInput.el.value='+966'
                }
            }
        )
        super.setup()
    },
})

patch(PaymentScreen.prototype, {

    async validateOrder(isForceValidate) {
        if(!this.currentOrder.get_partner()){
            this.popup.add(ErrorPopup, {
                title: "You Must Select A customer",
                body: "the customer is mandatory to be selected",
            });
            return false;
        }

        await super.validateOrder(arguments);
    },

})


// this.currentOrder.get_partner()