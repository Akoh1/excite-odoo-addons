# -*- coding: utf-8 -*-
import logging
import json
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class HRAPI(http.Controller):

    @http.route('/custom/api/job/positions', type='http', methods=['GET'], auth='public', csrf=False)
    def get_active_job_positions(self, **kw):
        
        jobPositionsModel = request.env['hr.job']
        jobLocModel = request.env['job.location']
        response = {}
        try:
            positionsRecords = jobPositionsModel.sudo().search([
                    ('state', '=', 'recruit')
                ])
            response['data'] = []
            for rec in positionsRecords:
                code  = dict(jobPositionsModel.fields_get(allfields=['job_type'])
                             ['job_type']['selection'])\
                        [rec.job_type] if rec.job_type else False

                jobLocRec = jobLocModel.sudo().search([
                        ('id', '=', rec.job_location.id)
                    ], limit=1)

                response['data'].append({
                    'id': rec.id,
                    'name': rec.name,
                    'description': rec.description,
                    'job_type': code,
                    'job_location': jobLocRec.name
                })
            response['message'] = "ok"

        except Exception as e:
            response['message'] = "ERROR fetching records: %r" % (e)
        dump_res = json.dumps(response, default=lambda o: o.__dict__)
        return dump_res


class ApplicationAPI(http.Controller):

    @http.route('/custom/api/job/application', type='http', methods=['GET'], auth='public', csrf=False)
    def get_applications(self, **kw):
        
        applicantModel = request.env['hr.applicant']
       
        response = {}
        try:
            applicantRecords = applicantModel.sudo().search([])
            response['data'] = []
            for rec in applicantRecords:

                response['data'].append({
                    'id': rec.id,
                    'name': rec.name,
                    'applicant_name': rec.partner_name,
                    'email': rec.email_from,
                    'resume': rec.resume.decode('utf-8') if rec.resume else False
                })
            response['message'] = "ok"

        except Exception as e:
            response['message'] = "ERROR fetching records: %r" % (e)
        dump_res = json.dumps(response)
        return dump_res

    @http.route('/custom/api/job/application', type='json', methods=['POST'], auth='public', csrf=False)
    def create_application(self, **kw):
        data = kw
        http_data = request.httprequest.data and json.loads(request.httprequest.data.decode('utf-8')) or {}
        _logger.info("Json Data from Journal API: %s", data)
        _logger.info("http Data from Journal API: %s", http_data)
        modelObj = request.env['hr.applicant']
        jobPosModel = request.env['hr.job']
        response = {}
        try:
            record = http_data or data

            if 'resume' in record and record.get('resume'):
                record['resume'] = record.get('resume').encode('utf-8')

            if 'job_id' in record and record.get('job_id'):
                getJobPos = jobPosModel.sudo().search([
                        ('id', '=', int(record.get('job_id')))
                    ], limit=1)
                record['job_id'] = getJobPos.id
            
            _logger.info("Record: %s", record)
            
            createModel = modelObj.sudo().create(record)
            request.env.cr.commit()
            response['model_id'] = createModel.id
            response['message'] = "Record has been created"
            response['success'] = True
        except Exception as e:
            response['message'] = "ERROR: %r %r" % (e, kw)
            response['success'] = False
        # _logger.info("Response: %s", response)
        dump_res = json.dumps(response, default=lambda o: o.__dict__)
        load_res = json.loads(dump_res)
        return response

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
