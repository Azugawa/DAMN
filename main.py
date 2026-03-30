#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雅思口语练习助手 - 主程序

IELTS Speaking Buddy - Your personal English speaking practice partner
"""
import os
import sys
import time
from typing import Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    ZHIPU_API_KEY, TAVILY_API_KEY, ZHIPU_LLM_MODEL,
    WHISPER_CONFIG, TTS_CONFIG, SEARCH_CONFIG, HISTORY_DIR
)
from core import SpeakingBot


def print_banner():
    """打印欢迎横幅"""
    print("\n" + "=" * 60)
    print("🎓 DAMN - IELTS Speaking Assistant")
    print("   Daily Assistant for Mastering Native")
    print("=" * 60)
    print()
    print("功能:")
    print("  🎤 语音输入  |  ⌨️ 文字输入")
    print("  📚 雅思话题  |  💬 自由聊天")
    print("  🔍 联网搜索  |  💡 语法纠正")
    print("  🔊 语音输出  |  📝 文字输出")
    print()
    print("=" * 60)


def print_help():
    """打印帮助信息"""
    print("\n📖 可用命令:")
    print("  /help          - 显示帮助")
    print("  /mode          - 切换模式 (自由/雅思)")
    print("  /topic         - 获取新话题 (雅思模式)")
    print("  /search <内容>  - 搜索后回复")
    print("  /history       - 保存对话历史")
    print("  /clear         - 清空对话历史")
    print("  /quit          - 退出程序")
    print()


def get_user_input() -> tuple:
    """
    获取用户输入
    
    Returns:
        (输入类型，内容)
        输入类型："text" 或 "voice"
    """
    print("\n请选择输入方式:")
    print("  [1] ⌨️ 文字输入")
    print("  [2] 🎤 语音输入 (麦克风)")
    print()
    
    choice = input("→ 选择 (1/2): ").strip()
    
    if choice == "2":
        # 语音输入
        return "voice", None
    else:
        text = input("\n👤 你：").strip()
        return "text", text


def record_voice_input(bot) -> tuple:
    """
    录制语音输入
    
    Args:
        bot: SpeakingBot 实例
    
    Returns:
        (输入类型，音频路径)
    """
    print("\n📖 录音说明:")
    print("   - 说完后等待 3 秒自动停止")
    print("   - 或按 Ctrl+C 手动停止")
    print("   - 最长录制 30 秒")
    print()
    
    # 使用 try-except 处理 Ctrl+C
    try:
        input("   按 Enter 开始录音...")
        
        # 录音
        audio_path = bot.record_voice(duration=30)
        
        if audio_path and os.path.exists(audio_path):
            print(f"✅ 录音完成：{audio_path}")
            return "voice", audio_path
        else:
            print("⚠️ 录音失败或已中断")
            return "text", ""
    
    except KeyboardInterrupt:
        print("\n⏹️  录音已取消")
        return "text", ""


def choose_mode() -> tuple:
    """选择对话模式"""
    print("\n📋 选择练习模式:")
    print("  [1] 💬 自由聊天")
    print("  [2] 📚 雅思话题练习")
    print()
    
    choice = input("→ 选择 (1/2): ").strip()
    
    if choice == "2":
        print("\n选择雅思部分:")
        print("  [1] Part 1 - 简介与问答 (4-5 分钟)")
        print("  [2] Part 2 - 个人陈述 (3-4 分钟)")
        print("  [3] Part 3 - 深入讨论 (4-5 分钟)")
        print()
        
        part_choice = input("→ 选择 (1/2/3): ").strip()
        part = int(part_choice) if part_choice in ["1", "2", "3"] else 1
        
        return "ielts", part
    else:
        return "free", 1


def choose_output_mode() -> str:
    """选择输出模式"""
    print("\n🔊 选择回复方式:")
    print("  [1] 🔊 文字 + 语音")
    print("  [2] 📝 仅文字")
    print("  [3] 🎧 仅语音")
    print()
    
    choice = input("→ 选择 (1/2/3): ").strip()
    
    if choice == "2":
        return "text"
    elif choice == "3":
        return "voice"
    else:
        return "both"


def display_grammar_feedback(feedback: Optional[str]):
    """显示语法反馈"""
    if feedback:
        print("\n" + "-" * 40)
        print(feedback)
        print("-" * 40)


def main():
    """主函数"""
    # 检查 API Key
    if not ZHIPU_API_KEY or ZHIPU_API_KEY == "your_zhipu_api_key_here":
        print("❌ 错误：请先配置 ZHIPU_API_KEY")
        print("   1. 复制 .env.example 为 .env")
        print("   2. 在 .env 中填入你的 API Key")
        print("   3. 重新运行程序")
        return
    
    # 打印欢迎信息
    print_banner()
    
    # 选择模式
    mode, ielts_part = choose_mode()
    
    # 选择输出方式
    output_mode = choose_output_mode()
    
    # 初始化机器人
    print("\n🔄 正在初始化...")
    bot = SpeakingBot(
        zhipu_api_key=ZHIPU_API_KEY,
        tavily_api_key=TAVILY_API_KEY if TAVILY_API_KEY else None,
        whisper_model=WHISPER_CONFIG["model"],
        tts_voice=TTS_CONFIG["voice"]
    )
    
    # 设置配置
    bot.auto_search_keywords = SEARCH_CONFIG["auto_search_keywords"]
    bot.search_commands = SEARCH_CONFIG["search_commands"]
    
    # 设置模式
    bot.set_mode(mode, ielts_part)
    
    print(f"\n✅ 准备就绪！当前模式：{bot.get_mode_info()}")
    print("   输出方式：", "文字 + 语音" if output_mode == "both" else "仅文字" if output_mode == "text" else "仅语音")
    print("\n输入 /help 查看可用命令")
    
    # 雅思模式：获取初始话题
    if mode == "ielts":
        topic = bot.get_ielts_topic()
        print("\n" + "=" * 50)
        print(f"📝 当前话题:\n{topic}")
        print("=" * 50)
    
    # 主循环
    while True:
        try:
            # 获取输入
            input_type, user_input = get_user_input()
            
            # 如果是语音输入，进行录音
            if input_type == "voice":
                input_type, user_input = record_voice_input(bot)
            
            if not user_input:
                continue
            
            # 处理命令
            if user_input.startswith("/"):
                cmd = user_input.lower().split()[0]
                
                if cmd in ["/quit", "/exit", "/退出"]:
                    print("\n👋 再见！祝你学习进步！")
                    break
                
                elif cmd == "/help":
                    print_help()
                    continue
                
                elif cmd == "/mode":
                    mode, ielts_part = choose_mode()
                    bot.set_mode(mode, ielts_part)
                    
                    if mode == "ielts":
                        topic = bot.get_ielts_topic()
                        print(f"\n📝 新话题:\n{topic}")
                    continue
                
                elif cmd == "/topic":
                    if mode != "ielts":
                        print("⚠️ 请先切换到雅思模式 (/mode)")
                    else:
                        topic = bot.get_ielts_topic()
                        print(f"\n📝 新话题:\n{topic}")
                    continue
                
                elif cmd == "/search":
                    # 强制搜索
                    query = user_input[len(cmd):].strip()
                    if query:
                        print("\n🔍 搜索模式...")
                        response, feedback = bot.chat(query, use_search=True)
                        print(f"\n🤖 AI: {response}")
                        display_grammar_feedback(feedback)

                        if output_mode in ["both", "voice"]:
                            bot.speak(response)
                    continue
                
                elif cmd == "/history":
                    bot.save_history()
                    continue
                
                elif cmd == "/clear":
                    bot.clear_history()
                    continue
                
                else:
                    print(f"⚠️ 未知命令：{cmd}，输入 /help 查看帮助")
                    continue
            
            # 正常对话
            if input_type == "voice":
                # 语音输入
                print("\n🔄 正在识别语音...", end="", flush=True)
                _, response, feedback = bot.voice_chat(user_input)
                print("\r" + " " * 20 + "\r", end="")
            else:
                # 文字输入
                print("\n🔄 思考中...", end="", flush=True)
                response, feedback = bot.chat(user_input)
                print("\r" + " " * 20 + "\r", end="")  # 清除"思考中"

            # 显示回复
            print(f"\n🤖 AI: {response}")
            display_grammar_feedback(feedback)
            
            # 语音输出
            if output_mode in ["both", "voice"]:
                bot.speak(response)
            
        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 错误：{e}")
            print("   请重试或输入 /quit 退出")


if __name__ == "__main__":
    main()
