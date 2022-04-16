import logging
import requests
from bson import json_util
import json
import datetime

today = datetime.date.today()
today_date = datetime.datetime.today()
test_ip = '127.0.0.1'
test_port = '7092'
test_url = 'http://%s:%s/custom/api/create-journal-entry' % (test_ip, test_port)

prod_ip = '51.145.48.170'
url = 'http://%s/custom/api/create-journal-entry' % (prod_ip)
headers = {
    "content-type": "application/jsonp"
    # "content-type": "application/x-www-form-urlencoded"
}
# today.strftime('%m/%d/%Y'),
# today_date.strftime('%m/%d/%Y %H:%M:%S'),
# data = {
#       # 'field1': "Test",
#       # 'field2': 5
#       'transaction_date': today.strftime('%m/%d/%Y'),
#       'value_date': today.strftime('%m/%d/%Y'), 
#       'transaction_amount': 181,
#       'transaction_timestamp': today_date.strftime('%m/%d/%Y %H:%M:%S'),
#       # 'customer_id': 10,
#       # 'application_id': 'rrrr1'
# }

data = {
      # 'field1': "Test",
      # 'field2': 5
      'transaction_date': today.strftime('%m/%d/%Y'),
      'value_date': today.strftime('%m/%d/%Y'), 
      'transaction_amount': 1800,
      'transaction_timestamp': today_date.strftime('%m/%d/%Y %H:%M:%S'),
      # 'customer_id': 55,
      # 'application_id': 'rrrr1'
}

print("Journal Push Data: %s" % data)
# datas = json.dumps(data, default=json_util.default)
datas = json.dumps(data)
      # datas = json.loads(data)
      # req = requests.post(url, data=datas)
try:
      # response = requests.post(url, data=datas, headers=headers)
      response = requests.post(test_url, data=datas)
      print("Journal Push Data receiving......")
      j = json.loads(response.text)
            # j = response.text
      print("Jounral Recieve data: %s" % j)

except requests.ConnectionError as e:
      raise print("Connection failure : %s" % str(e))

