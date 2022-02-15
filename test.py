import requests
import json

# url = "http://127.0.0.1:7092/api/auth/token"
# url = "http://51.145.48.170/api/auth/token"
# # headers = {
# #     "login": "admin",
# #     "password": "admin",
# #     "db": "excite091221",
# #     "content-type": "application/jsonp"
# # }
# headers = {
#     "login": "admin",
#     "password": "banner123",
#     "db": "fhfl_live",
#     "content-type": "application/jsonp"
# }
# response = requests.get(url, headers=headers)

# print(response)
# print(json.loads(response.content))
# print(content)


# headers = {
#         # 'content-type': 'application/x-www-form-urlencoded',
#         # 'charset':'utf-8'
#         "content-type": "application/jsonp"
#     }

# # data = {
# #         'login': 'admin',
# #         'password': 'admin',
# #         'db': 'excite091221'
# #     }
# data = {
#         'login': 'admin',
#         'password': 'banner123',
#         'db': 'fhfl_live'
#     }
# base_url = 'http://51.145.48.170'

# req = requests.get('{}/api/auth/token'.format(base_url), data=data, headers=headers)

# content = json.loads(req.content.decode('utf-8'))
# print(f'Content: {content}')

# headers['access-token'] = content.get('access_token') # add the access token to the header
# print(headers)



url = 'http://51.145.48.170/api/sale.order/create'
order_line = "http://51.145.48.170/api/sale.order.line/create"

headers = {
	'Api-Key': 'KDWPBOHDF96H1H4MXLFD7M211SDGIHST',
	# "content-type": "application/json"
	# 'content-type': 'application/x-www-form-urlencoded',
	# 'charset':'utf-8'
}
data = {
	'partner_id': 3,
	'sales_type': 'installment',
	
}

# url = "http://127.0.0.1:7092/api/sale.order/create"
# headers = {
# 	'api_key': 'DI6MHCUIGIBC0O7AOL0BVS4LKPEWRNF9',
# 	# "content-type": "application/json"
# 	# 'content-type': 'application/x-www-form-urlencoded',
# 	# 'charset':'utf-8'
# }
# (0, 0,  {'product_id': 16, 'name': 'Test', 'product_uom_qty': 2, 'price_unit':2000})
# data = {
# 	'partner_id': 48,
# 	'sales_type': 'installment',
# 	# 'order_line': [(0, 0,  {'product_id': 37, 'price_unit':4000}),
# 	# 				(0, 0,  {'product_id': 37, 'price_unit':2000})
# 	# 				]
# }

# data = {
# 	'name': 'Mr Sam',
# 	'email': 'sam@gmail.com'
# }
# data = {
# 	'name': 'Invest 5',
# 	'customer': 14,
# 	'company_name': 'Test Company',
# 	'application_id': 'inv5'
# }
datas = json.dumps(data)


req = requests.post(url, data=datas, headers=headers)

print("Posting")
print(req.text)


j = json.loads(req.text)
order_id = j['create_id']

print(f"Order id: {order_id}")

# order_line = "http://127.0.0.1:7092/api/sale.order.line/create"

# line = {'order_id':order_id, 'product_id': 37, 'price_unit':2500}
line = {'order_id':order_id, 'product_id': 2, 'price_unit':2500}

lines = json.dumps(line)


req_line = requests.post(order_line, data=lines, headers=headers)

print("Posting Lines")
print(req_line.text)