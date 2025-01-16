// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/*jshint smarttabs: true */
frappe.ui.form.on('Stop payment Schedule', {
	validate:function(frm){
		make_repayment_schedule(frm)
	},
	refresh:function(frm){
		make_repayment_schedule(frm)
	},
	setup: function(frm) {
		get_loan_month_years(frm);
		frm.set_query("loan", function() {
			return {
                filters: {
                    "applicant": frm.doc.applicant,
					"docstatus": 1
                }
			};
		});
	},
	loan:function(frm){
		get_loan_month_years(frm)
	},
	epmloyee:function(frm){
		get_loan_month_years(frm)
	}
});

var make_repayment_schedule = function(frm){
		cur_frm.doc.repayment_schedule = [];
		if(cur_frm.doc.applicant && cur_frm.doc.loan) {
			cur_frm.call("make_repayment_schedule");
			cur_frm.set_df_property("move_repayment_schedule_to_loan", "hidden", 0);
			//refresh_many(["repayment_schedule","move_repayment_schedule_to_loan"]);
		}
}

cur_frm.cscript.move_repayment_schedule_to_loan = function(){
		if(cur_frm.doc.applicant && cur_frm.doc.loan) {
			cur_frm.call("move_repayment_schedule_to_loan");
		}
}

var load_repayment_schedule = function (frm) {
		cur_frm.doc.repayment_schedule = [];
		if(frm.doc.applicant && frm.doc.loan){
			cur_frm.call("load_repayment_schedule");
			get_loan_month_years(frm)
		}
}

var get_loan_month_years = function (frm) {
	if(cur_frm.doc.applicant && cur_frm.doc.loan) {
		frappe.call({
				method:"get_loan_month_years",
				doc:frm.doc,
				args:{
					"employee":frm.doc.applicant,
					"loan":frm.doc.loan
				},
				callback:function(data){
					if(data.message){
						// frm.set_df_property("from_month", "options", data.message[0]);
						frm.set_df_property("from_year", "options", data.message[1]);
						// frm.set_df_property("to_month", "options", data.message[0]);
						frm.set_df_property("to_year", "options", data.message[1]);

						frm.set_df_property("from_month", "reqd", 1);
						frm.set_df_property("from_year", "reqd", 1);
						frm.set_df_property("to_month", "reqd", 1);
						frm.set_df_property("to_year", "reqd", 1);
					}
					else{
						frm.set_df_property("from_month", "reqd", 0);
						frm.set_df_property("from_year", "reqd", 0);
						frm.set_df_property("to_month", "reqd", 0);
						frm.set_df_property("to_year", "reqd", 0);
					}
						refresh_many(["from_month","from_year","to_month","to_year"]);
				}
			});
	}
}