#!/usr/bin/env python3
"""
Backend proxy server for City Brain frontend to call Modal functions.
This server acts as a bridge between the frontend and Modal.
"""

import os
import json
import subprocess
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Modal configuration
MODAL_APP_NAME = "city-brain-urban-planning"
MODAL_FUNCTION = "get_scenario_insights"

# Get the frontend directory
FRONTEND_DIR = Path(__file__).parent

@app.route('/')
def index():
    """Serve the main HTML file."""
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, etc.)."""
    return send_from_directory(FRONTEND_DIR, filename)

@app.route('/api/modal/status', methods=['GET'])
def check_modal_status():
    """Check if Modal app is deployed and accessible."""
    try:
        # Check if Modal CLI is available
        result = subprocess.run(['modal', '--version'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return jsonify({
                'status': 'error',
                'message': 'Modal CLI not available',
                'details': result.stderr
            }), 500
        
        # Check if our app is deployed
        result = subprocess.run(['modal', 'app', 'list'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return jsonify({
                'status': 'error',
                'message': 'Failed to list Modal apps',
                'details': result.stderr
            }), 500
        
        # Check if our app is in the list
        if MODAL_APP_NAME in result.stdout:
            return jsonify({
                'status': 'success',
                'message': f'Modal app {MODAL_APP_NAME} is deployed',
                'modal_version': result.stdout.strip()
            })
        else:
            return jsonify({
                'status': 'warning',
                'message': f'Modal app {MODAL_APP_NAME} not found',
                'available_apps': result.stdout.strip()
            })
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'status': 'error',
            'message': 'Modal CLI command timed out'
        }), 500
    except FileNotFoundError:
        return jsonify({
            'status': 'error',
            'message': 'Modal CLI not installed. Install with: pip install modal'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}'
        }), 500

@app.route('/api/modal', methods=['POST'])
def call_modal_function():
    """Call a Modal function and return the result."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        query = data.get('query')
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        logger.info(f"Calling Modal function with query: {query}")
        
        # First check if Modal app is deployed
        status_result = check_modal_status_internal()
        if status_result.get('status') != 'success':
            return jsonify({
                'error': 'Modal app not properly deployed',
                'details': status_result
            }), 400
        
        # Call the Modal function
        result = call_modal_function_internal(query)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error calling Modal function: {e}")
        return jsonify({'error': str(e)}), 500

def check_modal_status_internal():
    """Internal function to check Modal status."""
    try:
        # Check if Modal CLI is available
        result = subprocess.run(['modal', '--version'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return {
                'status': 'error',
                'message': 'Modal CLI not available',
                'details': result.stderr
            }
        
        # Check if our app is deployed
        result = subprocess.run(['modal', 'app', 'list'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return {
                'status': 'error',
                'message': 'Failed to list Modal apps',
                'details': result.stderr
            }
        
        # Check if our app is in the list
        if MODAL_APP_NAME in result.stdout:
            return {
                'status': 'success',
                'message': f'Modal app {MODAL_APP_NAME} is deployed',
                'modal_version': result.stdout.strip()
            }
        else:
            return {
                'status': 'warning',
                'message': f'Modal app {MODAL_APP_NAME} not found',
                'available_apps': result.stdout.strip()
            }
            
    except subprocess.TimeoutExpired:
        return {
            'status': 'error',
            'message': 'Modal CLI command timed out'
        }
    except FileNotFoundError:
        return {
            'status': 'error',
            'message': 'Modal CLI not installed. Install with: pip install modal'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Unexpected error: {str(e)}'
        }

def call_modal_function_internal(query):
    """Execute the Modal function call."""
    try:
        # Build the Modal command - use the file path to the function
        # The correct format is: modal run path/to/file.py::function_name
        cmd = [
            'modal', 'run', 
            '../../citybrain/modal_app.py::get_scenario_insights',
            '--user-query', query
        ]
        
        logger.info(f"Executing command: {' '.join(cmd)}")
        
        # Execute the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=FRONTEND_DIR  # Run from frontend directory
        )
        
        logger.info(f"Modal command return code: {result.returncode}")
        logger.info(f"Modal command stdout length: {len(result.stdout)}")
        logger.info(f"Modal command stderr length: {len(result.stderr)}")
        
        # Log the full output for debugging
        if result.stdout:
            logger.info(f"Modal command stdout (full): {result.stdout}")
        if result.stderr:
            logger.info(f"Modal command stderr (full): {result.stderr}")
        
        if result.returncode != 0:
            logger.error(f"Modal command failed with return code {result.returncode}")
            logger.error(f"Modal command failed: {result.stderr}")
            raise Exception(f"Modal command failed: {result.stderr}")
        
        # Parse the output
        try:
            # Check if stdout is empty or just whitespace
            if not result.stdout or result.stdout.strip() == "":
                logger.warning("Modal command returned empty stdout")
                return {
                    'status': 'warning',
                    'message': 'Modal function executed but returned no output',
                    'raw_output': '',
                    'stdout_empty': True
                }
            
            # Try to parse JSON from stdout directly
            logger.info(f"Attempting to parse JSON from stdout: {result.stdout[:200]}...")
            response_data = json.loads(result.stdout.strip())
            logger.info("Successfully parsed Modal response as JSON")
            logger.info(f"Response data keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dict'}")
            return response_data
            
        except json.JSONDecodeError as e:
            # If not JSON, attempt to extract JSON portion from stdout
            logger.warning(f"Modal response is not valid JSON on first parse: {e}")
            logger.warning(f"JSON parse error at line {e.lineno}, column {e.colno}")
            logger.warning(f"Raw output (first 500 chars): {result.stdout[:500]}")
            
            # Strategy 1: Find the first line that looks like JSON and parse from there
            try:
                lines = result.stdout.splitlines()
                json_start_idx = None
                for i, line in enumerate(lines):
                    if line.strip().startswith('{'):
                        json_start_idx = i
                        break
                
                if json_start_idx is not None:
                    candidate = '\n'.join(lines[json_start_idx:]).strip()
                    logger.info(f"Attempting to parse JSON starting from line {json_start_idx+1}")
                    try:
                        response_data = json.loads(candidate)
                        logger.info("Successfully parsed JSON from trimmed stdout")
                        return response_data
                    except json.JSONDecodeError as e2:
                        logger.warning(f"Trimmed JSON parse failed: {e2}")
                        # Strategy 2: Try progressive trimming from the bottom
                        for j in range(len(lines)-1, json_start_idx, -1):
                            candidate2 = '\n'.join(lines[json_start_idx:j]).strip()
                            if not candidate2:
                                continue
                            try:
                                response_data = json.loads(candidate2)
                                logger.info(f"Successfully parsed JSON using progressive trim ending at line {j}")
                                return response_data
                            except json.JSONDecodeError:
                                continue
                
                # Strategy 3: Find the last '{' and parse substring
                last_brace = result.stdout.rfind('{')
                if last_brace != -1:
                    candidate3 = result.stdout[last_brace:].strip()
                    logger.info("Attempting to parse JSON from last brace position")
                    try:
                        response_data = json.loads(candidate3)
                        logger.info("Successfully parsed JSON from last brace substring")
                        return response_data
                    except json.JSONDecodeError as e3:
                        logger.warning(f"Last-brace JSON parse failed: {e3}")
            except Exception as parse_debug_error:
                logger.warning(f"Advanced JSON extraction encountered an error: {parse_debug_error}")
            
            # Fall back to returning raw output with detailed error info
            logger.warning("Falling back to returning raw output; unable to parse JSON")
            return {
                'status': 'success',
                'raw_output': result.stdout.strip(),
                'message': 'Modal function executed successfully but response was not valid JSON',
                'parse_error': str(e),
                'stdout_length': len(result.stdout),
                'stdout_preview': result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout
            }
            
    except subprocess.TimeoutExpired:
        logger.error("Modal command timed out")
        raise Exception("Modal function execution timed out after 5 minutes")
    except Exception as e:
        logger.error(f"Error executing Modal command: {e}")
        raise e

@app.route('/api/modal/test', methods=['GET'])
def test_modal_connection():
    """Test the Modal connection with a simple query."""
    try:
        test_query = "What is urban planning?"
        logger.info("Testing Modal connection with simple query")
        
        result = call_modal_function_internal(test_query)
        
        return jsonify({
            'status': 'success',
            'message': 'Modal connection test successful',
            'test_query': test_query,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Modal connection test failed: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Modal connection test failed',
            'error': str(e)
        }), 500

@app.route('/api/modal/test-raw', methods=['GET'])
def test_modal_raw():
    """Test the Modal function and return the raw response for debugging."""
    try:
        test_query = "What is urban planning?"
        logger.info("Testing Modal function with raw output capture")
        
        # Call the Modal function
        result = call_modal_function_internal(test_query)
        
        # Return the raw result for debugging
        return jsonify({
            'status': 'success',
            'message': 'Modal function test completed',
            'test_query': test_query,
            'raw_result': result,
            'result_type': str(type(result)),
            'result_keys': list(result.keys()) if isinstance(result, dict) else 'Not a dict',
            'debug_info': {
                'has_llm_analysis': 'llm_analysis' in result if isinstance(result, dict) else False,
                'has_analysis': 'analysis' in result if isinstance(result, dict) else False,
                'has_raw_output': 'raw_output' in result if isinstance(result, dict) else False,
                'has_message': 'message' in result if isinstance(result, dict) else False
            }
        })
        
    except Exception as e:
        logger.error(f"Modal raw test failed: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Modal raw test failed',
            'error': str(e),
            'traceback': str(e)
        }), 500

@app.route('/api/modal/debug', methods=['GET'])
def debug_modal_setup():
    """Debug endpoint to show Modal setup and test basic commands."""
    try:
        debug_info = {
            'modal_app_name': MODAL_APP_NAME,
            'modal_function': MODAL_FUNCTION,
            'expected_command': f'modal run ../../citybrain/modal_app.py::get_scenario_insights --user-query "test"',
            'frontend_directory': str(FRONTEND_DIR),
            'files_available': [f.name for f in FRONTEND_DIR.iterdir() if f.is_file()],
            'modal_app_path': str(FRONTEND_DIR.parent / 'citybrain' / 'modal_app.py'),
            'modal_app_exists': (FRONTEND_DIR.parent / 'citybrain' / 'modal_app.py').exists()
        }
        
        # Test Modal CLI availability
        try:
            version_result = subprocess.run(['modal', '--version'], 
                                          capture_output=True, text=True, timeout=5)
            debug_info['modal_cli_available'] = version_result.returncode == 0
            debug_info['modal_version'] = version_result.stdout.strip() if version_result.returncode == 0 else version_result.stderr
        except Exception as e:
            debug_info['modal_cli_available'] = False
            debug_info['modal_cli_error'] = str(e)
        
        # Test app listing
        try:
            app_list_result = subprocess.run(['modal', 'app', 'list'], 
                                           capture_output=True, text=True, timeout=10)
            debug_info['app_list_success'] = app_list_result.returncode == 0
            debug_info['available_apps'] = app_list_result.stdout.strip() if app_list_result.returncode == 0 else app_list_result.stderr
            debug_info['our_app_found'] = MODAL_APP_NAME in app_list_result.stdout if app_list_result.returncode == 0 else False
        except Exception as e:
            debug_info['app_list_success'] = False
            debug_info['app_list_error'] = str(e)
        
        # Test the actual Modal command
        try:
            test_cmd = ['modal', 'run', '../../citybrain/modal_app.py::get_scenario_insights', '--user-query', 'test']
            test_result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=30, cwd=FRONTEND_DIR)
            debug_info['test_command_success'] = test_result.returncode == 0
            debug_info['test_command_output'] = test_result.stdout.strip()[:500] if test_result.returncode == 0 else test_result.stderr.strip()[:500]
        except Exception as e:
            debug_info['test_command_success'] = False
            debug_info['test_command_error'] = str(e)
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({
            'error': f'Debug endpoint failed: {str(e)}',
            'traceback': str(e)
        }), 500

@app.route('/api/modal/debug-response', methods=['GET'])
def debug_modal_response():
    """Debug endpoint to show the raw Modal response structure."""
    try:
        test_query = "What is urban planning?"
        logger.info("Testing Modal function to show response structure")
        
        # Call the Modal function
        result = call_modal_function_internal(test_query)
        
        # Return detailed debug info
        return jsonify({
            'status': 'success',
            'message': 'Modal response structure analysis',
            'test_query': test_query,
            'raw_result': result,
            'result_type': str(type(result)),
            'result_keys': list(result.keys()) if isinstance(result, dict) else 'Not a dict',
            'structure_analysis': {
                'has_llm_analysis': 'llm_analysis' in result if isinstance(result, dict) else False,
                'llm_analysis_keys': list(result.get('llm_analysis', {}).keys()) if isinstance(result, dict) and 'llm_analysis' in result else [],
                'has_scenario_packet': 'scenario_packet' in result if isinstance(result, dict) else False,
                'scenario_packet_keys': list(result.get('scenario_packet', {}).keys()) if isinstance(result, dict) and 'scenario_packet' in result else [],
                'has_status': 'status' in result if isinstance(result, dict) else False,
                'status_value': result.get('status') if isinstance(result, dict) else None,
                'has_timestamp': 'timestamp' in result if isinstance(result, dict) else False
            },
            'full_response_preview': str(result)[:1000] + "..." if len(str(result)) > 1000 else str(result)
        })
        
    except Exception as e:
        logger.error(f"Modal debug response failed: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Modal debug response failed',
            'error': str(e),
            'traceback': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'City Brain Backend Proxy',
        'modal_app': MODAL_APP_NAME
    })

if __name__ == '__main__':
    print("🏙️ City Brain Backend Proxy Server")
    print("=" * 40)
    print("This server acts as a bridge between the frontend and Modal")
    print("Make sure your Modal app is deployed before testing")
    print("-" * 40)
    
    # Check Modal status on startup
    try:
        result = subprocess.run(['modal', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✓ Modal CLI available: {result.stdout.strip()}")
        else:
            print("⚠️  Modal CLI not working properly")
    except Exception as e:
        print(f"⚠️  Modal CLI not available: {e}")
    
    print(f"🌐 Starting server on http://localhost:5001")
    print("💡 Frontend can now make API calls to /api/modal")
    print("🎨 Serving static files (CSS, JS) for beautiful UI")
    
    app.run(host='0.0.0.0', port=5001, debug=True) 