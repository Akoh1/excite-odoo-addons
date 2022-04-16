
import logging
import requests
import json
today = datetime.date.today()

_logger = logging.getLogger(__name__)

# test_ip = '51.145.88.82'
# test_port = '8080'
# url = 'http://%s:%s/neptune/rest/createNewCustomer' % (test_ip, test_port)
# headers = {
#     "content-type": "application/json"
# }

# data = {
#         'name': "Akoh Ojimaojo",
#         'email': 'samuel@gmail.com',
#         'mobile': '0809456789',
#         'phone': '0018283737',
#         'user_id': 3
# }



# print("LMS Push Data: %s" % data)
# datas = json.dumps(data)
#       # datas = json.loads(data)
#       # req = requests.post(url, data=datas)
# try:
# 	response = requests.post(url, data=datas, headers=headers)
# except requests.ConnectionError as e:
# 	raise print("Connection failure : %s" % str(e))
# print("LMS Push Data receiving......")
# j = json.loads(response.text)
#       # j = response.text
# print("LMS Recieve data: %s" % j)

test_ip = '51.145.88.82'
test_port = '8080'
url = 'http://%s:%s/neptune/rest/createCreditApplication' % (test_ip, test_port)
headers = {
    "content-type": "application/json"
}

data = {
      'totalApprovedAmount': 20000.00,
      # 'firstDisbursementAmount': 5000,
      'applicationDate': today.strftime('%Y-%m-%d')2022-1-15,
      # 'effectiveDate': 2022-1-30,
      # 'creditPurpose':,
      'application_id': 'test018',
      'interestRate': 3, 
      'user_id': 11,
}

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

# test_ip = '51.145.88.82'
# test_port = '8080'
# url = 'http://%s:%s/neptune /rest/getLoanAccounts' % (test_ip, test_port)
# headers = {
#     "content-type": "application/json"
# }

# data = {
#       'custNumber': '0000000003'
# }

# print("LMS Push Data: %s" % data)
# datas = json.dumps(data)
#       # datas = json.loads(data)
#       # req = requests.post(url, data=datas)
# try:
#       response = requests.post(url, data=datas, headers=headers)
# except requests.ConnectionError as e:
#       raise print("Connection failure : %s" % str(e))
# print("LMS Push Data receiving......")
# j = json.loads(response.text)
#       # j = response.text
# print("LMS Recieve data: %s" % j)

