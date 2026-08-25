import requests

response = requests.get("https://jsonplaceholder.typicode.com/todos/1")

print("Status Code:")
print(response.status_code)

print()

print("Headers:")
print(response.headers)