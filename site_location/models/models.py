from odoo import models, fields, api,_


class site_location(models.Model):
	_name = 'site_location.site_location'
	_description = 'Site Location'
	_rec_name= 'site_location'
  

	site_location = fields.Text(string='Site Location')
	partner_id = fields.Many2one('res.partner',string="Customer")



class SaleOrder(models.Model):
	_inherit = 'sale.order'
	_description='Sale Order'

	site_location_id = fields.Many2one('site_location.site_location', string='Site Location')

	def _create_invoices(self, grouped=False, final=False):
		invoices= super(SaleOrder, self)._create_invoices(grouped=grouped, final=final)
		if invoices:
			for sale in self:
				if sale.site_location_id:
						for inv in invoices:
							inv.sudo().update({'site_location_id':sale.site_location_id.id})
		return invoices


class AccountMove(models.Model):
	_inherit = 'account.move'
	_description='Account Move'

	site_location_id = fields.Many2one('site_location.site_location', string='Site Location',readonly=True)




class adv_in_payment(models.TransientModel):
	_inherit = 'sale.advance.payment.inv'
	_description='Advance Payment'

	def _create_invoice(self, order, so_line, amount):
		result = super(adv_in_payment, self)._create_invoice(order, so_line, amount)
		if order:
			if result:
				for sale in order:
					if sale.site_location_id:
							for inv in result:
								inv.sudo().update({'site_location_id':sale.site_location_id.id})
		return result