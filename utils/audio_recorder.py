"""
录音模块 - 使用 pyaudio 录制音频
"""
import os
import wave
import numpy as np
from typing import Optional, Callable

# 导入 pyaudio 模块
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    pyaudio = None


class AudioRecorder:
    """音频录音器"""

    def __init__(self, sample_rate: int = 16000, channels: int = 1,
                 chunk_size: int = 1024):
        """
        初始化录音器

        Args:
            sample_rate: 采样率 (16000 适合语音识别)
            channels: 声道数 (1=单声道)
            chunk_size: 块大小
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.pyaudio_instance = None
        self.stream = None
        self.is_recording = False
        self._init_pyaudio()

    def _init_pyaudio(self):
        """初始化 PyAudio"""
        if not PYAUDIO_AVAILABLE:
            print("⚠️ 未安装 pyaudio，请运行：pip install pyaudio")
            return
        
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            print("✅ 音频录制模块已初始化")
        except Exception as e:
            print(f"⚠️ PyAudio 初始化失败：{e}")
            self.pyaudio_instance = None
    
    def list_input_devices(self) -> list:
        """
        列出所有可用的输入设备
        
        Returns:
            设备信息列表
        """
        if not self.pyaudio_instance:
            return []

        devices = []
        for i in range(self.pyaudio_instance.get_device_count()):
            try:
                info = self.pyaudio_instance.get_device_info_by_index(i)
                if info.get('maxInputChannels', 0) > 0:
                    devices.append({
                        'index': i,
                        'name': info['name'],
                        'channels': info['maxInputChannels'],
                        'sample_rate': int(info['defaultSampleRate'])
                    })
            except:
                continue

        return devices

    def record(self, output_path: str, duration: float = None,
               silence_timeout: float = 3.0, callback: Callable = None) -> Optional[str]:
        """
        录制音频
        
        Args:
            output_path: 输出文件路径
            duration: 最大录制时长 (秒)，None 表示手动停止
            silence_timeout: 静音超时时间 (秒)，用于自动停止
            callback: 回调函数，用于显示录音状态
        
        Returns:
            输出文件路径，失败返回 None
        """
        if not self.pyaudio_instance:
            print("❌ PyAudio 未初始化")
            return None
        
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 获取默认输入设备
            device_index = self._get_default_input_device()
            if device_index is None:
                print("❌ 未找到可用的输入设备")
                return None
            
            # 打开音频流
            self.stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            
            print("🎤 开始录音...")
            print("   💡 提示：说完后等待 3 秒自动停止，或按 Ctrl+C 手动停止")
            if callback:
                callback("recording")
            
            frames = []
            silent_chunks = 0
            max_silent_chunks = int(silence_timeout * self.sample_rate / self.chunk_size)
            start_time = None
            has_spoken = False  # 标记是否已经开始说话
            
            self.is_recording = True
            
            while self.is_recording:
                # 检查时长限制
                if duration:
                    elapsed = (len(frames) * self.chunk_size) / self.sample_rate
                    if elapsed >= duration:
                        print("\n⏱️  达到最大录制时长")
                        break
                
                # 读取音频数据
                try:
                    data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                except OSError as e:
                    print(f"\n⚠️  音频读取错误：{e}")
                    break
                except Exception:
                    continue
                
                frames.append(data)
                
                # 检测静音
                audio_data = np.frombuffer(data, dtype=np.int16)
                volume = np.abs(audio_data).mean()
                
                # 检测是否开始说话（有声音）
                if volume > 500:
                    if not has_spoken:
                        has_spoken = True
                        print("   🎤 检测到声音，正在录音...")
                    silent_chunks = 0
                    if start_time is None:
                        import time
                        start_time = time.time()
                else:
                    # 只有在已经开始说话后才计算静音
                    if has_spoken:
                        silent_chunks += 1
                        if silent_chunks >= max_silent_chunks:
                            print("\n🔇 检测到静音，自动停止录音")
                            break
                
                # 显示录音状态
                if callback and len(frames) % 50 == 0:
                    elapsed = (len(frames) * self.chunk_size) / self.sample_rate
                    callback(f"recording", elapsed)
            
            # 停止录音
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            print("✅ 录音完成")
            if callback:
                callback("finished")
            
            # 保存为 WAV 文件
            self._save_wav(output_path, frames)
            
            return output_path
        
        except KeyboardInterrupt:
            print("\n⏹️  录音已中断")
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            return None
        
        except Exception as e:
            print(f"❌ 录音失败：{e}")
            if self.stream:
                self.stream.close()
                self.stream = None
            return None
    
    def _save_wav(self, output_path: str, frames: list):
        """保存为 WAV 文件"""
        import wave

        with wave.open(output_path, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.pyaudio_instance.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))

        print(f"💾 已保存：{output_path}")

    def _get_default_input_device(self) -> Optional[int]:
        """获取默认输入设备索引"""
        if not self.pyaudio_instance:
            return None

        # 尝试获取默认设备
        try:
            default_device = self.pyaudio_instance.get_default_input_device_info()
            return default_device['index']
        except:
            pass

        # 查找第一个可用的输入设备
        for i in range(self.pyaudio_instance.get_device_count()):
            try:
                info = self.pyaudio_instance.get_device_info_by_index(i)
                if info.get('maxInputChannels', 0) > 0:
                    return info['index']
            except:
                continue

        return None

    def stop(self):
        """停止录音"""
        self.is_recording = False

    def is_available(self) -> bool:
        """检查录音模块是否可用"""
        return self.pyaudio_instance is not None and self._get_default_input_device() is not None


# 简单的录音函数（用于主程序）
def record_audio(output_path: str, duration: float = None) -> Optional[str]:
    """
    简单录音函数
    
    Args:
        output_path: 输出文件路径
        duration: 最大录制时长 (秒)
    
    Returns:
        输出文件路径
    """
    recorder = AudioRecorder()
    
    if not recorder.is_available():
        print("❌ 录音功能不可用")
        return None
    
    # 显示设备信息
    devices = recorder.list_input_devices()
    if devices:
        print(f"📡 使用输入设备：{devices[0]['name']}")
    
    # 录音
    return recorder.record(output_path, duration=duration)


if __name__ == "__main__":
    # 测试录音
    import tempfile
    
    output_path = os.path.join(tempfile.gettempdir(), "test_recording.wav")
    
    print("🎤 录音测试")
    print("   请说话，3 秒静音后自动停止")
    print()
    
    result = record_audio(output_path, duration=10)
    
    if result:
        print(f"\n✅ 测试完成！文件：{result}")
    else:
        print("\n❌ 测试失败")
