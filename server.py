#!/usr/bin/env python3
"""
NaniResumu Local Server:
Provides a local HTTP API (with CORS) and Web Dashboard for switching resumes in OpenResume.
Runs on http://127.0.0.1:4040
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" if (BASE_DIR / "data").exists() else BASE_DIR / "data.example"
BUILD_DIR = BASE_DIR / "build"
WEB_DIR = BASE_DIR / "web"
ENV_FILE = BASE_DIR / ".env"

PORT = 4040


class ResumeServerHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for open-resume.com and localhost
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # 1. API: List all available resumes
        if path == "/api/resumes":
            try:
                roles_path = DATA_DIR / "roles.json"
                with open(roles_path, "r", encoding="utf-8") as f:
                    roles = json.load(f)

                resumes_list = []
                for rk, rval in roles.items():
                    resumes_list.append({
                        "id": rk,
                        "name": rval.get("name", rk),
                        "projects_count": len(rval.get("projects", [])),
                        "has_work_exp": bool(rval.get("work_experiences", [])),
                        "themeColor": rval.get("settings", {}).get("themeColor", "#38bdf8")
                    })

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(resumes_list, indent=2).encode("utf-8"))
            except Exception as e:
                self.send_error(500, f"Error listing resumes: {e}")
            return

        # 2. API: Get specific resume JSON
        if path == "/api/resume":
            role = query.get("role", ["sqa"])[0]
            # Ensure build exists or build on the fly
            build_file = BUILD_DIR / f"{role}.json"
            if not build_file.exists():
                # Run builder on the fly
                from builder import load_env, load_json, build_role_resume
                try:
                    env_vars = load_env(ENV_FILE)
                    master_data = {
                        "profile": load_json(DATA_DIR / "profile.json"),
                        "education": load_json(DATA_DIR / "education.json"),
                        "work_experience": load_json(DATA_DIR / "work_experience.json"),
                        "skills": load_json(DATA_DIR / "skills.json"),
                        "projects": load_json(DATA_DIR / "projects.json"),
                        "certifications": load_json(DATA_DIR / "certifications.json"),
                        "roles": load_json(DATA_DIR / "roles.json")
                    }
                    state = build_role_resume(role, env_vars, master_data)
                    BUILD_DIR.mkdir(parents=True, exist_ok=True)
                    with open(build_file, "w", encoding="utf-8") as f:
                        json.dump(state, f, indent=2)
                except Exception as e:
                    self.send_error(404, f"Role '{role}' could not be built: {e}")
                    return

            try:
                with open(build_file, "r", encoding="utf-8") as f:
                    content = f.read()

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
            except Exception as e:
                self.send_error(500, f"Error reading resume '{role}': {e}")
            return

        # 3. Serve userscript or bookmarklet
        if path == "/openresume-switcher.user.js":
            user_script = WEB_DIR / "openresume-switcher.user.js"
            if user_script.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/javascript; charset=utf-8")
                self.end_headers()
                with open(user_script, "rb") as f:
                    self.wfile.write(f.read())
                return

        # 4. Serve index.html or static files
        if path in ("/", "/index.html"):
            index_file = WEB_DIR / "index.html"
            if index_file.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(index_file, "rb") as f:
                    self.wfile.write(f.read())
                return

        # Fallback 404
        self.send_error(404, "Not Found")

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == "/api/build":
            # Rebuild all resumes
            from builder import load_env, load_json, build_role_resume
            try:
                env_vars = load_env(ENV_FILE)
                master_data = {
                    "profile": load_json(DATA_DIR / "profile.json"),
                    "education": load_json(DATA_DIR / "education.json"),
                    "work_experience": load_json(DATA_DIR / "work_experience.json"),
                    "skills": load_json(DATA_DIR / "skills.json"),
                    "projects": load_json(DATA_DIR / "projects.json"),
                    "certifications": load_json(DATA_DIR / "certifications.json"),
                    "roles": load_json(DATA_DIR / "roles.json")
                }
                BUILD_DIR.mkdir(parents=True, exist_ok=True)
                built = []
                for rk in master_data["roles"].keys():
                    state = build_role_resume(rk, env_vars, master_data)
                    with open(BUILD_DIR / f"{rk}.json", "w", encoding="utf-8") as f:
                        json.dump(state, f, indent=2)
                    built.append(rk)

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "built": built}).encode("utf-8"))
            except Exception as e:
                self.send_error(500, f"Build error: {e}")
            return

        self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        # Clean custom logging
        print(f"[{self.log_date_time_string()}] {format % args}")


def run_server():
    server_address = ("127.0.0.1", PORT)
    httpd = HTTPServer(server_address, ResumeServerHandler)
    print(f"NaniResumu local server running on http://127.0.0.1:{PORT}")
    print(f"  Web dashboard:        http://127.0.0.1:{PORT}/")
    print(f"  API resumes list:     http://127.0.0.1:{PORT}/api/resumes")
    print(f"  Tampermonkey script:  http://127.0.0.1:{PORT}/openresume-switcher.user.js")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
