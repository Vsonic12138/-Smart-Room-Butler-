let currentLoginType = 'admin';

function switchLoginType(type) {
    currentLoginType = type;
    document.querySelectorAll('.type-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // 只在客户登录模式下显示注册选项
    const registerSection = document.getElementById('registerSection');
    registerSection.style.display = type === 'customer' ? 'block' : 'none';
    
    // 只在客户登录模式下显示忘记密码链接
    const forgotPasswordLink = document.getElementById('forgotPasswordLink');
    forgotPasswordLink.style.display = type === 'customer' ? 'inline' : 'none';
}

async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const role = currentLoginType === 'admin' ? 'Admin' : 'Customer';
    
    console.log('Login attempt:');
    console.log('- Username:', username);
    console.log('- Role:', role);
    
    try {
        const response = await fetch('http://localhost:5000/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password, role })
        });
        
        console.log('Response status:', response.status);
        const data = await response.json();
        console.log('Login response:', data);
        
        if (data.success) {
            console.log('Login successful, user data:', data);
            
            // 验证返回的数据结构
            if (!data.data || !data.data.role) {
                console.error('Invalid response data structure:', data);
                alert('登录返回数据格式错误，请联系管理员');
                return;
            }
            
            console.log('Role from server:', data.data.role);
            
            // 保存用户信息到 localStorage
            const userInfo = {
                username: username,
                role: data.data.role
            };
            console.log('Saving user info:', userInfo);
            localStorage.setItem('userInfo', JSON.stringify(userInfo));
            
            // 根据角色跳转到对应页面
            const userRole = data.data.role.toLowerCase();  // 转换为小写进行比较
            console.log('Redirecting based on role:', userRole);
            
            if (userRole === 'admin') {
                console.log('Redirecting to admin page');
                window.location.href = '/static/html/admin.html';
            } else {
                console.log('Redirecting to customer page');
                window.location.href = '/static/html/customer.html';
            }
        } else {
            console.log('Login failed:', data.message);
            alert(`登录失败: ${data.message}\n\n请确认：\n1. 用户名和密码正确\n2. 选择了正确的登录类型（${role}）`);
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('登录失败，请检查网络连接并稍后重试');
    }
}

function showRegister() {
    // 显示注册表单
    window.location.href = 'register.html';
}

// 添加表单提交事件监听
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('loginForm');
    if (form) {
        form.addEventListener('submit', handleLogin);
    }
}); 