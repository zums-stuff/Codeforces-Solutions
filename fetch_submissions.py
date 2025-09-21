import requests
import json
import os
from datetime import datetime
import time

# Your Codeforces handle will be replaced by the environment variable
HANDLE = "zum"

# Number of recent submissions to check
COUNT = 10

# Codeforces API URLs
SUBMISSION_API = f"https://codeforces.com/api/user.status?handle={HANDLE}&from=1&count={COUNT}"

def fetch_with_retry(url, max_retries=3):
    """Fetch data from API with retry mechanism"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if data["status"] == "OK":
                return data
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)

def load_submission_history():
    """Load previously submitted problems"""
    history_file = "submission_history.json"
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            return json.load(f)
    return []

def save_submission_history(history):
    """Save submission history"""
    with open("submission_history.json", "w") as f:
        json.dump(history, f, indent=4)

def get_solution_code(contest_id, submission_id):
    """Get the code from a Codeforces submission"""
    try:
        url = f"https://codeforces.com/contest/{contest_id}/submission/{submission_id}"
        response = requests.get(url)
        response.raise_for_status()
        
        content = response.text
        start_marker = '<pre id="program-source-text"'
        end_marker = '</pre>'
        
        start_idx = content.find(start_marker)
        if start_idx == -1:
            print(f"Could not find code for submission {submission_id}")
            return None
            
        code_start = content.find('>', start_idx) + 1
        code_end = content.find(end_marker, code_start)
        
        if code_end > code_start:
            code = content[code_start:code_end]
            import html
            code = html.unescape(code)
            return code
        return None
    except Exception as e:
        print(f"Error getting solution code: {e}")
        return None

def get_file_extension(lang):
    """Get the file extension based on programming language"""
    lang = lang.lower()
    if "c++" in lang or "gcc" in lang:
        return "cpp"
    elif "python" in lang:
        return "py"
    elif "java" in lang:
        return "java"
    # Add more languages as needed
    return "txt"  # Default

def main():
    os.makedirs("submissions", exist_ok=True)
    submitted_problems = load_submission_history()
    
    print(f"Fetching submissions for {HANDLE}...")
    try:
        data = fetch_with_retry(SUBMISSION_API)
        submissions = data["result"]
    except Exception as e:
        print(f"Failed to fetch submissions: {e}")
        return
    
    new_count = 0
    for submission in reversed(submissions): # Process oldest first
        if submission.get("verdict") != "OK":
            continue
            
        contest_id = submission["contestId"]  
        problem_index = submission["problem"]["index"]
        submission_id = submission["id"]
        problem_id = f"{contest_id}_{problem_index}"
        
        if problem_id in submitted_problems:
            continue
            
        lang = submission["programmingLanguage"]
        extension = get_file_extension(lang)
        
        code = get_solution_code(contest_id, submission_id)
        if not code:
            print(f"Couldn't get code for {problem_id}, skipping")
            continue
        
        file_path = f"submissions/{problem_id}.{extension}"
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(code)
        
        problem_name = submission["problem"].get("name", "Unknown")
        with open("submissions/log.txt", "a") as log:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log.write(f"{problem_id} - {problem_name} - Solved on {timestamp}\n")
        
        submitted_problems.append(problem_id)
        new_count += 1
        print(f"Added solution for {problem_id} - {problem_name}")
    
    save_submission_history(submitted_problems)
    print(f"Processed {new_count} new accepted solutions")
    if new_count > 0:
        print("New solutions have been saved to the submissions directory")

if __name__ == "__main__":
    main()
