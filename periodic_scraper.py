import os
import time
import shutil
import subprocess
from datetime import datetime, timedelta

last_run_file = "last_run_date.txt"
export_source = "export.xlsx"
export_destination = r"C:\Users\berti\OneDrive\Docs\export.xlsx"

def get_current_date():
    return datetime.now().strftime("%Y-%m-%d")

def get_yesterday_date():
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

def run_script():
    print("Running python -m src")
    subprocess.run(["python", "-m", "src"])
    # copy export.xlsx to the destination
    shutil.copy(export_source, export_destination)

def update_last_run_date(date):
    with open(last_run_file, "w") as f:
        f.write(date)

def main():
    while True:
        current_date = get_current_date()
        yesterday_date = get_yesterday_date()
        current_hour = datetime.now().hour

        print("Current Date:", current_date)
        print("Yesterday's Date:", yesterday_date)
        print("Current Hour:", current_hour)

        if os.path.exists(last_run_file):
            with open(last_run_file, "r") as f:
                last_run_date = f.read().strip()
            print("Last Run Date:", last_run_date)
        else:
            print("No last run date file found, therefore running the script.")
            last_run_date = ""

        if current_hour >= 13:
            if last_run_date != current_date:
                run_script()
                update_last_run_date(current_date)
                print("Updated last run date to:", current_date)
            else:
                print("Last run date is today.")
        else:
            print("It is not yet 1 PM.")

        time.sleep(3600)

if __name__ == "__main__":
    main()
