import requests

r = requests.post(
    'https://api.deepseek.com/chat/completions',
    headers={
        'Authorization': 'Bearer sk-4afce7cdf54c482abe7285400c13fffd',
        'Content-Type': 'application/json'
    },
    json={
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': 'hello'}],
        'max_tokens': 10
    }
)
print(f"Status: {r.status_code}")
print(f"Response: {r.text}")
