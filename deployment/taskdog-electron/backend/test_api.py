import requests
import json

# Test the TaskDog backend API
API_BASE_URL = 'http://localhost:3001'

def test_api():
    print("Testing TaskDog backend API...")
    
    # Test the health endpoint
    try:
        response = requests.get(f'{API_BASE_URL}/health')
        print(f"Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
    
    # Test the tasks endpoint
    try:
        response = requests.get(f'{API_BASE_URL}/api/tasks')
        if response.status_code == 200:
            data = response.json()
            print(f"Tasks endpoint: {response.status_code} - Got {len(data['tasks'])} tasks")
            print(f"Stats: {data['stats']}")
        else:
            print(f"Tasks endpoint failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Tasks endpoint failed: {e}")

if __name__ == "__main__":
    test_api()