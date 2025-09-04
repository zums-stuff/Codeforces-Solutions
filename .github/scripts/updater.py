import os
import requests
import sys
import json
from datetime import datetime

def get_cf_submissions(handle):
    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=100"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK':
            return data['result']
    return []

def main(handle, token):
    submissions = get_cf_submissions(handle)
    if not submissions:
        print("No submissions found or API error.")
        return

    history_file = 'submission_history.json'
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            committed_ids = set(json.load(f))
    else:
        committed_ids = set()

    new_solutions = False
    for sub in reversed(submissions):
        if sub['verdict'] == 'OK' and sub['id'] not in committed_ids:
            problem = sub['problem']
            problem_id = f"{problem['contestId']}_{problem['index']}"
            
            lang_ext = {
                "GNU C++17": "cpp", "Python 3": "py", "Java 8": "java", "C#": "cs",
                # Agrega otras extensiones si es necesario
            }.get(sub['programmingLanguage'], 'txt')

            filename = f"submissions/{problem_id}.{lang_ext}"
            
            # Obtener el código fuente (requiere scraping, este script simplificado no lo hace)
            # Para una solución completa, se necesitaría una librería como BeautifulSoup
            # Por ahora, se crea un archivo de marcador de posición
            source_code_url = f"https://codeforces.com/contest/{sub['contestId']}/submission/{sub['id']}"

            os.makedirs('submissions', exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"// Solution for {problem['name']}\n")
                f.write(f"// Language: {sub['programmingLanguage']}\n")
                f.write(f"// Submission URL: {source_code_url}\n")
                f.write(f"// Submission ID: {sub['id']}\n\n")
                f.write("// NOTE: The source code is not automatically fetched by this simplified script.\n")
                f.write("// Please visit the URL above to see the code.\n")


            print(f"Added solution for {problem_id}")
            committed_ids.add(sub['id'])
            new_solutions = True
    
    if new_solutions:
        with open(history_file, 'w') as f:
            json.dump(list(committed_ids), f)

if __name__ == "__main__":
    cf_handle = sys.argv[1]
    gh_token = sys.argv[2]
    main(cf_handle, gh_token)
