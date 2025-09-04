# Official Updater Script with User-Agent Fix
import os
import requests
from bs4 import BeautifulSoup
import sys
import json
from datetime import datetime

def get_cf_submissions(handle):
    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=100"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data['status'] == 'OK':
            return data['result']
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
    return []

def get_source_code(contest_id, submission_id):
    url = f"https://codeforces.com/contest/{contest_id}/submission/{submission_id}"
    
    # ESTA ES LA LÍNEA CLAVE: AÑADIMOS UN HEADER PARA SIMULAR UN NAVEGADOR
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Usamos los headers en la petición
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Esto verificará si hay errores como el 403
        soup = BeautifulSoup(response.text, 'html.parser')
        source_code_div = soup.find("pre", {"id": "program-source-text"})
        if source_code_div:
            return source_code_div.get_text().strip()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch source code for {submission_id}: {e}")
    return None

def main(handle):
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
            
            source_code = get_source_code(contest_id, submission_id)

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
