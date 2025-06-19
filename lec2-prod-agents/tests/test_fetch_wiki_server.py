import requests
import json

# Base URL for the server (assumes it's running on localhost:8000)
BASE_URL = "http://localhost:8000"

def test_root_endpoint():
    """Test the root endpoint."""
    print("=== Testing Root Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_search_endpoint():
    """Test searching for Wikipedia articles."""
    print("=== Testing Search Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/search", params={"query": "python", "limit": 5})
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Query: {data['query']}")
        print(f"Results count: {data['count']}")
        print(f"Results: {data['results']}")
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_article_endpoint():
    """Test getting an article as markdown."""
    print("=== Testing Article Endpoint (Markdown) ===")
    try:
        response = requests.get(f"{BASE_URL}/article", params={"title": "Python (programming language)"})
        print(f"Status: {response.status_code}")
        content = response.text
        print(f"Content length: {len(content)} characters")
        print("First 200 characters:")
        print(content[:200] + "..." if len(content) > 200 else content)
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_article_summary():
    """Test getting article (now only full articles available)."""
    print("=== Testing Article Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/article", params={"title": "FastAPI"})
        print(f"Status: {response.status_code}")
        content = response.text
        print(f"Article length: {len(content)} characters")
        print("First 300 characters:")
        print(content[:300] + "..." if len(content) > 300 else content)
    except Exception as e:
        print(f"Error: {e}")
    print()



def test_nonexistent_article():
    """Test handling of non-existent article."""
    print("=== Testing Non-existent Article ===")
    try:
        response = requests.get(f"{BASE_URL}/article", params={"title": "ThisArticleDoesNotExist12345"})
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_disambiguation():
    """Test disambiguation handling."""
    print("=== Testing Disambiguation (Mercury) ===")
    try:
        response = requests.get(f"{BASE_URL}/article", params={"title": "Mercury"})
        print(f"Status: {response.status_code}")
        if response.status_code == 400:
            data = response.json()
            print("Disambiguation detected!")
            print(f"Suggestions: {data['detail']['suggestions'][:5]}")
        elif response.status_code == 200:
            print("Found specific Mercury article")
            content = response.text
            print(f"Content length: {len(content)} characters")
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_full_article_markdown():
    """Test fetching a complete article as one big markdown document."""
    print("=== Testing Full Article as Markdown ===")
    try:
        response = requests.get(f"{BASE_URL}/article", params={"title": "Python (programming language)"})
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            print(f"Full article length: {len(content)} characters")
            print(f"Number of lines: {len(content.splitlines())}")
            
            # Show structure by finding headers
            lines = content.splitlines()
            headers = [line for line in lines if line.startswith('#')]
            print(f"Found {len(headers)} headers:")
            for i, header in enumerate(headers[:10]):  # Show first 10 headers
                print(f"  {i+1}. {header}")
            if len(headers) > 10:
                print(f"  ... and {len(headers) - 10} more headers")
            
            print("\nFirst 300 characters:")
            print(content[:300] + "...")
            
            print("\nLast 200 characters:")
            print("..." + content[-200:])
            
        else:
            print(f"Error response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_full_workflow():
    """Test complete workflow: search then get article."""
    print("=== Testing Full Workflow ===")
    try:
        # Search first
        print("1. Searching for 'artificial intelligence'...")
        search_response = requests.get(f"{BASE_URL}/search", 
                                     params={"query": "artificial intelligence", "limit": 3})
        print(f"Search status: {search_response.status_code}")
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            print(f"Found {search_data['count']} results")
            
            if search_data['results']:
                first_result = search_data['results'][0]
                print(f"2. Getting article for: {first_result}")
                
                article_response = requests.get(f"{BASE_URL}/article", 
                                              params={"title": first_result})
                print(f"Article status: {article_response.status_code}")
                
                if article_response.status_code == 200:
                    content = article_response.text
                    print(f"Article summary length: {len(content)} characters")
                    print("First 150 characters:")
                    print(content[:150] + "...")
    except Exception as e:
        print(f"Error: {e}")
    print()

if __name__ == "__main__":
    print("Wikipedia FastAPI Server Test Demo")
    print("=" * 40)
    print("Make sure the server is running on http://localhost:8000")
    print("=" * 40)
    print()
    
    test_root_endpoint()
    test_search_endpoint()
    test_article_endpoint()
    test_article_summary()
    test_full_article_markdown()
    test_nonexistent_article()
    test_disambiguation()
    test_full_workflow()
    
    print("Demo completed!")
