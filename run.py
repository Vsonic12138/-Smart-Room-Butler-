import os
import sys
import signal
from pathlib import Path

# 获取项目根目录的绝对路径
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

def signal_handler(signum, frame):
    print('\n')  # 打印一个空行，让输出更整洁
    print('正在关闭服务器...')
    try:
        # 清理资源
        from server.app import cleanup
        cleanup()
    except Exception as e:
        print(f"清理资源时出错: {e}")
    print('服务器已安全关闭')
    sys.exit(0)

try:
    from server.app import app
    print("Successfully imported app")
except Exception as e:
    print(f"Error importing app: {e}")
    sys.exit(1)

if __name__ == '__main__':
    # 注册信号处理函数
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print(f"Python path: {sys.path}")
    print(f"Current directory: {os.getcwd()}")
    print('按Ctrl+C可以安全地关闭服务器')
    
    try:
        app.run(
            debug=True,
            host='127.0.0.1',
            port=5000,
            threaded=True
        )
    except KeyboardInterrupt:
        # 这里的代码通常不会执行，因为Flask自己会处理SIGINT
        # 但为了以防万一还是加上
        print('\n检测到Ctrl+C，正在关闭服务器...')
        try:
            from server.app import cleanup
            cleanup()
        except Exception as e:
            print(f"清理资源时出错: {e}")
        print('服务器已安全关闭')
        sys.exit(0)
    except Exception as e:
        print(f"Error running app: {e}")
        sys.exit(1) 