# DAMN - IELTS Speaking Assistant

🎓 **D**aily **A**ssistant for **M**astering **N**ative - 你的雅思口语练习伙伴

> 💬 *"Damn! My speaking is so good now!"*

---

## 😎 关于名字

**Q: 为什么叫 DAMN？**

A: 因为这是一个**正经**的缩写：
- **D**aily **A**ssistant for **M**astering **N**ative
- 日常母语掌握助手

当然，你也可以理解为：
- *"Damn! 我的口语真 TM 厉害！"*
- *"Damn! 这个助手好用！"*

🤫 老师问起时，请使用第一个解释。

## ✨ 功能特性

- 🎤 **语音输入** - 使用 Whisper 进行准确的语音识别，支持自动静音检测
- 🔊 **语音输出** - 使用 Edge TTS 生成自然的英语发音
- 💬 **自由聊天** - 日常英语对话练习
- 📚 **雅思话题** - 支持 Part 1/2/3 全真模拟
- 🔍 **联网搜索** - 获取最新信息和时事内容
- 💡 **语法纠正** - 实时语法反馈和改进建议
- 🌐 **混合搜索** - Tavily API + DuckDuckGo 双引擎

## 📁 项目结构

```
ielts_speaking_buddy/
├── main.py                 # 主程序入口 (CLI 版本)
├── app.py                  # Web API 服务器
├── index.html              # Web 前端页面
├── config.py               # 配置文件
├── requirements.txt        # 依赖列表
├── .env.example           # 环境变量模板
│
├── core/
│   ├── bot.py             # 对话机器人核心
│   ├── modes.py           # 模式管理
│   └── feedback.py        # 语法反馈
│
├── llm/
│   └── glm_client.py      # 智谱 AI 客户端
│
├── stt/
│   └── whisper_engine.py  # 语音识别
│
├── tts/
│   └── edge_tts_engine.py # 语音合成
│
├── search/
│   └── search_engine.py   # 搜索模块
│
├── utils/
│   └── audio_player.py    # 音频播放
│
├── static/                # Web 前端资源
│   ├── style.css          # 样式文件
│   └── script.js          # 前端逻辑
│
└── data/
    ├── topics/            # 雅思话题库
    └── history/           # 对话历史
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

复制环境变量模板并填写：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 智谱 AI API (免费)
# 获取地址：https://open.bigmodel.cn/
ZHIPU_API_KEY=your_api_key_here

# Tavily 搜索 API (免费额度 1000 次/月)
# 获取地址：https://tavily.com/
TAVILY_API_KEY=your_api_key_here
```

### 3. 下载whisper模型（国内镜像）

```bash
python download_whisper.py
```

### 4. 运行程序

**方式一：命令行版本**
```bash
python main.py
```

**方式二：Web 版本（推荐）**
```bash
python app.py
```

然后访问：http://localhost:5000

## 🌐 Web 前端

Web 版本采用 **ChatGPT 风格**的简洁界面，提供以下功能：

- 💬 **实时对话** - 类似 ChatGPT 的对话体验
- 🎤 **语音输入** - 点击麦克风按钮即可录音
- 🔊 **语音输出** - AI 回复自动朗读（可选）
- 📚 **雅思模式** - 选择 Part 1/2/3 进行专项练习
- 💡 **语法反馈** - 实时显示语法建议
- 🔍 **智能搜索** - 自动检测需要搜索的问题

### Web 版快捷键

| 快捷键 | 功能 |
|--------|------|
| Enter | 发送消息 |
| Shift+Enter | 换行 |

## 📖 使用说明

### 基本流程

1. **选择模式**
   - 自由聊天：日常英语对话
   - 雅思练习：Part 1/2/3 模拟

2. **选择输入方式**
   - 文字输入：直接打字
   - 语音输入：麦克风录音（待实现完整功能）

3. **选择输出方式**
   - 文字 + 语音
   - 仅文字
   - 仅语音

### 可用命令

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/mode` | 切换对话模式 |
| `/topic` | 获取新雅思话题 |
| `/search <内容>` | 强制搜索后回复 |
| `/history` | 保存对话历史 |
| `/clear` | 清空对话历史 |
| `/quit` | 退出程序 |

### 搜索功能

支持**混合触发模式**：

1. **自动搜索** - 当检测到以下关键词时自动搜索：
   - 最新、最近、新闻、时事
   - 2025/2026/2027
   - new, latest, news, recent, today

2. **手动搜索** - 使用 `/search` 命令：
   ```
   /search 最新 AI 技术突破
   ```

## ⚙️ 配置说明

### 主要配置项 (config.py)

```python
# 语音合成声音
TTS_CONFIG = {
    "voice": "en-US-JennyNeural",  # 推荐女声
}

# Whisper 模型
WHISPER_CONFIG = {
    "model": "base",  # tiny/base/small/medium/large
}

# 搜索关键词
SEARCH_CONFIG = {
    "auto_search_keywords": ["最新", "最近", "news", "latest"],
}
```

### 更换 TTS 声音

编辑 `config.py` 中的 `TTS_CONFIG`：

```python
# 可选声音
"en-US-JennyNeural"     # 女声 (推荐)
"en-US-GuyNeural"       # 男声
"en-GB-SoniaNeural"     # 英式女声
"en-GB-RyanNeural"      # 英式男声
```

## 🔧 进阶用法

### 仅使用文字模式（无需音频设备）

修改输出模式选择为"仅文字"即可。

### 提高语音识别准确度

使用更大的 Whisper 模型：

```python
WHISPER_CONFIG = {
    "model": "small",  # 更准确但更慢
}
```

### 自定义雅思话题

在 `data/topics/` 目录下添加自定义话题文件。

## 📋 依赖说明

| 依赖 | 用途 |
|------|------|
| faster-whisper | 语音识别 (STT) |
| edge-tts | 语音合成 (TTS) |
| httpx | HTTP 客户端 |
| tavily-python | 搜索 API |
| duckduckgo-search | 备选搜索 |
| python-dotenv | 环境变量管理 |
| pygame | 音频播放 |

## 🆓 API 额度说明

### 智谱 AI (GLM-4-Flash)
- ✅ **完全免费**
- 速率限制：约 60 次/分钟
- 适合日常练习

### Tavily Search
- ✅ **免费额度**: 1000 次搜索/月
- 超出后可切换到 DuckDuckGo（完全免费）

## 🐛 常见问题

### Q: 语音识别不准确？
A: 尝试使用更大的 Whisper 模型（small 或 medium），或确保发音清晰。

### Q: TTS 生成失败？
A: 检查网络连接，Edge TTS 需要访问微软服务。

### Q: 搜索功能不可用？
A: 检查是否配置了 TAVILY_API_KEY，或确保 duckduckgo-search 已安装。

### Q: 语法反馈不显示？
A: 短句（<10 词）不会触发语法检查，这是正常行为。

## 📝 更新日志

- **v0.1.0** (2026-03) - 初始版本
  - 基础对话功能
  - 语音输入/输出
  - 语法纠正
  - 联网搜索
  - 雅思话题库

## 📄 许可证

MIT License

## 🙏 致谢

- [智谱 AI](https://open.bigmodel.cn/) - 提供免费的 LLM API
- [Tavily](https://tavily.com/) - 搜索服务
- [OpenAI Whisper](https://github.com/openai/whisper) - 语音识别
- [Edge TTS](https://github.com/rany2/edge-tts) - 微软语音合成
