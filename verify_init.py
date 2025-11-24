import urllib.request
import urllib.parse
import json

base_url = "http://localhost:8000/api"
project_path = "/Users/gravity/Desktop/合同法制审核工作总结"

print(f"Testing init for: {project_path}")

# 1. Call /api/init
try:
    params = urllib.parse.urlencode({"project_path": project_path})
    url = f"{base_url}/init?{params}"
    req = urllib.request.Request(url, method="POST")
    
    with urllib.request.urlopen(req) as response:
        print(f"POST /api/init status: {response.status}")
        print(f"Response: {response.read().decode('utf-8')}")
    
except Exception as e:
    print(f"Request failed: {e}")

# 2. Check status
try:
    params = urllib.parse.urlencode({"project_path": project_path})
    url = f"{base_url}/status?{params}"
    
    with urllib.request.urlopen(url) as response:
        print(f"GET /api/status status: {response.status}")
        # print(f"Response: {response.read().decode('utf-8')}")
except Exception as e:
    print(f"Status check failed: {e}")
