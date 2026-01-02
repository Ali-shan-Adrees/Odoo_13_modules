# -*- coding: utf-8 -*-
# from odoo import http


# class SiteLocation(http.Controller):
#     @http.route('/site_location/site_location/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/site_location/site_location/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('site_location.listing', {
#             'root': '/site_location/site_location',
#             'objects': http.request.env['site_location.site_location'].search([]),
#         })

#     @http.route('/site_location/site_location/objects/<model("site_location.site_location"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('site_location.object', {
#             'object': obj
#         })
