#!/usr/bin/env python3

import sys
import subprocess
import argparse
from pathlib import Path

# --- V4.7 架构 (Web API Ready) ---
# 1. 重构为库模式: 所有 handle_* 函数接受 project_path
# 2. 返回数据而非打印: 供 API 调用
# 3. 异常处理: 抛出异常而非 sys.exit

def run_command(command, capture_output=False, check=True, shell=False, cwd=None):
    """(V3.1 修复) 一个通用的、健壮的子进程运行器"""
    try:
        # Pager logic (git log/diff) only applies when running as CLI script and not capturing output
        is_pager_command = (
            (command[0] == "git" and command[1] == "log") or
            (command[0] == "git" and command[1] == "diff" and "--quiet" not in command)
        )

        if is_pager_command and not capture_output and not shell:
            # Note: Interactive pager won't work well in API mode, but kept for CLI compatibility
            process = subprocess.Popen(command, text=True, cwd=cwd)
            process.wait() 
            if check and process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, command)
            return process
        
        result = subprocess.run(
            command,
            check=check,
            text=True,
            capture_output=capture_output,
            shell=shell,
            cwd=cwd
        )
        return result
        
    except FileNotFoundError as e:
        # In library mode, we might want to raise this to be caught by API
        raise RuntimeError(f"依赖命令未找到: {e.filename}. 请确保 git 和 pandoc 都在系统 PATH 中。")
    except subprocess.CalledProcessError as e:
        # Capture stderr for better error messages
        error_msg = f"命令执行失败 (Code: {e.returncode}): {command}"
        if e.stderr:
            error_msg += f"\nStderr:\n{e.stderr}"
        if e.stdout:
            error_msg += f"\nStdout:\n{e.stdout}"
        raise RuntimeError(error_msg)

def check_init_status(project_path):
    """(V4.0 简化) 检查 .git 目录是否存在"""
    git_dir = Path(project_path) / ".git"
    if not git_dir.is_dir():
        raise RuntimeError(f"这不是一个 'wg' 仓库 (未找到 .git 目录: {git_dir})。请先初始化。")

# --- (V4.5 新增) ---
def get_docx_files(project_path):
    """
    (V4.6 QoL 修复) 
    获取指定目录下的所有 .docx 文件, 忽略 Office 临时文件。
    返回一个相对路径的字符串列表。
    """
    current_dir = Path(project_path)
    if not current_dir.exists():
         raise RuntimeError(f"项目路径不存在: {project_path}")

    all_files = current_dir.glob("*.docx")
    
    valid_files = [
        f for f in all_files 
        if not f.name.startswith("~$") and not f.name.startswith(".~")
    ]
    
    return [f.name for f in valid_files] # (V4.6 修复) str(f) -> f.name

# --- (V4.4 修复) ---
def handle_init(project_path):
    """
    (V4.4 核心) 
    初始化 Git 仓库并自动配置 'textconv' 以便 diff .docx。
    """
    path_obj = Path(project_path)
    if not path_obj.exists():
        path_obj.mkdir(parents=True, exist_ok=True)

    # Check if git is already initialized
    git_dir = Path(project_path) / ".git"
    if not git_dir.exists():
        # print(f"Initializing Git repository in {project_path}...") # Removed print for API mode
        run_command(["git", "init"], cwd=project_path)
    else:
        pass # print(f"Git repository already exists in {project_path}.") # Removed print for API mode

    # Always ensure pandoc config is applied (idempotent)
    # 1. Configure gitattributes
    attr_file = Path(project_path) / ".gitattributes"
    if not attr_file.exists() or "*.docx diff=pandoc" not in attr_file.read_text():
        with open(attr_file, "a") as f:
            f.write("\n*.docx diff=pandoc\n")

    # 2. Configure git config for textconv
    # We use 'pandoc -t markdown' to convert docx to text for diffing
    pandoc_cmd_string = "git config diff.pandoc.textconv \"pandoc -t markdown\""
    try:
        run_command(pandoc_cmd_string, shell=True, cwd=project_path)
        # (V5.1 Fix) Disable quotePath to handle non-ASCII filenames correctly
        run_command(["git", "config", "core.quotePath", "false"], cwd=project_path)
    except Exception as e:
        raise RuntimeError(f"配置 Git 驱动失败: {e}")
    
    # 4. (V4.0 修改) 创建 .gitignore
    gitignore_path = path_obj / ".gitignore"
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
                patterns_added = True

    # 5. (V4.0 新增) 提交配置文件
    config_files_to_add = []
    # Check if we need to commit .gitattributes (we just ensured it exists above)
    # To be safe, we can just check if it has changes or is untracked
    status_output = run_command(["git", "status", "--porcelain", ".gitattributes"], capture_output=True, check=False, cwd=project_path).stdout
    if status_output:
        config_files_to_add.append(".gitattributes")

    if patterns_added:
        config_files_to_add.append(".gitignore")

    if config_files_to_add:
        # print("正在提交 'wg' 配置文件到仓库...")
        is_initial_commit = run_command(["git", "rev-parse", "--verify", "HEAD"], check=False, cwd=project_path).returncode != 0
        
        run_command(["git", "add"] + config_files_to_add, cwd=project_path)
        
        commit_msg = "Initial commit: Configure wg (pandoc diff)" if is_initial_commit else "Update wg config (pandoc diff)"
        run_command(["git", "commit", "-m", commit_msg], cwd=project_path)

    return True

# --- (V4.5 修复) ---
def handle_status(project_path, files=None):
    """
    (V4.5 修复) 运行 'git status'
    Returns: List of dicts [{'path': 'file.docx', 'status': 'M'}, ...]
    """
    check_init_status(project_path)
    # (V4.5 修复) 使用 get_docx_files() 替代 '*.docx'
    files_to_check = files if files else get_docx_files(project_path)
    if not files_to_check:
        return []

    # Run git status --short
    # Output format: " M file.docx", "?? new.docx"
    result = run_command(
        ["git", "status", "--short", "--"] + files_to_check, 
        capture_output=True, 
        check=False,
        cwd=project_path
    )
    
    status_list = []
    if result.stdout:
        lines = result.stdout.split('\n')
        for line in lines:
            if not line: continue
            # XY Path
            # X: index status, Y: worktree status
            status_code = line[:2].strip()
            file_path = line[3:].strip()
            # 简单映射：如果有任何修改，就显示状态
            status_list.append({"path": file_path, "status": status_code})
            
    return status_list

# --- (V4.5 修复) ---
def handle_diff(project_path, files=None):
    """
    (V4.5 修复) 运行 'git diff'
    Returns: String (diff output)
    """
    check_init_status(project_path)
    # (V4.5 修复) 使用 get_docx_files() 替代 '*.docx'
    files_to_check = files if files else get_docx_files(project_path)
    if not files_to_check:
        return "No .docx files found."

    # Capture output instead of printing
    result = run_command(
        ["git", "diff", "--"] + files_to_check, 
        capture_output=True, 
        check=False,
        cwd=project_path
    )
    return result.stdout

# --- (V4.5 修复) ---
def handle_commit(project_path, message, files=None):
    """
    (V4.5 修复) 'git add' 并 'git commit'
    Returns: True if committed, False if nothing to commit. Raises exception on error.
    """
    check_init_status(project_path)
    
    # (V4.5 修复) 使用 get_docx_files() 替代 '*.docx'
    files_to_add = files if files else get_docx_files(project_path)
    if not files_to_add:
        raise RuntimeError("未找到要提交的 .docx 文件。")
    
    run_command(["git", "add"] + files_to_add, cwd=project_path)
    
    # (V4.1 修复) 检查是否有实际变更或错误
    check_cmd = run_command(["git", "diff", "--staged", "--quiet"], check=False, cwd=project_path)
    
    if check_cmd.returncode == 0:
        return False # Nothing to commit
    elif check_cmd.returncode == 1:
        run_command(["git", "commit", "-m", message], cwd=project_path)
        return True
    else:
        raise RuntimeError("git diff 检查失败 (可能由 pandoc 引起)。")

# --- (V4.5 修复) ---
def handle_log(project_path, files=None):
    """
    (V4.5 修复) 显示 .docx 文件的 'git log'
    Returns: List of dicts [{'id': '...', 'message': '...', 'author': '...', 'date': '...'}]
    """
    check_init_status(project_path)
    # (V4.5 修复) 使用 get_docx_files() 替代 '*.docx'
    files_to_log = files if files else get_docx_files(project_path)
    if not files_to_log:
        return []

    # Custom format for parsing
    # %h: short hash, %s: subject, %an: author name, %ad: author date
    fmt = "%h|%s|%an|%ad"
    result = run_command(
        ["git", "log", f"--format={fmt}", "--date=short", "--"] + files_to_log, 
        capture_output=True, 
        check=False,
        cwd=project_path
    )
    
    logs = []
    if result.stdout:
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if not line: continue
            parts = line.split('|')
            if len(parts) >= 4:
                logs.append({
                    "id": parts[0],
                    "message": parts[1],
                    "author": parts[2],
                    "date": parts[3]
                })
    return logs

# --- (V4.0 重大简化) ---
def handle_restore(project_path, commit_id, docx_file_name):
    """
    (V4.0 简化)
    从 Git 历史中恢复一个 100% 保真度的 .docx 文件。
    Returns: Path of restored file (str)
    """
    check_init_status(project_path)
    
    path_obj = Path(project_path)
    docx_path = path_obj / docx_file_name
    
    if not docx_file_name.endswith(".docx"):
        raise ValueError(f"文件 {docx_file_name} 不是 .docx 文件")

    restored_docx_name = f"{Path(docx_file_name).stem}.{commit_id[:7]}.restored.docx"
    restored_docx_path = path_obj / restored_docx_name

    try:
        run_command(["git", "checkout", commit_id, "--", docx_file_name], cwd=project_path)
        
        # Rename the checked out file (which overwrote the current one temporarily) to the restored name
        # Wait, git checkout <commit> -- <file> updates the file in working directory.
        # We want to keep current file and save restored as new file.
        # So we rename the checked-out file to restored_name, then checkout HEAD to restore current.
        
        if docx_path.exists():
            docx_path.rename(restored_docx_path)
        else:
             # Should not happen if git checkout succeeded
             raise RuntimeError("Checkout succeeded but file not found.")
        
        return str(restored_docx_path)
        
    except Exception as e:
        raise RuntimeError(f"恢复过程中发生错误: {e}")
        
    finally:
        # Clean up: restore the original file from HEAD
        run_command(["git", "checkout", "HEAD", "--", docx_file_name], check=False, cwd=project_path)

# --- (V5.0 新增) ---
def handle_reset(project_path, commit_id):
    """
    (V5.0 新增)
    执行 'git reset --hard <commit_id>'
    警告: 这将丢弃所有未提交的更改以及该 commit 之后的提交。
    """
    check_init_status(project_path)
    try:
        run_command(["git", "reset", "--hard", commit_id], cwd=project_path)
        return True
    except Exception as e:
        raise RuntimeError(f"重置失败: {e}")

def handle_revert_commit(project_path, commit_id):
    """
    (V5.0 新增)
    执行 'git revert --no-edit <commit_id>'
    创建一个新的提交来撤销指定 commit 的更改。
    """
    check_init_status(project_path)
    try:
        # --no-edit: 不打开编辑器，直接使用默认提交信息
        run_command(["git", "revert", "--no-edit", commit_id], cwd=project_path)
        return True
    except Exception as e:
        # 如果 revert 失败（例如冲突），必须 abort 以清理状态
        print(f"DEBUG: Revert failed, attempting abort. Error: {e}")
        try:
            run_command(["git", "revert", "--abort"], check=False, cwd=project_path)
        except:
            pass
        
        # 检查是否是二进制文件冲突
        if "Cannot merge binary files" in str(e) or "conflict" in str(e).lower():
             raise RuntimeError(f"撤销失败: 检测到二进制文件冲突。对于 .docx 文件，git revert 经常会因为无法自动合并而失败。建议使用 Reset 回退到旧版本，或者手动恢复文件。")
        
        raise RuntimeError(f"撤销失败: {e}")

# --- CLI Entry Point ---
def main():
    parser = argparse.ArgumentParser(
        description="一个用于 .docx 文件的 Git 版本控制工具 (V4.7 - Lib/CLI)。",
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
        help="从历史记录中恢复一个 100%% 保真度的 .docx 版本" 
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
    
    # CLI 模式下，project_path 默认为当前目录
    current_cwd = str(Path.cwd())

    try:
        if args.command == "init":
            handle_init(current_cwd)
            print("WG 仓库初始化完成。")
        elif args.command == "status":
            items = handle_status(current_cwd, args.files)
            if not items:
                print("没有变更或未找到 .docx 文件。")
            else:
                print(f"--- Git 状态 ---")
                for item in items:
                    print(f"{item['status']} {item['path']}")
        elif args.command == "diff":
            diff = handle_diff(current_cwd, args.files)
            print(diff)
        elif args.command == "commit":
            if handle_commit(current_cwd, args.message, args.files):
                print("提交成功！")
            else:
                print("无需提交。")
        elif args.command == "log":
            logs = handle_log(current_cwd, args.files)
            print(f"--- Git 日志 ---")
            for log in logs:
                print(f"{log['id'][:7]} | {log['message']} | {log['author']} | {log['date']}")
        elif args.command == "restore":
            path = handle_restore(current_cwd, args.commit_id, args.docx_file)
            print(f"成功！版本已恢复为: {path}")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()