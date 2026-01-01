# -*- coding: utf-8 -*-
{
	'name': "EUSOL Company Policy",

	'summary': """
	  EUSOL Company Policy""",

	'description': """
	   EUSOL Company Policy
	""",

	'author': "Ali Shan Dev at Eusol",
	'website': "http://www.eusol.net",

	'category': 'Uncategorized',
	'version': '13.0.0.1',

	'depends': ['base','hr'],

	# always loaded
	'data': [
		'security/eusol_company_policy_security.xml',
		'security/ir.model.access.csv',
		'views/views.xml',
		'data/eusol_company_policy_data.xml',
	],
	'assets': {
		'web.assets_backend': [
			'eusol_company_policy/static/src/css/style.css',
		],
	},
}
