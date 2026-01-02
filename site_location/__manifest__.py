# -*- coding: utf-8 -*-
{
    'name': "site_location",

    'summary': """

        Site Locations""",

    'description': """
     purpose of the module is to manage location of sites 
     """,

    'author': "Ali Shan",

    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'LGPL-3',

    'depends': ['base','sale','account'],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/menuitem.xml'
    ],
  }
