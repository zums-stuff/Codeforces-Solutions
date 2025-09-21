import requests
import cloudscraper
import json
import os
from datetime import datetime
import time
import html

HANDLE = "zum"
COUNT = 10
SUBMISSION_API = f"https://codeforces.com/api/user.status?handle={HANDLE}&from=1&count={COUNT}"

scraper = cloudscraper.create_scraper() 

def fetch_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = scraper.get(url)
            response.raise_for_status()
            data = response.json()
            if data["status"] == "OK":
                return data
        except Exception as e:
            print(f"API fetch attempt {attempt+1} failed: {e}")
            if attempt == max_retries - 1: raise
            time.sleep(2 ** attempt)

def load_submission_history():
    history_file = "submission_history.json"
    if os.path.exists(history_file):
        with open(history_file, "r") as f: return json.load(f)
    return []

def save_submission_history(history):
    with open("submission_history.json", "w") as f: json.dump(history, f, indent=4)

# --- INICIO DE LA MODIFICACIÓN FINAL ---
def get_solution_code(contest_id, submission_id):
    """Get code using cloudscraper and a more robust parsing method."""
    try:
        url = f"https://codeforces.com/contest/{contest_id}/submission/{submission_id}"
        response = scraper.get(url)
        response.raise_for_status()
        
        content = response.text
        
        # Marker for the unique ID of the code block
        id_marker = 'id="program-source-text"'
        end_marker = '</pre>'
        
        # Find the unique ID first
        id_idx = content.find(id_marker)
        if id_idx == -1:
            print(f"Could not find ID 'program-source-text' for submission {submission_id}")
            return None
        
        # Find the start of the <pre> tag before this ID
        pre_tag_start = content.rfind('<pre', 0, id_idx)
        if pre_tag_start == -1:
            print(f"Could not find start of <pre> tag for submission {submission_id}")
            return None
        
        # Find the end of the opening <pre...> tag
        code_start = content.find('>', pre_tag_start) + 1
        
        # Find the closing </pre> tag
        code_end = content.find(end_marker, code_start)

        if code_end > code_start:
            code = content[code_start:code_end]
            return html.unescape(code)
        
        print(f"Could not extract code between tags for submission {submission_id}")
        return None
        
    except Exception as e:
        print(f"Error getting solution code for {submission_id}: {e}")
        return None
# --- FIN DE LA MODIFICACIÓN FINAL ---

def get_file_extension(lang):
    lang = lang.lower()
    if "c++" in lang or "gcc" in lang: return "cpp"
    if "python" in lang: return "py"
    if "java" in lang: return "java"
    return "txt"

def main():
    os.makedirs("submissions", exist_ok=True)
    submitted_problems = load_submission_history()
    
    print(f"Fetching submissions for {HANDLE}...")
    data = fetch_with_retry(SUBMISSION_API)
    if not data:
        print("Failed to fetch submissions from API. Exiting.")
        return
    
    submissions = data["result"]
    new_count = 0
    
    for submission in sorted(submissions, key=lambda s: s['creationTimeSeconds'], reverse=True):
        if submission.get("verdict") != "OK": continue
        contest_id, problem_index, submission_id = submission["contestId"], submission["problem"]["index"], submission["id"]
        problem_id = f"{contest_id}_{problem_index}"
        
        if problem_id in submitted_problems: continue
        
        print(f"Found new accepted solution: {problem_id}")
        code = get_solution_code(contest_id, submission_id)

        if not code:
            print(f"Could not get code for {problem_id}, skipping.")
            continue
        
        lang = submission["programmingLanguage"]
        extension = get_file_extension(lang)
        file_path = f"submissions/{problem_id}.{extension}"
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(code)
        
        submitted_problems.append(problem_id)
        new_count += 1
        print(f"Successfully added solution for {problem_id}")
    
    save_submission_history(submitted_problems)
    print(f"Processed {new_count} new accepted solutions.")

if __name__ == "__main__":
    main()
