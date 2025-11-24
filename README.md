# AutoStepLogger

AutoStepLogger is a simple toolkit that helps users upload simulated steps to a Fitbit account (for example, automatically upload 10,000 steps every day). This repository contains two main scripts:

- `fitbit_login.py` — Run locally to perform OAuth login and produce `fitbit_tokens.json` (access + refresh token).
- `fitbit_host.py` — Run on a host (e.g. PythonAnywhere) to read `fitbit_tokens.json` and `fitbit_config.json`, refresh tokens when required, and upload steps.
- `fitbit_config.json` — Configuration template (replace with your own credentials).

Prerequisites
- Python 3.8+
- requests: `pip install requests`
- A Fitbit developer application: https://dev.fitbit.com/apps/new

Quick Overview
1. Register a Fitbit application (https://dev.fitbit.com/apps/new), add `http://127.0.0.1:8080/` as Redirect URL, and copy your OAuth 2.0 Client ID and Client Secret value.
2. Fill `fitbit_config.json` (OAuth 2.0 Client ID value and Client Secret value) with your credentials.
3. Run `fitbit_login.py` locally to authorize and generate `fitbit_tokens.json`.
4. Upload `fitbit_host.py`, `fitbit_config.json`, and `fitbit_tokens.json` to your host (e.g. PythonAnywhere).
5. Schedule `fitbit_host.py` to run daily.

## Step-by-step tutorial

Step 0 — Create a Fitbit App
1. Go to https://dev.fitbit.com/apps and create a new app (or edit an existing one).
2. Add Redirect URL: `http://127.0.0.1:8080/` (must exactly match the redirect_uri used by the login script).
For example:
<img width="594" height="846" alt="image" src="https://github.com/user-attachments/assets/8de82355-47f8-4870-a705-cb563d2f51eb" />

3. Save and copy the `OAuth 2.0 Client ID` and `Client Secret value` !!!! and paste values to `fitbit_config.json`.

Step 1 — Prepare config (local)
Edit `fitbit_config.json` in the project directory and fill in your values. Example:

```json
{
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET",
  "redirect_uri": "http://127.0.0.1:8080/",
  "scope": "activity",
  "default_port": 8080,
  "daily_steps": 10000,
  "start_time": "08:00"
}
```

Step 2 — Run local login to obtain tokens
1. Install requests if needed:
   ```
   pip install requests
   ```
2. Run:
   ```
   python fitbit_login.py
   ```
3. The script opens your browser to the Fitbit authorization page. Sign in and click "Allow".
<img width="481" height="370" alt="Screenshot 2025-11-24 104839" src="https://github.com/user-attachments/assets/68b8f30f-a853-4d65-bba7-1f559a9b205f" /><br>
4. The local server will capture the authorization code and exchange it for tokens.
5. The script writes `fitbit_tokens.json`. Keep this file private.
6. You can try to run the `fitbit_host.py`. It should increase 10k steps on your Fitbit.

Step 3 — Prepare host environment (this example uses PythonAnywhere)
1. Register a PythonAnywhere account
2. Click the `Dashboard` -> `Files` page
3. Click `New file`
4. Upload these files to your host:
   - `fitbit_host.py`
   - `fitbit_config.json` (with your client_id/client_secret)
   - `fitbit_tokens.json` (from Step 2)
5. — Schedule daily run
  Client the `Tasks` → Scheduled tasks
  - Command:
    ```
    python3 /home/yourusername/fitbit_host.py
    ```
  - Remember PythonAnywhere uses UTC. Convert your desired time to UTC. (UTC 2:00 am = HK time 10:00 am). If you don't understand, just fill 2:00

Common issues & troubleshooting
- invalid_request - Invalid redirect_uri parameter value:
  - Ensure the redirect URI you registered on Fitbit exactly matches `redirect_uri` in `fitbit_config.json` (include trailing slash and port).
- No code after clicking Allow:
  - Confirm your local server is listening on the same port defined in `redirect_uri` and that no firewall blocks it.
- Refresh token fails:
  - If refresh_token is revoked or expired, re-run `fitbit_login.py` locally to obtain a new `fitbit_tokens.json`.

License
- Add a license file to your repo (MIT recommended) if you want others to reuse the code.
