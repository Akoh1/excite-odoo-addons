import requests
import json



# url = 'http://51.145.48.170/api/sale.order/create'
# order_line = "http://51.145.48.170/api/sale.order.line/create"

# headers = {
# 	'Api-Key': 'KDWPBOHDF96H1H4MXLFD7M211SDGIHST',
# 	# "content-type": "application/json"
# 	# 'content-type': 'application/x-www-form-urlencoded',
# 	# 'charset':'utf-8'
# }
# data = {
# 	'partner_id': 3,
# 	'sales_type': 'installment',
	
# }

# url = "http://127.0.0.1:7092/api/sale.order/create"
url = "http://127.0.0.1:7092/api/crm.investment/%d" % 4
headers = {
	'api_key': 'ZXPRRR4BOUZA3G299GYY3I4IEEFV0VTD',
	# "content-type": "application/json"
	# 'content-type': 'application/x-www-form-urlencoded',
	# 'charset':'utf-8'
}
# (0, 0,  {'product_id': 16, 'name': 'Test', 'product_uom_qty': 2, 'price_unit':2000})
# data = {
# 	'partner_id': 48,
# 	'sales_type': 'installment',
# 	# 'order_line': [(0, 0,  {'product_id': 37, 'price_unit':4000}),
# 	# 				(0, 0,  {'product_id': 37, 'price_unit':2000})
# 	# 				]
# }

data = {
	'company_name': 'Alexix LTD'
}
# data = {
# 	'name': 'Invest 5',
# 	'customer': 14,
# 	'company_name': 'Test Company',
# 	'application_id': 'inv5'
# }
datas = json.dumps(data)

req = requests.put(url, data=datas, headers=headers)

print("Posting")
print(req.text)


# j = json.loads(req.text)
# order_id = j['create_id']

# print(f"Order id: {order_id}")

# # order_line = "http://127.0.0.1:7092/api/sale.order.line/create"

# # line = {'order_id':order_id, 'product_id': 37, 'price_unit':2500}
# line = {'order_id':order_id, 'product_id': 2, 'price_unit':2500}

# lines = json.dumps(line)


# req_line = requests.post(order_line, data=lines, headers=headers)

# print("Posting Lines")
# print(req_line.text)