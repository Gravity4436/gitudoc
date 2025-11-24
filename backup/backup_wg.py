#!/usr/bin/env python3

import sys
import subprocess
import argparse
from pathlib import Path

# --- V4.5 架构 ---
# 1. 'get_docx_files' 函数回归, 用于智能过滤临时文件。
# 2. 'wg init' 配置 'textconv' (V4.4 修复)。
# 3. 'wg diff/commit' (无参数) 将使用 'get_docx_files()' 而不是易出错的 '*.docx'。
# 4. 'argparse' 100%% 修复 (V4.3 修复)。

def run_command(command, capture_output=False, check=True, shell=False):
    """(V3.1 修复) 一个通用的、健壮的子进程运行器"""
    try:
        is_pager_command = (
            (command[0] == "git" and command[1] == "log") or
            (command[0] == "git" and command[1] == "diff" and "--quiet" not in command)
        )

        if is_pager_command and not capture_output and not shell:
            process = subprocess.Popen(command, text=True)
            process.wait() 
            if check and process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, command)
            return process
        
        result = subprocess.run(
            command,
            check=check,
            text=True,
            capture_output=capture_output,
            shell=shell 
        )
        return result
        
    except FileNotFoundError as e:
        print(f"Error: 依赖命令未找到: {e.filename}")
        print("请确保 git 和 pandoc 都在您的系统 PATH 中。")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error: 命令执行失败 (Code: {e.returncode}): {command}")
        if e.stderr:
            print(f"Stderr:\n{e.stderr}")
        if e.stdout:
            print(f"Stdout:\n{e.stdout}")
        sys.exit(1)

def check_init_status():
    """(V4.0 简化) 检查 .git 目录是否存在"""
    if not Path(".git").is_dir():
        print("Error: 这不是一个 'wg' 仓库 (未找到 .git 目录)。")
        print(f"请先运行 'python3 {sys.argv[0]} init'")
        sys.exit(1)

# --- (V4.5 新增) ---
def get_docx_files():
    """
    (V4.6 QoL 修复) 
    获取当前目录下的所有 .docx 文件, 忽略 Office 临时文件。
    返回一个相对路径的字符串列表。
    """
    current_dir = Path.cwd()
    all_files = current_dir.glob("*.docx")
    
    valid_files = [
        f for f in all_files 
        if not f.name.startswith("~$") and not f.name.startswith(".~")
    ]
    
    return [f.name for f in valid_files] # (V4.6 修复) str(f) -> f.name

# --- (V4.4 修复) ---
def handle_init():
    """
    (V4.4 核心) 
    初始化 Git 仓库并自动配置 'textconv' 以便 diff .docx。
    """
    # 1. 初始化 Git 仓库
    if not Path(".git").is_dir():
        run_command(["git", "init"])
        print("Git 仓库已初始化。")
    else:
        print("Git 仓库已存在。")

    # 2. (V4.4 修复) 配置 Git textconv 驱动
    pandoc_cmd_string = "git config diff.pandoc.textconv 'pandoc -t plain'"
    try:
        run_command(pandoc_cmd_string, shell=True)
        print("已配置 Git 'pandoc' diff 驱动。")
    except Exception as e:
        print(f"Error: 配置 Git diff 驱动失败。请确保 pandoc 已安装。")
        print(e)
        sys.exit(1)

    # 3. (V4.0 新增) 创建 .gitattributes
    attr_path = Path(".gitattributes")
    attr_pattern = "*.docx diff=pandoc"
    
    attr_content = ""
    if attr_path.exists():
        with open(attr_path, "r") as f:
            attr_content = f.read()

    if attr_pattern not in attr_content:
        with open(attr_path, "a") as f:
            f.write(f"\n{attr_pattern}\n")
        print("已创建/更新 .gitattributes 并关联 .docx 文件。")
    
    # 4. (V4.0 修改) 创建 .gitignore
    gitignore_path = Path(".gitignore")
    ignore_patterns = ["*.doc", ".DS_Store"] 
    
    existing_patterns = []
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            existing_patterns = [line.strip() for line in f.readlines()]

    patterns_added = False
    with open(gitignore_path, "a") as f:
        for pattern in ignore_patterns:
            if pattern not in existing_patterns:
                f.write(f"{pattern}\n")
                print(f"已将 '{pattern}' 添加到 .gitignore")
                patterns_added = True

    # 5. (V4.0 新增) 提交配置文件
    config_files_to_add = []
    if attr_pattern not in attr_content:
        config_files_to_add.append(str(attr_path))
    if patterns_added:
        config_files_to_add.append(str(gitignore_path))

    if config_files_to_add:
        print("正在提交 'wg' 配置文件到仓库...")
        is_initial_commit = run_command(["git", "rev-parse", "--verify", "HEAD"], check=False).returncode != 0
        
        run_command(["git", "add"] + config_files_to_add)
        
        commit_msg = "Initial commit: Configure wg (pandoc diff)" if is_initial_commit else "Update wg config (pandoc diff)"
        run_command(["git", "commit", "-m", commit_msg])

    print("\nWG 仓库 (V4.5) 初始化完成。")
    print("现在您可以直接 'add' 和 'commit' 您的 .docx 文件了。")

# --- (V4.5 修复) ---
def handle_status(files):
    """(V4.5 修复) 运行 'git status'"""
    check_init_status()
    # (V4.5 修复) 使用 get_docx_files() 替代 '*.docx'
    files_to_check = files if files else get_docx_files()
    if not files_to_check:
        print("未找到 .docx 文件。")
        return

    print(f"\n--- Git 状态 ({' '.join(files_to_check)}) ---")
    run_command(["git", "status", "--short", "--"] + files_to_check, check=False)

# --- (V4.5 修复) ---
def handle_diff(files):
    """(V4.5 修复) 运行 'git diff'"""
    check_init_status()
    # (V4.5 修复) 使用 get_docx_files() 替代 '*.docx'
    files_to_check = files if files else get_docx_files()
    if not files_to_check:
        print("未找到 .docx 文件。")
        return

    print(f"\n--- Git 差异 ({' '.join(files_to_check)}) ---")
    run_command(["git", "diff", "--"] + files_to_check, capture_output=False, check=False)

# --- (V4.5 修复) ---
def handle_commit(message, files):
    """(V4.5 修复) 'git add' 并 'git commit'"""
    check_init_status()
    
    # (V4.5 修复) 使用 get_docx_files() 替代 '*.docx'
    files_to_add = files if files else get_docx_files()
    if not files_to_add:
        print("未找到要提交的 .docx 文件。")
        return
    
    print(f"\n--- 正在暂存 (Add) {files_to_add} ---")
    run_command(["git", "add"] + files_to_add)
    
    # (V4.1 修复) 检查是否有实际变更或错误
    check_cmd = run_command(["git", "diff", "--staged", "--quiet"], check=False)
    
    if check_cmd.returncode == 0:
        print("\n暂存区与上次提交相比没有变化。")
        print("无需提交。")
        return
    elif check_cmd.returncode == 1:
        print("\n--- 正在提交 (Commit) ---")
        run_command(["git", "commit", "-m", message])
        print("\n提交成功！")
    else:
        print("\n错误: 'git diff' 检查失败 (可能由 pandoc 引起)。")
        print("提交已中止。")
        return

# --- (V4.5 修复) ---
def handle_log(files):
    """(V4.5 修复) 显示 .docx 文件的 'git log'"""
    check_init_status()
    # (V4.5 修复) 使用 get_docx_files() 替代 '*.docx'
    files_to_log = files if files else get_docx_files()
    if not files_to_log:
        print("未找到 .docx 文件。")
        return

    print(f"\n--- Git 日志 ({' '.join(files_to_log)}) ---")
    run_command(["git", "log", "--"] + files_to_log, capture_output=False, check=False)

# --- (V4.0 重大简化) ---
def handle_restore(commit_id, docx_file_name):
    """
    (V4.0 简化)
    从 Git 历史中恢复一个 100% 保真度的 .docx 文件。
    """
    check_init_status()
    
    docx_path = Path(docx_file_name)
    if not docx_file_name.endswith(".docx"):
        print(f"Error: 文件 {docx_file_name} 不是 .docx 文件")
        return

    restored_docx_name = f"{docx_path.stem}.{commit_id[:7]}.restored.docx"
    restored_docx_path = Path(restored_docx_name)

    print(f"正在从 {commit_id} 检出 {docx_file_name}...")
    
    try:
        run_command(["git", "checkout", commit_id, "--", str(docx_path)])
        print(f"  [检出] 成功，正在重命名为 {restored_docx_name}...")
        docx_path.rename(restored_docx_path)
        
        print(f"\n成功！版本已恢复为: {restored_docx_path}")
        
    except Exception as e:
        print(f"\n恢复过程中发生错误: {e}")
        print("正在尝试清理工作目录...")
        
    finally:
        print(f"  [清理] 正在将 {docx_path} 重置回 HEAD...")
        run_command(["git", "checkout", "HEAD", "--", str(docx_path)], check=False)
        print("清理完成。")

# --- (V4.5 修复) ---
def main():
    parser = argparse.ArgumentParser(
        description="一个用于 .docx 文件的 Git 版本控制工具 (V4.5 - textconv)。",
        prog="wg"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Init
    subparsers.add_parser("init", help="在一个新目录中初始化 'wg' 仓库并配置 pandoc diff。")

    # Status
    status_parser = subparsers.add_parser("status", help="运行 'git status' (默认所有 .docx)。")
    status_parser.add_argument(
        "files", 
        nargs="*", 
        help="[可选] 指定要检查的 .docx 文件 (默认: 所有)"
    )

    # Diff
    diff_parser = subparsers.add_parser("diff", help="运行 'git diff' (Git 会自动调用 pandoc)。")
    diff_parser.add_argument(
        "files", 
        nargs="*", 
        help="[可选] 指定要比较的 .docx 文件 (默认: 所有)"
    )

    # Log
    log_parser = subparsers.add_parser("log", help="显示 .docx 文件的提交历史。")
    log_parser.add_argument(
        "files", 
        nargs="*", 
        help="[可选] 指定要查看日志的 .docx 文件 (默认: 所有)"
    )

    # Commit
    commit_parser = subparsers.add_parser("commit", help="运行 'git add' 和 'git commit'。")
    commit_parser.add_argument("-m", "--message", required=True, help="提交信息 (必填)")
    commit_parser.add_argument(
        "files", 
        nargs="*", 
        help="[可选] 指定要提交的 .docx 文件 (默认: 所有)"
    )

    # Restore
    restore_parser = subparsers.add_parser(
        "restore", 
        help="从历史记录中恢复一个 100%% 保真度的 .docx 版本" # (V4.3 修复: 100% -> 100%%)
    )
    restore_parser.add_argument(
        "commit_id", 
        help="要恢复的 commit ID (可以从 'wg log' 中获取)"
    )
    restore_parser.add_argument(
        "docx_file", 
        help="您想要恢复的原始 .docx 文件名 (例如 'pr.docx')"
    )

    args = parser.parse_args()

    # --- 路由更新 ---
    if args.command == "init":
        handle_init()
    elif args.command == "status":
        handle_status(args.files)
    elif args.command == "diff":
        handle_diff(args.files)
    elif args.command == "commit":
        handle_commit(args.message, args.files)
    elif args.command == "log":
        handle_log(args.files)
    elif args.command == "restore":
        handle_restore(args.commit_id, args.docx_file)

if __name__ == "__main__":
    main()