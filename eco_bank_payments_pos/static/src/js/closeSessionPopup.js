/** @odoo-module */

import { ClosePosPopup } from "@point_of_sale/app/navbar/closing_popup/closing_popup";
import { patch } from "@web/core/utils/patch";
patch(ClosePosPopup.prototype, {
    async closeSession() {

        const all_payment_bank = this.props.other_payment_methods.filter((pm) => pm.type == "bank")

        const response = await this.orm.call(
            "pos.session",
            "save_bank_payments",
            [this.pos.pos_session.id],
            {
                payment_methods: all_payment_bank
            }
        );

        
        const result = super.closeSession()
        return result;
    }
})