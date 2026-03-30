"""
LLM 客户端 - 智谱 AI GLM-4-Flash
"""
import os
import httpx
from typing import List, Dict, Optional, Generator


class GLMClient:
    """智谱 AI GLM-4-Flash 客户端"""
    
    def __init__(self, api_key: str, model: str = "glm-4-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://open.bigmodel.cn/api/paas/v4"
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        )
        print(f"✅ GLM-4-Flash 客户端已初始化 (模型：{model})")
    
    def chat(self, messages: List[Dict], temperature: float = 0.7, 
             max_tokens: int = 1024) -> str:
        """
        发送对话请求
        
        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}, ...]
            temperature: 温度参数
            max_tokens: 最大生成 token 数
        
        Returns:
            AI 回复的文本
        """
        try:
            response = self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP 错误：{e}")
            return f"Error: {e}"
        except Exception as e:
            print(f"❌ LLM 请求失败：{e}")
            return f"Error: {e}"
    
    def chat_stream(self, messages: List[Dict], temperature: float = 0.7,
                    max_tokens: int = 1024) -> Generator[str, None, None]:
        """
        流式对话（可选功能）
        
        Yields:
            逐步生成的回复文本
        """
        try:
            with self.client.stream(
                "POST",
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                }
            ) as response:
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            import json
                            parsed = json.loads(data)
                            content = parsed["choices"][0]["delta"].get("content", "")
                            if content:
                                yield content
                        except:
                            continue
        
        except Exception as e:
            print(f"❌ 流式请求失败：{e}")
            yield f"Error: {e}"
    
    def judge_need_search(self, text: str, judge_prompt: str) -> bool:
        """
        判断是否需要搜索
        
        Args:
            text: 用户输入
            judge_prompt: 判断 Prompt 模板
        
        Returns:
            True 表示需要搜索
        """
        messages = [
            {"role": "user", "content": judge_prompt.format(text=text)}
        ]
        response = self.chat(messages, temperature=0.1, max_tokens=10)
        return "YES" in response.upper()
    
    def integrate_search_results(self, search_results: str, question: str,
                                  integrate_prompt: str) -> str:
        """
        整合搜索结果生成回复
        
        Args:
            search_results: 格式化后的搜索结果
            question: 用户问题
            integrate_prompt: 整合 Prompt 模板
        
        Returns:
            整合后的回复
        """
        messages = [
            {"role": "user", "content": integrate_prompt.format(
                search_results=search_results,
                question=question
            )}
        ]
        return self.chat(messages)
