#!/usr/bin/env python3
import json
import re

def process_openapi_file():
    # Read the OpenAPI file
    with open('openapi.json', 'r') as f:
        data = json.load(f)
    
    # Process each path and method
    for path, path_item in data['paths'].items():
        for method, operation in path_item.items():
            if method in ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']:
                # Add security if not present
                if 'security' not in operation:
                    operation['security'] = [{"ApiKeyAuth": []}]
                
                # Remove Authorization header parameters
                if 'parameters' in operation:
                    # Filter out Authorization parameters
                    operation['parameters'] = [
                        param for param in operation['parameters'] 
                        if param.get('name') != 'Authorization'
                    ]
                    
                    # Remove parameters array if empty
                    if not operation['parameters']:
                        del operation['parameters']
    
    # Write the updated file
    with open('openapi.json', 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    process_openapi_file()
    print("OpenAPI file processed successfully!") 