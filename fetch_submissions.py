import requests
from playwright.sync_api import sync_playwright
import json
import os
from datetime import datetime
import time
import html

HANDLE = "zum"
COUNT = 15
SUBMISSION_API = f"https://codeforces.com/api/user.status?handle={HANDLE}&from=1&count={COUNT}"

def get_solution_code(page, contest_id, submission_id):
    """Obtiene el código usando una página de navegador ya existente."""
    try:
        url = f"https://codeforces.com/contest/{contest_id}/submission/{submission_id}"
        print(f"Navigating to {url}...")
        
        page.goto(url, wait_until='domcontentloaded', timeout=90000)
        
        code_selector = "pre#program-source-text"
        page.wait_for_selector(code_selector, timeout=60000)
        
        code_content = page.inner_text(code_selector)
        
        if code_content:
            return code_content
        
        print(f"Code block found but was empty for {submission_id}")
        return None

    except Exception as e:
        print(f"An error occurred with Playwright for submission {submission_id}: {e}")
        # --- INICIO DEL CAMBIO PARA DIAGNÓSTICO ---
        # Si el selector falla, imprimimos el HTML de la página para ver la estructura real.
        print("\n--- DEBUG: PRINTING PAGE HTML AS SEEN BY PLAYWRIGHT ---")
        try:
            html_content = page.content()
            print(html_content)
        except Exception as inner_e:
            print(f"Could not get page content for debugging: {inner_e}")
        print("--- DEBUG: END OF PAGE HTML ---\n")
        # --- FIN DEL CAMBIO PARA DIAGNÓSTICO ---
        return None

def load_submission_history():
    if os.path.exists("submission_history.json"):
        with open("submission_history.json", "r") as f: return json.load(f)
    return []

def save_submission_history(history):
    with open("submission_history.json", "w") as f: json.dump(history, f, indent=4)

def get_file_extension(lang):
    lang = lang.lower()
    if "c++" in lang or "gcc" in lang: return "cpp"
    if "python" in lang: return "py"
    if "java" in lang: return "java"
    return "txt"

def main():
    os.makedirs("submissions", exist_ok=True)
    submitted_problems = load_submission_history()
    
    print(f"Fetching submissions for {HANDLE} from API...")
    response = requests.get(SUBMISSION_API)
    data = response.json()
    if data["status"] != "OK":
        print("Failed to fetch submissions from API. Exiting.")
        return
    
    submissions = data["result"]
    new_submissions_to_fetch = []
    for submission in sorted(submissions, key=lambda s: s['creationTimeSeconds'], reverse=True):
        if submission.get("verdict") != "OK": continue
        problem_id = f"{submission['contestId']}_{submission['problem']['index']}"
        if problem_id not in submitted_problems:
            new_submissions_to_fetch.append(submission)

    if not new_submissions_to_fetch:
        print("No new accepted solutions found.")
        return

    print(f"Found {len(new_submissions_to_fetch)} new solutions to process.")
    new_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Para el diagnóstico, solo procesamos la primera solución para ser más rápidos.
        first_submission = new_submissions_to_fetch[0]
        contest_id, p_index, s_id = first_submission["contestId"], first_submission["problem"]["index"], first_submission["id"]
        problem_id = f"{contest_id}_{p_index}"
        
        print(f"Processing solution (DEBUG MODE): {problem_id}")
        get_solution_code(page, contest_id, s_id)
        print("Debug run finished. Exiting to allow log inspection.")
        
        browser.close()

if __name__ == "__main__":
    main()
