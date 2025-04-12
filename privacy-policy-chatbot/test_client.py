import requests
import json

url = "http://127.0.0.1:5000/generate-policy"
payload = {
  "company_name": "My Test App",
  "website_url": "https://test.com",
  "data_collected": "Emails, Names",
  "data_usage": "Sending newsletters",
  "contact_email": "privacy@test.com",
  # Add other required fields
  "data_sharing": "None",
  "security_measures": "Standard",
  "user_rights": "Access, Deletion",
  "cookie_usage": "Only essential"
}
headers = {'Content-Type': 'application/json'}

response = requests.post(url, headers=headers, data=json.dumps(payload))

print(response.status_code)
print(response.json())