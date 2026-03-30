"""
音频播放工具
"""
import os
from typing import Optional


class AudioPlayer:
    """音频播放器 - 使用 pygame"""
    
    def __init__(self):
        """初始化音频播放器"""
        try:
            import pygame
            pygame.mixer.init()
            self.pygame = pygame
            print("✅ 音频播放器已初始化")
        except Exception as e:
            print(f"⚠️ 音频播放器初始化失败：{e}")
            self.pygame = None
    
    def play(self, file_path: str, wait: bool = True) -> bool:
        """
        播放音频文件
        
        Args:
            file_path: 音频文件路径
            wait: 是否等待播放完成
        
        Returns:
            True 表示成功
        """
        if not self.pygame:
            print("❌ 音频播放器未初始化")
            return False
        
        try:
            if not os.path.exists(file_path):
                print(f"❌ 音频文件不存在：{file_path}")
                return False
            
            self.pygame.mixer.music.load(file_path)
            self.pygame.mixer.music.play()
            
            if wait:
                # 等待播放完成
                clock = self.pygame.time.Clock()
                while self.pygame.mixer.music.get_busy():
                    clock.tick(10)
            
            return True
        
        except Exception as e:
            print(f"❌ 播放失败：{e}")
            return False
    
    def stop(self):
        """停止播放"""
        if self.pygame:
            self.pygame.mixer.music.stop()
    
    def is_playing(self) -> bool:
        """检查是否正在播放"""
        if self.pygame:
            return self.pygame.mixer.music.get_busy()
        return False
