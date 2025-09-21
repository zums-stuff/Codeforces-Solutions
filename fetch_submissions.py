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
        
        # --- INICIO DEL CAMBIO CRÍTICO ---
        # Cambiamos 'networkidle' por 'domcontentloaded'.
        # Esto espera a que el HTML principal esté listo, sin preocuparse por el "ruido" de red de fondo.
        # Es una estrategia mucho más robusta y rápida.
        page.goto(url, wait_until='domcontentloaded', timeout=90000) # Aumentamos un poco el timeout general por si acaso
        # --- FIN DEL CAMBIO CRÍTICO ---
        
        code_selector = "pre#program-source-text"
        # La siguiente línea se encarga ahora de esperar a que el desafío de Cloudflare se resuelva
        # y el elemento del código aparezca visible en la página.
        page.wait_for_selector(code_selector, timeout=60000)
        
        code_content = page.inner_text(code_selector)
        
        if code_content:
            return code_content
        
        print(f"Code block found but was empty for {submission_id}")
        return None

    except Exception as e:
        print(f"An error occurred with Playwright for submission {submission_id}: {e}")
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
        
        for submission in new_submissions_to_fetch:
            contest_id, p_index, s_id = submission["contestId"], submission["problem"]["index"], submission["id"]
            problem_id = f"{contest_id}_{p_index}"
            
            print(f"Processing solution: {problem_id}")
            code = get_solution_code(page, contest_id, s_id)

            if not code:
                print(f"Could not get code for {problem_id}, skipping.")
                continue
            
            extension = get_file_extension(submission["programmingLanguage"])
            file_path = f"submissions/{problem_id}.{extension}"
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(code)
            
            submitted_problems.append(problem_id)
            new_count += 1
            print(f"Successfully added solution for {problem_id}")
        
        browser.close()
    
    save_submission_history(submitted_problems)
    print(f"Processed {new_count} new accepted solutions.")

if __name__ == "__main__":
    main()
