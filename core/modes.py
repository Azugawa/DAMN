"""
模式管理 - 雅思话题和自由聊天
"""
from typing import Dict, List


class ModeManager:
    """模式管理器"""
    
    def __init__(self):
        self.current_mode = "free"  # "free" 或 "ielts"
        self.ielts_part = 1
        self.current_topic = ""
        self.topic_history = []
    
    def set_free_mode(self):
        """切换到自由聊天模式"""
        self.current_mode = "free"
        self.current_topic = ""
        return "💬 已切换到自由聊天模式"
    
    def set_ielts_mode(self, part: int = 1):
        """
        切换到雅思练习模式
        
        Args:
            part: 雅思部分 (1, 2, 3)
        """
        self.current_mode = "ielts"
        self.ielts_part = part
        return f"📚 已切换到雅思练习模式 (Part {part})"
    
    def get_mode_info(self) -> str:
        """获取当前模式信息"""
        if self.current_mode == "ielts":
            return f"📚 IELTS Part {self.ielts_part}"
        else:
            return "💬 Free Chat"
    
    def get_ielts_part_info(self) -> str:
        """获取雅思部分说明"""
        parts = {
            1: (
                "Part 1 - Introduction & Interview (4-5 分钟)\n"
                "• 考官会问一些关于你的熟悉话题\n"
                "• 例如：工作、学习、家乡、爱好等\n"
                "• 回答要自然、简洁（2-3 句话）"
            ),
            2: (
                "Part 2 - Long Turn (3-4 分钟)\n"
                "• 你会拿到一个话题卡\n"
                "• 有 1 分钟准备时间\n"
                "• 需要连续说 1-2 分钟"
            ),
            3: (
                "Part 3 - Discussion (4-5 分钟)\n"
                "• 更深入的双向讨论\n"
                "• 话题更抽象、更复杂\n"
                "• 需要表达观点和论证"
            ),
        }
        return parts.get(self.ielts_part, "")
