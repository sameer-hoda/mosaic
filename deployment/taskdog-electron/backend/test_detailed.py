import requests
import json

# Test the TaskDog backend API in more detail
API_BASE_URL = 'http://localhost:3001'

def test_detailed_api():
    print("Testing TaskDog backend API in detail...")
    
    # Test the tasks endpoint and print the full response
    try:
        response = requests.get(f'{API_BASE_URL}/api/tasks')
        print(f"Tasks endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Full response: {json.dumps(data, indent=2)}")
        else:
            print(f"Tasks endpoint failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Tasks endpoint failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_detailed_api()