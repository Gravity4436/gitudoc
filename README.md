# GituDoc - 你的 Word 文档“时光机” 🕰️

欢迎使用 **GituDoc**！这是一个专门为不懂代码、不熟悉 Git 的用户设计的工具。它可以帮你轻松管理电脑上的 Word 文档（.docx），记录每一次修改，对比不同版本的差异，甚至随时“穿越”回之前的版本。

不再需要手动复制粘贴文件名（如 `终稿_v1.docx`, `终稿_打死不改版.docx`），GituDoc 帮你搞定一切！

---

## 🚀 第一步：环境准备

在使用之前，你需要确保电脑上安装了以下 3 个基础软件。别担心，只需要安装一次。

### 1. 安装 Git (版本控制核心)
*   **Windows**: 下载 [Git for Windows](https://git-scm.com/download/win) 并安装。一路点击“下一步”即可。
*   **Mac**: 打开终端（Terminal），输入 `git --version`。如果没有安装，系统会提示你安装 Xcode Command Line Tools，点击确认即可。

### 2. 安装 Pandoc (文档解析神器)
GituDoc 需要它来“看懂”你的 Word 文档内容。
*   **下载地址**: [Pandoc 安装包](https://github.com/jgm/pandoc/releases/latest)
*   下载对应系统的安装包（Windows 是 `.msi`，Mac 是 `.pkg`），双击安装。

### 3. 安装 Python (运行环境)
*   **下载地址**: [Python 官网](https://www.python.org/downloads/)
*   **注意**: 安装时务必勾选 **"Add Python to PATH"** (将 Python 添加到环境变量)。

---

## 🛠️ 第二步：安装与启动

1.  **下载本项目**: 点击右上角的 "Code" -> "Download ZIP"，解压到你喜欢的文件夹（例如桌面）。
2.  **打开终端/命令行**:
    *   **Windows**: 在解压后的文件夹内，右键点击空白处，选择 "Open in Terminal" 或 "Git Bash Here"。
    *   **Mac**: 打开“终端”，输入 `cd ` (注意有个空格)，然后把解压后的文件夹拖进终端窗口，按回车。

### 1. 安装依赖 (仅需一次)
在终端中输入以下命令并回车：

```bash
pip install fastapi uvicorn python-multipart
```

### 2. 一键启动 🚀
在终端中输入：

```bash
python start.py
```

**系统会自动打开浏览器访问 GituDoc，您可以直接开始使用了！**

*(以后每次使用，只需要运行 `python start.py` 这一条命令即可)*

---

## 📖 第四步：使用指南

### 1. 添加项目 (Add Project)
*   在网页首页，找到 "Add New Project"。
*   输入你存放 Word 文档的**文件夹绝对路径**。
    *   *Mac 技巧*: 在 Finder 中找到文件夹，按 `Option + Command + C` 复制路径。
    *   *Windows 技巧*: 打开文件夹，点击顶部地址栏复制路径。
*   点击 **Add**。系统会自动初始化该文件夹。

### 2. 查看变更 (View Changes)
*   点击左侧的文件名。
*   **绿色背景**表示新增的内容，**红色背景**表示删除的内容。
*   你可以清晰地看到你对文档做了哪些修改。

### 3. 保存版本 (Commit)
*   勾选你想要保存的文件（或者直接在输入框里写）。
*   在 "Commit message..." 框中写一句话，描述你改了什么（例如：“修改了第一章的错别字”）。
*   点击 **Commit** 按钮。
*   🎉 你的修改已被永久记录！

### 4. 历史与回溯 (History & Restore)
*   右侧面板显示了所有的提交历史。
*   **Revert (撤销)**: 创建一个新的提交，把文件改回那个版本的样子（“后悔药”）。
*   **Reset (重置)**: **慎用！** 彻底回到那个版本，丢弃之后的所有修改（“读档”）。

---

## ❓ 常见问题

**Q: 为什么显示 "Not a git repository"?**
A: 请尝试在首页重新点击一下该项目，系统会自动修复初始化配置。

**Q: 中文文件名乱码或 404?**
A: 我们已经修复了这个问题。重新点击项目即可自动应用修复。

**Q: 无法显示 Diff?**
A: 请确保你安装了 Pandoc 并且它在系统路径中。

---
*Enjoy your writing!* 📝
