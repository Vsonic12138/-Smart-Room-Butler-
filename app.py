"""Flask应用主文件"""
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_session import Session
from datetime import timedelta
import os
from services.mqtt_service import mqtt_service
from handlers.user_handler import user_bp
from handlers.notification_handler import notification_bp
import atexit
import signal
import logging
import sys
import threading
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 退出标志
is_shutting_down = False
shutdown_event = threading.Event()

def create_app():
    """创建Flask应用"""
    # 创建Flask应用
    app = Flask(__name__)
    
    # 配置应用
    app.config.update(
        # Session配置
        SECRET_KEY=os.urandom(24).hex(),  # 使用随机生成的24字节密钥
        SESSION_TYPE='filesystem',
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        
        # 静态文件配置
        STATIC_FOLDER='static',
        
        # 其他配置
        JSON_AS_ASCII=False,  # 支持中文
        MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 最大16MB
    )
    
    # 初始化扩展
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })  # 启用CORS
    Session(app)  # 启用Session
    
    # 注册蓝图
    app.register_blueprint(user_bp)
    app.register_blueprint(notification_bp)  # 注册通知处理蓝图
    
    # 根路径重定向到登录页面
    @app.route('/')
    def root():
        return send_from_directory('static/html', 'login.html')
        
    # 添加常用路径的别名
    @app.route('/login')
    def login_page():
        return send_from_directory('static/html', 'login.html')
        
    @app.route('/admin')
    def admin_page():
        return send_from_directory('static/html', 'admin.html')
        
    @app.route('/register')
    def register_page():
        return send_from_directory('static/html', 'register.html')
    
    # 静态文件路由
    @app.route('/static/<path:filename>')
    def serve_static_files(filename):
        return send_from_directory('static', filename)
        
    @app.route('/<path:filename>')
    def serve_html(filename):
        return send_from_directory('static/html', filename)
    
    # 错误处理
    @app.errorhandler(404)
    def page_not_found(e):
        return {"success": False, "message": "接口不存在"}, 404
        
    @app.errorhandler(500)
    def internal_server_error(e):
        return {"success": False, "message": "服务器内部错误"}, 500
    
    return app

def handle_exit(signum, frame):
    """处理退出信号"""
    global is_shutting_down
    if is_shutting_down:
        logger.warning("已经在关闭中，请耐心等待...")
        return
        
    is_shutting_down = True
    logger.info("正在关闭应用...")
    
    try:
        # 设置退出事件
        shutdown_event.set()
        
        # 停止MQTT服务
        mqtt_service.stop()
        
        # 等待所有服务完全停止
        wait_time = 0
        max_wait = 10  # 最多等待10秒
        while mqtt_service.reconnect_thread and mqtt_service.reconnect_thread.is_alive():
            if wait_time >= max_wait:
                logger.warning("等待服务停止超时")
                break
            time.sleep(1)
            wait_time += 1
            
        logger.info("应用已关闭")
        sys.exit(0)
    except Exception as e:
        logger.error(f"关闭应用时发生错误: {e}")
        sys.exit(1)

def main():
    """主函数"""
    try:
        # 创建应用
        app = create_app()
        
        # 只在主进程中启动MQTT服务
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            # 启动MQTT服务
            mqtt_service.start()
            
            # 注册退出处理
            signal.signal(signal.SIGINT, handle_exit)
            signal.signal(signal.SIGTERM, handle_exit)
            atexit.register(mqtt_service.stop)
        
        # 运行应用
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}")
        raise

if __name__ == '__main__':
    main() 