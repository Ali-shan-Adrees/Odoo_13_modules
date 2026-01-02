{
	'name': "Internal Transfer Report",
	'summary': "Custom PDF report for Internal Transfers",
	'description': """
Internal Transfer Report
========================
Custom printable report for internal transfers showing journal, amount, currency, and related journal entries.
""",
	'author': "Ali Shan (EUSOL)",
	'website': "http://www.eusol.net",
	'license': 'LGPL-3',
	'category': 'Accounting',
	'version': '18.1',
	'depends': ['base', 'account'], 
	'data': [
		'views/views.xml',
		'views/templates.xml',
	],
	'installable': True,
	'application': False,
	'auto_install': False,
}
