# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import datetime
from datetime import datetime
from frappe.model.document import Document
from pordany.utils.utils import get_dates_diff, get_month_days
from frappe.utils import add_days, cint, cstr, flt, getdate, rounded,date_diff
from frappe.utils.data import get_first_day
from frappe import _
from hrms.hr.utils import get_leave_period
from pordany.utils.utils import get_additional_salary_component
from hrms.hr.doctype.leave_application.leave_application \
	import get_leave_allocation_records, get_leave_balance_on, get_approved_leaves_for_period

class Indemnity(Document):

	def __init__(self, *args, **kwargs):
		super(Indemnity, self).__init__(*args, **kwargs)
		self.whitelisted_globals = {
			"int": int,
			"float": float,
			"long": int,
			"round": round,
			"date": datetime.date,
			"getdate": getdate
		}
	def validate(self):
		date_of_joining = self.get_last_join_date()
		self.last_joining_day = date_of_joining
		if date_diff(self.relieving_date,date_of_joining) < 0:
			frappe.throw(_("Last Working Day must be after Joining Date {0}".format(date_of_joining)))

		self.calculate_net_pay()

	def on_submit(self):
		frappe.db.set_value("Employee", self.employee, "status", "Left")
		frappe.db.set_value("Employee", self.employee, "relieving_date", self.relieving_date)
		frappe.db.set_value("Employee", self.employee, "reason_for_leaving", self.reason_for_leaving)

	def on_cancel(self):
		frappe.db.set_value("Employee", self.employee, "status", "Active")
		frappe.db.set_value("Employee", self.employee, "relieving_date", None)
		frappe.db.set_value("Employee", self.employee, "reason_for_leaving", None)

	def get_years_of_service(self):
		date_of_joining = frappe.db.get_value("Employee",self.employee,"date_of_joining")
		if(not date_of_joining):
			frappe.throw("Please set date of joining")
		deducted_days = frappe.db.get_value("Deduct Days from Service Period",{"name":self.employee,"type":"Service Period"},"number_of_days") or 0

		self.deduct_days_from_service_period = deducted_days
		service_details = get_dates_diff(add_days(date_of_joining,deducted_days),add_days(self.relieving_date,1))

		date_of_joining = self.get_last_join_date()

		adj_service_details = get_dates_diff(date_of_joining,add_days(self.relieving_date,1))
		service_details["adj_years"] = (adj_service_details["years"] if cint(adj_service_details["years"]) > 0 else 0)
		service_details["adj_months"] = (adj_service_details["months"] if cint(adj_service_details["months"]) > 0 else 0)
		service_details["adj_days"] = (adj_service_details["days"] if cint(adj_service_details["days"]) > 0 else 0)

		return service_details

	def add_additional_salary_components(self):
		# end_date = str(getdate(self.relieving_date).year)+"-"+ str(getdate(self.relieving_date).month)+"-"+ str(get_month_days(self.relieving_date))
		# start_date = str(getdate(str(self.relieving_date)).year)+"-"+ str(getdate(str(self.relieving_date)).month)+"-"+str(get_first_day(self.relieving_date))

		additional_components = get_additional_salary_component(self.employee, self.start_date, self.end_date)
		if additional_components:
			for additional_component in additional_components:
				amount = additional_component.amount
				overwrite = additional_component.overwrite
				key = "earnings" if additional_component.type == "Earning" else "deductions"
				self.update_component_row(frappe._dict(additional_component.struct_row), amount, key,
										  overwrite=overwrite)

	def get_tickets_details(self):
		tickets_details = frappe.db.get_list("Airplane Tickets Request", filters={"employee":self.employee,"contract":self.contract},fields=["employee_share","company_share"])
		if tickets_details:
			for item in tickets_details:
				amount = item.employee_share
				self.company_share = item.company_share
				item.salary_component = "Tickets Employee Share"
				item.abbr = "TES"
				self.update_component_row(frappe._dict(item), amount, "deductions", overwrite="overwrite")

	def calculate_component_amounts(self):
		self.include_in_indemnity_amount= 0.0
		data = self.get_data_for_eval()

		month_days = get_month_days(self.relieving_date)

		from calendar import monthrange
		days_in_month = monthrange(getdate(self.relieving_date).year, getdate(self.relieving_date).month)[1]
		month_working_days = getdate(self.relieving_date).day

		if month_working_days >= month_days:
			month_working_days = month_days
		elif month_working_days == cint(days_in_month):
			month_working_days = 30
		base_eos_sal = frappe.db.get_value("Salary Slip", filters={"employee": self.employee,"start_date":self.start_date}, fieldname =["gross_pay"])#  "docstatus": "1",
		for_leave_encashment = 0.0
		# if not base_eos_sal:
		self.add_additional_salary_components()
		self.get_tickets_details()
		for key in ('earnings', 'deductions'):
			for struct_row in self._salary_structure_doc.get(key):
				include_in_indemnity = frappe.db.get_value("Salary Component",struct_row.salary_component,"include_in_indemnity")
				if key == "earnings":
					amount = self.eval_condition_and_formula(struct_row, data)
					if include_in_indemnity:
						self.include_in_indemnity_amount+=amount

					if key == "earnings" and frappe.db.get_value("Salary Component", struct_row.salary_component,"include_in_leave_encashment_") == 1:
						for_leave_encashment += amount

					if amount and struct_row.statistical_component == 0 and not base_eos_sal:
						self.update_component_row(struct_row, amount, "earning")

					amount = (flt(amount) / month_days) * month_working_days

					if amount and struct_row.statistical_component == 0 and not base_eos_sal:
						self.update_component_row(struct_row, amount, key)

				elif key == "deductions":
					amount = self.eval_condition_and_formula(struct_row, data)

					if amount and struct_row.statistical_component == 0 and not base_eos_sal:
						self.update_component_row(struct_row, amount, "deduction")

					amount = (flt(amount) / month_days) * month_working_days

					if amount and struct_row.statistical_component == 0 and not base_eos_sal:
						self.update_component_row(struct_row, amount, key)

		closing, paid_leave = 0.0, 0.0
		filters = frappe._dict()
		start_date = get_first_day(self.relieving_date)

		if date_diff(self.relieving_date, self.joining_date) < 1:
			frappe.throw(_("relieving date should be after joining date"))
		self.total_leave_encashed = 0

		if for_leave_encashment > 0:
			deducted_days = frappe.db.get_value("Deduct Days from Service Period", {"name":self.employee,"type":"Leave En-Cash"}, "number_of_days") or 0

			calculate_leave_encasement = (frappe.db.get_single_value("HR Settings", "calculate_leave_encasement") or "Day Rate")
			if calculate_leave_encasement=="Day Rate":
				day_rate = str(flt(for_leave_encashment) / month_days)# month_working_days
				# frappe.msgprint(str(for_leave_encashment)+"====day_rate===="+str(day_rate)+"====month_working_days===="+str(month_days))
				if self.current_leave_balance > self.leave_balance:
					self.current_leave_balance = self.leave_balance
				elif flt(self.current_leave_balance) < 0:
					self.current_leave_balance = 0

				self.total_leave_encashed = flt(day_rate) * flt(self.current_leave_balance)
			else:
				if self.contract:
					last_join_date = self.get_last_join_date()

					contract_duration_days = (cint(self.contract_duration) * 30) + flt(deducted_days)
					# if cint(date_diff(self.relieving_date,last_join_date)) < contract_duration_days :
					# 	self.total_leave_encashed = flt((flt(for_leave_encashment)/11) * (cint(self.years) + cint(self.months) + (flt(self.days) /30)))
					# else:

					service_duration_days = contract_duration_days - (cint(self.yearly_vacation) * (flt(self.contract_duration)/12))

					service_duration_months = flt(service_duration_days / 30)

					total_sevice_months = (cint(self.adj_years) * 12) + cint(self.adj_months) + flt(self.adj_days)/30

					self.total_leave_encashed = (flt(for_leave_encashment) / service_duration_months) * ((cint(self.yearly_vacation) * (flt(self.contract_duration)/12))/30) * total_sevice_months

			if self.total_leave_encashed < 0:
				self.total_leave_encashed = 0

	def get_last_join_date(self):
		last_join_date = ""
		last_join = frappe.db.sql("""
			select joining_date
				from `tabBack From Leave`
				where employee = %s
					and docstatus = 1
					-- and leave_type ='Casual Leave'
				order by from_date desc 
				limit 1
		""", (self.employee),as_dict=True)

		if last_join:
			last_join_date = last_join[0]["joining_date"]
		else:
			if not self.joining_date:
				frappe.throw(_("Please Check Joning Date"))
			last_join_date = self.joining_date

		return last_join_date

	def calculate_net_pay(self):
		self.balance_loan_amount = 0
		self.start_date = str(get_first_day(self.relieving_date))
		self.end_date = str(getdate(self.relieving_date).year)+"-"+ str(getdate(self.relieving_date).month)+"-"+ str(int(get_month_days(self.relieving_date)))

		self.get_leave_balance()

		self.calculate_component_amounts()

		self.earning_amount = self.get_component_totals("earning")
		self.deduction_sum = self.get_component_totals("deduction")

		self.gross_pay = self.get_component_totals("earnings")
		self.total_deduction = self.get_component_totals("deductions")

		if self.ignore_loan:
			self.set('loans', [])
		else:
			self.set_loan_repayment()

		self.net_sum = flt(self.earning_amount) - (flt(self.total_deduction) )
		self.net_pay = flt(self.gross_pay) - (flt(self.total_deduction) )# + flt(self.total_loan_repayment)
		# self.net_pay = rounded(self.net_pay)
		if self.form_type=='Indemnity':
			is_paid = frappe.db.get_value("Reason for Leaving", filters={"name":self.reason_for_leaving},fieldname=["paid"])
			if is_paid:
				idemnity_amount = self.calculate_idemnity_amount()
				self.total_indemnity = flt(idemnity_amount)  # - flt(self.total_principal_amount - self.total_loan_repayment)
			else:
				self.total_indemnity = 0.0
		# frappe.msgprint("net_pay=============>" + str(self.net_pay))
		self.total_net_pay = ((self.total_indemnity if self.form_type=='Indemnity' else 0) + self.net_pay + self.total_leave_encashed) - self.balance_loan_amount
		# frappe.msgprint("idemnity_amount=============>"+str(idemnity_amount)+"==============="+str(self.include_in_indemnity_amount)+"month_days=============="+str(get_month_days(self.relieving_date)))
	def get_leave_balance(self):
		leave_types = []
		leaves_taken,opening,closing = 0.0, 0.0, 0.0
		allocation_records_based_on_to_date = get_leave_allocation_records(self.start_date)
		# frappe.msgprint(str(allocation_records_based_on_to_date))
		# allocation_records_based_on_from_date = get_leave_allocation_records(self.end_date)
		leave_period = get_leave_period(self.start_date, self.end_date, frappe.db.get_value("Employee",self.employee,"company"))
		if leave_period:
			leave_period = leave_period[0]
			leave_types = frappe.db.get_all("Leave Type",filters={"is_lwp":0,"is_carry_forward":1},fields=["name"])

			for leave_type in leave_types:
				# leaves taken
				leaves_taken += get_approved_leaves_for_period(self.employee, leave_type.name,
															  leave_period.from_date, leave_period.to_date)
				# opening balance
				opening += get_leave_balance_on(self.employee, leave_type.name, leave_period.from_date,
											   allocation_records_based_on_to_date.get(self.employee, frappe._dict()))

				# closing balance
				closing += get_leave_balance_on(self.employee, leave_type.name, leave_period.to_date,
											   allocation_records_based_on_to_date.get(self.employee, frappe._dict()))
			self.leave_balance=closing

	def calculate_idemnity_amount(self):
		month_days = get_month_days(self.relieving_date)
		idemnity_amount, days_months_value = 0.0, 0.0
		conditions = frappe.get_list("Payment Detail",filters={"parent":self.reason_for_leaving,"parentfield":"payment_detail"},fields=["years_from","years_to","pay_percentage"],order_by="idx desc")
		total_years = self.years

		if 5 > self.years > 0:
			idemnity_amount = flt(flt(self.include_in_indemnity_amount) / 23) * (cint(self.years * 12) + cint(self.months) + (flt(self.days) /30))
			# frappe.msgprint("idemnity_amount=============>"+str(self.include_in_indemnity_amount))
		elif self.years >= 5:
			idemnity_amount = flt(flt(self.include_in_indemnity_amount) / 23) * 60 # (cint(self.years * 12) + cint(self.months) + (flt(self.days) / 30))
			idemnity_amount+=(flt(flt(self.include_in_indemnity_amount) / 11) * ((cint(self.years) - 5) * 12) + cint(self.months) + (flt(self.days) /30))
		elif self.months > 0:
			idemnity_amount = (flt(flt(self.include_in_indemnity_amount) / 23) * (cint(self.months) + (flt(self.days) /30)))

		# frappe.msgprint(str(idemnity_amount))
		for item in conditions:
			if flt(item["years_to"]) >= total_years > flt(item["years_from"]):
				idemnity_amount = flt(idemnity_amount)  * (flt(item["pay_percentage"]) / 100)

		return rounded(idemnity_amount,2)

	def get_component_totals(self, component_type):
		total = 0.0
		for d in self.get(component_type):
			if not d.do_not_include_in_total:
				d.amount = flt(d.amount, d.precision("amount"))
				total += d.amount
		return total

	def get_data_for_eval(self):
		'''Returns data for evaluating formula'''
		data = frappe._dict()
		salary_structure = frappe.get_list("Salary Structure Assignment",{"employee":self.employee,"docstatus":1},"salary_structure", order_by =" from_date desc ",limit_start=0,limit_page_length=1)
		if salary_structure:
			salary_structure = salary_structure[0]["salary_structure"]
			self._salary_structure_doc = frappe.get_doc('Salary Structure', salary_structure)
			data.update(frappe.get_doc("Salary Structure Assignment",
								   {"employee": self.employee, "salary_structure": salary_structure}).as_dict())
		else:
			frappe.throw(_("Please make New Salary Structure Assignment"))

		data.update(frappe.get_doc("Employee", self.employee).as_dict())
		data.update(self.as_dict())

		# set values for components
		salary_components = frappe.get_all("Salary Component", fields=["salary_component_abbr"])
		for sc in salary_components:
			data.setdefault(sc.salary_component_abbr, 0)

		return data

	def eval_condition_and_formula(self, d, data):
		try:
			condition = d.condition.strip() if d.condition else None
			if condition:
				if not frappe.safe_eval(condition, self.whitelisted_globals, data):
					return None
			amount = d.amount
			if d.amount_based_on_formula:
				formula = d.formula.strip() if d.formula else None
				if formula:
					amount = flt(frappe.safe_eval(formula, self.whitelisted_globals, data), d.precision("amount"))
			if amount:
				data[d.abbr] = amount

			return amount

		except NameError as err:
			frappe.throw(_("Name error: {0}".format(err)))
		except SyntaxError as err:
			frappe.throw(_("Syntax error in formula or condition: {0}".format(err)))
		except Exception as e:
			frappe.throw(_("Error in formula or condition: {0}".format(e)))
			raise

	def update_component_row(self, struct_row, amount, key, overwrite=1):
		component_row = None
		for d in self.get(key):
			if d.salary_component == struct_row.salary_component:
				component_row = d

		if not component_row:
			if amount:
				self.append(key, {
					'amount': amount,
					'default_amount': amount if not struct_row.get("is_additional_component") else 0,
					'depends_on_payment_days' : struct_row.depends_on_payment_days,
					'salary_component' : struct_row.salary_component,
					'abbr' : struct_row.abbr,
					'do_not_include_in_total' : struct_row.do_not_include_in_total,
					'is_tax_applicable': struct_row.is_tax_applicable,
					'is_flexible_benefit': struct_row.is_flexible_benefit,
					'variable_based_on_taxable_salary': struct_row.variable_based_on_taxable_salary,
					'deduct_full_tax_on_selected_payroll_date': struct_row.deduct_full_tax_on_selected_payroll_date,
					'additional_amount': amount if struct_row.get("is_additional_component") else 0
				})
		else:
			if struct_row.get("is_additional_component"):
				if overwrite:
					component_row.additional_amount = amount - component_row.get("default_amount", 0)
				else:
					component_row.additional_amount = amount

				if not overwrite and component_row.default_amount:
					amount += component_row.default_amount
			else:
				component_row.default_amount = amount

			component_row.amount = amount
			component_row.deduct_full_tax_on_selected_payroll_date = struct_row.deduct_full_tax_on_selected_payroll_date

	def set_loan_repayment(self):
		self.set('loans', [])
		self.total_loan_repayment = 0
		self.total_interest_amount = 0
		self.total_principal_amount = 0
		self.balance_loan_amount = 0
		for loan in self.get_loan_details():
			self.append('loans', {
				'loan': loan.name,
				'total_payment': loan.total_payment,
				'interest_amount': loan.interest_amount,
				'principal_amount': loan.principal_amount,
				'loan_account': loan.loan_account,
				'interest_income_account': loan.interest_income_account
			})

			self.balance_loan_amount = flt(loan.balance_loan_amount)
			self.total_loan_repayment += flt(loan.total_payment) - flt(loan.balance_loan_amount)# + loan.principal_amount
			self.total_interest_amount += loan.interest_amount
			self.total_principal_amount += loan.total_payment

	def get_loan_details(self):
		return frappe.db.sql("""select 
					rps.principal_amount, 
					rps.interest_amount, 
					l.name,
					l.total_payment, 
					l.loan_account, 
					l.interest_income_account,
					rps.balance_loan_amount
			from
				`tabRepayment Schedule` as rps, `tabLoan` as l
			where
				l.name = rps.parent and rps.payment_date between %s and %s and
				l.repay_from_salary = 1 and l.docstatus = 1 and l.applicant = %s
				and rps.parenttype ='Loan' """,
							 (self.start_date, self.end_date, self.employee), as_dict=True,debug=False) or []

	def get_employee_contract(self,employee):
		contract = frappe.db.sql("""
			select `name` contract
				from `tabEmployee contract`
					where employee = %s
							and docstatus = 1
							order by contract_start_date desc 
							limit 1
		""",(employee),as_dict=True)
		if contract:
			return contract[0]["contract"]

