#!/usr/bin/env python3
"""
Simple HTTP server for testing the City Brain frontend locally.
Run this script to test the frontend before deploying.
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

# Get the directory where this script is located
FRONTEND_DIR = Path(__file__).parent
os.chdir(FRONTEND_DIR)

PORT = 8000

class CityBrainHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.end_headers()

def main():
    print("🏙️ City Brain Frontend Server")
    print("=" * 40)
    print(f"Serving frontend from: {FRONTEND_DIR}")
    print(f"Local URL: http://localhost:{PORT}")
    print(f"Press Ctrl+C to stop the server")
    print("-" * 40)
    
    try:
        with socketserver.TCPServer(("", PORT), CityBrainHandler) as httpd:
            print(f"✓ Server started successfully on port {PORT}")
            print(f"🌐 Open your browser and go to: http://localhost:{PORT}")
            print("💡 Try asking: 'If we pedestrianize Broadway from 14th to 34th in NYC, what zoning amendments would be required?'")
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {PORT} is already in use. Try a different port:")
            print(f"   python server.py --port {PORT + 1}")
        else:
            print(f"❌ Error starting server: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    # Check for custom port argument
    if len(sys.argv) > 1 and sys.argv[1] == "--port":
        try:
            PORT = int(sys.argv[2])
        except (IndexError, ValueError):
            print("Invalid port number. Using default port 8000")
    
    main() 