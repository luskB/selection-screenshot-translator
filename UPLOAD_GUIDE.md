# GitHub 上传指南

由于系统未安装 Git，请按照以下步骤手动上传项目到 GitHub：

## 方式一：使用 GitHub Desktop（推荐）

1. 下载并安装 [GitHub Desktop](https://desktop.github.com/)
2. 登录你的 GitHub 账号
3. 点击 File → Add Local Repository
4. 选择项目文件夹：`D:\opencodetext`
5. 点击 "Publish repository"
6. 设置仓库名称：`selection-translator`
7. 添加描述：`A lightweight Windows desktop translation tool with mouse selection and image translation support`
8. 取消勾选 "Keep this code private"（如果要公开）
9. 点击 "Publish repository"

## 方式二：使用 Git 命令行

1. 下载并安装 [Git for Windows](https://git-scm.com/download/win)
2. 打开命令行，进入项目目录：
```bash
cd D:\opencodetext
```

3. 初始化仓库并提交：
```bash
git init
git add .
git commit -m "Initial commit: Selection Translator v1.0"
```

4. 在 GitHub 网站创建新仓库：
   - 访问 https://github.com/new
   - 仓库名：`selection-translator`
   - 描述：`A lightweight Windows desktop translation tool with mouse selection and image translation support`
   - 选择 Public
   - 不要勾选任何初始化选项（README、.gitignore、license）

5. 关联远程仓库并推送：
```bash
git remote add origin https://github.com/你的用户名/selection-translator.git
git branch -M main
git push -u origin main
```

## 方式三：直接在 GitHub 网站上传

1. 访问 https://github.com/new 创建新仓库
   - 仓库名：`selection-translator`
   - 描述：`A lightweight Windows desktop translation tool with mouse selection and image translation support`
   - 选择 Public
   - 不要勾选任何初始化选项

2. 创建后，点击 "uploading an existing file"

3. 将以下文件拖拽到网页上传：
   - `main.py`
   - `translator_engines.py`
   - `ui_components.py`
   - `config_manager.py`
   - `icon.ico`
   - `README.md`
   - `LICENSE`
   - `requirements.txt`
   - `.gitignore`

4. 填写提交信息：`Initial commit: Selection Translator v1.0`

5. 点击 "Commit changes"

## 需要上传的文件清单

✅ 核心代码文件：
- main.py
- translator_engines.py
- ui_components.py
- config_manager.py

✅ 资源文件：
- icon.ico

✅ 文档文件：
- README.md
- LICENSE
- requirements.txt
- .gitignore

❌ 不要上传：
- config.json（配置文件，包含敏感信息）
- dist/ 目录（编译��出）
- build/ 目录（编译临时文件）
- __pycache__/ 目录
- *.pyc 文件
- *.spec 文件
- 备份文件（dist16, dist18 等）

## 发布 Release

上传完成后，建议创建一个 Release：

1. 进入仓库页面
2. 点击右侧的 "Releases" → "Create a new release"
3. Tag version: `v1.0.0`
4. Release title: `Selection Translator v1.0.0`
5. 描述发布内容（可以从 README 复制主要特性）
6. 上传编译好的 `划词翻译.exe` 文件（从 dist 目录）
7. 点击 "Publish release"

## 仓库设置建议

- **Topics**: 添加标签如 `translation`, `windows`, `pyqt5`, `ocr`, `translator`
- **About**: 添加项目描述和网站链接
- **README**: 已自动生成，包含完整的使用说明

## 后续维护

每次更新代码后：
```bash
git add .
git commit -m "描述你的更改"
git push
```

---

项目已准备就绪，所有必要文件都已创建！
