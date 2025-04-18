from flask import Flask, render_template_string, request, jsonify
import requests
from datetime import datetime
import os
import re
from functools import wraps
from dotenv import load_dotenv

app = Flask(__name__)
API_KEYS = os.getenv('API_KEYS',).split(',')
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')
RAPIDAPI_HOST = os.getenv('RAPIDAPI_HOST')
BASE_URL = os.getenv('BASE_URL')

def get_headers():
    return {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }


HOME_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Sneaker API Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        code { background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }
        .endpoint { margin: 20px 0; padding: 20px; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <h1>Sneaker API Documentation</h1>
    <div class="endpoint">
        <h2>Single Page Search</h2>
        <p>Endpoint: <code>/api/search</code></p>
        <p>Method: <code>GET</code></p>
        <p>Parameters:</p>
        <ul>
            <li><code>token</code> (required): Your API token</li>
            <li><code>query</code> (required): Search term</li>
            <li><code>page</code> (optional): Page number (default: 1)</li>
            <li><code>limit</code> (optional): Results per page (default: 100)</li>
        </ul>
        <p>Example:</p>
        <code>GET /api/search?token=your-secret-key-123&query=nike&page=1&limit=100</code>
    </div>
    <div class="endpoint">
        <h2>All Pages Search</h2>
        <p>Endpoint: <code>/api/search/all</code></p>
        <p>Method: <code>GET</code></p>
        <p>Parameters:</p>
        <ul>
            <li><code>token</code> (required): Your API token</li>
            <li><code>query</code> (required): Search term</li>
        </ul>
        <p>Example:</p>
        <code>GET /api/search/all?token=your-secret-key-123&query=nike</code>
    </div>
</body>
</html>
'''


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.args.get('token')
        if token is None or token not in API_KEYS:
            return jsonify({"error": "Invalid or missing API token"}), 401
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def home():
    return render_template_string(HOME_TEMPLATE)

@app.route('/api/search', methods=['GET'])
@require_api_key
def search_shoes():
    # Get parameters from request
    query = request.args.get('query', '')
    page = request.args.get('page', '1')
    limit = request.args.get('limit', '100')
    
    # Prepare query parameters
    params = {
        "query": query,
        "page": page,
        "limit": limit
    }
    
    try:
        # Make request to RapidAPI
        response = requests.get(
            BASE_URL,
            headers=get_headers(),
            params=params
        )
        
        # Return the response
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search/all', methods=['GET'])
@require_api_key
def search_all_pages():
    query = request.args.get('query', '')
    # save_file = request.args.get('save', 'false').lower() == 'true'
    
    all_results = []
    
    try:
        # Get first page
        response = requests.get(
            BASE_URL,
            headers=get_headers(),
            params={"query": query, "limit": "100", "page": "1"}
        )
        
        if response.status_code == 200:
            data = response.json()
            all_results.extend(data['results'])
            total_pages = data['totalPages']
            
            # Get remaining pages
            for page in range(2, total_pages + 1):
                response = requests.get(
                    BASE_URL,
                    headers=get_headers(),
                    params={"query": query, "limit": "100", "page": str(page)}
                )
                if response.status_code == 200:
                    page_data = response.json()
                    all_results.extend(page_data['results'])
            
            result = {
                "shoe_name": query,
                "count": data['count'],
                "total_items": len(all_results),
                "results": all_results
            }
            
            # Save to file if requested
            # if save_file:
            #     os.makedirs('json', exist_ok=True)
            #     clean_name = re.sub(r'[^a-zA-Z0-9]', '_', query.lower())
            #     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            #     filename = os.path.join('json', f"{clean_name}_{timestamp}.json")
                
            #     with open(filename, 'w', encoding='utf-8') as f:
            #         import json
            #         json.dump(result, f, indent=4)
            #     result["saved_to"] = filename
            
            return jsonify(result)
            
        return jsonify({"error": "Failed to fetch data"}), response.status_code
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)