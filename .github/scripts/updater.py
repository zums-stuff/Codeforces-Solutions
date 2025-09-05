import os
import requests
from bs4 import BeautifulSoup
import sys
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException

# --- NUEVA LIBRERÍA ---
from selenium_stealth import stealth

def get_cf_submissions(handle):
    # (Esta función no cambia)
    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=50"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data['status'] == 'OK':
            return data['result']
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
    return []

def get_source_code_with_selenium(contest_id, submission_id):
    url = f"https://codeforces.com/contest/{contest_id}/submission/{submission_id}"
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Evitar que Selenium imprima tantos logs
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = None
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # --- APLICAMOS EL MODO SIGILOSO (STEALTH) ---
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )

        driver.get(url)
        
        wait = WebDriverWait(driver, 25) # Aumentamos un poco el tiempo de espera
        source_code_element = wait.until(
            EC.presence_of_element_located((By.ID, "program-source-text"))
        )
        
        time.sleep(3) # Pequeña pausa final por si acaso

        return source_code_element.text.strip()

    # --- Manejo de errores más específico ---
    except TimeoutException:
        print(f"Selenium timed out waiting for submission {submission_id}. Page might be blocked or changed.")
        driver.save_screenshot(f'selenium_timeout_error_{submission_id}.png')
        return None
    except Exception as e:
        print(f"An unexpected Selenium error occurred for submission {submission_id}: {e}")
        driver.save_screenshot(f'selenium_unexpected_error_{submission_id}.png')
        return None
    finally:
        if driver:
            driver.quit()

def main(handle):
    # (El resto de la función main es idéntica)
    submissions = get_cf_submissions(handle)
    if not submissions:
        print("No submissions found or API error.")
        return

    history_file = '.github/scripts/submission_history.json'
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                committed_ids = set(json.load(f))
        except json.JSONDecodeError:
            committed_ids = set()
    else:
        committed_ids = set()
        os.makedirs(os.path.dirname(history_file), exist_ok=True)


    new_solutions_found = False
    for sub in reversed(submissions):
        if sub.get('verdict') == 'OK' and sub.get('id') not in committed_ids:
            problem = sub.get('problem', {})
            contest_id = problem.get('contestId')
            problem_index = problem.get('index')
            problem_name = problem.get('name', 'UnknownProblem').replace(' ', '_')
            submission_id = sub.get('id')
            language = sub.get('programmingLanguage', 'UnknownLang')

            if not all([contest_id, problem_index, submission_id]):
                continue

            lang_ext_map = {
                "GNU C++17": "cpp", "GNU C++14": "cpp", "GNU C++11": "cpp", "GNU C++20": "cpp",
                "Python 3": "py", "PyPy 3": "py",
                "Java 8": "java", "Java 11": "java",
                "C#": "cs", "Go": "go", "Rust": "rs"
            }
            extension = lang_ext_map.get(language, 'txt')
            
            dir_path = f"Codeforces/{contest_id}"
            os.makedirs(dir_path, exist_ok=True)
            
            filename = f"{dir_path}/{problem_index}_{problem_name}.{extension}"
            
            source_code = get_source_code_with_selenium(contest_id, submission_id)

            if source_code:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(source_code)
                print(f"Successfully added solution: {filename}")
                committed_ids.add(submission_id)
                new_solutions_found = True
            else:
                print(f"Could not retrieve source code for submission {submission_id}")

    if new_solutions_found:
        with open(history_file, 'w') as f:
            json.dump(list(committed_ids), f)

if __name__ == "__main__":
    cf_handle = sys.argv[1]
    main(cf_handle)
