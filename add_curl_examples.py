#!/usr/bin/env python3
"""
Script to add curl examples to all endpoints in the OpenAPI specification.
This script will analyze each endpoint and add appropriate curl examples.
"""

import json
import re
from typing import Dict, Any, List, Optional

def generate_curl_example(path: str, method: str, operation: Dict[str, Any]) -> str:
    """Generate a curl example for a given endpoint."""
    base_url = "https://api.accredible.com"
    full_url = f"{base_url}{path}"
    
    # Handle path parameters
    if "{" in path:
        # Replace path parameters with example values
        path_params = re.findall(r'\{([^}]+)\}', path)
        for param in path_params:
            if "id" in param.lower():
                full_url = full_url.replace(f"{{{param}}}", "12345")
            elif "slug" in param.lower():
                full_url = full_url.replace(f"{{{param}}}", "example-slug")
            else:
                full_url = full_url.replace(f"{{{param}}}", "example")
    
    # Build curl command
    curl_parts = [f"curl -X {method.upper()}"]
    curl_parts.append(f'  "{full_url}"')
    curl_parts.append('  -H "Authorization: Token token=YOUR_API_KEY"')
    
    # Add request body for POST/PUT/PATCH methods
    if method.upper() in ['POST', 'PUT', 'PATCH']:
        curl_parts.append('  -H "Content-Type: application/json"')
        
        # Get request body schema
        request_body = operation.get('requestBody', {})
        if request_body:
            content = request_body.get('content', {})
            json_content = content.get('application/json', {})
            
            # Use existing example if available
            if 'example' in json_content:
                example_data = json_content['example']
            elif 'schema' in json_content:
                # Generate example data from schema
                example_data = generate_example_from_schema(json_content['schema'])
            else:
                example_data = {}
            
            if example_data:
                # Convert to JSON string and escape for shell
                json_str = json.dumps(example_data, indent=2)
                # Escape single quotes for shell
                json_str = json_str.replace("'", "'\"'\"'")
                
                curl_parts.append(f"  -d '{json_str}'")
            else:
                # Fallback minimal JSON
                curl_parts.append("  -d '{}'")
        else:
            # No request body schema, use empty JSON
            curl_parts.append("  -d '{}'")
    
    return " \\\n".join(curl_parts)

def generate_example_from_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Generate example data from a JSON schema."""
    if not schema:
        return {}
    
    # Handle different schema types
    schema_type = schema.get('type')
    properties = schema.get('properties', {})
    
    if schema_type == 'object' and properties:
        example = {}
        for prop_name, prop_schema in properties.items():
            prop_type = prop_schema.get('type')
            
            if prop_type == 'string':
                if 'email' in prop_name.lower():
                    example[prop_name] = "person@example.com"
                elif 'name' in prop_name.lower():
                    example[prop_name] = "John Doe"
                elif 'description' in prop_name.lower():
                    example[prop_name] = "Example description"
                else:
                    example[prop_name] = "example"
            elif prop_type == 'integer':
                example[prop_name] = 12345
            elif prop_type == 'number':
                example[prop_name] = 123.45
            elif prop_type == 'boolean':
                example[prop_name] = True
            elif prop_type == 'array':
                items_schema = prop_schema.get('items', {})
                if items_schema.get('type') == 'object':
                    example[prop_name] = [generate_example_from_schema(items_schema)]
                else:
                    example[prop_name] = [1, 2, 3]
            elif prop_type == 'object':
                example[prop_name] = generate_example_from_schema(prop_schema)
            else:
                example[prop_name] = None
        
        return example
    elif schema_type == 'array':
        items_schema = schema.get('items', {})
        return [generate_example_from_schema(items_schema)]
    else:
        return {}

def add_curl_examples_to_openapi(openapi_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add curl examples to all endpoints in the OpenAPI specification."""
    paths = openapi_data.get('paths', {})
    
    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if method.lower() in ['get', 'post', 'put', 'patch', 'delete']:
                # Check if curl example already exists
                if 'x-code-samples' not in operation or not isinstance(operation['x-code-samples'], list):
                    operation['x-code-samples'] = []
                
                # Check if a cURL sample already exists in the array
                has_curl = any(
                    sample.get('lang', '').lower() == 'curl' 
                    for sample in operation['x-code-samples']
                )
                
                if not has_curl:
                    curl_example = generate_curl_example(path, method, operation)
                    operation['x-code-samples'].append({
                        "lang": "curl",
                        "label": "cURL",
                        "source": curl_example
                    })
    
    return openapi_data

def main():
    """Main function to process the OpenAPI file."""
    try:
        # Read the OpenAPI file
        with open('openapi.json', 'r', encoding='utf-8') as f:
            openapi_data = json.load(f)
        
        # Add curl examples
        updated_openapi = add_curl_examples_to_openapi(openapi_data)
        
        # Write back to file
        with open('openapi.json', 'w', encoding='utf-8') as f:
            json.dump(updated_openapi, f, indent=2, ensure_ascii=False)
        
        print("Successfully added curl examples to all endpoints!")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 