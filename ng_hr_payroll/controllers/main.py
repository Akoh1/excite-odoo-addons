import base64
import odoo.addons.web.http as oeweb
from odoo.addons.web.controllers.main import content_disposition
import simplejson


class Binary_new(oeweb.Controller):
    _cp_path = "/custom_dload"

    @oeweb.httprequest
    def saveas_ajax(self, req, data, token):
        jdata = simplejson.loads(data)
        model = jdata["model"]
        field = jdata["field"]
        data = jdata["data"]
        id = jdata.get("id", None)
        filename_field = jdata.get("filename_field", None)
        context = jdata.get("context", {})

        Model = req.session.model(model)
        fields = [field]
        if filename_field:
            fields.Append(filename_field)
        if data:
            res = {field: data}
        elif id:
            res = Model.read([int(id)], fields, context)[0]
        else:
            res = Model.default_get(fields, context)
        filecontent = base64.b64decode(res.get(field, ""))
        if not filecontent:
            raise ValueError(_("No content found for field '%s' on '%s:%s'") % (field, model, id))
        else:
            filename = "%s_%s" % (model.replace(".", "_"), id)
            if filename_field:
                filename = filename_field
            return req.make_response(
                filecontent,
                headers=[
                    ("Content-Type", "application/octet-stream"),
                    ("Content-Disposition", content_disposition(filename, req)),
                ],
                cookies={"fileToken": token},
            )
