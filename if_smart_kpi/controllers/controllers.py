# -*- coding: utf-8 -*-
# from odoo import http


# class IfSmartKpi(http.Controller):
#     @http.route('/if_smart_kpi/if_smart_kpi/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/if_smart_kpi/if_smart_kpi/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('if_smart_kpi.listing', {
#             'root': '/if_smart_kpi/if_smart_kpi',
#             'objects': http.request.env['if_smart_kpi.if_smart_kpi'].search([]),
#         })

#     @http.route('/if_smart_kpi/if_smart_kpi/objects/<model("if_smart_kpi.if_smart_kpi"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('if_smart_kpi.object', {
#             'object': obj
#         })
