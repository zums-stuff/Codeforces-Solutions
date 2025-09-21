import requests
from playwright.sync_api import sync_playwright # <-- Importamos Playwright
import json
import os
from datetime import datetime
import time
import html

HANDLE = "zum"
COUNT = 15 # Aumentamos un poco por si acaso
SUBMISSION_API = f"https://codeforces.com/api/user.status?handle={HANDLE}&from=1&count={COUNT}"

# --- INICIO DE LA NUEVA LÓGICA CON PLAYWRIGHT ---
def get_solution_code(contest_id, submission_id):
    """Obtiene el código usando un navegador real con Playwright."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            url = f"https://codeforces.com/contest/{contest_id}/submission/{submission_id}"
            print(f"Navigating to {url} with Playwright...")
            
            # Navegamos a la página. Playwright esperará a que cargue.
            page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Esperamos explícitamente a que el selector del código sea visible
            # Esta es la forma más robusta de hacerlo
            code_selector = "pre#program-source-text"
            page.wait_for_selector(code_selector, timeout=30000)
            
            # Extraemos el contenido del elemento
            code_content = page.inner_text(code_selector)
            
            browser.close()
            
            if code_content:
                # Playwright ya devuelve el texto decodificado
                return code_content
            
            print(f"Code block found but was empty for {submission_id}")
            return None

    except Exception as e:
        print(f"An error occurred with Playwright for submission {submission_id}: {e}")
        return None
# --- FIN DE LA NUEVA LÓGICA CON PLAYWRIGHT ---

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
    new_count = 0
    
    for submission in sorted(submissions, key=lambda s: s['creationTimeSeconds'], reverse=True):
        if submission.get("verdict") != "OK": continue
        contest_id, p_index, s_id = submission["contestId"], submission["problem"]["index"], submission["id"]
        problem_id = f"{contest_id}_{p_index}"
        
        if problem_id in submitted_problems: continue
        
        print(f"Found new accepted solution: {problem_id}")
        code = get_solution_code(contest_id, s_id)

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
    
    save_submission_history(submitted_problems)
    print(f"Processed {new_count} new accepted solutions.")

if __name__ == "__main__":
    main()
