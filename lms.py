
import logging
import requests
import json

_logger = logging.getLogger(__name__)

test_ip = '51.145.88.82'
test_port = '8080'
url = 'http://%s:%s/neptune/rest/createNewCustomer' % (test_ip, test_port)
headers = {
    "content-type": "application/json"
}

data = {
        'name': "Akoh Samuel",
        'email': 'samuel@gmail.com',
        'mobile': '0809456789',
        'phone': '0018283737',
        'user_id': 2
}

# data = {
#         'organisationName': "Test Company",
#         'registrationNumber': "XXTH123",
#         # 'registrationDate': self.date.strftime("%Y-%m-%d"),
#         'FirstName': 'Akoh',
#         'CustomerName': 'Akoh Samuel',
#   		'LastName': 'Samuel',
#         'UserId': 2,
#         'AccountNumber': '0690000032',
#         'AccountName': 'Akoh Samuel',
# }

print("LMS Push Data: %s" % data)
datas = json.dumps(data)
      # datas = json.loads(data)
      # req = requests.post(url, data=datas)
try:
	response = requests.post(url, data=datas, headers=headers)
except requests.ConnectionError as e:
	raise print("Connection failure : %s" % str(e))
print("LMS Push Data receiving......")
j = json.loads(response.text)
      # j = response.text
print("LMS Recieve data: %s" % j)
