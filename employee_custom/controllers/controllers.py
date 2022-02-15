# -*- coding: utf-8 -*-
# from odoo import http


# class Module14Template(http.Controller):
#     @http.route('/module_14_template/module_14_template/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/module_14_template/module_14_template/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('module_14_template.listing', {
#             'root': '/module_14_template/module_14_template',
#             'objects': http.request.env['module_14_template.module_14_template'].search([]),
#         })

#     @http.route('/module_14_template/module_14_template/objects/<model("module_14_template.module_14_template"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('module_14_template.object', {
#             'object': obj
#         })
