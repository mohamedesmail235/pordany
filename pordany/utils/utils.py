# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals, print_function
import frappe
from frappe import _
import frappe.sessions
from frappe.utils import getdate
import calendar
from collections import namedtuple
import json
from six import string_types
from calendar import monthrange
from datetime import datetime, timedelta
from dateutil import relativedelta
from frappe.utils.data import get_first_day, date_diff, flt, get_last_day, add_months
from frappe.utils import getdate, nowdate, cint


def Overlab_Dates(R1_Start_Date, R1_End_date, R2_Start_Date, R2_End_date):
	a, b, c, d = \
		datetime.strptime(R1_Start_Date, '%Y-%m-%d'), \
		datetime.strptime(R1_End_date, '%Y-%m-%d'), \
		datetime.strptime(R2_Start_Date, '%Y-%m-%d'), \
		datetime.strptime(R2_End_date, '%Y-%m-%d')

	Range = namedtuple('Range', ['start', 'end'])

	r1 = Range(start=datetime(a.year, a.month, a.day), end=datetime(b.year, b.month, b.day))
	r2 = Range(start=datetime(c.year, c.month, c.day), end=datetime(d.year, d.month, d.day))

	latest_start = max(r1.start, r2.start)
	earliest_end = min(r1.end, r2.end)
	delta = (earliest_end - latest_start).days + 1
	overlap = max(0, delta)

	return overlap


def get_month_days(start_date):
	option = frappe.db.get_single_value("HR Settings", "day_calculation")
	MonthDays = Switcher(option, start_date)

	return MonthDays


def get_month_name(month, lang=frappe.local.lang):
	month_name = ""
	import datetime
	if (isinstance(month, datetime.date)) or (isinstance(month, str) and month.find('-') != -1):
		month = int(str(month).split('-')[1])
	else:
		if month:
			month = int(month)
	months = {
		1: _("January", lang=lang), 2: _("February", lang=lang), 3: _("March", lang=lang), 4: _("April", lang=lang),
		5: _("May", lang=lang), 6: _("June", lang=lang),
		7: _("July", lang=lang), 8: _("August", lang=lang), 9: _("September", lang=lang), 10: _("October", lang=lang),
		11: _("November", lang=lang), 12: _("December", lang=lang)
	}
	month_name = months.get(month, "Invalid Month")
	return month_name

def get_month_number(month):
	import calendar
	month_dict = (dict((v, k) for k, v in enumerate(calendar.month_name)))

	return month_dict[month]

def Switcher(option, start_date):
	switcher = calendar.monthrange(int(getdate(start_date).year), int(getdate(start_date).month))[1]
	if option == "360":
		switcher = float(360 / 12)
	elif option == "365":
		switcher = float(365 / 12)

	return switcher


@frappe.whitelist()
def get_user_group():
	ret_Dict = frappe.db.sql('''
                    select Module_Group,Icon
                    from (
                        select  distinct  (select  `name`  from `tabModule Def` where `name` = DT.module and `group` is not NULL
                            and restrict_to_domain = 'Services') Module_Group,
                            (select  idx from `tabModule Def` where `name` = DT.module) Idx,
                            (select  icon from `tabModule Def` where `name` = DT.module) Icon
                            from `tabHas Role` HR
                                inner join tabDocPerm DP
                                on HR.role = DP.role
                                inner join tabDocType DT
                                on DP.parent = DT.`name`
                                and HR.parent = %s
                                order by Idx
                                )T
                                where  T.Module_Group is not NULL

					'''
							 , (frappe.session.user), as_dict=True)
	# print("=====================" + str(ret_Dict))
	if ret_Dict != []:
		from frappe.desk.moduleview import get
		for item in ret_Dict:
			item.update(get(item["Module_Group"]))
		# item.update(get(item["Module_Group"]))
		# try:
		#     ret_Dict[item].update(get(ret_Dict[item]["Module_Group"]))
		# except:
		#     pass

	return ret_Dict


@frappe.whitelist()
def next_previous_item(doctype, element_name, filters=[], page_lenght=20, start=0, order_by=""):
	message_status = False
	if (doctype == '' or doctype == None or element_name == '' or element_name == None):
		return message_status
	filter_conditions = ""
	# print("====="+str(filters)+"====")
	if filters != "" and filters != "[]" and filters != []:
		filters = str(filters).replace('[', '').replace(']', '').replace('"', '').split(',')

		filters = list(divide_chunks(filters, 4))

		for item in range(0, len(filters)):
			if filters[item][3] != 'null':
				filter_conditions += " AND " + filters[item][1] + " " + filters[item][2] + " '" + filters[item][3] + "'"

	ret_dict = {}
	teble_name = "`tab" + doctype + "`"
	try:
		tem_dict = frappe.db.sql(
			""
			"    select (select `name` from {0} where idx > T.idx order by `name`  limit 1) next_item , \n"
			"    (select `name` from {1} where idx < T.idx order by `name` desc  limit 1) previous_item \n"
			"        from {2} T \n"
			"               where `name` = {3} \n"
			"                   {4}   \n"
			"           {5}  \n"
			" limit {6},{7}   \n".format(
				teble_name, teble_name, teble_name,
				"'" + element_name + "'",
				filter_conditions,
				("order by " + order_by.split('.')[1] if order_by != "" else ""),
				start,
				page_lenght
			), as_dict=True, debug=False
		)
		if tem_dict != []:
			ret_dict["message_status"] = True
			ret_dict.update(tem_dict[0])
			return ret_dict
	except:
		return message_status


def divide_chunks(l, n):
	# looping till length l
	for i in range(0, len(l), n):
		yield l[i:i + n]


@frappe.whitelist()
def get_widgets(module, filter=[]):
	# module = "People"
	widgets = []
	module_widgets = frappe.db.sql('''
            select title , widget_name ,`query`,chart_type, hide_title ,widget_column_size , widget_order , background_color ,text_color , hide_filter
            from tabWidget
            where  module =%s 
            order by widget_order 
	''', format(module), as_dict=True)

	if module_widgets:
		i = 0
		for widget in module_widgets:
			json_result = {}
			widget_filter = []
			widget_query = frappe.get_value("Widget Query", {"name": widget["query"]}, ['query'], as_dict=True)
			if widget["hide_filter"] == 0:
				widget_filter = frappe.get_value("Widget Filter", {"parent": widget["query"]},
												 ['label', 'type', 'value', 'ref_field'], as_dict=True)
				filter_result = handle_widget_filter(widget_filter)
				json_result["filters"] = filter_result

			result = frappe.db.sql(widget_query["query"], as_dict=True)
			# if widget["chart_type"]=="count-circle":
			json_result["result"] = result
			json_result.update(widget)
			widgets.append(json_result)
		# if widget["chart_type"]=="charts-column-wide":

	# frappe.msgprint(str(widgets))
	return widgets


def handle_widget_filter(filters):
	result = []
	if filters:
		filters["label"] = [filters["label"]]
		if filters["type"] == "Select":
			result = frappe.db.sql(filters["value"], as_dict=True)
			if result:
				filters["value"] = [d for d in result]
		if filters["type"] == "range_date":
			pass
		if filters["type"] == "date":
			pass

		result = [filters]

	# frappe.msgprint(str(result))
	return result


def monthdelta(d1, d2):
	d1 = getdate(d1)
	d2 = getdate(d2)
	delta = 0
	while True:
		mdays = monthrange(d1.year, d1.month)[1]
		d1 += timedelta(days=mdays)
		if d1 <= d2:
			delta += 1
		else:
			break
	return delta


def get_dates_diff(a, b):
	a = getdate(a)
	b = getdate(b)
	diff_dict = {}
	a = datetime(a.year, a.month, a.day)
	b = datetime(b.year, b.month, b.day)
	delta = relativedelta.relativedelta(b, a)
	diff_dict["years"] = delta.years
	diff_dict["months"] = delta.months
	diff_dict["days"] = delta.days

	return diff_dict


def Calculate_component_percentage(disbursement_period, posting_date, joining_date, relieving_date=None, double_NO=0.0):
	percentage = 0
	if relieving_date and getdate(relieving_date).month == getdate(posting_date).month:
		months = {"Quarterly": 3, "Biannual": 6, "Annual": 12}

		days = get_month_days(posting_date) - get_dates_diff(getdate(relieving_date), getdate(posting_date))["days"]
		if disbursement_period in ("Quarterly", "Biannual", "Annual"):
			if getdate(posting_date).month > months[disbursement_period]:
				percentage = ((getdate(posting_date).month - months[disbursement_period]) / months[
					disbursement_period]) + (
										 (days / get_month_days(getdate(posting_date))) / months[disbursement_period])
			else:
				percentage = getdate(posting_date).month / months[disbursement_period] + (
							(days / get_month_days(getdate(posting_date))) / months[disbursement_period])
			frappe
			if double_NO > 0:
				double_NO = float(percentage * double_NO)
			else:
				double_NO = float(percentage)
	else:
		double_NO = {"Quarterly": 3, "Biannual": 6, "Annual": 12}[disbursement_period]
		dates_diff_details = get_dates_diff(getdate(joining_date), getdate(posting_date))

		if getdate(posting_date).year == getdate(joining_date).year and int(dates_diff_details["months"]) < int(
				double_NO):
			double_NO = get_diff_days(double_NO, joining_date)

	# frappe.msgprint(str(disbursement_period)+"====="+str(double_NO) + "======================" +str(percentage))

	return double_NO


def get_diff_days(double_NO, target_date):
	Calculation_option = frappe.db.get_single_value("HR Settings", "day_calculation")
	days_diff = date_diff(get_last_day(target_date), target_date) + 1

	if Calculation_option == "Calendar":
		days_diff = days_diff / get_month_days(target_date)
	elif Calculation_option == "360":
		days_diff = (days_diff / 360) * 12
	elif Calculation_option == "365":
		days_diff = (days_diff / 365) * 12

	double_NO = (double_NO - 1) + days_diff

	return double_NO


def round_to_nearest_half(num):
	syllable = flt("0." + str(num).split('.')[1])

	if syllable > 0.5:
		syllable = syllable - 0.5
	num = num - syllable

	return num


def get_leaves_without_pay(from_date, to_date, employee):
	total_lwp_days = 0.0
	total_lwp_days = frappe.db.sql("""
            select sum(total_leave_days) total_lwp_days
                    from(
                        select leave_type ,from_date,to_date,
                            case
                                    when from_date BETWEEN %s and %s and to_date BETWEEN %s and %s then total_leave_days
                                    when from_date < %s and to_date > %s then DATEDIFF(to_date,%s)+1
                                    when from_date > %s and to_date > %s  then DATEDIFF(%s ,from_date)
                                    else total_leave_days
                                end 	total_leave_days
                            from `tabLeave Application`	L
                                where employee=%s
                                    and (select is_lwp from `tabLeave Type` where `name` = L.leave_type ) = 1
                                    and (
                                        from_date BETWEEN %s and %s
                                or to_date BETWEEN %s and %s
                                )
            )T
    """, (
		from_date,
		to_date,
		from_date,
		to_date,
		from_date,
		from_date,
		from_date,
		from_date,
		to_date,
		to_date,
		employee,
		from_date,
		to_date,
		from_date,
		to_date
	), as_dict=1, debug=False)

	if total_lwp_days:
		total_lwp_days = flt(total_lwp_days[0]["total_lwp_days"])
	return total_lwp_days


def get_leave_allocation(encashment_date, leave_type, employee):
	leave_allocation = frappe.db.sql("""select name from `tabLeave Allocation` where '{0}'
		between from_date and to_date and docstatus=1 and leave_type='{1}'
		and employee= '{2}'""".format(encashment_date or getdate(nowdate()), leave_type, employee))

	return leave_allocation[0][0] if leave_allocation else None


def get_encashment_leaves(date, leave_type, employee):
	encashment_leaves = frappe.db.sql("""select total_leaves_encashed
        from `tabLeave Allocation` where '{0}'
		    between from_date and to_date and docstatus=1 and leave_type='{1}'
		    and employee= '{2}'""".format(date or getdate(nowdate()), leave_type, employee))

	return encashment_leaves[0][0] if encashment_leaves else None


def get_time_diffrence(time_from, time_to):
	from datetime import datetime
	FMT = '%H:%M:%S'
	tdelta = datetime.strptime(time_to, FMT) - datetime.strptime(time_from, FMT)
	return tdelta

@frappe.whitelist()
def Calculation_option(date):
	Calculation_day = 0
	Calculation_option = frappe.db.get_single_value("HR Settings", "day_calculation")
	if Calculation_option == "Calendar":
		Calculation_day = cint(get_month_days(date))
	else:
		Calculation_day = cint(Calculation_option)

	return Calculation_day



@frappe.whitelist()
def get_additional_salary_component(employee, start_date, end_date):
	additional_components = frappe.db.sql("""
		select salary_component, sum(amount) as amount, overwrite_salary_structure_amount, deduct_full_tax_on_selected_payroll_date
		from `tabAdditional Salary`
		where employee=%(employee)s
			and docstatus = 1
			and payroll_date between %(from_date)s and %(to_date)s
		group by salary_component, overwrite_salary_structure_amount
		order by salary_component, overwrite_salary_structure_amount
	""", {
		'employee': employee,
		'from_date': start_date,
		'to_date': end_date
	}, as_dict=1)

	additional_components_list = []
	component_fields = ["depends_on_payment_days", "salary_component_abbr", "is_tax_applicable", "variable_based_on_taxable_salary", 'type']
	for d in additional_components:
		struct_row = frappe._dict({'salary_component': d.salary_component})
		component = frappe.get_all("Salary Component", filters={'name': d.salary_component}, fields=component_fields)
		if component:
			struct_row.update(component[0])

		struct_row['deduct_full_tax_on_selected_payroll_date'] = d.deduct_full_tax_on_selected_payroll_date
		struct_row['is_additional_component'] = 1

		additional_components_list.append(frappe._dict({
			'amount': d.amount,
			'type': component[0].type,
			'struct_row': struct_row,
			'overwrite': d.overwrite_salary_structure_amount,
		}))
	return additional_components_list








def autoname(doc, method):
	parts = doc.naming_series
	doctype = doc.doctype
	count = frappe.db.sql("""
						SELECT count(*)+1 `current` 
								FROM `tab{1}` 
								where  SUBSTRING_INDEX(`name`,'-',1)  = '{0}'
									and month(posting_date) = {2}
									and year(posting_date) = {3}
								;
						""".format(str(parts.split('-')[0]),doctype,getdate(doc.posting_date).month,getdate(doc.posting_date).year) ,as_dict=True,debug=False) or 1
	# frappe.throw(str(count))
	if count:
		current = count[0]["current"]
	n = ''
	if isinstance(parts, string_types):
		parts = parts.split('.')
	series_set = False
	try:
		today = doc.posting_date
		posting_date = getdate(doc.posting_date)
	except:
		today = doc.transaction_date
		posting_date = getdate(doc.transaction_date)


	for e in parts:
		part = ''
		if e.startswith('#'):
			if not series_set:
				digits = len(e)
				part = getseries(n, digits)
				series_set = True
		elif e == 'YY':
			part = posting_date.strftime('%y')
		elif e == 'MM':
			part = posting_date.strftime('%m')
		elif e == 'DD':
			part = posting_date.strftime("%d")
		elif e == 'YYYY':
			part = posting_date.strftime('%Y')
		elif e == 'timestamp':
			part = str(posting_date)
		elif e == 'FY':
			part = frappe.defaults.get_user_default("fiscal_year")
		elif e.startswith('{') and doc:
			e = e.replace('{', '').replace('}', '')
			part = doc.get(e)
		elif doc and doc.get(e):
			part = doc.get(e)
		else:
			part = e

		if isinstance(part, string_types):
			n += part
	# frappe.throw(str(n))
	doc.name = n+str(current)






@frappe.whitelist()
def get_customer_branch(customer):
	list_items = []
	grades = frappe.get_all("Customer Branches",filters={"parent":customer},fields=['branch'],order_by="branch")
	if grades:
		for item in grades:
			list_items.append(item["branch"])

	return list_items