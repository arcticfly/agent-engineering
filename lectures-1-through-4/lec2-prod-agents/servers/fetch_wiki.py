from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse
import requests
import re
from typing import Dict, Any
from markdownify import markdownify # type: ignore
from bs4 import BeautifulSoup

app = FastAPI(title="Wikipedia Search API", version="1.0.0")

# Wikipedia API endpoints
WIKI_API_BASE = "https://en.wikipedia.org/api/rest_v1"
WIKI_SEARCH_API = "https://en.wikipedia.org/w/api.php"

def clean_html(html_content: str) -> str:
    """Clean Wikipedia HTML before converting to markdown."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted elements
    for element in soup.find_all(['script', 'style', 'sup', 'table', 'div']):
        # Keep div content but remove the div wrapper if it has text
        if element.name == 'div' and element.get_text(strip=True):
            element.unwrap()
        else:
            element.decompose()
    
    # Remove all CSS classes and inline styles
    for tag in soup.find_all(True):
        tag.attrs = {k: v for k, v in tag.attrs.items() if k not in ['class', 'style', 'id']}
    
    # Remove reference links like [1], [2], etc.
    for link in soup.find_all('a'):
        if link.get_text(strip=True).startswith('[') and link.get_text(strip=True).endswith(']'):
            link.decompose()
    
    return str(soup)

def clean_content(content: str) -> str:
    """Clean Wikipedia content for markdown formatting."""
    # Remove citation markers like [1], [2], etc.
    content = re.sub(r'\[\d+\]', '', content)
    # Convert &nbsp; to space
    content = re.sub(r'&nbsp;', ' ', content)
    # Clean up extra spaces (but preserve newlines)
    content = re.sub(r'[ \t]+', ' ', content)  # Only collapse spaces and tabs
    # Clean up multiple newlines (3+ becomes 2)
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in content.split('\n')]
    # Rejoin and clean up empty lines
    content = '\n'.join(lines)
    # Clean up multiple consecutive newlines again
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
    return content.strip()

def search_wikipedia(query: str, limit: int = 10) -> Dict[str, Any]:
    """Search Wikipedia using the API."""
    params = {
        'action': 'query',
        'format': 'json',
        'list': 'search',
        'srsearch': query,
        'srlimit': limit
    }
    
    response = requests.get(WIKI_SEARCH_API, params=params)
    response.raise_for_status()
    data = response.json()
    
    if 'query' in data and 'search' in data['query']:
        results = [item['title'] for item in data['query']['search']]
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    return {"query": query, "results": [], "count": 0}

def get_page_content(title: str) -> str:
    """Get full Wikipedia page content using the parse API and convert to markdown."""
    # Use parse API to get HTML content
    parse_params = {
        'action': 'parse',
        'format': 'json',
        'page': title,
        'prop': 'text',
        'redirects': True,
        'disableeditsection': True,  # Remove edit section links
        'disabletoc': True  # Remove table of contents
    }
    
    parse_response = requests.get(WIKI_SEARCH_API, params=parse_params)
    parse_response.raise_for_status()
    parse_data = parse_response.json()
    
    # Check if page exists
    if 'error' in parse_data:
        error_code = parse_data['error'].get('code', '')
        if error_code == 'missingtitle':
            raise HTTPException(status_code=404, detail=f"No Wikipedia page found for '{title}'")
        else:
            raise HTTPException(status_code=500, detail=f"Error fetching page: {parse_data['error'].get('info', 'Unknown error')}")
    
    # Get the HTML content
    if 'parse' not in parse_data:
        raise HTTPException(status_code=404, detail=f"No content found for '{title}'")
    
    parse_info = parse_data['parse']
    html_content = parse_info.get('text', {}).get('*', '')
    actual_title = parse_info.get('title', title)
    
    if not html_content:
        raise HTTPException(status_code=404, detail=f"No content available for '{title}'")
    
    # Clean the HTML first to remove Wikipedia-specific markup
    cleaned_html = clean_html(html_content)
    
    # Convert HTML to markdown using markdownify
    markdown_content = markdownify(
        cleaned_html,
        heading_style="ATX",  # Use # for headers
        bullets="-",  # Use - for bullets
        strip=['script', 'style', 'sup', 'table']  # Remove unwanted tags
    )
    
    # Clean up the markdown
    cleaned_content = clean_content(markdown_content)
    
    # Add title and return
    final_content = f"# {actual_title}\n\n{cleaned_content}"
    
    return final_content



@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Wikipedia Search API - Simplified",
        "endpoints": {
            "/search": "Search for Wikipedia articles",
            "/article": "Get full article content as markdown"
        }
    }

@app.get("/search")
async def search_endpoint(
    query: str = Query(..., description="Search query for Wikipedia"),
    limit: int = Query(default=10, ge=1, le=20, description="Number of results to return")
):
    """Search Wikipedia and return a list of matching article titles."""
    try:
        return search_wikipedia(query, limit)
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/article", response_class=PlainTextResponse)
async def get_article(
    title: str = Query(..., description="Wikipedia article title")
):
    """Get full Wikipedia article content as markdown."""
    try:
        return get_page_content(title)
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch article: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch article: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
