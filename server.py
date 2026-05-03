"""
SmartBudget AI Web Server
Serves the HTML dashboard and provides API endpoints to run the pipeline
"""

import json
import subprocess
import threading
import time
import sys
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import os


class SmartBudgetHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for SmartBudget AI"""

    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        normalized_path = parsed_path.path.rstrip('/') or '/'
        
        # API endpoint to run the pipeline
        if normalized_path == '/api/run-pipeline':
            self.handle_run_pipeline()
        # API endpoint to get latest results
        elif normalized_path == '/api/latest-results':
            self.handle_latest_results()
        # API health endpoint
        elif normalized_path == '/api/health':
            self.handle_health()
        # Serve dashboard HTML
        elif normalized_path == '/' or normalized_path == '/dashboard.html':
            self.serve_dashboard()
        else:
            super().do_GET()

    def handle_health(self):
        """Health check endpoint for frontend connectivity tests"""
        payload = {
            "status": "ok",
            "service": "smartbudget-api",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def handle_run_pipeline(self):
        """Run the SmartBudget pipeline and return status"""
        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "status": "running",
                "message": "Pipeline execution started...",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.wfile.write(json.dumps(response).encode())
            
            # Run the pipeline in background
            threading.Thread(target=self._execute_pipeline, daemon=True).start()
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _execute_pipeline(self):
        """Execute main.py in subprocess"""
        try:
            venv_python = Path(__file__).parent / "venv" / "Scripts" / "python.exe"
            python_cmd = str(venv_python) if venv_python.exists() else sys.executable
            
            subprocess.run(
                [python_cmd, "main.py"],
                cwd=Path(__file__).parent,
                capture_output=False,
                timeout=300  # 5 minute timeout
            )
            print("✅ Pipeline execution complete!")
        except subprocess.TimeoutExpired:
            print("⏱️ Pipeline execution timeout!")
        except Exception as e:
            print(f"❌ Pipeline error: {e}")

    def handle_latest_results(self):
        """Return the latest results from logs"""
        try:
            # Read and parse JSONL file
            results = {
                "agents": {
                    "collector": "",
                    "categorizer": "",
                    "analyst": "",
                    "reporter": ""
                },
                "timestamp": None
            }

            logs_dir = Path(__file__).parent / "logs"
            logs_candidates = [
                logs_dir / "agent_logs.jsonl",
                logs_dir / "agent_logs.json",
            ]
            logs_file = next((p for p in logs_candidates if p.exists()), None)
            
            recent_by_agent = {}
            if logs_file:
                with open(logs_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                entry = json.loads(line)
                                agent_name = entry.get('agent', '')
                                if agent_name:
                                    recent_by_agent[agent_name] = entry
                            except json.JSONDecodeError:
                                pass
            
            # Map agent names to output
            if "DataCollectorAgent" in recent_by_agent:
                results["agents"]["collector"] = recent_by_agent["DataCollectorAgent"].get("output", "")
            if "CategorizerAgent" in recent_by_agent:
                results["agents"]["categorizer"] = recent_by_agent["CategorizerAgent"].get("output", "")
            if "AnalystAgent" in recent_by_agent:
                results["agents"]["analyst"] = recent_by_agent["AnalystAgent"].get("output", "")
            if "ReporterAgent" in recent_by_agent:
                results["agents"]["reporter"] = recent_by_agent["ReporterAgent"].get("output", "")
            
            # Get the latest report
            reports_dir = Path(__file__).parent / "reports"
            if reports_dir.exists():
                reports = sorted(reports_dir.glob("budget_report_*.md"), reverse=True)
                if reports:
                    with open(reports[0], 'r') as f:
                        results["report_content"] = f.read()
                    results["report_file"] = reports[0].name
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(results, indent=2).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def serve_dashboard(self):
        """Serve the dashboard HTML"""
        try:
            dashboard_path = Path(__file__).parent / "dashboard.html"
            
            if not dashboard_path.exists():
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"Dashboard not found")
                return
            
            with open(dashboard_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"Error: {e}".encode())

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass  # Comment out to see HTTP logs


def run_server(port=8080):
    """Start the SmartBudget AI web server"""
    os.chdir(Path(__file__).parent)
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, SmartBudgetHandler)
    
    print("\n" + "="*60)
    print("   SmartBudget AI — Web Server")
    print("="*60)
    print(f"\n🌐 Server running at: http://localhost:{port}")
    print(f"📊 Dashboard: http://localhost:{port}/dashboard.html")
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
        httpd.server_close()


if __name__ == "__main__":
    run_server(port=8080)
