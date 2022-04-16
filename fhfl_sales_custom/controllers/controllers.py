# -*- coding: utf-8 -*-
import logging
import json
import re
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import http, tools, _
from odoo.http import request
from odoo.addons.portal.controllers import portal

from odoo import http

_logger = logging.getLogger(__name__)


class CreateJouranlAPI(http.Controller):

    @http.route('/custom/api/create-journal-entry', type='http', methods=['POST'], auth='public', csrf=False, cors='*')
    def create_journal_entry(self, **kw):
        data = kw
        http_data = request.httprequest.data and json.loads(request.httprequest.data.decode('utf-8')) or {}
        _logger.info("Json Data from Journal API: %s", data)
        _logger.info("http Data from Journal API: %s", http_data)
        response = {}
        try:
            record = http_data or data
            if 'transaction_date' in record and record['transaction_date']:
                date_obj = datetime.strptime(record['transaction_date'], '%m/%d/%Y')
                record['transaction_date'] = date_obj
            if 'value_date' in record and record['value_date']:
                date_obj = datetime.strptime(record['value_date'], '%m/%d/%Y')
                record['value_date'] = date_obj
            if 'transaction_timestamp' in record and record['transaction_timestamp']:
                date_time_obj = datetime.strptime(record['transaction_timestamp'], '%m/%d/%Y %H:%M:%S')
                record['transaction_timestamp'] = date_time_obj
            _logger.info("Record: %s", record)
            modelObj = request.env['loan.journal']
            createModel = modelObj.sudo().create(record)
            request.env.cr.commit()
            response['model_id'] = createModel.id
            response['message'] = "Record has been created"
            response['success'] = True
        except Exception as e:
            response['message'] = "ERROR: %r %r" % (e, kw)
            response['success'] = False
        _logger.info("Response: %s", response)
        dump_res = json.dumps(response,default=lambda o: o.__dict__)
        # load_res = json.loads(dump_res)
        return dump_res

    # @http.route('/membership/registration/auto-save',
 #                type='json', methods=['POST'], auth='user',
 #                website=True, )
 #    def auto_save(self, **data):
 #        cleaned_data = self.clean_data(data.copy())
 #        partner = request.env.user.partner_id
 #        current_page = data.get("current_page")
 #        previous_page = current_page - 1

 #        registration = request.env["membership.registration"]. \
 #            sudo().search([["member", "=", partner.id]], limit=1)

 #        if 'liasion_number' in cleaned_data and cleaned_data['liasion_number']:
 #            liasion_partner = request.env["res.partner"]. \
 #                sudo().search([
 #                    ["membership_number", "=", cleaned_data['liasion_number']]
 #                ], limit=1)
 #            if liasion_partner:
 #                cleaned_data['liaising_officer_name'] = liasion_partner.name
 #                cleaned_data['liaising_officer_phone'] = liasion_partner.phone
 #                cleaned_data['liaising_officer_email'] = liasion_partner.email
 #            else:
 #                cleaned_data['liasion_number'] = False

 #        if 'liasion_check' in cleaned_data and cleaned_data['liasion_check']:
 #            if cleaned_data['liasion_check'] == 'yes':
 #                cleaned_data['is_member'] = True
 #            else:
 #                cleaned_data['is_member'] = False
 #            del cleaned_data['liasion_check']

 #        if previous_page == self.pages["previous_organisation"] \
 #                and data.get("name/0/", False):
 #            lines = self.parse_dict(cleaned_data)
 #            registration.previous_organization_ids.unlink()
 #            cleaned_data.update({
 #                "previous_organization_ids": lines,
 #            })

 #        if "pardon_evidence" in data and data["pardon_evidence"]:
 #            cleaned_data["pardon_evidence"] = True

 #        if previous_page == self.pages["declaration"]:
 #            cleaned_data["state"] = "new"

 #        _logger.info("Cleaned date: %s", cleaned_data)
 #        self.add_attachments(data, registration.id)
 #        registration.sudo().write(cleaned_data)

 #        partner_data = {}
 #        fields_to_map = ["mobile_phone", "home_address", "nationality"]
 #        field_map = {
 #            "mobile_phone": "phone",
 #            "home_address": "street",
 #            "nationality": "country_id",
 #        }
 #        for field in fields_to_map:
 #            if field in cleaned_data:
 #                if field == "nationality":
 #                    partner_data[field_map[field]] = \
 #                        int(cleaned_data[field])
 #                else:
 #                    partner_data[field_map[field]] = \
 #                        cleaned_data[field]

 #        partner = request.env.user.partner_id
 #        partner.sudo().write(partner_data)
 #        request.env.cr.commit()
 #        return {
 #            "completed": previous_page == self.pages["declaration"],
 #            "updated": True,
 #        }

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
