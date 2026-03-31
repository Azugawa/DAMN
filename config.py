"""
项目配置文件
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==================== 路径配置 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TOPICS_DIR = os.path.join(DATA_DIR, "topics")
HISTORY_DIR = os.path.join(DATA_DIR, "history")
TMP_DIR = os.path.join(BASE_DIR, "tmp")
DB_PATH = os.path.join(DATA_DIR, "damn.db")

# 确保目录存在
for dir_path in [DATA_DIR, TOPICS_DIR, HISTORY_DIR, TMP_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# ==================== API 配置 ====================
# 智谱 AI API
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
ZHIPU_LLM_MODEL = os.getenv("ZHIPU_LLM_MODEL", "glm-4-flash")

# Tavily 搜索 API
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# ==================== 搜索配置 ====================
SEARCH_CONFIG = {
    "provider": "tavily",  # 或 "duckduckgo"
    "max_results": 3,
    # 自动搜索关键词（检测到这些词时自动触发搜索）
    "auto_search_keywords": [
        "最新", "最近", "新闻", "时事",
        "2025", "2026", "2027",
        "new", "latest", "news", "recent",
        "today", "this week", "this month", "this year",
    ],
    # 强制搜索命令
    "search_commands": ["/search", "/s "],
}

# ==================== 语音配置 ====================
AUDIO_CONFIG = {
    "input_device_index": None,  # None 表示使用默认设备
    "sample_rate": 16000,
    "output_file": os.path.join(TMP_DIR, "output.mp3"),
}

# ==================== Whisper 配置 ====================
WHISPER_CONFIG = {
    "model": "D:\desktop\DAMN\models\whisper",  # tiny, base, small, medium, large
    "device": "auto",  # auto, cpu, cuda
    "compute_type": "float16",  # float16, int8, int8_float16
}

# ==================== Edge TTS 配置 ====================
TTS_CONFIG = {
    "voice": "en-US-JennyNeural",  # 推荐的女声，清晰自然
    # 其他可选声音:
    # - en-US-GuyNeural (男声)
    # - en-GB-SoniaNeural (英式女声)
    # - en-GB-RyanNeural (英式男声)
    "rate": "+0%",  # 语速
    "volume": "+0%",  # 音量
    "pitch": "+0Hz",  # 音调
}

# ==================== LLM 配置 ====================
LLM_CONFIG = {
    "temperature": 0.7,
    "max_tokens": 1024,
    "timeout": 30,
}

# ==================== 系统提示词 ====================
SYSTEM_PROMPT = """You are DAMN (Daily Assistant for Mastering Native), an IELTS speaking practice assistant. Your role is to:

1. Help users practice English speaking through natural conversation
2. Provide gentle grammar corrections when needed
3. Ask follow-up questions to encourage longer responses
4. Simulate IELTS speaking test scenarios (Part 1, 2, 3)
5. **Actively challenge the user** with thought-provoking questions to test their speaking abilities

**Important Guidelines:**
- Speak naturally and friendly, like a real conversation partner
- Keep responses concise (2-4 sentences for normal chat)
- When the user makes noticeable grammar mistakes, provide brief corrections
- For IELTS practice, follow the official IELTS speaking format
- You have access to web search for current events and latest information
- **After every 2-3 exchanges, ask a challenging follow-up question** to push the user's speaking abilities
- **Use varied question types**: opinion questions, hypothetical scenarios, comparison questions, "why" questions
- **Encourage elaboration**: Ask users to explain their reasoning, give examples, or consider alternative perspectives

**Question Types to Use:**
1. Opinion: "What's your stance on...?" / "Do you believe that...?"
2. Hypothetical: "If you could..., what would you...?" / "Imagine a scenario where..."
3. Comparison: "How does X compare to Y in terms of...?"
4. Evaluation: "What are the advantages and disadvantages of...?"
5. Prediction: "How do you think... will change in the future?"

**Response Format:**
When providing grammar feedback, use this format:
```
💡 Quick tip: [brief suggestion]
Better: [improved version]
```

Then continue the conversation naturally with a challenging question.
"""

# ==================== 语法纠正 Prompt ====================
GRAMMAR_CHECK_PROMPT = """Please analyze the following English text (may contain some Chinese words) for grammar issues and provide helpful feedback for an IELTS speaking student:

Text: "{text}"

**Important Guidelines:**
1. **Understand the meaning first**: Read the entire text to understand what the student is trying to express, even if some words are used incorrectly.
2. **Chinese words**: The student may use Chinese when they don't know the English word. Provide the English translation as a vocabulary suggestion - do NOT treat this as an error.
3. **Wrong word usage**: If a word seems misused, try to understand what they meant and correct it in the "More Natural Expression" section.
4. **Be encouraging**: Focus on communication effectiveness, not just grammatical perfection.

Provide feedback in this format:

**1. More Natural Expression:**
First understand the intended meaning, then rewrite the ENTIRE text in a natural, fluent way that an IELTS band 7+ speaker would use. Correct any misused words based on context. If there are Chinese words, provide their English translation in parentheses. Keep it conversational but polished.

**2. Grammar & Vocabulary Issues:**
- List 2-3 specific grammar/vocabulary errors with brief explanations
- For Chinese words, simply provide the English translation (don't treat as errors)
- If a word was misused, explain what the correct word should be and why
- Be encouraging and focus on the most important issues

**3. Tips for Expanding Your Answer:**
Suggest 2-3 specific aspects or angles the student could elaborate on to make their answer richer and longer. For example:
- Personal examples or experiences
- Comparisons (past vs present, pros vs cons)  
- Reasons and consequences
- Feelings and opinions
- Future plans or predictions

Keep feedback concise, supportive, and practical.
"""

# ==================== 搜索相关 Prompt ====================
SEARCH_JUDGE_PROMPT = """Determine if this question requires web search:

User input: "{text}"

Answer YES if:
- It's about current events, news, or recent information
- It asks about something you're unsure about
- It requires up-to-date information (after your knowledge cutoff)
- The user explicitly asks you to search

Answer NO for:
- General knowledge questions
- Personal questions about the user
- Opinion-based questions
- IELTS practice questions

Just answer "YES" or "NO".
"""

SEARCH_INTEGRATE_PROMPT = """Here's some information I found:

{search_results}

Based on this, please answer the user's question naturally:

User: {question}

Integrate the information naturally into your response. Don't say "according to search results".
Just answer as if you naturally know this information.
"""

# ==================== 雅思话题配置 ====================
IELTS_CONFIG = {
    "part1_topics": [
        "Work/Studies",
        "Hometown",
        "Accommodation",
        "Hobbies",
        "Music",
        "Reading",
        "Sports",
        "Travel",
        "Food",
        "Weather",
    ],
    "part2_categories": [
        "Describe a person",
        "Describe a place",
        "Describe an object",
        "Describe an event",
        "Describe an activity",
        "Describe a memory",
    ],
    "part3_themes": [
        "Education",
        "Technology",
        "Environment",
        "Society",
        "Culture",
        "Work",
    ],
}
