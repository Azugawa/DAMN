#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DAMN - Web API 服务器
提供 RESTful API 供前端调用
"""
import os
import sys
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    ZHIPU_API_KEY, TAVILY_API_KEY, ZHIPU_LLM_MODEL,
    WHISPER_CONFIG, TTS_CONFIG, SEARCH_CONFIG, TMP_DIR, DB_PATH
)
from core import SpeakingBot
from db.db import get_database, init_database

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# 全局变量
bot = None
db = None
current_session_id = None


def init_bot():
    """初始化 bot 实例"""
    global bot, db
    bot = SpeakingBot(
        zhipu_api_key=ZHIPU_API_KEY,
        tavily_api_key=TAVILY_API_KEY if TAVILY_API_KEY else None,
        whisper_model=WHISPER_CONFIG["model"],
        tts_voice=TTS_CONFIG["voice"]
    )
    bot.auto_search_keywords = SEARCH_CONFIG["auto_search_keywords"]
    bot.search_commands = SEARCH_CONFIG["search_commands"]

    # 初始化数据库
    db = init_database(DB_PATH)

    # 清理临时目录
    cleanup_tmp_dir()


def cleanup_tmp_dir():
    """清理临时目录中的旧文件"""
    import glob
    try:
        files = glob.glob(os.path.join(TMP_DIR, "*"))
        for file in files:
            if os.path.isfile(file):
                try:
                    os.remove(file)
                    print(f"🗑️ 已清理旧文件：{os.path.basename(file)}")
                except Exception as e:
                    pass
        print("✅ 临时目录已清理")
    except Exception as e:
        print(f"⚠️ 清理临时目录失败：{e}")


@app.route('/')
def index():
    """返回前端页面"""
    return send_from_directory('.', 'index.html')


@app.route('/api/init', methods=['POST'])
def init():
    """初始化机器人（不创建会话）"""
    data = request.json
    mode = data.get('mode', 'free')
    ielts_part = data.get('ielts_part', 1)

    bot.set_mode(mode, ielts_part)

    # 雅思模式：获取初始话题
    topic = ""
    if mode == "ielts":
        topic = bot.get_ielts_topic()

    return jsonify({
        'success': True,
        'mode': mode,
        'ielts_part': ielts_part,
        'topic': topic
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """文字聊天"""
    global current_session_id
    data = request.json
    message = data.get('message', '')
    use_search = data.get('use_search', None)
    session_id = data.get('session_id')  # 前端传递的 session_id
    voice_only = data.get('voice_only', False)  # 纯语音模式标记

    if not message:
        return jsonify({'error': '消息不能为空'}), 400

    # 如果没有 session_id，使用或创建当前会话
    if not session_id:
        if not current_session_id:
            # 创建新会话
            current_session_id = db.create_session(
                title=f"free - {datetime.now().strftime('%m-%d %H:%M')}",
                mode='free',
                ielts_part=1
            )
        session_id = current_session_id
    else:
        # 验证会话是否存在
        session = db.get_session(session_id)
        if not session:
            return jsonify({'error': '会话不存在'}), 404
        current_session_id = session_id

    response, grammar_feedback = bot.chat(message, use_search=use_search)

    # 提取生词（从 AI 回复中）
    vocab_data = None
    try:
        vocab_list = bot.extract_vocab(response, max_words=3)
        if vocab_list:
            import json
            vocab_data = json.dumps(vocab_list, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ 提取生词失败：{e}")

    # 保存到数据库
    db.add_message(session_id, 'user', message, display=not voice_only)
    db.add_message(session_id, 'assistant', response, grammar_feedback, vocab_data=vocab_data)

    return jsonify({
        'success': True,
        'response': response,
        'grammar_feedback': grammar_feedback,
        'session_id': session_id
    })


@app.route('/api/tts', methods=['POST'])
def tts():
    """语音合成"""
    data = request.json
    text = data.get('text', '')

    if not text:
        return jsonify({'error': '文本不能为空'}), 400

    # 生成唯一文件名
    import uuid
    output_path = os.path.join(TMP_DIR, f"tts_{uuid.uuid4().hex}.mp3")

    # 确保目录存在
    os.makedirs(TMP_DIR, exist_ok=True)

    if bot.tts.generate(text, output_path):
        # 返回文件 URL 和文件名（用于后续删除）
        filename = os.path.basename(output_path)
        return jsonify({
            'success': True,
            'audio_url': f'/tmp/{filename}',
            'filename': filename  # 返回文件名用于追踪
        })
    else:
        return jsonify({'error': '语音合成失败'}), 500


@app.route('/tmp/<filename>')
def serve_audio(filename):
    """提供音频文件下载，播放后自动删除"""
    from flask import send_file, make_response
    import time

    file_path = os.path.join(TMP_DIR, filename)

    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404

    # 延迟删除：在后台线程中延迟删除文件
    def delayed_delete(path):
        time.sleep(2)  # 等待 2 秒确保文件已发送
        try:
            if os.path.exists(path):
                os.remove(path)
                print(f"🗑️ 已清理音频文件：{os.path.basename(path)}")
        except Exception as e:
            print(f"⚠️ 清理音频文件失败：{e}")

    # 启动后台线程进行延迟删除
    import threading
    thread = threading.Thread(target=delayed_delete, args=(file_path,))
    thread.daemon = True
    thread.start()

    return send_file(
        file_path,
        mimetype='audio/mpeg',
        as_attachment=False,
        download_name=filename
    )


@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    """语音识别"""
    if 'audio' not in request.files:
        return jsonify({'error': '没有音频文件'}), 400
    
    audio_file = request.files['audio']
    
    # 保存临时文件
    import uuid
    temp_path = os.path.join(TMP_DIR, f"transcribe_{uuid.uuid4().hex}.wav")
    os.makedirs(TMP_DIR, exist_ok=True)
    audio_file.save(temp_path)
    
    # 识别
    text = bot.stt.transcribe(temp_path)
    
    # 清理临时文件
    try:
        os.remove(temp_path)
    except:
        pass
    
    if not text:
        return jsonify({'error': '语音识别失败'}), 400
    
    return jsonify({
        'success': True,
        'text': text
    })


@app.route('/api/topic', methods=['POST'])
def get_topic():
    """获取雅思话题"""
    topic = bot.get_ielts_topic()
    return jsonify({
        'success': True,
        'topic': topic
    })


@app.route('/api/challenge', methods=['POST'])
def generate_challenge():
    """生成口语考验问题"""
    data = request.json
    topic = data.get('topic', '')
    difficulty = data.get('difficulty', 'medium')  # easy, medium, hard

    # 根据难度和话题生成挑战性问题
    difficulty_prompts = {
        'easy': "Ask a simple follow-up question that requires a 2-3 sentence answer.",
        'medium': "Ask a thought-provoking question that requires reasoning and examples.",
        'hard': "Ask a complex hypothetical or abstract question that challenges critical thinking."
    }

    prompt = f"""You are an IELTS speaking examiner. Generate a challenging speaking question for the user.

Topic: {topic if topic else 'General conversation'}
Difficulty: {difficulty}

{difficulty_prompts.get(difficulty, difficulty_prompts['medium'])}

The question should:
- Be open-ended (cannot be answered with yes/no)
- Encourage the user to speak for 1-2 minutes
- Use natural, conversational English
- Be appropriate for IELTS Speaking Part 3 level

Only output the question, nothing else."""

    try:
        from llm import GLMClient
        messages = [{"role": "user", "content": prompt}]
        challenge_question = bot.llm.chat(messages, temperature=0.8, max_tokens=200)
        
        return jsonify({
            'success': True,
            'question': challenge_question.strip(),
            'difficulty': difficulty
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== 数据库 API ====================

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """获取会话列表"""
    limit = request.args.get('limit', 50, type=int)
    sessions = db.list_sessions(limit)
    return jsonify({
        'success': True,
        'sessions': sessions
    })


@app.route('/api/sessions/<int:session_id>', methods=['GET'])
def get_session(session_id):
    """获取会话详情"""
    session = db.get_session(session_id)
    if session:
        return jsonify({
            'success': True,
            'session': session
        })
    return jsonify({'error': '会话不存在'}), 404


@app.route('/api/sessions/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    """删除会话"""
    db.delete_session(session_id)
    return jsonify({'success': True})


@app.route('/api/sessions/<int:session_id>/messages', methods=['GET'])
def get_session_messages(session_id):
    """获取会话消息"""
    limit = request.args.get('limit', 100, type=int)
    messages = db.get_messages(session_id, limit)
    return jsonify({
        'success': True,
        'messages': messages
    })


@app.route('/api/sessions/load', methods=['POST'])
def load_session():
    """加载会话"""
    global current_session_id
    data = request.json
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({'error': '会话 ID 不能为空'}), 400

    session = db.get_session(session_id)
    if not session:
        return jsonify({'error': '会话不存在'}), 404

    current_session_id = session_id

    # 获取消息（默认只显示 display=True 的消息）
    messages = db.get_messages(session_id)

    return jsonify({
        'success': True,
        'session': session,
        'messages': messages
    })


@app.route('/api/sessions/<int:session_id>/vocab', methods=['GET'])
def get_session_vocab(session_id):
    """获取会话生词本"""
    session = db.get_session(session_id)
    if not session:
        return jsonify({'error': '会话不存在'}), 404

    vocab_list = db.get_session_vocab(session_id)
    return jsonify({
        'success': True,
        'vocab': vocab_list
    })


@app.route('/api/sessions/<int:session_id>/transcript', methods=['GET'])
def get_session_transcript(session_id):
    """获取会话原文（所有消息，包括隐藏的）"""
    session = db.get_session(session_id)
    if not session:
        return jsonify({'error': '会话不存在'}), 404

    # 获取所有消息，包括隐藏的
    from db.db import get_database
    db_instance = get_database()
    
    with db_instance.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, role, content, grammar_feedback, created_at 
            FROM messages 
            WHERE session_id = ? 
            ORDER BY created_at ASC
        """, (session_id,))
        messages = [dict(row) for row in cursor.fetchall()]

    return jsonify({
        'success': True,
        'messages': messages
    })


@app.route('/api/sessions/new', methods=['POST'])
def new_session():
    """创建新会话"""
    global current_session_id
    data = request.json
    mode = data.get('mode', 'free')
    ielts_part = data.get('ielts_part', 1)

    # 创建新会话
    current_session_id = db.create_session(
        title=f"{mode} - {datetime.now().strftime('%m-%d %H:%M')}",
        mode=mode,
        ielts_part=ielts_part
    )

    return jsonify({
        'success': True,
        'session_id': current_session_id
    })


@app.route('/api/sessions/reset', methods=['POST'])
def reset_session():
    """重置当前会话（用于点击新对话时）"""
    global current_session_id
    current_session_id = None
    return jsonify({'success': True})


@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    """清空对话历史"""
    global current_session_id
    if current_session_id:
        db.clear_messages(current_session_id)
    bot.clear_history()
    return jsonify({'success': True})


@app.route('/api/history/save', methods=['POST'])
def save_history():
    """保存对话历史"""
    bot.save_history()
    return jsonify({'success': True})


@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'ok', 'message': 'DAMN API 运行中'})


if __name__ == '__main__':
    # 检查 API Key
    if not ZHIPU_API_KEY or ZHIPU_API_KEY == "your_zhipu_api_key_here":
        print("❌ 错误：请先配置 ZHIPU_API_KEY")
        print("   1. 复制 .env.example 为 .env")
        print("   2. 在 .env 中填入你的 API Key")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎓 DAMN - IELTS Speaking Assistant (Web Version)")
    print("=" * 60)
    
    # 初始化 bot
    init_bot()
    
    print("\n🌐 访问地址：http://localhost:5000")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
