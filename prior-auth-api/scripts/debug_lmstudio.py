import httpx
import json

try:
    with httpx.Client() as client:
        response = client.post(
            "http://127.0.0.1:1234/v1/chat/completions",
            json={
                "model": "qwen/qwen3-4b-2507",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello"}
                ],
                "temperature": 0.0
            }
        )
        print("Status Code:", response.status_code)
        print("Response:", response.text)
except Exception as e:
    print("Error:", e)
