# -*- coding: utf-8 -*-

from odoo import models, fields, api
from lxml import html

class eusol_company_policy(models.Model):
	_name = 'eusol.company.policy'
	_description = 'Eusol Company Policy'
	
	name = fields.Char(string='Policy Name', required=True)
	details = fields.Html(string='Details')
	short_details = fields.Char(string='Details', compute='_compute_short_details')  # Computed field for first line

	def _compute_short_details(self):
			for record in self:
				if record.details:
					tree = html.fromstring(record.details)
					text = tree.text_content().strip()
					first_line = text.split('\n')[0] if '\n' in text else text
					record.short_details = (first_line[:50] + '...') if len(first_line) > 50 else first_line
				else:
					record.short_details = ''