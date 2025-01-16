from . import __version__ as app_version

app_name = "pordany"
app_title = "Pordany"
app_publisher = "MiM"
app_description = "Pordany Change requests "
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "m.ismail@datavaluenet.net"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/pordany/css/pordany.css"
# app_include_js = "/assets/pordany/js/pordany.js"

# include js, css files in header of web template
# web_include_css = "/assets/pordany/css/pordany.css"
# web_include_js = "/assets/pordany/js/pordany.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "pordany/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Quotation" : "public/js/quotation.js",
	"Sales Invoice" : "public/js/sales_invoice.js",
	"Sales Order" : "public/js/sales_order.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "pordany.install.before_install"
# after_install = "pordany.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "pordany.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"Stock Entry": "pordany.override.stock_entry.CustomStockEntry"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }
#
# doc_events ={
# 	"Journal Entry":{
# 		"before insert":"pordany.utils.utils.autoname"
# 	},
# 	"Delivery Note":{
# 		"before insert":"pordany.utils.utils.autoname"
# 	},
# 	"Employee Advance":{
# 		"before insert":"pordany.utils.utils.autoname"
# 	},
# 	"Expense Claim":{
# 		"before insert":"pordany.utils.utils.autoname"
# 	},
# 	"Leave Application":{
# 		"before insert":"pordany.utils.utils.autoname"
# 	},
# 	"Material Request":{
# 		"before insert":"pordany.utils.utils.autoname"
# 	},
# 	"Payment Entry":{
# 		"before insert":"pordany.utils.utils.autoname"
# 	},
# 	"Purchase Invoice":{
# 		"before insert":"pordany.utils.utils.autoname"
# 	},
# 	"Purchase Order":{
# 		"before insert":"pordany.utils.utils.autoname"
# 	},
# 	"Purchase Receipt":{
# 		"before insert":"pordany.utils.utils.autoname"
# 	},
# 	"Quotation":{
# 		"before insert":"pordany.utils.utils.autoname"
# 	},
# 	"Sales Invoice":{
# 		"before insert":"pordany.utils.utils.autoname"
# 	},
# 	"Sales Order":{
# 		"before insert":"pordany.utils.utils.autoname"
# 	},
# 	"Stock Entry":{
# 		"before insert":"pordany.utils.utils.autoname"
# 	},
# 	"Stock Reconciliation":{
# 		"before insert":"pordany.utils.utils.autoname"
# 	},
# 	"Supplier Quotation":{
# 		"before insert":"pordany.utils.utils.autoname"
# 	},
# 	"Work Order":{
# 		"before insert":"pordany.utils.utils.autoname"
# 	},
# 	"Asset":{
# 		"before insert":"pordany.utils.utils.autoname"
# 	}
# }
# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"pordany.tasks.all"
# 	],
# 	"daily": [
# 		"pordany.tasks.daily"
# 	],
# 	"hourly": [
# 		"pordany.tasks.hourly"
# 	],
# 	"weekly": [
# 		"pordany.tasks.weekly"
# 	]
# 	"monthly": [
# 		"pordany.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "pordany.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "pordany.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "pordany.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------
# auth_hooks = [
# 	"pordany.auth.validate"
# ]

fixtures = [
    {
    "dt": "Custom Field",
    "filters": [["name", "in", [
        'Work Order-posting_date',
        'Asset-posting_date',
		'Sales Invoice-customer_branch',
		'Customer-customer_branches',
		'Sales Order-customer_branch',
		'Quotation-customer_branch',
		'Customer-customer_branches_details'
    ]]]
}
]