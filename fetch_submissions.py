import requests
import json
import os
from datetime import datetime
import time

# Your Codeforces handle - REPLACE THIS
HANDLE = ""

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
        # Directly accessing the submission page
        url = f"https://codeforces.com/contest/{contest_id}/submission/{submission_id}"
        response = requests.get(url)
        response.raise_for_status()
        
        # This is a simple approach - might need improvements for reliability
        # We're looking for code within specific HTML elements
        content = response.text
        start_marker = '<pre id="program-source-text"'
        end_marker = '</pre>'
        
        start_idx = content.find(start_marker)
        if start_idx == -1:
            print(f"Could not find code for submission {submission_id}")
            return None
            
        # Find the actual code start after the pre tag
        code_start = content.find('>', start_idx) + 1
        code_end = content.find(end_marker, code_start)
        
        if code_end > code_start:
            code = content[code_start:code_end]
            # HTML decode the code
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
    elif "javascript" in lang or "js" in lang:
        return "js"
    elif "c#" in lang or "csharp" in lang:
        return "cs"
    elif "go" in lang:
        return "go"
    elif "rust" in lang:
        return "rs"
    elif "kotlin" in lang:
        return "kt"
    elif "ruby" in lang:
        return "rb"
    # Add more languages as needed
    return "txt"  # Default

def main():
    # Make sure submissions directory exists
    os.makedirs("submissions", exist_ok=True)
    
    # Load submission history
    submitted_problems = load_submission_history()
    
    # Fetch recent submissions
    print(f"Fetching submissions for {HANDLE}...")
    try:
        data = fetch_with_retry(SUBMISSION_API)
        submissions = data["result"]
    except Exception as e:
        print(f"Failed to fetch submissions: {e}")
        return
    
    # Process new accepted submissions
    new_count = 0
    for submission in submissions:
        # Only process accepted solutions
        if submission["verdict"] != "OK":
            continue
            
        contest_id = submission["contestId"] 
        problem_index = submission["problem"]["index"]
        submission_id = submission["id"]
        problem_id = f"{contest_id}_{problem_index}"
        
        # Skip if already processed
        if problem_id in submitted_problems:
            continue
            
        # Get the programming language
        lang = submission["programmingLanguage"]
        extension = get_file_extension(lang)
        
        # Get solution code
        code = get_solution_code(contest_id, submission_id)
        if not code:
            print(f"Couldn't get code for {problem_id}, skipping")
            continue
        
        # Save the code to a file
        file_path = f"submissions/{problem_id}.{extension}"
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(code)
        
        # Add problem metadata as a comment
        problem_name = submission["problem"].get("name", "Unknown")
        contest_name = f"Contest {contest_id}"
        with open("submissions/log.txt", "a") as log:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log.write(f"{problem_id} - {problem_name} - Solved on {timestamp}\n")
        
        # Add to history
        submitted_problems.append(problem_id)
        new_count += 1
        print(f"Added solution for {problem_id} - {problem_name}")
    
    # Save updated history
    save_submission_history(submitted_problems)
    
    print(f"Processed {new_count} new accepted solutions")
    if new_count > 0:
        print("New solutions have been saved to the submissions directory")

if __name__ == "__main__":
    main()
