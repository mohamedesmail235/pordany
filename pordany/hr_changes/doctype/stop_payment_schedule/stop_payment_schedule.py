# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, rounded, getdate, date_diff, add_months
from pordany.utils.utils import get_month_name, get_month_number
from frappe.model.document import Document
class StoppaymentSchedule(Document):
	def validate(self):
		start_date = getdate(self.from_year+"-"+str(get_month_number(self.from_month))+"-1")
		end_date= getdate(self.to_year+"-"+str(get_month_number(self.to_month))+"-1")
		self.validate_fromto_dates(start_date,end_date)

	def load_repayment_schedule(self):
		docs = frappe.db.get_all("Repayment Schedule",filters={"parent":self.loan},\
								 fields=["payment_date","principal_amount","interest_amount","total_payment","balance_loan_amount"],order_by="payment_date asc")
		for doc in docs:
			self.append("repayment_schedule", {
				"payment_date": doc["payment_date"],
				"principal_amount": doc["principal_amount"],
				"interest_amount": doc["interest_amount"],
				"total_payment": doc["total_payment"],
				"balance_loan_amount": doc["balance_loan_amount"]
			})

	def get_loan_month_years(self):
		month,months, years = [], [], []
		docs = frappe.db.get_all("Repayment Schedule",filters={"parent":self.loan},\
								 fields=["payment_date","principal_amount","interest_amount","total_payment","balance_loan_amount"],order_by="payment_date asc")
		if docs:
			for doc in docs:
				month.append(getdate(doc["payment_date"]).month)
				years.append(getdate(doc["payment_date"]).year)

			month.sort()
			for item in month:
				months.append(get_month_name(item))

			months = set(months)
			years = set(years)

		return months,years

	def make_repayment_schedule(self):
		self.repayment_schedule = []
		start_date = getdate(self.from_year+"-"+str(get_month_number(self.from_month))+"-1")
		end_date= getdate(self.to_year+"-"+str(get_month_number(self.to_month))+"-1")
		payment_date = frappe.db.get_value("Loan",self.loan,"repayment_start_date")
		rate_of_interest = frappe.db.get_value("Loan",self.loan,"rate_of_interest")
		monthly_repayment_amount = frappe.db.get_value("Loan",self.loan,"monthly_repayment_amount")
		balance_amount = self.loan_amount
		while(balance_amount > 0):
			if end_date >= getdate(payment_date) >= start_date:
				next_payment_date = add_months(payment_date, 1)
				payment_date = next_payment_date
				continue

			interest_amount = rounded(balance_amount * flt(rate_of_interest) / (12*100))
			principal_amount = monthly_repayment_amount - interest_amount
			balance_amount = rounded(balance_amount + interest_amount - monthly_repayment_amount)

			if balance_amount < 0:
				principal_amount += balance_amount
				balance_amount = 0.0

			total_payment = principal_amount + interest_amount
			self.append("repayment_schedule", {
				"payment_date": payment_date,
				"principal_amount": principal_amount,
				"interest_amount": interest_amount,
				"total_payment": total_payment,
				"balance_loan_amount": balance_amount
			})
			next_payment_date = add_months(payment_date, 1)
			payment_date = next_payment_date

	def move_repayment_schedule_to_loan(self):
		try:
			frappe.db.sql("""delete from `tabRepayment Schedule` where parent=%s and parenttype='Loan' """,(self.name))
			frappe.db.sql("""update `tabRepayment Schedule` set parenttype='Loan' where parent=%s and parenttype='Stop payment Schedule' """, (self.name))
			frappe.msgprint(_("Repayment Schedule Updated Successfully"))
		except:
			frappe.msgprint(_("there is a problem...please contact your administrator"))

	def validate_fromto_dates(self, from_date_field, to_date_field):
		'''
		Generic validation to verify date sequence
		'''
		if date_diff(to_date_field, from_date_field) < 0:
			frappe.throw(_('{0} must be after {1}').format(
				str("to_date_field"),
				str("from_date_field")),
			)