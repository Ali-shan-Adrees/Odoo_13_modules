# -*- coding: utf-8 -*-
{
	'name': "Performance Analysis",

	'summary': """
	  Employee Performance Analysis""",

	'description': """
	   A module that evaluates employees’ weekly and monthly performance 
	   based on timesheet data and manager review.
	""",

	'author': "Ali shan dev at Eusol",
	'website': "http://www.eusol.net",

	'category': 'Uncategorized',
	'version': '13.1.0.0.',
	'depends': ['base','hr','mail','project'],
	'external_dependencies': {'python': ['psycopg2']},
	# 'images': ["static/description/icon.png"],
	
	# always loaded
	'data': [
		# 'security/security.xml',
		'security/ir.model.access.csv',
		'views/views.xml',
		'data/performance_cron.xml',
	],
	'application': True,
}
