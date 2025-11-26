# 基于 Pandoc 的 Docx 文档版本管理的实现

## 1. 引言 (Introduction)

在传统的文档管理中，Microsoft Word (.docx) 文件由于其二进制（实际上是压缩的 XML）格式，难以像纯文本代码那样进行版本控制。Git 虽然强大，但默认无法直观地展示 .docx 文件的具体修改内容（Diff）。

本项目 **GituDoc** 旨在解决这一痛点，通过结合 **Git** 的版本控制能力与 **Pandoc** 的文档转换能力，实现了一个对非技术用户友好的、可视化的 Word 文档版本管理系统。

## 2. 系统架构 (System Architecture)

本项目采用 **B/S (Browser/Server)** 架构，分为前端、后端和核心逻辑层。

*   **前端 (Frontend)**: 基于 **Vue.js 3** + **Vite** 构建。提供直观的用户界面，包括文件列表、提交历史、Diff 视图等。
*   **后端 (Backend)**: 基于 **Python FastAPI**。提供 RESTful API，负责处理前端请求并调用底层 Git 操作。
*   **核心逻辑 (Core)**: 封装在 `wg.py` 模块中，通过 Python 的 `subprocess` 调用系统 Git 和 Pandoc 命令。

## 3. 核心技术实现 (Core Implementation)

### 3.1 Git 与 Pandoc 的结合 (Textconv)

这是本项目的核心创新点。Git 允许用户定义 "textconv" 驱动，在进行 diff 操作前先将二进制文件转换为文本。

1.  **配置 `.gitattributes`**:
    我们在项目初始化时，自动在仓库根目录创建 `.gitattributes` 文件，指定 `.docx` 文件使用名为 `pandoc` 的 diff 驱动：
    ```text
    *.docx diff=pandoc
    ```

2.  **配置 Git Config**:
    通过 `git config` 命令，定义 `pandoc` 驱动的具体转换逻辑：
    ```bash
    git config diff.pandoc.textconv "pandoc -t markdown"
    ```
    这意味着，每当 Git 需要比较两个 .docx 文件时，它会先调用 Pandoc 将它们转换为 **Markdown** 格式，然后比较 Markdown 文本的差异。

### 3.2 自动化初始化 (Automated Initialization)

为了降低用户门槛，系统实现了“一键初始化”：

*   当用户添加一个文件夹时，后端会自动检查是否存在 `.git` 目录。
*   如果不存在，自动执行 `git init`。
*   自动配置上述的 `.gitattributes` 和 `git config`。
*   自动创建 `.gitignore` 排除临时文件（如 `~$*.docx`）。

### 3.3 安全的版本回溯 (Safe Restore)

传统的 `git checkout` 或 `git revert` 对于二进制文件容易产生冲突或覆盖风险。本项目设计了 **"Restore Copy"** 机制：

*   **原理**: 使用 `git show <commit_id>:<filename>` 命令，直接从 Git 对象库中读取指定版本的二进制流。
*   **实现**: 将读取到的流写入到一个**新文件**中（命名为 `原文件名_v<commit_hash>_copy.docx`），并存放在 `Restore Copy` 子目录下。
*   **优势**: 这种方式完全不触碰当前工作区的文件，避免了 Git 索引冲突，保证了数据的绝对安全。

## 4. 前端交互设计 (Frontend Design)

*   **可视化 Diff**: 前端接收后端返回的 Diff 文本（Markdown 格式），通过自定义的解析器将其渲染为“绿色背景（新增）”和“红色背景（删除）”的直观视图。
*   **实时状态轮询**: 使用 `setInterval` 定期轮询后端 API，实时感知文件的修改状态（Modified / Untracked），实现了类似 IDE 的实时 Git 状态监控。
*   **单文件历史**: 通过 `git log -- <filename>` 获取特定文件的提交历史，使用户能专注于单个文档的演变。

## 5. 便携化部署 (Portable Deployment)

为了方便非技术用户使用，项目实现了“服务器版”打包：

1.  **前端内嵌**: Vue 项目编译为静态资源 (`dist/`)。
2.  **后端托管**: FastAPI 配置 `StaticFiles` 挂载，直接托管前端静态文件。
3.  **一键启动**: 编写 `start.py` 脚本，自动启动 Web 服务器并调用系统浏览器打开页面，实现了“双击即用”的体验。

## 6. 总结 (Conclusion)

本项目成功地将 Git 的强大功能封装在了一个简洁的 Web 界面之下，利用 Pandoc 巧妙地解决了 Word 文档的 Diff 难题。它不仅适合个人文档管理，也为非技术团队的文档协作提供了一种轻量级、低成本的解决方案。
