# -*- coding: utf-8 -*-
"""
ResumeRoaster API Server
提供 RESTful API 接口支持移动端应用
"""

import os
import sys
import configparser
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from main import load_config, get_llm, load_resume, create_interview_chain


# Flask 应用
app = Flask(__name__)

# 全局配置
api_config = {
    'port': 5000,
    'cors_enabled': True,
    'cors_origins': '*'
}

# 全局存储
resume_store: Dict[str, any] = {}  # resume_id -> resume data
session_store: Dict[str, any] = {}  # session_id -> session data

# 创建临时目录
TEMP_DIR = Path(__file__).parent / "temp"
TEMP_DIR.mkdir(exist_ok=True)


class SessionManager:
    """会话管理器"""
    
    @staticmethod
    def create_session(resume_id: str, chain: any) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        session_store[session_id] = {
            'resume_id': resume_id,
            'chain': chain,
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'message_count': 0
        }
        return session_id
    
    @staticmethod
    def get_session(session_id: str) -> Optional[dict]:
        """获取会话"""
        if session_id not in session_store:
            return None
        
        # 更新最后活动时间
        session_store[session_id]['last_activity'] = datetime.now()
        return session_store[session_id]
    
    @staticmethod
    def end_session(session_id: str) -> bool:
        """结束会话"""
        if session_id not in session_store:
            return False
        
        session = session_store[session_id]
        
        # 清理资源
        if 'chain' in session:
            try:
                del session['chain']
            except:
                pass
        
        del session_store[session_id]
        return True
    
    @staticmethod
    def cleanup_expired_sessions():
        """清理过期会话（超过30分钟无活动）"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session in session_store.items():
            if (now - session['last_activity']).total_seconds() > 1800:  # 30分钟
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            SessionManager.end_session(session_id)
        
        if expired_sessions:
            print(f"已清理 {len(expired_sessions)} 个过期会话")


def load_api_config():
    """加载 API 配置"""
    global api_config
    
    # 首先加载现有配置
    config = load_config()
    if config is None:
        print("警告：无法加载 config.ini，使用默认 API 配置")
        return
    
    # 读取 API 配置（从 config.ini 的 [api] 部分）
    try:
        api_config['port'] = config.get('api', 'port', fallback='5000')
        api_config['cors_enabled'] = config.getboolean('api', 'cors_enabled', fallback=True)
        api_config['cors_origins'] = config.get('api', 'cors_origins', fallback='*')
    except configparser.NoSectionError:
        print("警告：config.ini 中没有 [api] 配置段，使用默认配置")
    except Exception as e:
        print(f"警告：读取 API 配置失败：{e}，使用默认配置")
    
    # 配置 CORS
    if api_config['cors_enabled']:
        CORS(app, resources={
            r"/api/*": {
                "origins": api_config['cors_origins'],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization", "X-Session-ID"]
            }
        })
        print(f"CORS 已启用，允许来源：{api_config['cors_origins']}")


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }), 200


@app.route('/api/upload-resume', methods=['POST'])
def upload_resume():
    """上传简历接口"""
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file provided',
                'message': '请提供简历文件'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'message': '请选择文件'
            }), 400
        
        # 验证文件格式
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({
                'error': 'Invalid file format',
                'message': '仅支持 PDF 格式的简历文件'
            }), 400
        
        # 验证文件大小（10MB限制）
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 10 * 1024 * 1024:
            return jsonify({
                'error': 'File too large',
                'message': '文件大小不能超过10MB'
            }), 400
        
        # 保存文件到临时目录
        resume_id = str(uuid.uuid4())
        temp_file = TEMP_DIR / f"{resume_id}.pdf"
        file.save(str(temp_file))
        
        # 加载简历并创建简历数据
        chunks = load_resume(temp_file)
        if chunks is None:
            if temp_file.exists():
                temp_file.unlink()
            return jsonify({
                'error': 'Failed to load resume',
                'message': '无法读取简历内容'
            }), 400
        
        # 存储简历数据
        resume_store[resume_id] = {
            'file_path': str(temp_file),
            'file_name': file.filename,
            'file_size': file_size,
            'chunks': chunks,
            'uploaded_at': datetime.now()
        }
        
        return jsonify({
            'success': True,
            'resume_id': resume_id,
            'filename': file.filename,
            'file_size': file_size,
            'uploaded_at': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Upload failed',
            'message': f'上传失败：{str(e)}'
        }), 500


@app.route('/api/interview/start', methods=['POST'])
def start_interview():
    """开始面试接口"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided',
                'message': '请提供必要的参数'
            }), 400
        
        resume_id = data.get('resume_id')
        interview_style = data.get('interview_style', 'critical')  # 获取面试官风格，默认为刁钻型
        
        if not resume_id:
            return jsonify({
                'error': 'Missing resume_id',
                'message': '请提供简历ID'
            }), 400
        
        # 验证面试官风格
        valid_styles = ['critical', 'partner', 'guide']
        if interview_style not in valid_styles:
            interview_style = 'critical'
        
        # 检查简历是否存在
        if resume_id not in resume_store:
            return jsonify({
                'error': 'Resume not found',
                'message': '简历不存在或已过期'
            }), 404
        
        # 检查并发限制（防止内存溢出）
        if len(session_store) >= 10:
            return jsonify({
                'error': 'Too many sessions',
                'message': '服务器繁忙，请稍后再试'
            }), 503
        
        # 加载配置和LLM
        config = load_config()
        if config is None:
            return jsonify({
                'error': 'Configuration error',
                'message': '配置加载失败'
            }), 500
        
        # 临时设置面试官风格到配置中
        config.set('DEFAULT', 'interview_style', interview_style)
        
        llm = get_llm(config)
        if llm is None:
            return jsonify({
                'error': 'LLM initialization failed',
                'message': '无法初始化语言模型，请检查API配置'
            }), 500
        
        # 创建面试链
        try:
            chain = create_interview_chain(resume_store[resume_id]['chunks'], llm, config)
        except Exception as e:
            return jsonify({
                'error': 'Failed to create interview chain',
                'message': f'初始化面试失败：{str(e)}'
            }), 500
        
        # 创建会话
        session_id = SessionManager.create_session(resume_id, chain)
        
        # 保存面试官风格到会话中
        session_store[session_id]['interview_style'] = interview_style
        
        # 生成面试官的第一个问题
        try:
            print(f"正在生成面试官的第一个问题（风格：{interview_style}）...")
            first_response = chain.invoke({"question": "请开始面试"})
            first_question = first_response.get('answer', '你好，我是今天的面试官。让我们开始吧，请先做个自我介绍。')
            print(f"第一个问题已生成：{first_question[:50]}...")
        except Exception as e:
            print(f"生成第一个问题失败：{str(e)}")
            first_question = '你好，我是今天的面试官。让我们开始吧，请先做个自我介绍。'
        
        # 风格名称映射
        style_names = {
            'critical': '刁钻型',
            'partner': '伙伴型',
            'guide': '引导型'
        }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': first_question,
            'interview_style': interview_style,
            'style_name': style_names.get(interview_style, '刁钻型'),
            'started_at': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Start interview failed',
            'message': f'开始面试失败：{str(e)}'
        }), 500


@app.route('/api/interview/message', methods=['POST'])
def send_message():
    """发送消息接口"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided',
                'message': '请提供必要的参数'
            }), 400
        
        session_id = data.get('session_id')
        message = data.get('message')
        
        if not session_id:
            return jsonify({
                'error': 'Missing session_id',
                'message': '请提供会话ID'
            }), 400
        
        if not message or not message.strip():
            return jsonify({
                'error': 'Missing message',
                'message': '请提供消息内容'
            }), 400
        
        # 获取会话
        session = SessionManager.get_session(session_id)
        if session is None:
            return jsonify({
                'error': 'Session not found',
                'message': '会话不存在或已过期'
            }), 404
        
        # 调用面试链获取回答
        chain = session.get('chain')
        if chain is None:
            return jsonify({
                'error': 'Interview chain not found',
                'message': '面试链不存在'
            }), 500
        
        try:
            response = chain.invoke({"question": message})
            answer = response.get('answer', '抱歉，我没有收到回答。')
            
            # 更新消息计数
            session['message_count'] += 1
            
            return jsonify({
                'success': True,
                'response': answer,
                'session_id': session_id,
                'message_count': session['message_count'],
                'timestamp': datetime.now().isoformat()
            }), 200
            
        except Exception as e:
            return jsonify({
                'error': 'Failed to get response',
                'message': f'获取回答失败：{str(e)}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'error': 'Send message failed',
            'message': f'发送消息失败：{str(e)}'
        }), 500


@app.route('/api/interview/end', methods=['POST'])
def end_interview():
    """结束面试接口"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided',
                'message': '请提供必要的参数'
            }), 400
        
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({
                'error': 'Missing session_id',
                'message': '请提供会话ID'
            }), 400
        
        # 结束会话
        if SessionManager.end_session(session_id):
            return jsonify({
                'success': True,
                'message': '面试已结束，感谢您的参与！',
                'session_id': session_id,
                'ended_at': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Session not found',
                'message': '会话不存在或已过期'
            }), 404
            
    except Exception as e:
        return jsonify({
            'error': 'End interview failed',
            'message': f'结束面试失败：{str(e)}'
        }), 500


@app.errorhandler(400)
def bad_request(error):
    """处理 400 错误"""
    return jsonify({
        'error': 'Bad Request',
        'message': str(error),
        'timestamp': datetime.now().isoformat()
    }), 400


@app.errorhandler(404)
def not_found(error):
    """处理 404 错误"""
    return jsonify({
        'error': 'Not Found',
        'message': '请求的资源不存在',
        'timestamp': datetime.now().isoformat()
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """处理 500 错误"""
    return jsonify({
        'error': 'Internal Server Error',
        'message': str(error),
        'timestamp': datetime.now().isoformat()
    }), 500


def run_api_server():
    """启动 API 服务器"""
    print("\n" + "=" * 60)
    print("   ResumeRoaster API Server")
    print("=" * 60)
    
    # 加载配置
    load_api_config()
    
    # 启动服务器
    print(f"\nAPI 服务器启动中...")
    print(f"监听端口：{api_config['port']}")
    print(f"健康检查：http://localhost:{api_config['port']}/api/health")
    print("\n按 Ctrl+C 停止服务器\n")
    
    app.run(
        host='0.0.0.0',
        port=int(api_config['port']),
        debug=False,
        threaded=True
    )


if __name__ == '__main__':
    run_api_server()
