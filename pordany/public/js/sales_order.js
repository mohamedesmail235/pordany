// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on('Sales Order', {
    setup: function (frm) {
        get_customer_branch(frm)
    },
    customer: function (frm) {
        get_customer_branch(frm)
    }
})


let get_customer_branch = function (frm) {
    if (frm.doc.customer) {
        frappe.call({
            method: "pordany.utils.utils.get_customer_branch",
            args: {
                customer: frm.doc.customer
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