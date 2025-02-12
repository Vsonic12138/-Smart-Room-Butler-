"""用户处理程序"""
from flask import Blueprint, request, jsonify, session
from services.user_service import UserService
from functools import wraps
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建蓝图
user_bp = Blueprint('user', __name__)

# 初始化用户服务
data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
user_service = UserService(data_dir)

def admin_required(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({
                'success': False,
                'message': '请先登录'
            }), 401
            
        username = session['username']
        role = session.get('role')
        
        if role != 'Admin':
            return jsonify({
                'success': False,
                'message': '需要管理员权限'
            }), 403
            
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({
                'success': False,
                'message': '请先登录'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

@user_bp.route('/api/register', methods=['POST'])
def register():
    """用户注册接口"""
    try:
        data = request.get_json()
        
        # 验证请求数据
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({
                'success': False,
                'message': '请提供用户名和密码'
            }), 400
            
        username = data['username']
        password = data['password']
        
        # 注册用户
        success, message = user_service.register_user(username, password)
        
        return jsonify({
            'success': success,
            'message': message
        }), 200 if success else 400
        
    except Exception as e:
        logger.error(f"注册接口错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '注册失败，请稍后重试'
        }), 500

@user_bp.route('/api/login', methods=['POST'])
def login():
    """用户登录接口"""
    try:
        data = request.get_json()
        
        # 验证请求数据
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({
                'success': False,
                'message': '请提供用户名和密码'
            }), 400
            
        username = data['username']
        password = data['password']
        role = data.get('role', 'User')  # 默认为普通用户
        
        # 验证登录信息
        success, message, user_role = user_service.verify_login(username, password, role)
        
        if success:
            # 设置会话
            session['username'] = username
            session['role'] = user_role
            
            return jsonify({
                'success': True,
                'message': '登录成功',
                'data': {
                    'username': username,
                    'role': user_role
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
            
    except Exception as e:
        logger.error(f"登录接口错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '登录失败，请稍后重试'
        }), 500

@user_bp.route('/api/logout', methods=['POST'])
@login_required
def logout():
    """用户登出接口"""
    try:
        session.clear()
        return jsonify({
            'success': True,
            'message': '登出成功'
        }), 200
        
    except Exception as e:
        logger.error(f"登出接口错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '登出失败，请稍后重试'
        }), 500

@user_bp.route('/api/pending-users', methods=['GET'])
@admin_required
def get_pending_users():
    """获取待审核用户列表接口"""
    try:
        pending_users = user_service.get_pending_users()
        return jsonify({
            'success': True,
            'message': '获取成功',
            'data': pending_users
        }), 200
        
    except Exception as e:
        logger.error(f"获取待审核用户列表接口错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取失败，请稍后重试'
        }), 500

@user_bp.route('/api/approve-user', methods=['POST'])
@admin_required
def approve_user():
    """审核通过用户接口"""
    try:
        data = request.get_json()
        
        # 验证请求数据
        if not data or 'username' not in data:
            return jsonify({
                'success': False,
                'message': '请提供用户名'
            }), 400
            
        username = data['username']
        room_id = data.get('room_id', 'without')  # 可选参数
        
        # 审核用户
        success, message = user_service.approve_user(username, room_id)
        
        return jsonify({
            'success': success,
            'message': message
        }), 200 if success else 400
        
    except Exception as e:
        logger.error(f"审核通过用户接口错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '审核失败，请稍后重试'
        }), 500

@user_bp.route('/api/reject-user', methods=['POST'])
@admin_required
def reject_user():
    """拒绝用户注册接口"""
    try:
        data = request.get_json()
        
        # 验证请求数据
        if not data or 'username' not in data:
            return jsonify({
                'success': False,
                'message': '请提供用户名'
            }), 400
            
        username = data['username']
        
        # 拒绝用户
        success, message = user_service.reject_user(username)
        
        return jsonify({
            'success': success,
            'message': message
        }), 200 if success else 400
        
    except Exception as e:
        logger.error(f"拒绝用户接口错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '操作失败，请稍后重试'
        }), 500

@user_bp.route('/api/register-admin', methods=['POST'])
@admin_required
def register_admin():
    """注册管理员账号接口（需要管理员权限）"""
    try:
        data = request.get_json()
        
        # 验证请求数据
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({
                'success': False,
                'message': '请提供用户名和密码'
            }), 400
            
        username = data['username']
        password = data['password']
        
        # 注册管理员账号
        success, message = user_service.register_admin(username, password)
        
        return jsonify({
            'success': success,
            'message': message
        }), 200 if success else 400
        
    except Exception as e:
        logger.error(f"注册管理员账号接口错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': '注册失败，请稍后重试'
        }), 500 