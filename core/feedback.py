"""
语法反馈模块
"""
from typing import Optional, Dict


class GrammarFeedback:
    """语法反馈生成器"""
    
    def __init__(self, llm_client):
        """
        初始化
        
        Args:
            llm_client: LLM 客户端
        """
        self.llm = llm_client
    
    def check(self, text: str) -> Optional[Dict]:
        """
        检查语法
        
        Args:
            text: 用户输入的文本
        
        Returns:
            反馈字典，包含 issues 和 suggestions
        """
        if len(text) < 10:  # 太短的句子不检查
            return None
        
        prompt = self._build_prompt(text)
        
        try:
            feedback = self.llm.chat(prompt, temperature=0.3, max_tokens=200)
            return self._parse_feedback(feedback)
        except Exception as e:
            return None
    
    def _build_prompt(self, text: str) -> str:
        """构建 Prompt"""
        return f"""Please analyze the following English text for grammar issues:

Text: "{text}"

Provide:
1. List any grammar/vocabulary issues (if any)
2. Suggest a more natural way to express it (if applicable)
3. Keep feedback brief and encouraging

Format your response concisely.
"""
    
    def _parse_feedback(self, feedback: str) -> Dict:
        """解析反馈"""
        # 简单解析，可以改进为更复杂的解析
        has_issues = "no issue" not in feedback.lower() and "perfect" not in feedback.lower()
        
        return {
            "has_issues": has_issues,
            "feedback": feedback,
        }
    
    def format_feedback(self, feedback: Dict) -> str:
        """格式化反馈用于显示"""
        if not feedback or not feedback["has_issues"]:
            return "✅ 语法很好！"
        
        return f"💡 语法建议:\n{feedback['feedback']}"
