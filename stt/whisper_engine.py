"""
STT 模块 - 使用 faster-whisper 进行语音识别
"""
import os
import numpy as np
from typing import Optional
from faster_whisper import WhisperModel


class WhisperEngine:
    """Whisper 语音识别引擎"""
    
    def __init__(self, model_size: str = "base", device: str = "auto",
                 compute_type: str = "float16"):
        """
        初始化 Whisper 引擎
        
        Args:
            model_size: 模型大小 (tiny, base, small, medium, large)
            device: 运行设备 (auto, cpu, cuda)
            compute_type: 计算精度 (float16, int8, int8_float16)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载 Whisper 模型"""
        try:
            print(f"🔄 加载 Whisper 模型 ({self.model_size})...")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
            print(f"✅ Whisper 模型加载完成")
        except Exception as e:
            print(f"❌ Whisper 模型加载失败：{e}")
            print("⚠️ 尝试使用 CPU 模式...")
            try:
                self.model = WhisperModel(
                    self.model_size,
                    device="cpu",
                    compute_type="int8"
                )
                print(f"✅ Whisper 模型已加载 (CPU 模式)")
            except Exception as e2:
                print(f"❌ 无法加载 Whisper 模型：{e2}")
                self.model = None
    
    def transcribe(self, audio_path: str, language: str = "en") -> Optional[str]:
        """
        转录音频文件
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码 (en 表示英语)
        
        Returns:
            转录的文本
        """
        if not self.model:
            print("❌ Whisper 模型未加载")
            return None
        
        try:
            segments, info = self.model.transcribe(
                audio_path,
                language=language,
                beam_size=5,
                vad_filter=True,  # 语音活动检测
            )
            
            text = " ".join([segment.text for segment in segments]).strip()
            return text
        
        except Exception as e:
            print(f"❌ 转录失败：{e}")
            return None
    
    def transcribe_array(self, audio_data: np.ndarray, sample_rate: int = 16000,
                         language: str = "en") -> Optional[str]:
        """
        转录音频数组
        
        Args:
            audio_data: 音频数据 (numpy array)
            sample_rate: 采样率
            language: 语言代码
        
        Returns:
            转录的文本
        """
        if not self.model:
            print("❌ Whisper 模型未加载")
            return None
        
        try:
            # 保存为临时文件
            import tempfile
            import scipy.io.wavfile as wav
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
                wav.write(temp_path, sample_rate, audio_data)
            
            # 转录
            text = self.transcribe(temp_path, language)
            
            # 清理临时文件
            os.unlink(temp_path)
            
            return text
        
        except Exception as e:
            print(f"❌ 转录失败：{e}")
            return None
    
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        return self.model is not None
