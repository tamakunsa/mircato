/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PartnerDetailsEdit } from "@point_of_sale/app/screens/partner_list/partner_editor/partner_editor";
import { useEffect, useRef } from "@odoo/owl";

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