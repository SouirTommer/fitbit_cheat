#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Host runner script.
# - reads fitbit_config.json (client credentials) and fitbit_tokens.json (tokens)
# - refreshes token if needed and logs steps
# - default daily steps = 10000

import json
import os
import base64
import requests
from datetime import datetime

CONFIG_FILE = "fitbit_config.json"
TOKEN_FILE = "fitbit_tokens.json"

class FitbitHost:
    def __init__(self):
        self.load_config()
        self.load_tokens()
        self.token_url = "https://api.fitbit.com/oauth2/token"
        self.base_api = "https://api.fitbit.com/1/user/-"

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            raise SystemExit(f"{CONFIG_FILE} missing. Provide client_id and client_secret.")
        with open(CONFIG_FILE, "r") as f:
            cfg = json.load(f)
        self.client_id = cfg["client_id"]
        self.client_secret = cfg["client_secret"]
        self.daily_steps = int(cfg.get("daily_steps", 10000))
        self.start_time = cfg.get("start_time", "08:00")

    def load_tokens(self):
        if not os.path.exists(TOKEN_FILE):
            raise SystemExit(f"{TOKEN_FILE} missing. Upload tokens obtained from login script.")
        with open(TOKEN_FILE, "r") as f:
            t = json.load(f)
        self.access_token = t.get("access_token")
        self.refresh_token = t.get("refresh_token")

    def save_tokens(self, access_token, refresh_token):
        out = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        with open(TOKEN_FILE, "w") as f:
            json.dump(out, f, indent=2)
        self.access_token = access_token
        self.refresh_token = refresh_token
        print(f"Updated {TOKEN_FILE}")

    def refresh_if_needed(self):
        # Try a lightweight call to check token validity
        url = f"{self.base_api}/activities/date/{datetime.utcnow().strftime('%Y-%m-%d')}.json"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        r = requests.get(url, headers=headers)
        if r.status_code == 401:
            return self.refresh_access_token()
        return True

    def refresh_access_token(self):
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        r = requests.post(self.token_url, headers=headers, data=data)
        if r.status_code != 200:
            print("Refresh failed:", r.status_code, r.text)
            return False
        jd = r.json()
        self.save_tokens(jd["access_token"], jd.get("refresh_token"))
        return True

    def log_steps(self, steps=None, date=None, start_time=None):
        if steps is None:
            steps = self.daily_steps
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        if start_time is None:
            start_time = self.start_time

        url = f"{self.base_api}/activities.json"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        duration_minutes = max(steps // 100, 1)
        data = {
            "activityId": 90013,
            "startTime": start_time,
            "durationMillis": duration_minutes * 60 * 1000,
            "date": date,
            "distance": round(steps * 0.0008, 3),
            "steps": steps
        }
        r = requests.post(url, headers=headers, data=data)
        if r.status_code == 401:
            print("Token expired, refreshing...")
            if not self.refresh_access_token():
                return False
            headers["Authorization"] = f"Bearer {self.access_token}"
            r = requests.post(url, headers=headers, data=data)
        if r.status_code not in (200, 201):
            print("Log failed:", r.status_code, r.text)
            return False
        jd = r.json()
        print("Logged steps:", steps, "date:", date)
        if "activityLog" in jd and "logId" in jd["activityLog"]:
            print("logId:", jd["activityLog"]["logId"])
        return True

def main():
    h = FitbitHost()
    print("Running at", datetime.utcnow().isoformat() + "Z")
    ok = h.refresh_if_needed()
    if not ok:
        print("Token refresh/check failed.")
        return
    if h.log_steps():
        print("Done.")
    else:
        print("Failed.")

if __name__ == "__main__":
    main()