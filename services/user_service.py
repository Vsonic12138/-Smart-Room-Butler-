"""用户服务类"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from werkzeug.security import generate_password_hash, check_password_hash
from utils.csv_helper import CSVHelper
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, data_dir: str):
        """
        初始化用户服务
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        
        # 初始化CSV处理器
        self.users_csv = CSVHelper(
            data_dir=data_dir,
            filename='hotel_login_data.csv',
            fieldnames=['Username', 'Password', 'Role', 'Room_ID']
        )
        
        self.pending_csv = CSVHelper(
            data_dir=data_dir,
            filename='pending_users.csv',
            fieldnames=['Username', 'Password', 'created_at']
        )
        
        # 添加管理员账号CSV处理器
        self.admin_csv = CSVHelper(
            data_dir=data_dir,
            filename='admin_accounts.csv',
            fieldnames=['Username', 'Password', 'Created_at']
        )
        
        self.logger = logging.getLogger(__name__)
        
    def validate_registration(self, username: str, password: str) -> Tuple[bool, str]:
        """
        验证注册信息
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            (是否有效, 错误信息)
        """
        # 检查用户名长度
        if len(username) < 3 or len(username) > 20:
            return False, "用户名长度必须在3-20个字符之间"
            
        # 检查密码长度
        if len(password) < 6 or len(password) > 20:
            return False, "密码长度必须在6-20个字符之间"
            
        # 检查用户名是否已存在（包括正式用户、待审核用户和管理员）
        if self.check_username_exists(username):
            return False, "用户名已存在"
            
        return True, ""
        
    def check_username_exists(self, username: str) -> bool:
        """
        检查用户名是否已存在
        
        Args:
            username: 用户名
            
        Returns:
            bool: 是否存在
        """
        # 检查正式用户
        users_data = self.users_csv.read_all()
        if any(row['Username'] == username for row in users_data):
            return True
            
        # 检查待审核用户
        pending_data = self.pending_csv.read_all()
        if any(row['Username'] == username for row in pending_data):
            return True
            
        # 检查管理员账号
        admin_data = self.admin_csv.read_all()
        if any(row['Username'] == username for row in admin_data):
            return True
            
        return False
        
    def verify_login(self, username: str, password: str, role: str) -> Tuple[bool, str, Optional[str]]:
        """
        验证登录信息
        
        Args:
            username: 用户名
            password: 密码
            role: 角色（Admin或User）
            
        Returns:
            (是否成功, 消息, 用户角色)
        """
        try:
            if role == 'Admin':
                # 验证管理员账号
                admin_data = self.admin_csv.read_all()
                for admin in admin_data:
                    if admin['Username'] == username:
                        if check_password_hash(admin['Password'], password):
                            return True, "登录成功", "Admin"
                        else:
                            return False, "密码错误", None
                return False, "管理员账号不存在", None
            else:
                # 验证普通用户账号
                users_data = self.users_csv.read_all()
                for user in users_data:
                    if user['Username'] == username:
                        if check_password_hash(user['Password'], password):
                            return True, "登录成功", user['Role']
                        else:
                            return False, "密码错误", None
                return False, "用户不存在", None
                
        except Exception as e:
            self.logger.error(f"验证登录信息时发生错误: {str(e)}")
            return False, "登录失败，请稍后重试", None
            
    def register_user(self, username: str, password: str) -> Tuple[bool, str]:
        """
        注册新用户（写入待审核列表）
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            (是否成功, 消息)
        """
        try:
            # 验证注册信息
            is_valid, message = self.validate_registration(username, password)
            if not is_valid:
                return False, message
                
            # 加密密码
            hashed_password = generate_password_hash(password)
            
            # 准备用户数据
            user_data = {
                'Username': username,
                'Password': hashed_password,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 写入待审核列表
            self.pending_csv.append_row(user_data)
            
            self.logger.info(f"新用户注册成功，等待审核: {username}")
            return True, "注册成功，等待管理员审核"
            
        except Exception as e:
            self.logger.error(f"注册用户时发生错误: {str(e)}")
            return False, "注册失败，请稍后重试"
            
    def register_admin(self, username: str, password: str) -> Tuple[bool, str]:
        """
        注册新管理员账号
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            (是否成功, 消息)
        """
        try:
            # 验证注册信息
            is_valid, message = self.validate_registration(username, password)
            if not is_valid:
                return False, message
                
            # 加密密码
            hashed_password = generate_password_hash(password)
            
            # 准备管理员数据
            admin_data = {
                'Username': username,
                'Password': hashed_password,
                'Created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 写入管理员账号列表
            self.admin_csv.append_row(admin_data)
            
            self.logger.info(f"新管理员账号注册成功: {username}")
            return True, "管理员账号注册成功"
            
        except Exception as e:
            self.logger.error(f"注册管理员账号时发生错误: {str(e)}")
            return False, "注册失败，请稍后重试"
            
    def get_pending_users(self) -> List[Dict]:
        """
        获取待审核用户列表
        
        Returns:
            待审核用户列表
        """
        try:
            return self.pending_csv.read_all()
        except Exception as e:
            self.logger.error(f"获取待审核用户列表失败: {str(e)}")
            return []
            
    def approve_user(self, username: str, room_id: str = 'without') -> Tuple[bool, str]:
        """
        审核通过用户
        
        Args:
            username: 用户名
            room_id: 房间号（可选）
            
        Returns:
            (是否成功, 消息)
        """
        try:
            # 查找待审核用户
            pending_users = self.pending_csv.read_all()
            user_data = None
            for user in pending_users:
                if user['Username'] == username:
                    user_data = user
                    break
                    
            if not user_data:
                return False, "用户不存在"
                
            # 创建正式用户记录
            new_user = {
                'Username': user_data['Username'],
                'Password': user_data['Password'],  # 密码已经是加密的
                'Role': 'User',
                'Room_ID': room_id
            }
            
            # 写入正式用户列表
            self.users_csv.append_row(new_user)
            
            # 从待审核列表中删除
            self.pending_csv.delete_row({'Username': username})
            
            self.logger.info(f"用户审核通过: {username}")
            return True, "审核通过"
            
        except Exception as e:
            self.logger.error(f"审核用户时发生错误: {str(e)}")
            return False, "审核失败，请稍后重试"
            
    def reject_user(self, username: str) -> Tuple[bool, str]:
        """
        拒绝用户注册
        
        Args:
            username: 用户名
            
        Returns:
            (是否成功, 消息)
        """
        try:
            # 从待审核列表中删除
            if self.pending_csv.delete_row({'Username': username}):
                self.logger.info(f"拒绝用户注册: {username}")
                return True, "已拒绝该用户的注册申请"
            else:
                return False, "用户不存在"
                
        except Exception as e:
            self.logger.error(f"拒绝用户时发生错误: {str(e)}")
            return False, "操作失败，请稍后重试"
            
    def verify_password(self, username: str, password: str) -> bool:
        """
        验证用户密码
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            bool: 密码是否正确
        """
        try:
            users_data = self.users_csv.read_all()
            for user in users_data:
                if user['Username'] == username:
                    return check_password_hash(user['Password'], password)
            return False
            
        except Exception as e:
            self.logger.error(f"验证密码时发生错误: {str(e)}")
            return False
            
    def get_user_role(self, username: str) -> Optional[str]:
        """
        获取用户角色
        
        Args:
            username: 用户名
            
        Returns:
            Optional[str]: 用户角色
        """
        try:
            users_data = self.users_csv.read_all()
            for user in users_data:
                if user['Username'] == username:
                    return user['Role']
            return None
            
        except Exception as e:
            self.logger.error(f"获取用户角色时发生错误: {str(e)}")
            return None 