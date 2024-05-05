/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {

	openCashControl() {
		// make the function empty so the cash controll popup never opened
	}
})


