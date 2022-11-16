import requests
from bson import json_util
import json
import datetime
import base64

today = datetime.date.today()
today_date = datetime.datetime.today()
test_ip = '127.0.0.1'
test_port = '7092'
# test_url = 'http://%s:%s/custom/api/create-journal-entry' % (test_ip, test_port)
test_url = 'http://%s:%s/custom/api/job/application' % (test_ip, test_port)
prod_ip = '51.145.48.170'
url = 'http://%s/custom/api/create-journal-entry' % (prod_ip)
headers = {
    "content-type": "application/jsonp"
    # "content-type": "application/x-www-form-urlencoded"
}
f = open("01_SAMUEL AKOH New Resume.docx", "rb")
# data = {
#     'name': "TESTAPP01",
#     'partner_name': 'Akoh Samuel',
#     'resume': base64.b64encode(f.read())
# }
print(f"File: {base64.b64encode(f.read())}")
# try:
#       # response = requests.post(url, data=datas, headers=headers)
#     response = requests.post(test_url, data=data)
#     print("Push Data receiving......")
#       # j = json.loads(response.text)
#             # j = response.text
#     print("Recieve data: %s" % response)

# except requests.ConnectionError as e:
#     raise print("Connection failure : %s" % str(e))