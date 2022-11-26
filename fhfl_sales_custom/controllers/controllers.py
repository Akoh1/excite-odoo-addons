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


class TenderAPI(http.Controller):

    @http.route('/custom/api/tenders', type='http', methods=['GET'], auth='public', csrf=False)
    def get_tenders(self, **kw):
        
        purReqModel = request.env['purchase.requisition']
       
        response = {}
        try:
            purReqRecords = purReqModel.sudo().search([])
            response['data'] = []
            for rec in purReqRecords:

                response['data'].append({
                    'id': rec.id,
                    'name': rec.name,
                    'title': rec.title,
                    'company_name': rec.company_name,
                    'company_email': rec.company_email,
                    'contact_name': rec.contact_name,
                    'contact_phone': rec.contact_phone,
                    'files_url': rec.files_url,
                })
            response['message'] = "ok"

        except Exception as e:
            response['message'] = "ERROR fetching records: %r" % (e)
        dump_res = json.dumps(response)
        return dump_res

    @http.route('/custom/api/tenders/<int:record_id>', type='json', methods=['PATCH'], auth='public', csrf=False)
    def update_tenders(self, record_id, **kw):
        data = kw
        http_data = request.httprequest.data and json.loads(request.httprequest.data.decode('utf-8')) or {}
        _logger.info("Json Data from Tenders API: %s", data)
        _logger.info("http Data from Tenders API: %s", http_data)
        modelObj = request.env['purchase.requisition']
        jobPosModel = request.env['hr.job']
        response = {}
        record = http_data or data
        _logger.info("Record: %s", record)


        modelObjData = modelObj.sudo().search([('id', '=', record_id)])
        
        try:
            if 'title' in record:
                record['title'] = int(record['title'])

            if not modelObjData:
                response['message'] = "No Record found for id(%s) in given model(%s)." % (
                record_id, 'purchase.requisition')
                response['success'] = False
            
            # modelObjData = modelObj.sudo().search([('id', '=', record_id)])
            else:
                modelObjData.sudo().write(record)
                request.env.cr.commit()
                response['model_id'] = modelObjData.id
                response['message'] = "Record has been updated"
                response['success'] = True
                
        except Exception as e:
            e = "Cannot update title of this record from Web" if 'title' in record else e
            response['message'] = "ERROR: %r" % (e)
            response['success'] = False
        # _logger.info("Response: %s", response)
        # if response.get('success') is True:
        #     _logger.info("Send mail function")
        #     templ = request.env.ref('fhfl_sales_custom.tender_email_template')
        #     _logger.info("Mail template: %s", templ)
    
        #     _logger.info("Testing code block")

        
        #     _logger.info("Model to send mail: %s", modelObjData)
          
        #     _logger.info("Loop self")

            
        #     request.env['mail.template'].browse(templ.id). \
        #         send_mail(modelObjData.id, force_send=True, raise_exception=True)
                
        dump_res = json.dumps(response, default=lambda o: o.__dict__)
        load_res = json.loads(dump_res)
        return response










