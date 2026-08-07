import requests

# ======================================
# CONFIGURATION
# ======================================

API_URL = "http://127.0.0.1:8000/agent/resume_builder"

API_KEY = "sk_agent_72a6a8a722760b271e386586ef94cff284817d89035fe1f2"

# ======================================
# REQUEST HEADERS
# ======================================

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# ======================================
# USER MESSAGE
# ======================================

data = {
    "message": "Build a Resume for me"
}

# ======================================
# SEND REQUEST
# ======================================

response = requests.post(
    API_URL,
    headers=headers,
    json=data
)

# ======================================
# PRINT RESPONSE
# ======================================

print("Status Code:", response.status_code)
print("Response:\n")

print(response.json())