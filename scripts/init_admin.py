"""初始化管理员账号"""
import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash
import csv

def init_admin_account():
    """初始化默认管理员账号"""
    try:
        # 获取项目根目录
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(root_dir, 'data')
        admin_csv_path = os.path.join(data_dir, 'admin_accounts.csv')
        
        # 确保data目录存在
        os.makedirs(data_dir, exist_ok=True)
        
        # 默认管理员账号信息
        admin_username = 'admin'
        admin_password = 'admin'
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 生成密码哈希
        hashed_password = generate_password_hash(admin_password)
        
        # 写入CSV文件
        with open(admin_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # 写入表头
            writer.writerow(['Username', 'Password', 'Created_at'])
            # 写入管理员账号
            writer.writerow([admin_username, hashed_password, created_at])
            
        print(f"成功创建管理员账号：")
        print(f"用户名: {admin_username}")
        print(f"密码: {admin_password}")
        print(f"CSV文件路径: {admin_csv_path}")
        
    except Exception as e:
        print(f"初始化管理员账号时发生错误: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    init_admin_account() 