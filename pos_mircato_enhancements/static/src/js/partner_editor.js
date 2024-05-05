/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";

import { patch } from "@web/core/utils/patch";
import { PartnerDetailsEdit } from "@point_of_sale/app/screens/partner_list/partner_editor/partner_editor";
import { useEffect, useRef } from "@odoo/owl";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { useService } from "@web/core/utils/hooks";

// pos order inherit
patch(PartnerDetailsEdit.prototype, {
    setup(){
        this.phoneInput = useRef("Phone");
        this.orm = useService("orm");

        this.mobileInput = useRef("Mobile");
        useEffect(
            () => {
                // set default value for phone
                if(!this.changes.phone){
                    this.phoneInput.el.value='+966'
                }
                if(!this.changes.mobile){
                    this.mobileInput.el.value='+966'
                }
            }
        )
        super.setup()
    },
    
    async  myAsyncFunction(mobile,partnerId) {
        const mobileExistance = await this.orm.call(
            "res.partner",
            "search_mobile_existance",
            [mobile,partnerId],
            
        );
        return mobileExistance

    },

    saveChanges() {
        // making mobile required and unique through pos (python constrians have no effect in pos js so we had to code these lines )
        if ((!this.props.partner.mobile && !this.changes.mobile) || this.changes.mobile === "") {
            return this.popup.add(ErrorPopup, {
                title: _t("A Customer Mobile Is Required"),
            });
        }
        var self = this
        var final
        if (this.changes.mobile!==''){
            if (typeof self.props.partner.id=== "undefined"){
                self.myAsyncFunction(self.changes.mobile).then(result => {
                    console.log(result);
                    if (result>=1){
                        final = false
                         this.popup.add(ErrorPopup, {
                            title: _t("A Customer with this mobile already exists"),
                        });
                        return false;
                    }else{
                        super.saveChanges()
                    }
                })
    
            }else{
                self.myAsyncFunction(self.changes.mobile,self.props.partner.id).then(result => {
                    console.log(result);
                    if (result>=1){
                        final = false
                        this.popup.add(ErrorPopup, {
                            title: _t("A Customer with this mobile already exists"),
                        });
                        return false;
                    }else{
                        super.saveChanges()
                    }
                })
            }
        }else{
            super.saveChanges()
        }          
    },
})