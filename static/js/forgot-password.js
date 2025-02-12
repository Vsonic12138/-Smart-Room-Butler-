async function handleResetRequest(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const reason = document.getElementById('reason').value;
    
    try {
        const response = await fetch('http://localhost:5000/api/reset-password-request', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, reason })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('密码重置申请已提交，请等待管理员审核');
            window.location.href = 'login.html';
        } else {
            alert(data.message || '申请提交失败');
        }
    } catch (error) {
        console.error('申请提交失败:', error);
        alert('申请提交失败，请稍后重试');
    }
} 