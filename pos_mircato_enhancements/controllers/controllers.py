# -*- coding: utf-8 -*-
# from odoo import http


# class PosMircatoEnhancements(http.Controller):
#     @http.route('/pos_mircato_enhancements/pos_mircato_enhancements', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_mircato_enhancements/pos_mircato_enhancements/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_mircato_enhancements.listing', {
#             'root': '/pos_mircato_enhancements/pos_mircato_enhancements',
#             'objects': http.request.env['pos_mircato_enhancements.pos_mircato_enhancements'].search([]),
#         })

#     @http.route('/pos_mircato_enhancements/pos_mircato_enhancements/objects/<model("pos_mircato_enhancements.pos_mircato_enhancements"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_mircato_enhancements.object', {
#             'object': obj
#         })

