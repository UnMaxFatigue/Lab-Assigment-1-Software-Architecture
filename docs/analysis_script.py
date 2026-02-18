import requests
import json
import time

# ===== SETTINGS =====
PROJECT_KEY = "smartmove"        # same as sonar.projectKey
PROJECT_NAME = "SmartMove"
SONAR_TOKEN = "squ_1437c407bdadbdf325ece300006670b3e03cb1cd"

def save_local_report():
    metrics = "bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density"
    url = f"http://localhost:9000/api/measures/component?component={PROJECT_KEY}&metricKeys={metrics}"

    try:
        response = requests.get(url, auth=(SONAR_TOKEN, ""))
        if response.status_code == 200:
            data = response.json()

            measures = data['component']['measures']
            final_report = {
                "project": PROJECT_NAME,
                "analysis_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "results": {m['metric']: m['value'] for m in measures}
            }

            file_name = f"report_{PROJECT_KEY}.json"
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(final_report, f, indent=4)

            print("JSON report created successfully!")

        else:
            print(f"Fail to recover the report: {response.text}")

    except Exception as e:
        print(f"Error during the save of the report: {e}")

# Run function
save_local_report()