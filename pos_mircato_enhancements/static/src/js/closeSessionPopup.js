/** @odoo-module */

import { ClosePosPopup } from "@point_of_sale/app/navbar/closing_popup/closing_popup";
import { patch } from "@web/core/utils/patch";
patch(ClosePosPopup.prototype, {
    async closeSession() {
        const result = super.closeSession()
        await this.downloadSalesReport()
        return result;
    }
})