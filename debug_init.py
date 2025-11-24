import sys
import traceback
import wg

project_path = "/Users/gravity/Desktop/合同法制审核工作总结"

print(f"Debugging handle_init for: {project_path}")

try:
    wg.handle_init(project_path)
    print("handle_init succeeded")
except Exception:
    traceback.print_exc()
