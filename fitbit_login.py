#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Simple Fitbit OAuth login script.
# - reads client_id/secret from fitbit_config.json
# - starts local HTTP server to capture code
# - exchanges code for tokens and saves fitbit_tokens.json

import json
import base64
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
import os
from datetime import datetime

CONFIG_FILE = "fitbit_config.json"
TOKEN_FILE = "fitbit_tokens.json"

class CallbackHandler(BaseHTTPRequestHandler):
    """Simple handler to catch OAuth code and show a tiny page."""

    auth_code = None

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if "code" in qs:
            CallbackHandler.auth_code = qs["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<html><body><h2>Authorized. You can close this window.</h2></body></html>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"<html><body><h2>No code found.</h2></body></html>")

    def log_message(self, format, *args):
        # silence default logging
        pass

def load_config():
    if not os.path.exists(CONFIG_FILE):
        sample = {
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "redirect_uri": "http://127.0.0.1:8080/",
            "scope": "activity",
            "default_port": 8080
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(sample, f, indent=2)
        print(f"Created sample {CONFIG_FILE}. Please edit it with your app credentials and run again.")
        raise SystemExit(1)
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_tokens(data):
    out = {
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token"),
        "scope": data.get("scope"),
        "token_type": data.get("token_type"),
        "expires_in": data.get("expires_in"),
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
    with open(TOKEN_FILE, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Saved tokens to {TOKEN_FILE}")

def exchange_code_for_token(client_id, client_secret, code, redirect_uri):
    token_url = "https://api.fitbit.com/oauth2/token"
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id
    }
    r = requests.post(token_url, headers=headers, data=data)
    r.raise_for_status()
    return r.json()

def run_local_server(port):
    server = HTTPServer(("127.0.0.1", port), CallbackHandler)
    thread = threading.Thread(target=server.handle_request)
    thread.daemon = True
    thread.start()
    return server, thread

def main():
    cfg = load_config()
    client_id = cfg["client_id"]
    client_secret = cfg["client_secret"]
    redirect = cfg.get("redirect_uri", "http://127.0.0.1:8080/")
    scope = cfg.get("scope", "activity")
    port = cfg.get("default_port", 8080)

    # build auth URL
    from urllib.parse import urlencode
    params = {
        "client_id": client_id,
        "response_type": "code",
        "scope": scope,
        "redirect_uri": redirect
    }
    auth_url = "https://www.fitbit.com/oauth2/authorize?" + urlencode(params)

    print("Open this URL in your browser and Allow the app:")
    print(auth_url)
    print("\nTrying to open browser automatically...")
    try:
        webbrowser.open(auth_url)
    except:
        pass

    server, thread = run_local_server(port)
    print(f"Waiting for redirect on http://127.0.0.1:{port}/ ...")
    thread.join(timeout=300)  # wait up to 5 minutes

    code = CallbackHandler.auth_code
    if not code:
        print("No code received. Make sure redirect uri matches and you allowed the app.")
        server.server_close()
        raise SystemExit(1)

    print("Got code, exchanging for token...")
    token_data = exchange_code_for_token(client_id, client_secret, code, redirect)
    save_tokens(token_data)
    server.server_close()
    print("Done. You can upload fitbit_tokens.json to your host server.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Error:", e)