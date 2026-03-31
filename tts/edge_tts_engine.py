"""
TTS 模块 - 使用 Edge TTS 进行语音合成
"""
import os
import asyncio
from typing import Optional


class EdgeTTSEngine:
    """Edge TTS 语音合成引擎"""
    
    def __init__(self, voice: str = "en-US-JennyNeural", rate: str = "+0%",
                 volume: str = "+0%", pitch: str = "+0Hz"):
        """
        初始化 Edge TTS
        
        Args:
            voice: 声音选择
            rate: 语速 (+0% 表示正常)
            volume: 音量
            pitch: 音调
        """
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.pitch = pitch
        print(f"✅ Edge TTS 已初始化 (声音：{voice})")
    
    async def _generate_async(self, text: str, output_path: str) -> bool:
        """异步生成语音"""
        try:
            import edge_tts
            
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                volume=self.volume,
                pitch=self.pitch,
            )
            
            await communicate.save(output_path)
            return True
        
        except Exception as e:
            print(f"❌ TTS 生成失败：{e}")
            return False
    
    def _clean_text_for_tts(self, text: str) -> str:
        """
        清理文本，移除 emoji 和特殊符号（TTS 不需要读的）
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        import re
        
        # 移除常见 emoji
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # 表情符号
            "\U0001F300-\U0001F5FF"  # 符号和象形文字
            "\U0001F680-\U0001F6FF"  # 交通和地图符号
            "\U0001F1E0-\U0001F1FF"  # 旗帜
            "\U00002702-\U000027B0"  # 装饰符号
            "\U000024C2-\U0001F251"  # 封闭符号
            "]+",
            flags=re.UNICODE
        )
        text = emoji_pattern.sub('', text)
        
        # 移除单独的 emoji 符号
        text = re.sub(r'[🎤🔊📚🔍💡📝🗑️📖🎧⚠️✅❌🔄💬👤🤖💭📋🌐]', '', text)
        
        # 清理多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def generate(self, text: str, output_path: str) -> bool:
        """
        生成语音文件

        Args:
            text: 要合成的文本
            output_path: 输出文件路径

        Returns:
            True 表示成功
        """
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 清理文本，移除 emoji
            clean_text = self._clean_text_for_tts(text)

            # 运行异步代码
            asyncio.run(self._generate_async(clean_text, output_path))
            
            # 检查文件是否生成
            if os.path.exists(output_path):
                print(f"✅ 语音已生成：{output_path}")
                return True
            else:
                print("❌ 语音文件生成失败")
                return False
        
        except Exception as e:
            print(f"❌ TTS 生成失败：{e}")
            return False
    
    def list_voices(self):
        """列出所有可用声音"""
        try:
            import edge_tts
            voices = asyncio.run(edge_tts.list_voices())
            
            print("\n可用声音列表:")
            print("-" * 50)
            
            # 过滤英语声音
            en_voices = [v for v in voices if v["Locale"].startswith("en")]
            
            for v in en_voices[:20]:  # 只显示前 20 个
                gender = "👩" if v["Gender"] == "Female" else "👨"
                print(f"{gender} {v['ShortName']}: {v['FriendlyName']}")
            
            print("-" * 50)
            return en_voices
        
        except Exception as e:
            print(f"❌ 获取声音列表失败：{e}")
            return []
    
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        try:
            import edge_tts
            return True
        except ImportError:
            return False
