// 添加到文件开头
async function checkLoginStatus() {
    const maxRetries = 3;
    let retries = 0;
    
    // 从 localStorage 获取用户信息
    const userInfo = JSON.parse(localStorage.getItem('userInfo'));
    
    if (!userInfo || !userInfo.username) {
        // 如果没有登录信息，重定向到登录页面
        window.location.href = 'login.html';
        return;
    }
    
    try {
        while (retries < maxRetries) {
            try {
                const response = await fetch('http://localhost:5000/api/verify-session', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        username: userInfo.username,
                        role: userInfo.role
                    })
                });
                
                const data = await response.json();
                
                if (!data.success) {
                    // 如果验证失败，清除登录信息并重定向
                    localStorage.removeItem('userInfo');
                    window.location.href = 'login.html';
                    return;
                }
                
                // 显示当前用户信息
                const userInfoElement = document.getElementById('currentUser');
                if (userInfoElement) {
                    userInfoElement.textContent = `当前用户: ${userInfo.username}`;
                }
                    
                // 加载用户房间信息
                await loadRoomInfo(userInfo.username);
                break;
            } catch (error) {
                retries++;
                if (retries === maxRetries) {
                    throw error;
                }
                // 等待一秒后重试
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }
    } catch (error) {
        console.error('验证登录状态失败:', error);
        const userInfoElement = document.getElementById('currentUser');
        if (userInfoElement) {
            userInfoElement.textContent = '服务器连接失败，请检查网络连接';
        }
    }
}

// 加载用户的房间信息
async function loadRoomInfo(username) {
    try {
        // 获取用户的房间信息
        const response = await fetch(`http://localhost:5000/api/user/room?username=${username}`);
        const data = await response.json();
        
        if (!data.success) {
            console.error('获取房间信息失败:', data.message);
            // 显示错误信息给用户
            document.querySelector('.temperature').textContent = '--°C';
            document.querySelector('.humidity').textContent = '--%';
            document.querySelector('.smoke').textContent = '--';
            alert('获取房间信息失败: ' + data.message);
            return;
        }

        if (!data.room_id) {
            console.error('用户未分配房间');
            alert('您还未分配房间，请联系管理员');
            return;
        }

        // 保存房间号到全局变量，供其他函数使用
        window.userRoomId = data.room_id;

        // 初始化传感器数据显示
        await refreshSensorData();

        // 设置日期选择器的默认值为今天
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('statsDate').value = today;
        
        // 更新日均值统计
        await updateDailyAverages(today);

    } catch (error) {
        console.error('加载房间信息失败:', error);
        alert('加载房间信息失败，请刷新页面重试');
    }
}

// 刷新当前房间的传感器数据
async function refreshSensorData() {
    try {
        if (!window.userRoomId) {
            console.error('未找到房间信息');
            return;
        }

        const response = await fetch(`http://localhost:5000/api/sensor-data/${window.userRoomId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        if (!data.success) {
            throw new Error(data.message || '获取传感器数据失败');
        }

        // 更新显示
        const tempElement = document.querySelector('.sensor-value.temperature');
        const humidElement = document.querySelector('.sensor-value.humidity');
        const smokeElement = document.querySelector('.sensor-value.smoke');

        if (tempElement) {
            tempElement.textContent = data.temperature !== null ? data.temperature.toFixed(1) : '--';
        }
        if (humidElement) {
            humidElement.textContent = data.humidity !== null ? data.humidity.toFixed(1) : '--';
        }
        if (smokeElement) {
            const isAlert = data.smoke > 100;
            smokeElement.textContent = isAlert ? '警报' : '正常';
            smokeElement.style.color = isAlert ? 'red' : 'green';
        }

    } catch (error) {
        console.error('刷新传感器数据失败:', error);
    }
}

// 添加警报声音
function playAlertSound() {
    // 创建音频对象
    const audio = new Audio('audio/alert.mp3');  // 需要添加音频文件
    audio.play().catch(e => console.log('播放警报声失败:', e));
}

// 更新日均值统计
async function updateDailyAverages(date) {
    try {
        if (!window.userRoomId) {
            console.error('未找到房间信息');
            return;
        }

        const response = await fetch(
            `http://localhost:5000/api/daily-averages?room_id=${window.userRoomId}&date=${date}`
        );
        const data = await response.json();
        
        // 更新显示
        document.querySelector('.day-temp').textContent = 
            data.day.temperature ? data.day.temperature.toFixed(1) : '--';
        document.querySelector('.day-humidity').textContent = 
            data.day.humidity ? data.day.humidity.toFixed(1) : '--';
        document.querySelector('.night-temp').textContent = 
            data.night.temperature ? data.night.temperature.toFixed(1) : '--';
        document.querySelector('.night-humidity').textContent = 
            data.night.humidity ? data.night.humidity.toFixed(1) : '--';
    } catch (error) {
        console.error('获取日均值失败:', error);
    }
}

// 添加退出登录功能
function logout() {
    localStorage.removeItem('userInfo');
    window.location.href = 'login.html';
}

// 页面加载完成后执行初始化
document.addEventListener('DOMContentLoaded', () => {
    checkLoginStatus();
});

async function callService() {
    try {
        const userInfo = JSON.parse(localStorage.getItem('userInfo'));
        if (!userInfo || !userInfo.username || !window.userRoomId) {
            alert('无法获取用户信息');
            return;
        }

        const button = document.querySelector('.service-btn');
        button.disabled = true;
        button.textContent = '已呼叫服务';

        const response = await fetch('http://localhost:5000/api/service-request', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: userInfo.username,
                room_id: window.userRoomId,
                timestamp: new Date().toISOString()
            })
        });

        const data = await response.json();
        if (data.success) {
            alert('服务请求已发送，工作人员稍后会来为您服务');
        } else {
            alert('服务请求发送失败: ' + data.message);
            button.disabled = false;
            button.textContent = '呼叫客房服务';
        }
    } catch (error) {
        console.error('呼叫服务失败:', error);
        alert('呼叫服务失败，请稍后重试');
        const button = document.querySelector('.service-btn');
        button.disabled = false;
        button.textContent = '呼叫客房服务';
    }
}

// 更新房间状态显示
async function updateRoomStatus() {
    try {
        const userInfo = JSON.parse(localStorage.getItem('userInfo'));
        if (!userInfo || !userInfo.username) {
            console.error('未找到用户信息');
            return;
        }

        const response = await fetch(`http://localhost:5000/api/user/room?username=${userInfo.username}`);
        const data = await response.json();

        const roomStatus = document.getElementById('roomStatus');
        const roomActions = document.getElementById('roomActions');
        
        if (!data.success) {
            roomStatus.innerHTML = `<p class="error">${data.message}</p>`;
            roomActions.innerHTML = '';
            return;
        }

        // 显示房间信息
        if (!data.room_id) {
            roomStatus.innerHTML = '<p>您还未分配房间</p>';
            roomActions.innerHTML = '';
            return;
        }

        // 根据房间状态显示不同的信息和按钮
        let statusHtml = `
            <p><strong>房间号:</strong> ${data.room_id}</p>
            <p><strong>状态:</strong> ${data.status}</p>
        `;
        
        // 只有在已入住状态下才显示入住时间
        if (data.status === '有客' && data.check_in) {
            statusHtml += `<p><strong>入住时间:</strong> ${new Date(data.check_in).toLocaleString()}</p>`;
        }
        
        roomStatus.innerHTML = statusHtml;

        // 根据状态显示不同的按钮
        if (data.status === '空闲') {
            // 未入住状态，显示入住按钮
            roomActions.innerHTML = `
                <button onclick="checkIn()" class="primary-btn">入住</button>
            `;
        } else if (data.status === '有客') {
            // 已入住状态，显示退房按钮
            roomActions.innerHTML = `
                <button onclick="requestCheckout()" class="secondary-btn">申请退房</button>
            `;
        } else if (data.status === '待退房') {
            // 退房申请中状态
            roomActions.innerHTML = `
                <p class="status-message">退房申请处理中...</p>
            `;
        }

    } catch (error) {
        console.error('更新房间状态失败:', error);
        const roomStatus = document.getElementById('roomStatus');
        roomStatus.innerHTML = '<p class="error">获取房间状态失败，请稍后重试</p>';
    }
}

// 入住功能
async function checkIn() {
    try {
        const userInfo = JSON.parse(localStorage.getItem('userInfo'));
        if (!userInfo || !userInfo.username) {
            alert('请先登录');
            return;
        }

        const response = await fetch('http://localhost:5000/api/rooms/checkin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: userInfo.username
            })
        });

        const result = await response.json();
        if (result.success) {
            alert('入住成功！');
            // 刷新房间状态
            updateRoomStatus();
        } else {
            alert(`入住失败: ${result.message}`);
        }
    } catch (error) {
        console.error('入住失败:', error);
        alert('入住失败，请稍后重试');
    }
}

// 申请退房
async function requestCheckout() {
    if (!confirm('确定要申请退房吗？')) {
        return;
    }

    try {
        const userInfo = JSON.parse(localStorage.getItem('userInfo'));
        if (!userInfo || !userInfo.username) {
            throw new Error('未找到用户信息');
        }

        // 获取当前房间信息
        const response = await fetch(`http://localhost:5000/api/user/room?username=${userInfo.username}`);
        const roomData = await response.json();
        
        if (!roomData.success || !roomData.room_id) {
            throw new Error('未找到房间信息');
        }

        // 发送退房申请
        const checkoutResponse = await fetch('http://localhost:5000/api/rooms/checkout/request', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: userInfo.username,
                room_id: roomData.room_id
            })
        });

        if (!checkoutResponse.ok) {
            throw new Error(`HTTP error! status: ${checkoutResponse.status}`);
        }

        const result = await checkoutResponse.json();
        if (result.success) {
            alert('退房申请已提交，等待管理员审核');
            // 刷新房间状态
            updateRoomStatus();
        } else {
            alert(`申请失败: ${result.message}`);
        }
    } catch (error) {
        console.error('申请退房失败:', error);
        alert('申请失败: ' + error.message);
    }
}

// 页面加载时更新房间状态
document.addEventListener('DOMContentLoaded', function() {
    updateRoomStatus();
});

// 传感器数据管理器类
class SensorDataManager {
    constructor() {
        this.updateInterval = null;
        this.lastSmokeStatus = false; // 记录上一次的烟雾状态
    }

    async updateSensorData() {
        try {
            // 更新按钮状态
            const refreshBtn = document.getElementById('refreshSensorData');
            if (refreshBtn) {
                refreshBtn.disabled = true;
                refreshBtn.textContent = '刷新中...';
            }

            const userInfo = JSON.parse(localStorage.getItem('userInfo'));
            if (!userInfo || !userInfo.username) {
                console.error('未找到用户信息');
                return;
            }

            // 获取用户的房间号
            const roomResponse = await fetch(`http://localhost:5000/api/user/room?username=${userInfo.username}`);
            const roomData = await roomResponse.json();
            
            if (!roomData.success || !roomData.room_id) {
                console.error('未找到房间信息');
                return;
            }

            // 获取传感器数据
            const response = await fetch(`http://localhost:5000/api/sensor-data/${roomData.room_id}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('传感器数据:', data);

            if (data.success) {
                this.updateUI(data);
            }
        } catch (error) {
            console.error('更新传感器数据失败:', error);
            alert('刷新数据失败，请稍后重试');
        } finally {
            // 恢复按钮状态
            const refreshBtn = document.getElementById('refreshSensorData');
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.textContent = '刷新数据';
            }
        }
    }

    updateUI(data) {
        // 更新温度
        const tempElement = document.querySelector('.temperature');
        if (tempElement && data.temperature !== null) {
            tempElement.textContent = data.temperature.toFixed(1);
        }
        
        // 更新湿度
        const humidElement = document.querySelector('.humidity');
        if (humidElement && data.humidity !== null) {
            humidElement.textContent = data.humidity.toFixed(1);
        }
        
        // 更新烟雾状态
        const smokeElement = document.querySelector('.smoke');
        if (smokeElement) {
            const smokeStatus = Boolean(data.smoke_alert); // 确保是布尔值
            console.log('当前烟雾状态:', smokeStatus, '上次状态:', this.lastSmokeStatus);
            
            // 更新显示
            if (smokeStatus) {
                smokeElement.textContent = '警报';
                smokeElement.style.color = 'red';
                // 只在状态从正常变为警报时显示提示
                if (!this.lastSmokeStatus) {
                    this.showAlert('检测到烟雾，请注意安全！');
                }
            } else {
                smokeElement.textContent = '正常';
                smokeElement.style.color = 'green';
            }
            
            // 更新状态记录
            this.lastSmokeStatus = smokeStatus;
        }
    }

    showAlert(message) {
        const alertElement = document.createElement('div');
        alertElement.className = 'alert-message';
        alertElement.innerHTML = `
            <div class="alert-content">
                <span class="alert-icon">⚠️</span>
                <span class="alert-text">${message}</span>
            </div>
        `;
        document.body.appendChild(alertElement);

        // 3秒后自动消失
        setTimeout(() => {
            alertElement.remove();
        }, 3000);
    }

    startAutoUpdate() {
        // 初始更新
        this.updateSensorData();
        // 设置定时更新
        this.updateInterval = setInterval(() => this.updateSensorData(), 5000);
    }

    stopAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
}

// 添加样式
const style = document.createElement('style');
style.textContent = `
.alert-message {
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    background-color: #fff2f0;
    border: 1px solid #ffccc7;
    padding: 10px 20px;
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    z-index: 1000;
    animation: slideDown 0.3s ease-out;
}

.alert-content {
    display: flex;
    align-items: center;
    gap: 10px;
}

.alert-icon {
    font-size: 20px;
}

.alert-text {
    color: #ff4d4f;
    font-weight: 500;
}

@keyframes slideDown {
    from {
        transform: translate(-50%, -100%);
        opacity: 0;
    }
    to {
        transform: translate(-50%, 0);
        opacity: 1;
    }
}
`;
document.head.appendChild(style);

// 创建传感器管理器实例
const sensorManager = new SensorDataManager();

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    // 启动自动更新
    sensorManager.startAutoUpdate();
    
    // 绑定刷新按钮事件（只绑定一次）
    const refreshButton = document.getElementById('refreshSensorData');
    if (refreshButton) {
        refreshButton.addEventListener('click', () => {
            sensorManager.updateSensorData();
        });
    }
});

// 页面关闭时清理
window.addEventListener('beforeunload', () => {
    sensorManager.stopAutoUpdate();
}); 