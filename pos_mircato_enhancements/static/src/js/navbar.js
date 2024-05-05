/** @odoo-module */

import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { ClosePosPopup } from "@point_of_sale/app/navbar/closing_popup/closing_popup";

patch(Navbar.prototype, {
    async closeSession() {
        const info = await this.pos.getClosePosInfo();
        console.log('info')
        // console.log(info)
        // console.log(info.other_payment_methods)
        for (var pm_info of info.other_payment_methods){
            console.log("pm_info")
            console.log(pm_info)
            pm_info.amount = 0
        }
        console.log("after")
        this.popup.add(ClosePosPopup, { ...info, keepBehind: true });
    }

})
