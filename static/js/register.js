// 获取可用房间列表
async function fetchAvailableRooms() {
    try {
        const response = await fetch('http://localhost:5000/api/rooms/available');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const rooms = await response.json();
        
        const roomSelect = document.getElementById('roomSelect');
        roomSelect.innerHTML = '<option value="without">无房间</option>';
        
        rooms.forEach(room => {
            const option = document.createElement('option');
            option.value = room;
            option.textContent = `${room}房间`;
            roomSelect.appendChild(option);
        });
    } catch (error) {
        console.error('获取可用房间失败:', error);
        const roomSelect = document.getElementById('roomSelect');
        roomSelect.innerHTML = '<option value="without">无房间</option>';
    }
}

async function handleRegister(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    // 验证密码
    if (password !== confirmPassword) {
        alert('两次输入的密码不一致');
        return;
    }
    
    try {
        const requestData = { 
            username, 
            password 
        };
        console.log('发送注册请求:', requestData);
        
        const response = await fetch('http://localhost:5000/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',  // 添加这行以支持跨域Cookie
            body: JSON.stringify(requestData)
        });
        
        console.log('服务器响应状态:', response.status);
        const data = await response.json();
        console.log('服务器响应数据:', data);
        
        if (data.success) {
            alert('注册申请已提交，请等待管理员审核');
            window.location.href = 'login.html';
        } else {
            alert(data.message || '注册失败');
        }
    } catch (error) {
        console.error('注册失败，详细错误:', error);
        alert('注册失败，请稍后重试');
    }
}

// 密码强度检查
function checkPasswordStrength(password) {
    const strengthBar = document.querySelector('.strength-bar');
    const strength = calculatePasswordStrength(password);
    
    strengthBar.style.width = `${strength}%`;
    strengthBar.style.backgroundColor = 
        strength < 33 ? '#ff4d4f' :
        strength < 66 ? '#faad14' : '#52c41a';
}

function calculatePasswordStrength(password) {
    let strength = 0;
    if (password.length >= 8) strength += 33;
    if (/[A-Z]/.test(password)) strength += 33;
    if (/[0-9]/.test(password)) strength += 34;
    return strength;
}

document.getElementById('password').addEventListener('input', (e) => {
    checkPasswordStrength(e.target.value);
});

// 页面加载时获取可用房间
document.addEventListener('DOMContentLoaded', () => {
    fetchAvailableRooms();
}); 