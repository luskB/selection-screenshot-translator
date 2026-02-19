# 划词翻译 (Selection Translator)

一个轻量级的 Windows 桌面划词翻译工具，支持多种翻译引擎和图片翻译功能。

## ✨ 主要特性

- 🖱️ **鼠标划词翻译** - 选中文本后2秒内点击ALT即可翻译
- 🖼️ **图片翻译** - 支持截图翻译，识别图片中的文字并翻译（截图到剪切板后电脑左侧中部弹出按键）
- 🌐 **多引擎支持** - 集成 Google、DeepL、微软、腾讯、火山、AI 大模型等多个翻译引擎
- 🎨 **现代化界面** - 支持深色/浅色主题切换
- 📋 **一键复制** - 快速复制翻译结果
- 🔄 **智能切换** - 支持中英文互译，自动识别源语言
- 💾 **配置持久化** - 保存 API 密钥和偏好设置
- 🚀 **开机自启** - 可选的系统启动项
- 🔒 **单实例运行** - 防止重复启动占用资源

## 📸 截图

### 翻译窗口
- 可拖拽、可调整大小
- 深色/浅色主题
- 引擎和语言快速切换

### 浮动按钮
- 按住ALT-选中文本-松开ALT-松开左键后自动显示（或先选中单机ALT）
- 5秒后自动消失
- 点击其他位置立即隐藏

## 🔧 支持的翻译引擎

### 文本翻译
- **Google 翻译** - 需要代理访问
- **DeepL** - 需要 API Key
- **微软翻译** - 需要 API Key + Region
- **腾讯翻译** - 需要 SecretId + SecretKey + Region
- **火山翻译** - 需要 AccessKey + SecretKey + Region
- **AI 大模型** - 支持 OpenAI 兼容 API（GPT、Claude 等）

### 图片翻译
- **腾讯翻译** - 支持图片 OCR 翻译
- **AI 大模型** - 支持 GPT-4V 等视觉模型

## 📦 安装使用

### 方式一：直接下载（推荐）
1. 从 [Releases](../../releases) 下载最新版本的 `划词翻译.exe`
2. 双击运行即可
3. 首次运行会在系统托盘显示图标
4. 右键托盘图标 → 设置，配置翻译引擎

### 方式二：从源码运行
```bash
# 克隆仓库
git clone https://github.com/你的用户名/selection-translator.git
cd selection-translator

# 安装依赖
pip install -r requirements.txt

# 运行程序
python main.py
```

### 方式三：自行编译
```bash
# 安装 PyInstaller
pip install pyinstaller

# 编译
pyinstaller --onefile --windowed --icon=icon.ico --add-data "icon.ico;." --name "划词翻译" main.py

# 编译后的程序在 dist 目录
```

## ⚙️ 配置说明

程序会在同目录下生成 `config.json` 配置文件，包含以下设置：

```json
{
  "engine": "google",              // 默认翻译引擎
  "image_engine": "tencent",       // 图片翻译引擎
  "target_lang": "zh-CN",          // 目标语言
  "theme": "dark",                 // 主题（dark/light）
  "proxy_mode": "auto",            // 代理模式（auto/manual/direct）
  "proxy_http": "",                // HTTP 代理地址
  "proxy_https": "",               // HTTPS 代理地址
  
  // 各引擎的 API 配置
  "deepl_api_key": "",
  "microsoft_api_key": "",
  "microsoft_region": "",
  "tencent_secret_id": "",
  "tencent_secret_key": "",
  "tencent_region": "ap-beijing",
  "volcano_access_key": "",
  "volcano_secret_key": "",
  "volcano_region": "cn-north-1",
  "ai_api_key": "",
  "ai_endpoint": "",
  "ai_model": "gpt-3.5-turbo",
  "ai_prompt": ""
}
```

## 🎯 使用方法

### 文本翻译
1. 用鼠标选中任意文本
2. 2秒内点击ALT查看翻译结果
3. 可在翻译窗口切换引擎和目标语言
或
1.在划词过程中单击ALT
2.鼠标右下角出现“译”图标
3.点击即可查看翻译结果和更换目标语言与翻译引擎

### 图片翻译
1. 按下 `Print` 截图（或使用其他截图工具）
2. 复制图片到剪贴板（大部分截图工具截图后自动复制）
3. 点击屏幕左侧的"译"按钮
4. 自动识别并翻译图片中的文字

### 快捷操作
- **切换主题**：点击翻译窗口右上角的 🌙/☀️ 图标
- **复制结果**：点击翻译窗口的 📋 图标
- **重新翻译**：切换引擎或目标语言后自动重新翻译
- **关闭程序**：右键系统托盘图标 → 退出

## 🔑 获取 API 密钥

### DeepL
1. 访问 [DeepL API](https://www.deepl.com/pro-api)
2. 注册并获取 API Key（免费版每月 50 万字符）

### 微软翻译
1. 访问 [Azure Portal](https://portal.azure.com/)
2. 创建"翻译"资源
3. 获取密钥和区域

### 腾讯翻译
1. 访问 [腾讯云控制台](https://console.cloud.tencent.com/cam/capi)
2. 创建 API 密钥
3. 获取 SecretId 和 SecretKey

### 火山翻译
1. 访问 [火山引擎控制台](https://console.volcengine.com/iam/keymanage/)
2. 创建访问密钥
3. 获取 AccessKey 和 SecretKey

### AI 大模型
- 支持任何 OpenAI 兼容的 API
- 可使用 OpenAI、Azure OpenAI、国内大模型等

## 📁 项目结构

```
selection-translator/
├── main.py                 # 主程序入口
├── translator_engines.py   # 翻译引擎实现
├── ui_components.py        # UI 组件
├── config_manager.py       # 配置管理
├── icon.ico               # 程序图标
├── config.json            # 配置文件（运行时生成）
├── requirements.txt       # Python 依赖
├── README.md             # 项目说明
└── LICENSE               # 开源协议
```

## 🛠️ 技术栈

- **Python 3.9+**
- **PyQt5** - GUI 框架
- **pynput** - 鼠标键盘监听
- **requests** - HTTP 请求
- **Pillow** - 图片处理

## 📝 开发计划

- [ ] 支持更多翻译引擎
- [ ] 添加翻译历史记录
- [ ] 支持自定义快捷键
- [ ] 支持更多语言对
- [ ] 添加发音功能
- [ ] 支持批量翻译

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

## ⚠️ 注意事项

1. **Google 翻译**需要配置代理才能在中国大陆使用
2. **API 密钥**请妥善保管，不要泄露
3. 部分翻译引擎有**免费额度限制**
4. 图片翻译功能需要相应引擎支持
5. 首次运行可能被杀毒软件拦截，请添加信任

## 💬 反馈与支持

如有问题或建议，请提交 [Issue](../../issues)。

---

⭐ 如果这个项目对你有帮助，欢迎 Star！
