"""
核心对话机器人 - 整合所有模块
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from config import (
    SYSTEM_PROMPT, GRAMMAR_CHECK_PROMPT, SEARCH_JUDGE_PROMPT,
    SEARCH_INTEGRATE_PROMPT, LLM_CONFIG, IELTS_CONFIG, HISTORY_DIR, TMP_DIR
)
from llm import GLMClient
from search import SearchEngine
from stt import WhisperEngine
from tts import EdgeTTSEngine
from utils import AudioPlayer, AudioRecorder, record_audio


class SpeakingBot:
    """雅思口语练习机器人"""
    
    def __init__(self, zhipu_api_key: str, tavily_api_key: str = None,
                 whisper_model: str = "base", tts_voice: str = "en-US-JennyNeural"):
        """
        初始化机器人
        
        Args:
            zhipu_api_key: 智谱 AI API Key
            tavily_api_key: Tavily 搜索 API Key (可选)
            whisper_model: Whisper 模型大小
            tts_voice: TTS 声音
        """
        # 初始化 LLM
        self.llm = GLMClient(api_key=zhipu_api_key)
        
        # 初始化搜索
        self.search_engine = SearchEngine(tavily_api_key)
        
        # 初始化 STT
        self.stt = WhisperEngine(model_size=whisper_model)
        
        # 初始化 TTS
        self.tts = EdgeTTSEngine(voice=tts_voice)
        
        # 初始化音频播放器
        self.audio_player = AudioPlayer()
        
        # 初始化录音器
        self.audio_recorder = AudioRecorder()
        
        # 对话历史
        self.history: List[Dict] = []
        
        # 配置
        self.auto_search_keywords = []
        self.search_commands = []
        
        # 当前模式
        self.mode = "free"  # "free" 或 "ielts"
        self.ielts_part = 1
        self.current_topic = ""
        
        print("✅ 口语练习机器人已就绪")

    def get_mode_info(self) -> str:
        """获取当前模式信息"""
        if self.mode == "ielts":
            return f"📚 IELTS Part {self.ielts_part}"
        else:
            return "💬 Free Chat"

    def set_mode(self, mode: str, ielts_part: int = 1):
        """
        设置对话模式
        
        Args:
            mode: "free" 或 "ielts"
            ielts_part: 雅思部分 (1, 2, 3)
        """
        self.mode = mode
        self.ielts_part = ielts_part
        
        if mode == "ielts":
            print(f"📚 已切换到雅思练习模式 (Part {ielts_part})")
        else:
            print("💬 已切换到自由聊天模式")
    
    def _should_search(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        判断是否需要搜索
        
        Returns:
            (是否需要搜索，搜索查询)
        """
        # 检查是否是搜索命令
        for cmd in self.search_commands:
            if text.strip().lower().startswith(cmd.lower()):
                query = text[len(cmd):].strip()
                return True, query if query else text
        
        # 检查是否包含自动搜索关键词
        for keyword in self.auto_search_keywords:
            if keyword.lower() in text.lower():
                return True, text
        
        # 使用 LLM 判断
        if self.llm.judge_need_search(text, SEARCH_JUDGE_PROMPT):
            return True, text
        
        return False, None
    
    def _do_search(self, query: str) -> Optional[str]:
        """
        执行搜索并格式化结果

        Returns:
            格式化后的搜索结果
        """
        print("\n🔍 正在联网搜索...")
        print(f"   查询：{query}")
        result = self.search_engine.search(query)

        if result:
            print(f"   ✅ 找到 {len(result.get('results', []))} 条结果")
            return self.search_engine.format_results(result)
        print("   ⚠️ 未找到搜索结果")
        return None
    
    def chat(self, text: str, use_search: bool = None) -> Tuple[str, Optional[str]]:
        """
        文字聊天

        Args:
            text: 用户输入文字
            use_search: 是否强制使用搜索 (None 表示自动判断)

        Returns:
            (AI 回复，语法反馈)
        """
        # 判断是否需要搜索
        if use_search is True:
            need_search = True
            search_query = text
            print("\n💡 使用搜索功能（用户强制）")
        elif use_search is False:
            need_search = False
            search_query = None
        else:
            need_search, search_query = self._should_search(text)
            if need_search:
                print("\n💡 检测到需要搜索的内容")

        # 执行搜索
        search_results = None
        if need_search and search_query:
            search_results = self._do_search(search_query)

        # 构建消息
        if search_results:
            # 整合搜索结果
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                *self.history,
                {"role": "user", "content": SEARCH_INTEGRATE_PROMPT.format(
                    search_results=search_results,
                    question=text
                )}
            ]
        else:
            # 直接回复
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                *self.history,
                {"role": "user", "content": text}
            ]

        # 调用 LLM
        response = self.llm.chat(
            messages,
            temperature=LLM_CONFIG["temperature"],
            max_tokens=LLM_CONFIG["max_tokens"]
        )

        # 更新历史
        self.history.append({"role": "user", "content": text})
        self.history.append({"role": "assistant", "content": response})

        # 限制历史长度
        if len(self.history) > 20:
            self.history = self.history[-20:]

        # 语法反馈（可选）
        grammar_feedback = None
        if len(text) > 10:  # 短句不反馈
            grammar_feedback = self._check_grammar(text)

        return response, grammar_feedback

    def extract_vocab(self, text: str, max_words: int = 5) -> List[Dict]:
        """
        从文本中提取生词/关键词

        Args:
            text: 要分析的文本
            max_words: 最多提取的单词数

        Returns:
            生词列表，每个生词包含 word, phonetic, definition, example
        """
        try:
            # 使用 LLM 提取生词
            prompt = f"""Extract {max_words} useful English vocabulary words from the following text that might be challenging for an IELTS student.

Text: "{text}"

For each word, provide:
- word: the word itself
- phonetic: pronunciation in IPA format (if you know it, otherwise skip)
- definition: brief English definition
- example: a short example sentence

Return the result as a JSON array format:
[
    {{"word": "example", "phonetic": "/ɪɡˈzæmpəl/", "definition": "a thing characteristic of its kind", "example": "This is a good example of the genre."}},
    ...
]

Only return the JSON array, nothing else.
"""
            messages = [{"role": "user", "content": prompt}]
            result = self.llm.chat(messages, temperature=0.3, max_tokens=500)
            
            # 尝试解析 JSON
            import json
            import re
            
            # 提取 JSON 部分
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                vocab_list = json.loads(json_match.group())
                return vocab_list
            return []
        except Exception as e:
            print(f"⚠️ 提取生词失败：{e}")
            return []
    
    def _check_grammar(self, text: str) -> Optional[str]:
        """检查语法并提供反馈"""
        try:
            messages = [
                {"role": "user", "content": GRAMMAR_CHECK_PROMPT.format(text=text)}
            ]
            feedback = self.llm.chat(messages, temperature=0.3, max_tokens=200)
            
            # 如果没有明显问题，返回 None
            if "no issue" in feedback.lower() or "perfect" in feedback.lower():
                return None
            
            return feedback
        except Exception as e:
            return None
    
    def speak(self, text: str, play: bool = True) -> Optional[str]:
        """
        语音合成并播放
        
        Args:
            text: 要合成的文本
            play: 是否自动播放
        
        Returns:
            输出文件路径
        """
        from config import AUDIO_CONFIG
        
        output_path = AUDIO_CONFIG["output_file"]
        
        print("🔊 正在生成语音...")
        if self.tts.generate(text, output_path):
            if play:
                self.audio_player.play(output_path)
            return output_path
        return None

    def record_voice(self, duration: float = None) -> Optional[str]:
        """
        录制语音
        
        Args:
            duration: 最大录制时长 (秒)，None 表示自动检测静音停止
        
        Returns:
            录制的音频文件路径
        """
        import glob
        
        # 清理旧的录音文件
        old_recordings = glob.glob(os.path.join(TMP_DIR, "recording_*.wav"))
        for old_file in old_recordings:
            try:
                os.remove(old_file)
            except:
                pass
        
        # 创建临时文件路径
        temp_path = os.path.join(TMP_DIR, f"recording_{os.getpid()}.wav")
        
        print("🎤 正在录音...", end=" ", flush=True)
        
        # 录音
        audio_path = record_audio(temp_path, duration=duration)
        
        return audio_path

    def voice_chat(self, audio_path: str, use_search: bool = None) -> Tuple[str, str, Optional[str]]:
        """
        语音聊天

        Args:
            audio_path: 输入音频文件路径
            use_search: 是否使用搜索

        Returns:
            (识别的文字，AI 回复，语法反馈)
        """
        # 语音识别
        print("🎤 正在识别语音...")
        text = self.stt.transcribe(audio_path)

        if not text:
            return "", "抱歉，没有听清楚，请再说一遍。", None

        print(f"👤 你：{text}")

        # 文字聊天
        response, grammar_feedback = self.chat(text, use_search)

        return text, response, grammar_feedback
    
    def get_ielts_topic(self) -> str:
        """获取一个雅思话题"""
        import random
        
        if self.ielts_part == 1:
            topic = random.choice(IELTS_CONFIG["part1_topics"])
            questions = self._get_part1_questions(topic)
            return f"Topic: {topic}\n\n{questions}"
        
        elif self.ielts_part == 2:
            category = random.choice(IELTS_CONFIG["part2_categories"])
            return self._get_part2_prompt(category)
        
        else:  # Part 3
            theme = random.choice(IELTS_CONFIG["part3_themes"])
            return self._get_part3_questions(theme)
    
    def _get_part1_questions(self, topic: str) -> str:
        """获取 Part 1 问题"""
        questions = {
            "Work/Studies": [
                "Do you work or are you a student?",
                "What do you like most about your work/studies?",
                "Why did you choose this job/major?"
            ],
            "Hometown": [
                "Where is your hometown?",
                "What do you like most about your hometown?",
                "Is there anything you would change about your hometown?"
            ],
            "Hobbies": [
                "What do you like to do in your free time?",
                "How long have you had this hobby?",
                "Do you prefer doing hobbies alone or with others?"
            ],
        }
        
        qs = questions.get(topic, [
            f"Tell me about {topic}.",
            f"Do you like {topic}?",
            f"Why do you like {topic}?"
        ])
        
        return "\n".join([f"  • {q}" for q in qs])
    
    def _get_part2_prompt(self, category: str) -> str:
        """获取 Part 2 话题卡"""
        prompts = {
            "Describe a person": (
                "Describe a person who has influenced you.\n\n"
                "You should say:\n"
                "  • Who this person is\n"
                "  • How you know this person\n"
                "  • What qualities they have\n"
                "  • And explain why they have influenced you"
            ),
            "Describe a place": (
                "Describe a place you have visited that you remember well.\n\n"
                "You should say:\n"
                "  • Where it is\n"
                "  • When you went there\n"
                "  • What you did there\n"
                "  • And explain why you remember it well"
            ),
            "Describe an event": (
                "Describe an important event in your life.\n\n"
                "You should say:\n"
                "  • What the event was\n"
                "  • When it happened\n"
                "  • Who was there\n"
                "  • And explain why it was important"
            ),
        }
        
        return prompts.get(category, f"Describe something related to {category}.")
    
    def _get_part3_questions(self, theme: str) -> str:
        """获取 Part 3 问题"""
        questions = {
            "Education": [
                "How has education changed in recent years?",
                "What role does technology play in education?",
                "Do you think university education is still valuable today?"
            ],
            "Technology": [
                "How has technology changed the way we communicate?",
                "What are the benefits and drawbacks of social media?",
                "Do you think AI will replace many jobs in the future?"
            ],
            "Environment": [
                "What environmental problems do we face today?",
                "How can individuals help protect the environment?",
                "Do you think governments are doing enough to combat climate change?"
            ],
        }
        
        qs = questions.get(theme, [
            f"What's your opinion on {theme}?",
            f"How has {theme} changed in recent years?",
            f"What do you think about the future of {theme}?"
        ])
        
        return "\n".join([f"  • {q}" for q in qs])
    
    def save_history(self, filename: str = None):
        """保存对话历史"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"history_{timestamp}.json"
        
        filepath = os.path.join(HISTORY_DIR, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "mode": self.mode,
                "ielts_part": self.ielts_part,
                "history": self.history,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        print(f"💾 对话历史已保存：{filepath}")
    
    def clear_history(self):
        """清空对话历史"""
        self.history = []
        print("🗑️ 对话历史已清空")
    
    def get_history(self) -> List[Dict]:
        """获取对话历史"""
        return self.history
