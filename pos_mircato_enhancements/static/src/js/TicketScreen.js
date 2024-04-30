/** @odoo-module */

import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(TicketScreen.prototype, {
    _getSearchFields() {
        const fields = {
            RECEIPT_NUMBER: {
                repr: (order) => order.name,
                displayName: _t("Receipt Number"),
                modelField: "pos_reference",
            },

            TRACKING_NUMBER: {
                repr: (order) => order.trackingNumber,
                displayName: _t("Order Number"),
                modelField: "tracking_number",
            },
            DATE: {
                repr: (order) => order.date_order.toFormat("yyyy-MM-dd HH:mm a"),
                displayName: _t("Date"),
                modelField: "date_order",
            },
            PARTNER: {
                repr: (order) => order.get_partner_name(),
                displayName: _t("Customer"),
                modelField: "partner_id.complete_name",
            },
        };

        if (this.showCardholderName()) {
            fields.CARDHOLDER_NAME = {
                repr: (order) => order.get_cardholder_name(),
                displayName: _t("Cardholder Name"),
                modelField: "payment_ids.cardholder_name",
            };
        }

        return fields;
    }

})