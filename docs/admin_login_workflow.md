# 管理员登录工作流程文档

## 1. 组件架构

### 1.1 核心组件

1. **应用入口 (app.py)**
   ```python
   # 路由配置
   @app.route('/')
   def root():
       return send_from_directory('static/html', 'login.html')
   
   @app.route('/login')
   def login_page():
       return send_from_directory('static/html', 'login.html')
   ```

2. **用户服务 (services/user_service.py)**
   ```python
   class UserService:
       def __init__(self, data_dir: str):
           self.admin_csv = CSVHelper(
               data_dir=data_dir,
               filename='admin_accounts.csv',
               fieldnames=['Username', 'Password', 'Created_at']
           )
   
       def verify_login(self, username: str, password: str, role: str):
           if role == 'Admin':
               admin_data = self.admin_csv.read_all()
               for admin in admin_data:
                   if admin['Username'] == username:
                       if check_password_hash(admin['Password'], password):
                           return True, "登录成功", "Admin"
   ```

3. **用户处理器 (handlers/user_handler.py)**
   ```python
   @user_bp.route('/api/login', methods=['POST'])
   def login():
       data = request.get_json()
       username = data['username']
       password = data['password']
       role = data.get('role', 'User')
       
       success, message, user_role = user_service.verify_login(username, password, role)
       
       if success:
           session['username'] = username
           session['role'] = user_role
           return jsonify({
               'success': True,
               'message': '登录成功',
               'data': {
                   'username': username,
                   'role': user_role
               }
           })
   ```

4. **前端登录脚本 (static/js/login.js)**
   ```javascript
   async function handleLogin(event) {
       const username = document.getElementById('username').value.trim();
       const password = document.getElementById('password').value.trim();
       const role = currentLoginType === 'admin' ? 'Admin' : 'Customer';
       
       const response = await fetch('http://localhost:5000/api/login', {
           method: 'POST',
           headers: {
               'Content-Type': 'application/json',
           },
           body: JSON.stringify({ username, password, role })
       });
       
       const data = await response.json();
       if (data.success) {
           const userRole = data.data.role.toLowerCase();
           if (userRole === 'admin') {
               window.location.href = '/static/html/admin.html';
           }
       }
   }
   ```

5. **管理员初始化脚本 (scripts/init_admin.py)**
   ```python
   def init_admin_account():
       admin_username = 'admin'
       admin_password = 'admin'
       created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
       
       hashed_password = generate_password_hash(admin_password)
       
       with open(admin_csv_path, 'w', newline='', encoding='utf-8') as f:
           writer = csv.writer(f)
           writer.writerow(['Username', 'Password', 'Created_at'])
           writer.writerow([admin_username, hashed_password, created_at])
   ```

## 2. 工作流程

### 2.1 初始化流程

1. **管理员账号初始化**
   ```
   运行init_admin.py -> 生成密码哈希 -> 写入CSV文件
   ```
   - 创建默认管理员账号(admin/admin)
   - 使用werkzeug生成密码哈希
   - 写入admin_accounts.csv文件

### 2.2 登录流程

1. **前端输入**
   ```
   用户输入 -> 选择管理员登录 -> 提交表单 -> 发送API请求
   ```
   - 输入用户名和密码
   - 选择管理员登录类型
   - 表单验证
   - 发送POST请求

2. **后端验证**
   ```
   接收请求 -> 验证身份 -> 创建会话 -> 返回结果
   ```
   - 解析请求数据
   - 验证管理员身份
   - 检查密码哈希
   - 设置session

3. **登录成功**
   ```
   接收响应 -> 保存用户信息 -> 页面跳转
   ```
   - 验证响应数据
   - 存储用户信息
   - 跳转到管理页面

### 2.3 会话管理

1. **Session配置**
   ```python
   app.config.update(
       SECRET_KEY=os.urandom(24).hex(),
       SESSION_TYPE='filesystem',
       PERMANENT_SESSION_LIFETIME=timedelta(days=7)
   )
   ```

2. **权限验证装饰器**
   ```python
   def admin_required(f):
       @wraps(f)
       def decorated_function(*args, **kwargs):
           if 'username' not in session:
               return jsonify({'success': False, 'message': '请先登录'}), 401
           if session.get('role') != 'Admin':
               return jsonify({'success': False, 'message': '需要管理员权限'}), 403
           return f(*args, **kwargs)
       return decorated_function
   ```

## 3. 数据结构

### 3.1 管理员数据格式

CSV文件格式：
```
Username, Password, Created_at
admin, <hashed_password>, 2024-02-13 01:39:17
```

### 3.2 登录请求格式

```json
{
    "username": "admin",
    "password": "admin",
    "role": "Admin"
}
```

### 3.3 登录响应格式

```json
{
    "success": true,
    "message": "登录成功",
    "data": {
        "username": "admin",
        "role": "Admin"
    }
}
```

## 4. 安全考虑

### 4.1 密码安全

1. **密码加密**
   - 使用werkzeug.security加密
   - 使用安全的哈希算法
   - 加盐处理
   - 避免明文存储

2. **登录保护**
   - 密码强度验证
   - 登录失败限制
   - 会话超时设置
   - HTTPS传输

### 4.2 访问控制

1. **权限验证**
   - Session验证
   - 角色检查
   - 路由保护
   - API权限控制

2. **安全配置**
   - 安全的密钥生成
   - 跨域保护
   - 会话配置
   - 错误处理 