import wg
import os
from pathlib import Path

# Use current directory
cwd = os.getcwd()

print(f"Testing handle_log in: {cwd}")

try:
    logs = wg.handle_log(cwd)
    print(f"Found {len(logs)} commits.")
    if logs:
        print("First commit sample:")
        print(logs[0])
        print("Files in first commit:", logs[0].get('files'))
    else:
        print("No logs found.")

except Exception as e:
    print(f"Error: {e}")
