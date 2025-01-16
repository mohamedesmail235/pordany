// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt


frappe.ui.form.on('Quotation', {
    setup: function (frm) {
        get_customer_branch(frm)
    },
    party_name: function (frm) {
        get_customer_branch(frm)
    }
})


let get_customer_branch = function (frm) {
    if (frm.doc.quotation_to && frm.doc.party_name) {
        frappe.call({
            method: "pordany.utils.utils.get_customer_branch",
            args: {
                customer: frm.doc.party_name
            },
            callback: function (data) {
                if (data.message) {
                    let options = data.message;
                    console.log(data.message.length);
                    console.log("options.join:" + options.join("\n"));
                    let options_new = options.join("\n");
                    frm.set_df_property('customer_branch', 'options', options_new);
                }
            }
        })
    }
}