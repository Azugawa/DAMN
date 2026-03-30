"""
搜索模块 - 支持 Tavily 和 DuckDuckGo
"""
import os
from typing import List, Dict, Optional


class SearchEngine:
    """搜索引擎接口 - 支持混合模式"""
    
    def __init__(self, tavily_api_key: str = None):
        self.tavily_api_key = tavily_api_key
        self.tavily_client = None
        self._init_tavily()
    
    def _init_tavily(self):
        """初始化 Tavily 客户端"""
        if self.tavily_api_key:
            try:
                from tavily import TavilyClient
                self.tavily_client = TavilyClient(api_key=self.tavily_api_key)
                print("✅ Tavily 搜索已初始化")
            except ImportError:
                print("⚠️ 未安装 tavily-python，请运行：pip install tavily-python")
            except Exception as e:
                print(f"⚠️ Tavily 初始化失败：{e}")
        else:
            print("⚠️ 未配置 TAVILY_API_KEY，将使用 DuckDuckGo 作为备选")
    
    def search(self, query: str, max_results: int = 3) -> Optional[Dict]:
        """
        执行搜索
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
        
        Returns:
            搜索结果字典，包含 results 列表
        """
        # 优先使用 Tavily
        if self.tavily_client:
            try:
                return self._tavily_search(query, max_results)
            except Exception as e:
                print(f"⚠️ Tavily 搜索失败：{e}，切换到 DuckDuckGo")
        
        # 备选：DuckDuckGo
        return self._duckduckgo_search(query, max_results)
    
    def _tavily_search(self, query: str, max_results: int) -> Dict:
        """Tavily 搜索"""
        response = self.tavily_client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
            include_answer=True,
        )
        return response
    
    def _duckduckgo_search(self, query: str, max_results: int) -> Optional[Dict]:
        """DuckDuckGo 搜索（备选）"""
        try:
            from duckduckgo_search import DDGS
            
            results = []
            with DDGS() as ddgs:
                search_results = list(ddgs.text(query, max_results=max_results))
                
                for r in search_results:
                    results.append({
                        "title": r.get("title", ""),
                        "content": r.get("body", ""),
                        "url": r.get("href", ""),
                    })
            
            return {"results": results, "answer": ""}
        
        except ImportError:
            print("⚠️ 未安装 duckduckgo-search，请运行：pip install duckduckgo-search")
            return None
        except Exception as e:
            print(f"⚠️ DuckDuckGo 搜索失败：{e}")
            return None
    
    def format_results(self, search_result: Dict) -> str:
        """
        格式化搜索结果用于 LLM
        
        Returns:
            格式化后的文本
        """
        if not search_result or not search_result.get("results"):
            return "No search results found."
        
        parts = []
        
        # 如果有直接答案，优先使用
        if search_result.get("answer"):
            parts.append(f"Quick Answer: {search_result['answer']}")
        
        # 添加搜索结果
        for i, r in enumerate(search_result["results"], 1):
            source = f"[{i}] {r.get('title', 'Unknown')}"
            content = r.get('content', '')
            url = r.get('url', '')
            
            parts.append(f"{source}\n{content}\nSource: {url}")
        
        return "\n\n".join(parts)
    
    def should_auto_search(self, text: str, keywords: List[str]) -> bool:
        """
        判断是否应该自动触发搜索
        
        Args:
            text: 用户输入
            keywords: 自动搜索关键词列表
        
        Returns:
            True 表示应该搜索
        """
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True
        return False
    
    def is_search_command(self, text: str, commands: List[str]) -> bool:
        """
        判断是否是搜索命令
        
        Args:
            text: 用户输入
            commands: 搜索命令列表（如 /search）
        
        Returns:
            True 表示是搜索命令
        """
        text_stripped = text.strip().lower()
        for cmd in commands:
            if text_stripped.startswith(cmd.lower()):
                return True
        return False
    
    def extract_search_query(self, text: str, commands: List[str]) -> str:
        """
        从搜索命令中提取查询
        
        例如："/search 最新 AI 新闻" → "最新 AI 新闻"
        
        Args:
            text: 用户输入
            commands: 搜索命令列表
        
        Returns:
            搜索查询
        """
        text_stripped = text.strip()
        for cmd in commands:
            if text_stripped.lower().startswith(cmd.lower()):
                return text_stripped[len(cmd):].strip()
        return text_stripped
