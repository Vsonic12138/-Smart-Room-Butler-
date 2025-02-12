// MQTT客户端类
class MQTTClient {
    constructor() {
        this.client = null;
        this.lastValues = null;
    }

    connect() {
        // MQTT连接逻辑
    }

    async refreshSensorData(roomId) {
        // 刷新传感器数据逻辑
    }
}

// MQTT客户端初始化
const mqttClient = new MQTTClient();
mqttClient.connect();

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化加载
    loadUsers();
    fetchPendingItems();
    updateServiceRequests();
    loadRooms();
    initializeRoomSelector();

    // 设置定时刷新
    setInterval(updateServiceRequests, 30000); // 每30秒刷新一次服务请求
});

// 获取待处理事项
async function fetchPendingItems() {
    await Promise.all([
        fetchPendingUsers(),
        fetchPendingCheckouts()
    ]);
}

// 获取待审核用户
async function fetchPendingUsers() {
    try {
        console.log("Fetching pending users...");
        const response = await fetch('http://localhost:5000/api/pending-users', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });

        console.log("Response status:", response.status);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Received data:", data);
        
        const tbody = document.querySelector('#pendingUsersTable tbody');
        tbody.innerHTML = '';
        
        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="no-pending">暂无待审核用户</td></tr>';
            return;
        }
        
        data.forEach(user => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${user.Username}</td>
                <td>${user.room_id === 'without' ? '无' : user.room_id + '房间'}</td>
                <td>${new Date(user.created_at).toLocaleString()}</td>
                <td class="action-btns">
                    <button onclick="approveUser('${user.Username}')" class="primary-btn">批准</button>
                    <button onclick="rejectUser('${user.Username}')" class="secondary-btn">拒绝</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('获取待审核用户失败:', error);
        const tbody = document.querySelector('#pendingUsersTable tbody');
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="error-message">
                    获取待审核用户失败: ${error.message}
                </td>
            </tr>
        `;
    }
}

// 获取待审核退房申请
async function fetchPendingCheckouts() {
    try {
        const response = await fetch('http://localhost:5000/api/rooms/checkout/pending');
        const data = await response.json();
        
        const tbody = document.querySelector('#pendingCheckoutTable tbody');
        if (!tbody) {
            console.error('找不到退房申请表格');
            return;
        }
        
        tbody.innerHTML = '';
        
        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="no-pending">暂无退房申请</td></tr>';
            return;
        }
        
        data.forEach(request => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${request.room_id}</td>
                <td>${request.username}</td>
                <td>${new Date(request.timestamp).toLocaleString()}</td>
                <td class="action-btns">
                    <button onclick="approveCheckout('${request.username}', '${request.room_id}')" 
                            class="primary-btn">批准</button>
                    <button onclick="rejectCheckout('${request.username}', '${request.room_id}')" 
                            class="secondary-btn">拒绝</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('获取退房申请失败:', error);
        const tbody = document.querySelector('#pendingCheckoutTable tbody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="error-message">
                        获取退房申请失败: ${error.message}
                    </td>
                </tr>
            `;
        }
    }
}

async function approveUser(username) {
    try {
        const response = await fetch('http://localhost:5000/api/users/approve', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username })
        });

        const data = await response.json();
        if (data.success) {
            alert('用户审核通过');
            fetchPendingUsers();
            loadUsers();  // 刷新用户列表
            updateRoomStatus();  // 刷新房间状态
        } else {
            alert(data.message || '操作失败');
        }
    } catch (error) {
        console.error('审核用户失败:', error);
        alert('操作失败，请稍后重试');
    }
}

async function rejectUser(username) {
    if (!confirm(`确定要拒绝用户 ${username} 的注册申请吗？`)) return;
    
    try {
        const response = await fetch('http://localhost:5000/api/reject-user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });

        const data = await response.json();
        if (data.success) {
            alert('已拒绝该用户的注册申请');
            fetchPendingUsers();
        } else {
            alert(data.message || '操作失败');
        }
    } catch (error) {
        console.error('拒绝用户失败:', error);
        alert('操作失败，请稍后重试');
    }
}

// 获取房间状态文本
function getRoomStatusText(status) {
    const statusMap = {
        'available': '空闲',
        'occupied': '已入住',
        'assigned': '已分配',
        'pending_checkout': '待退房',
        'maintenance': '维护中'
    };
    return statusMap[status] || status;
}

// 创建房间卡片
function createRoomCard(room) {
    const card = document.createElement('div');
    card.className = 'room-card';
    card.setAttribute('data-room', room.room_id || room.Room_ID);
    
    // 格式化传感器数据显示
    const temperature = room.temperature !== null ? `${room.temperature.toFixed(1)}` : '暂无数据';
    const humidity = room.humidity !== null ? `${room.humidity.toFixed(1)}` : '暂无数据';
    const smoke = room.smoke ? 
        `${room.smoke.value.toFixed(1)} ${room.smoke.alert ? '<span class="alert">警报</span>' : '<span class="normal">正常</span>'}` : 
        '暂无数据';

    // 只有空闲房间可以删除
    const status = room.status || room.Status;
    const deleteButton = status === 'available' ? 
        `<button class="delete-btn" onclick="deleteRoom('${room.room_id || room.Room_ID}')">删除房间</button>` : '';
    
    card.innerHTML = `
        <div class="room-header">
            <h3>房间 ${room.room_id || room.Room_ID}</h3>
            ${deleteButton}
        </div>
        <div class="room-info">
            <p><span class="label">状态:</span> <span class="status">${getRoomStatusText(status)}</span></p>
            <p><span class="label">客户:</span> <span class="customer">${room.customer || room.Customer || '无'}</span></p>
            <p><span class="label">入住时间:</span> <span class="check-in">${(room.check_in || room.Check_in) ? new Date(room.check_in || room.Check_in).toLocaleString() : '无'}</span></p>
        </div>
        <div class="sensor-data">
            <p><span class="label">温度:</span> <span class="temperature">${temperature}</span>°C</p>
            <p><span class="label">湿度:</span> <span class="humidity">${humidity}</span>%</p>
            <p><span class="label">烟雾:</span> <span class="smoke">${smoke}</span></p>
        </div>
    `;
    
    return card;
}

// 更新房间状态
async function updateRoomStatus(rooms = []) {
    try {
        const roomList = document.getElementById('roomList');
        if (!roomList) {
            console.log('找不到房间列表容器，可能在其他页面');
            return;
        }

        // 清空现有内容
        roomList.innerHTML = '';
        
        // 如果没有房间数据，显示提示信息
        if (!rooms || rooms.length === 0) {
            roomList.innerHTML = '<div class="no-rooms">暂无房间数据</div>';
            return;
        }

        // 添加每个房间的卡片
        for (const room of rooms) {
            // 获取传感器数据
            try {
                const response = await fetch(`http://localhost:5000/api/sensor-data/${room.room_id || room.Room_ID}`);
                if (response.ok) {
                    const sensorData = await response.json();
                    // 合并传感器数据到房间对象
                    room.temperature = sensorData.temperature;
                    room.humidity = sensorData.humidity;
                    room.smoke = {
                        value: sensorData.smoke || 0,
                        alert: sensorData.smoke_alert
                    };
                }
            } catch (error) {
                console.error(`获取房间 ${room.room_id || room.Room_ID} 的传感器数据失败:`, error);
            }

            // 使用 createRoomCard 函数创建房间卡片
            const card = createRoomCard(room);
            roomList.appendChild(card);
        }
    } catch (error) {
        console.error('更新房间状态失败:', error);
        const roomList = document.getElementById('roomList');
        if (roomList) {
            roomList.innerHTML = `<div class="error">更新房间状态失败: ${error.message}</div>`;
        }
    }
}

// 房间切换处理
function switchRoomMonitor(roomId) {
    const roomList = document.getElementById('roomList');
    if (!roomList) {
        console.error('找不到房间列表容器');
        return;
    }

    // 获取所有房间卡片
    const roomCards = roomList.querySelectorAll('.room-card');
    let selectedRoom = null;

        roomCards.forEach(card => {
        const cardRoomId = card.getAttribute('data-room');
        const isVisible = roomId === 'all' || cardRoomId === roomId;
        card.style.display = isVisible ? 'block' : 'none';
        
        // 获取第一个可见房间的数据
        if (isVisible && !selectedRoom) {
            // 获取烟雾数据
            const smokeElement = card.querySelector('.smoke');
            const smokeText = smokeElement.textContent.trim();
            const smokeMatch = smokeText.match(/^(\d+\.?\d*)/);
            const smokeValue = smokeMatch ? parseFloat(smokeMatch[1]) : null;
            const isAlert = smokeElement.querySelector('.alert') !== null;

            selectedRoom = {
                room_id: cardRoomId,
                status: card.querySelector('.status').textContent,
                customer: card.querySelector('.customer').textContent,
                check_in: card.querySelector('.check-in').textContent,
                temperature: parseFloat(card.querySelector('.temperature').textContent) || null,
                humidity: parseFloat(card.querySelector('.humidity').textContent) || null,
                smoke: smokeValue !== null ? {
                    value: smokeValue,
                    alert: isAlert
                } : null
            };
        }
    });

    // 更新房间显示
    if (selectedRoom) {
        updateRoomDisplay(selectedRoom);
    } else {
        const roomDisplay = document.getElementById('roomDisplay');
        if (roomDisplay) {
            roomDisplay.innerHTML = `
                <div class="no-room-selected">
                    <h3>未找到房间</h3>
                    <p>选择的房间 ${roomId} 不存在或暂无数据</p>
                </div>
            `;
        }
    }
}

// 更新房间状态显示
function updateRoomDisplay(room) {
    const roomDisplay = document.getElementById('roomDisplay');
    if (!roomDisplay) {
        console.error('找不到房间显示区域');
        return;
    }

    roomDisplay.innerHTML = `
        <h2>房间 ${room.room_id}</h2>
        <div class="room-info">
            <p><span class="label">状态</span> <span class="status">${getRoomStatusText(room.status)}</span></p>
            <p><span class="label">客户</span> <span class="customer">${room.customer || '无'}</span></p>
            <p><span class="label">入住时间</span> <span class="check-in">${room.check_in ? new Date(room.check_in).toLocaleString() : '无'}</span></p>
        </div>
        <div class="sensor-data">
            <p><span class="label">温度</span> <span class="temperature">${room.temperature !== null ? room.temperature.toFixed(1) + '°C' : '暂无数据'}</span></p>
            <p><span class="label">湿度</span> <span class="humidity">${room.humidity !== null ? room.humidity.toFixed(1) + '%' : '暂无数据'}</span></p>
            <p><span class="label">烟雾</span> <span class="smoke">${
                room.smoke ? 
                `${room.smoke.value.toFixed(1)} ${room.smoke.alert ? '<span class="alert">警报</span>' : '<span class="normal">正常</span>'}` : 
                '暂无数据'
            }</span></p>
        </div>
    `;
}

// 日均值统计管理器
class DailyStatsManager {
    constructor() {
        this.currentDate = new Date().toISOString().split('T')[0];
    }

    async initialize() {
        // 设置日期选择器的默认值为今天
        const dateInput = document.getElementById('statsDate');
        if (dateInput) {
            dateInput.value = this.currentDate;
            dateInput.max = this.currentDate; // 限制最大日期为今天
            // 绑定日期变更事件
            dateInput.addEventListener('change', (e) => this.updateStats(e.target.value));
        }
        
        // 立即加载当天数据
        await this.updateStats(this.currentDate);
    }

    async updateStats(date) {
        try {
            console.log(`开始获取 ${date} 的统计数据...`);
            const response = await fetch(`http://localhost:5000/api/room-stats/daily/${date}`);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error(`HTTP错误: ${response.status}, 响应内容: ${errorText}`);
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('获取到的日均值数据:', data);

            // 更新日间数据
            const dayTemp = document.getElementById('dayTemp');
            const dayHumidity = document.getElementById('dayHumidity');
            
            // 显示日间数据（如果有）
            if (dayTemp) {
                if (data.data_points.day.temperature > 0) {
                    dayTemp.textContent = `${data.day.temperature.toFixed(1)}°C`;
                    dayTemp.title = `基于 ${data.data_points.day.temperature} 个数据点`;
                } else {
                    dayTemp.textContent = '--°C';
                    dayTemp.title = '暂无数据';
                }
            }
            
            if (dayHumidity) {
                if (data.data_points.day.humidity > 0) {
                    dayHumidity.textContent = `${data.day.humidity.toFixed(1)}%`;
                    dayHumidity.title = `基于 ${data.data_points.day.humidity} 个数据点`;
                } else {
                    dayHumidity.textContent = '--%';
                    dayHumidity.title = '暂无数据';
                }
            }

            // 更新夜间数据
            const nightTemp = document.getElementById('nightTemp');
            const nightHumidity = document.getElementById('nightHumidity');
            
            // 显示夜间数据（如果有）
            if (nightTemp) {
                if (data.data_points.night.temperature > 0) {
                    nightTemp.textContent = `${data.night.temperature.toFixed(1)}°C`;
                    nightTemp.title = `基于 ${data.data_points.night.temperature} 个数据点`;
                } else {
                    nightTemp.textContent = '--°C';
                    nightTemp.title = '暂无数据';
                }
            }
            
            if (nightHumidity) {
                if (data.data_points.night.humidity > 0) {
                    nightHumidity.textContent = `${data.night.humidity.toFixed(1)}%`;
                    nightHumidity.title = `基于 ${data.data_points.night.humidity} 个数据点`;
                } else {
                    nightHumidity.textContent = '--%';
                    nightHumidity.title = '暂无数据';
                }
            }

    } catch (error) {
            console.error('获取日均值数据失败:', error);
            // 显示错误状态
            ['dayTemp', 'dayHumidity', 'nightTemp', 'nightHumidity'].forEach(id => {
                const element = document.getElementById(id);
                if (element) {
                    element.textContent = '--';
                    element.title = '获取数据失败';
                }
            });
        }
    }
}

// 创建日均值统计管理器实例
const dailyStatsManager = new DailyStatsManager();

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', async () => {
    // ... 其他初始化代码 ...
    
    // 初始化日均值统计
    await dailyStatsManager.initialize();
});

async function updateDailyStats() {
    const roomId = document.getElementById('statsRoomSelect').value;
    const date = document.getElementById('statsDate').value;

    try {
        let data;
        if (roomId === 'all') {
            // 获取所有房间的数据
            const rooms = ['101', '102'];
            const allData = await Promise.all(rooms.map(async (room) => {
                const response = await fetch(`http://localhost:5000/api/daily-averages?room_id=${room}&date=${date}`);
                const roomData = await response.json();
                return { room, data: roomData };
            }));

            // 创建汇总显示
            const statsContent = allData.map(({ room, data }) => `
                <div class="room-stats">
                    <h4>${room}房间</h4>
                    <div class="day-night-stats">
                        <div class="time-period">
                            <h5>日间 (6:00-18:00)</h5>
                            <p>温度: ${data.day.temperature || '--'}°C</p>
                            <p>湿度: ${data.day.humidity || '--'}%</p>
                        </div>
                        <div class="time-period">
                            <h5>夜间 (18:00-6:00)</h5>
                            <p>温度: ${data.night.temperature || '--'}°C</p>
                            <p>湿度: ${data.night.humidity || '--'}%</p>
                        </div>
                    </div>
                </div>
            `).join('');

            document.querySelector('.stats-display').innerHTML = statsContent;
        } else {
            // 获取单个房间的数据
            const response = await fetch(`http://localhost:5000/api/daily-averages?room_id=${roomId}&date=${date}`);
            data = await response.json();
          
            // 更新单个房间的显示
            document.querySelector('.stats-display').innerHTML = `
                <div class="stats-card day-stats">
                    <h4>日间数据 (6:00-18:00)</h4>
                    <div class="stats-content">
                        <p>温度: ${data.day.temperature || '--'}°C</p>
                        <p>湿度: ${data.day.humidity || '--'}%</p>
                    </div>
                </div>
                <div class="stats-card night-stats">
                    <h4>夜间数据 (18:00-6:00)</h4>
                    <div class="stats-content">
                        <p>温度: ${data.night.temperature || '--'}°C</p>
                        <p>湿度: ${data.night.humidity || '--'}%</p>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('获取日均值失败:', error);
        document.querySelector('.stats-display').innerHTML = '<p>数据加载失败</p>';
    }
}

async function refreshSensorData(roomId) {
    try {
        await mqttClient.refreshSensorData(roomId);
        const roomCard = document.querySelector(`.room-item[data-room="${roomId}"]`);
        if (roomCard && mqttClient.lastValues) {
            roomCard.querySelector('.temperature').textContent = mqttClient.lastValues.temperature;
            roomCard.querySelector('.humidity').textContent = mqttClient.lastValues.humidity;
            roomCard.querySelector('.smoke').textContent = mqttClient.lastValues.smoke;
        }
    } catch (error) {
        console.error('刷新传感器数据失败:', error);
        alert('刷新数据失败，请稍后重试');
    }
}

// 加载房间列表
async function loadRooms() {
    try {
        const response = await fetch('http://localhost:5000/api/rooms/status');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const rooms = await response.json();
        updateRoomStatus(rooms);
    } catch (error) {
        console.error('加载房间列表失败:', error);
        alert('加载房间列表失败: ' + error.message);
    }
}

// 在页面加载时加载房间列表
document.addEventListener('DOMContentLoaded', () => {
    loadRooms();
    updateStatsRoomSelect();
});

// 添加新房间
async function addNewRoom() {
    const roomId = document.getElementById('newRoomId').value;
    if (!roomId) {
        alert('请输入房间号');
        return;
    }

    try {
        const response = await fetch('http://localhost:5000/api/rooms/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ room_id: roomId })
        });

        const result = await response.json();
        if (result.success) {
            alert('房间添加成功');
            document.getElementById('newRoomId').value = '';  // 清空输入框
            updateRoomStatus();  // 刷新房间列表
        } else {
            alert(`添加失败: ${result.message}`);
        }
    } catch (error) {
        console.error('添加房间失败:', error);
        alert('添加失败，请稍后重试');
    }
}

// 删除房间
async function deleteRoom(roomId) {
    try {
        if (!roomId) {
            throw new Error('房间ID不能为空');
        }

        // 确认删除
    if (!confirm(`确定要删除房间 ${roomId} 吗？`)) {
        return;
    }

        console.log(`正在删除房间: ${roomId}`);
        const response = await fetch(`http://localhost:5000/api/rooms/delete/${roomId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        if (!result.success) {
            throw new Error(result.message || '删除失败');
        }

        alert('房间删除成功');
        // 刷新房间列表
        loadRooms();

    } catch (error) {
        console.error('删除房间失败:', error);
        alert('删除失败: ' + error.message);
    }
}

// 用户管理相关函数
let allUsers = [];  // 存储所有用户数据

async function loadUsers() {
    try {
        const response = await fetch('http://localhost:5000/api/users');
        const data = await response.json();

        if (!Array.isArray(data)) {
            throw new Error('Invalid data format');
        }

        const tbody = document.querySelector('#userListTable tbody');
        tbody.innerHTML = '';

        data.forEach(user => {
            const tr = document.createElement('tr');
            tr.setAttribute('data-username', user.Username);
            tr.innerHTML = `
                <td>${user.Username}</td>
                <td>${user.Role}</td>
                <td>${user.Room_ID}</td>
                <td>
                    <button onclick="editUser('${user.Username}')" class="edit-btn">编辑</button>
                    <button onclick="deleteUser('${user.Username}')" class="delete-btn">删除</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

    } catch (error) {
        console.error('加载用户列表失败:', error);
        const tbody = document.querySelector('#userListTable tbody');
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="error-message">
                    加载用户列表失败: ${error.message}
                </td>
            </tr>
        `;
    }
}

function displayUsers(users) {
    const tbody = document.querySelector('#userListTable tbody');
    if (!tbody) {
        console.error("找不到用户表格tbody元素");
        return;
    }
    tbody.innerHTML = '';
    
    if (users.length === 0) {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td colspan="4" class="no-results">没有找到匹配的用户</td>
        `;
        tbody.appendChild(tr);
        return;
    }
    
    users.forEach(user => {
        console.log("处理用户:", user);
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${user.Username || ''}</td>
            <td>${user.Role || ''}</td>
            <td>${user.room_id || ''}</td>
            <td class="user-actions">
                <button onclick="editUser(this)" class="secondary-btn">编辑</button>
                ${user.Role !== 'Admin' ? 
                    `<button onclick="deleteUser('${user.Username}')" class="danger-btn">删除</button>` : 
                    ''}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function searchUsers() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    
    if (!searchTerm) {
        displayUsers(allUsers);
        return;
    }
    
    const filteredUsers = allUsers.filter(user => 
        user.Username.toLowerCase().includes(searchTerm) ||
        user.Role.toLowerCase().includes(searchTerm) ||
        user.room_id.toLowerCase().includes(searchTerm)
    );
    
    displayUsers(filteredUsers);
}

function resetSearch() {
    document.getElementById('searchInput').value = '';
    displayUsers(allUsers);
}

// 添加搜索框的实时搜索功能
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            // 使用防抖来优化性能
            clearTimeout(searchInput.timer);
            searchInput.timer = setTimeout(() => {
                searchUsers();
            }, 300);
        });
    }
});

async function updateRoomSelect() {
    try {
        const response = await fetch('http://localhost:5000/api/rooms');
        const rooms = await response.json();
        
        const select = document.getElementById('newUserRoom');
        select.innerHTML = '<option value="without">无房间</option>';
        
        Object.keys(rooms).forEach(room => {
            if (rooms[room].status === 'available') {
                const option = document.createElement('option');
                option.value = room;
                option.textContent = `${room}房间`;
                select.appendChild(option);
            }
        });
    } catch (error) {
        console.error('加载房间列表失败:', error);
    }
}

// 当角色选择改变时更新房间选择器
document.addEventListener('DOMContentLoaded', () => {
    const roleSelect = document.getElementById('newUserRole');
    const roomSelect = document.getElementById('roomSelect');
    
    if (roleSelect && roomSelect) {
        roleSelect.addEventListener('change', function() {
            console.log('角色选择改变:', this.value);
    if (this.value === 'Customer') {
        roomSelect.disabled = false;
                updateAvailableRooms();  // 更新可用房间列表
    } else {
        roomSelect.disabled = true;
        roomSelect.value = 'without';
            }
        });
        
        // 初始加载可用房间
        if (roleSelect.value === 'Customer') {
            updateAvailableRooms();
        }
    }
});

// 更新可用房间列表
async function updateAvailableRooms() {
    try {
        console.log('正在获取可用房间列表...');
        const response = await fetch('http://localhost:5000/api/rooms/available');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const rooms = await response.json();
        console.log('获取到的可用房间:', rooms);
        
        const roomSelect = document.getElementById('roomSelect');
        if (!roomSelect) {
            console.error('找不到房间选择器元素');
            return;
        }

        // 清空现有选项
        roomSelect.innerHTML = '<option value="without">无房间</option>';
        
        // 添加可用房间
        if (Array.isArray(rooms)) {
        rooms.forEach(room => {
                const option = document.createElement('option');
                option.value = room.Room_ID;
                option.textContent = `${room.Room_ID}房间`;
                roomSelect.appendChild(option);
        });
            console.log(`已添加 ${rooms.length} 个可用房间选项`);
        }
    } catch (error) {
        console.error('获取可用房间失败:', error);
        alert('获取可用房间列表失败，请稍后重试');
    }
}

// 添加新用户
async function addUser() {
    try {
    const username = document.getElementById('newUsername').value;
    const password = document.getElementById('newPassword').value;
    const role = document.getElementById('newUserRole').value;
        const roomId = document.getElementById('roomSelect').value;
        
        console.log('添加新用户:', {
            username,
            role,
            roomId
        });

        // 验证输入
    if (!username || !password) {
        alert('请填写用户名和密码');
        return;
    }

        // 如果是客户，必须选择房间
        if (role === 'Customer' && (!roomId || roomId === 'without')) {
            alert('客户必须选择房间');
        return;
    }

        const response = await fetch('http://localhost:5000/api/users/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                password,
                role,
                room_id: roomId
            })
        });
        
        const result = await response.json();
        if (result.success) {
            alert('用户添加成功');
            // 清空输入框
            document.getElementById('newUsername').value = '';
            document.getElementById('newPassword').value = '';
            document.getElementById('roomSelect').value = 'without';
            // 刷新用户列表和房间状态
            loadUsers();
            loadRooms();
            updateAvailableRooms();  // 更新可用房间列表
        } else {
            alert(result.message || '添加失败');
        }
    } catch (error) {
        console.error('添加用户失败:', error);
        alert('添加用户失败: ' + error.message);
    }
}

async function editUser(button) {
    try {
        // 确保获取到正确的按钮元素和行元素
        const row = button instanceof HTMLElement ? 
            button.closest('tr') : 
            document.querySelector(`tr[data-username="${button}"]`);

        if (!row) {
            throw new Error('未找到用户信息行');
        }

        const username = row.querySelector('td:first-child').textContent;
        const currentRole = row.querySelector('td:nth-child(2)').textContent;
        const currentRoom = row.querySelector('td:nth-child(3)').textContent;

        // 获取可用房间列表
        let availableRooms = [];
        try {
            const response = await fetch('http://localhost:5000/api/rooms/available');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const roomsData = await response.json();
            // 从返回的对象数组中提取房间ID
            availableRooms = roomsData.map(room => room.Room_ID);
            console.log('获取到的空闲房间:', availableRooms);
        } catch (error) {
            console.error('获取可用房间失败:', error);
            availableRooms = [];
        }

        // 创建编辑表单
        const form = document.createElement('div');
        form.className = 'edit-form';
        form.innerHTML = `
            <h3>编辑用户: ${username}</h3>
            <div class="form-group">
                <label>角色:</label>
                <select id="editRole">
                    <option value="Customer" ${currentRole === 'Customer' ? 'selected' : ''}>客户</option>
                    <option value="Admin" ${currentRole === 'Admin' ? 'selected' : ''}>管理员</option>
                </select>
            </div>
            <div class="form-group">
                <label>房间:</label>
                <select id="editRoom">
                    <option value="without">无房间</option>
                    ${currentRoom !== 'without' ? 
                        `<option value="${currentRoom}" selected>${currentRoom}</option>` : ''}
                    ${availableRooms.map(room => 
                        `<option value="${room}">${room}房间</option>`).join('')}
                </select>
            </div>
            <div class="form-group">
                <label>新密码:</label>
                <input type="password" id="editPassword" placeholder="留空表示不修改">
            </div>
            <div class="form-group buttons">
                <button onclick="saveUserEdit('${username}')" class="primary-btn">保存</button>
                <button onclick="cancelEdit()" class="secondary-btn">取消</button>
            </div>
        `;

        // 创建遮罩层并显示编辑表单
        const overlay = document.createElement('div');
        overlay.className = 'edit-overlay';
        overlay.appendChild(form);
        document.body.appendChild(overlay);

    } catch (error) {
        console.error('编辑用户失败:', error);
        alert('编辑用户失败: ' + error.message);
    }
}

async function updateEditRoomSelect(select, currentRoom) {
    try {
        const response = await fetch('http://localhost:5000/api/rooms');
        const rooms = await response.json();
        
        Object.keys(rooms).forEach(room => {
            if (rooms[room].status === 'available' || room === currentRoom) {
                const option = document.createElement('option');
                option.value = room;
                option.textContent = `${room}房间`;
                option.selected = room === currentRoom;
                select.appendChild(option);
            }
        });
    } catch (error) {
        console.error('加载房间列表失败:', error);
    }
}

async function saveUser(button, oldUsername) {
    const tr = button.closest('tr');
    const newUsername = tr.cells[0].querySelector('input').value;
    const newRole = tr.cells[1].querySelector('select').value;
    const newRoom = tr.cells[2].querySelector('select').value;
    
    try {
        const response = await fetch('http://localhost:5000/api/users/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                old_username: oldUsername,
                username: newUsername,
                role: newRole,
                room_id: newRoom
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            loadUsers();
        } else {
            alert(data.message || '更新失败');
        }
    } catch (error) {
        console.error('更新用户失败:', error);
        alert('更新失败，请稍后重试');
    }
}

function cancelEdit(button) {
    loadUsers();
}

async function deleteUser(username) {
    if (!confirm(`确定要删除用户 ${username} 吗？`)) {
        return;
    }
    
    try {
        const response = await fetch('http://localhost:5000/api/users/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('用户删除成功');
            loadUsers();
            updateRoomStatus();  // 刷新房间状态
        } else {
            alert(`删除失败: ${result.message}`);
        }
    } catch (error) {
        console.error('删除用户失败:', error);
        alert('删除失败，请稍后重试');
    }
}

// 密码重置请求相关函数
async function fetchResetRequests() {
    try {
        const response = await fetch('http://localhost:5000/api/pending-resets');
        const data = await response.json();
        
        const tbody = document.querySelector('#resetRequestsTable tbody');
        tbody.innerHTML = '';
        
        data.forEach(request => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${request.username}</td>
                <td>${request.reason}</td>
                <td>${new Date(request.created_at).toLocaleString()}</td>
                <td>
                    <button onclick="handleResetPassword('${request.username}')" class="primary-btn">
                        重置密码
                    </button>
                    <button onclick="rejectReset('${request.username}')" class="secondary-btn">
                        拒绝
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('获取密码重置请求失败:', error);
    }
}

// 处理密码重置请求
async function handleResetRequest(username) {
    try {
        const newPassword = prompt(`请输入用户 ${username} 的新密码：`);
        if (!newPassword) {
            return; // 用户取消了输入
        }

        console.log(`处理用户 ${username} 的密码重置请求`);
        const response = await fetch('http://localhost:5000/api/approve-reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                new_password: newPassword
            })
        });

        const result = await response.json();
        if (result.success) {
            alert('密码重置成功');
            // 刷新重置请求列表
            loadResetRequests();
        } else {
            alert('密码重置失败: ' + (result.message || '未知错误'));
        }
    } catch (error) {
        console.error('处理密码重置请求失败:', error);
        alert('操作失败，请稍后重试');
    }
}

async function rejectReset(username) {
    if (!confirm(`确定要拒绝 ${username} 的密码重置请求吗？`)) {
        return;
    }

    try {
        const response = await fetch('http://localhost:5000/api/reject-reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username })
        });

        const data = await response.json();
        if (data.success) {
            alert('已拒绝密码重置请求');
            fetchResetRequests();
        } else {
            alert(data.message || '操作失败');
        }
    } catch (error) {
        console.error('拒绝重置请求失败:', error);
        alert('操作失败，请稍后重试');
    }
}

// 切换模块显示
async function switchModule(moduleId) {
    try {
        // 更新按钮状态
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[onclick="switchModule('${moduleId}')"]`).classList.add('active');
        
    // 隐藏所有模块
    document.querySelectorAll('.module-container').forEach(container => {
        container.style.display = 'none';
    });
    
    // 显示选中的模块
        const selectedModule = document.getElementById(moduleId);
        if (selectedModule) {
            selectedModule.style.display = 'block';
            
            // 根据模块类型执行相应的初始化
            if (moduleId === 'room-management') {
                // 加载房间状态
                const response = await fetch('http://localhost:5000/api/rooms/status');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const rooms = await response.json();
                await updateRoomStatus(rooms);
            } else if (moduleId === 'user-management') {
                // 加载用户列表
        loadUsers();
                // 获取待处理事项
                fetchPendingItems();
            }
        }
    } catch (error) {
        console.error('切换模块失败:', error);
        alert('加载模块数据失败，请刷新页面重试');
    }
}

// 登录状态检查
async function checkLoginStatus() {
    // 从 localStorage 获取用户信息
    const userInfo = JSON.parse(localStorage.getItem('userInfo'));
    
    if (!userInfo || !userInfo.username || userInfo.role !== 'Admin') {
        // 如果没有登录信息或不是管理员，重定向到登录页面
        window.location.href = 'login.html';
        return;
    }
    
    try {
        // 验证登录状态
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
        document.getElementById('currentUser').textContent = 
            `当前用户: ${userInfo.username} (${userInfo.role})`;
             
    } catch (error) {
        console.error('验证登录状态失败:', error);
        window.location.href = 'login.html';
    }
}

// 退出登录
function logout() {
    localStorage.removeItem('userInfo');
    window.location.href = 'login.html';
}

// 页面初始化
document.addEventListener('DOMContentLoaded', () => {
    checkLoginStatus();
    // 设置默认日期
    document.getElementById('statsDate').value = new Date().toISOString().split('T')[0];
    // 默认显示用户管理模块
    switchModule('user-management');
    // 确保用户列表被加载
    loadUsers();
    // 初始化显示所有房间
    switchRoomMonitor('all');
    // 启动定时更新
    setInterval(updateRoomStatus, 30000);
    // 添加最近数据的初始化
    initializeRecentData();
});

// 初始化显示最近的传感器数据
async function initializeRecentData() {
    try {
        const response = await fetch('http://localhost:5000/api/recent-data');
        const data = await response.json();
        
        if (!Array.isArray(data) || data.length === 0) {
            // 如果没有数据，显示默认消息
            const defaultMessage = '<tr><td colspan="5">暂无最近数据</td></tr>';
            document.querySelector('#historyChart').innerHTML = createEmptyTable(defaultMessage);
            document.querySelector('#alertsTable tbody').innerHTML = '<tr><td colspan="4">近三天无烟雾警报</td></tr>';
            document.querySelector('.stats-display').innerHTML = '<p>暂无统计数据</p>';
            return;
        }

        // 更新传感器数据分析表格
        const analysisTable = document.createElement('table');
        analysisTable.className = 'sensor-history-table';
        analysisTable.innerHTML = `
            <thead>
                <tr>
                    <th>时间</th>
                    <th>房间</th>
                    <th>温度 (°C)</th>
                    <th>湿度 (%)</th>
                    <th>烟雾报警</th>
                </tr>
            </thead>
            <tbody>
                ${data.map(item => `
                    <tr>
                        <td>${item.timestamp}</td>
                        <td>${item.room_id}</td>
                        <td>${item.temperature !== null ? item.temperature.toFixed(1) : '--'}</td>
                        <td>${item.humidity !== null ? item.humidity.toFixed(1) : '--'}</td>
                        <td>${item.smoke ? '是' : '否'}</td>
                    </tr>
                `).join('')}
            </tbody>
        `;

        // 检查是否有烟雾警报
        const hasSmoke = data.some(item => item.smoke);
        
        // 更新各个数据显示区域
        // 1. 传感器历史数据
        document.getElementById('historyChart').innerHTML = '';
        document.getElementById('historyChart').appendChild(analysisTable.cloneNode(true));

        // 2. 警报历史
        const alertsBody = document.querySelector('#alertsTable tbody');
        if (hasSmoke) {
            alertsBody.innerHTML = data
                .filter(item => item.smoke || 
                              item.temperature > 28 || item.temperature < 18 ||
                              item.humidity > 70 || item.humidity < 30)
                .map(item => `
                    <tr>
                        <td>${item.timestamp}</td>
                        <td>${item.room_id}</td>
                        <td>${getAlertType(item)}</td>
                        <td>${getAlertStatus(item)}</td>
                    </tr>
                `).join('') || '<tr><td colspan="4">近期无异常数据</td></tr>';
        } else {
            alertsBody.innerHTML = '<tr><td colspan="4">近三天无烟雾警报</td></tr>';
        }

        // 3. 日均值统计
        const statsDisplay = document.querySelector('.stats-display');
        if (data.length > 0) {
            // 按房间分组计算平均值
            const roomStats = {};
            data.forEach(item => {
                if (!roomStats[item.room_id]) {
                    roomStats[item.room_id] = {
                        temps: [],
                        humids: []
                    };
                }
                if (item.temperature !== null) roomStats[item.room_id].temps.push(item.temperature);
                if (item.humidity !== null) roomStats[item.room_id].humids.push(item.humidity);
            });

            statsDisplay.innerHTML = Object.entries(roomStats)
                .map(([roomId, stats]) => `
                    <div class="stats-card">
                        <h4>${roomId}房间平均值</h4>
                        <p>温度: ${stats.temps.length ? 
                            (stats.temps.reduce((a,b) => a+b) / stats.temps.length).toFixed(1) : '--'}°C</p>
                        <p>湿度: ${stats.humids.length ? 
                            (stats.humids.reduce((a,b) => a+b) / stats.humids.length).toFixed(1) : '--'}%</p>
                    </div>
                `).join('');
        } else {
            statsDisplay.innerHTML = '<p>暂无统计数据</p>';
        }
        
    } catch (error) {
        console.error('获取最近数据失败:', error);
        // 显示错误信息
        document.getElementById('historyChart').innerHTML = '<p>数据加载失败</p>';
        document.querySelector('#alertsTable tbody').innerHTML = '<tr><td colspan="4">数据加载失败</td></tr>';
        document.querySelector('.stats-display').innerHTML = '<p>数据加载失败</p>';
    }
}

// 辅助函数：创建空表格
function createEmptyTable(message) {
    return `
        <table class="sensor-history-table">
            <thead>
                <tr>
                    <th>时间</th>
                    <th>房间</th>
                    <th>温度 (°C)</th>
                    <th>湿度 (%)</th>
                    <th>烟雾报警</th>
                </tr>
            </thead>
            <tbody>
                ${message}
            </tbody>
        </table>
    `;
}

// 辅助函数：获取警报类型
function getAlertType(data) {
    if (data.smoke) return '烟雾';
    if (data.temperature > 28 || data.temperature < 18) return '温度';
    if (data.humidity > 70 || data.humidity < 30) return '湿度';
    return '正常';
}

// 辅助函数：获取警报状态
function getAlertStatus(data) {
    if (data.smoke) return '报警';
    if (data.temperature > 28) return '温度过高';
    if (data.temperature < 18) return '温度过低';
    if (data.humidity > 70) return '湿度过高';
    if (data.humidity < 30) return '湿度过低';
    return '正常';
}

async function approveCheckout(username, roomId) {
    try {
        const response = await fetch('http://localhost:5000/api/rooms/checkout/approve', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                room_id: roomId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        if (result.success) {
            alert('已批准退房申请');
            // 刷新退房申请列表
            fetchPendingCheckouts();
        } else {
            alert(`批准失败: ${result.message}`);
        }
    } catch (error) {
        console.error('批准退房失败:', error);
        alert('批准退房失败，请稍后重试');
    }
}

async function rejectCheckout(username, roomId) {
    try {
        const response = await fetch('http://localhost:5000/api/rooms/checkout/reject', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                room_id: roomId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        if (result.success) {
            alert('已拒绝退房申请');
            // 刷新退房申请列表
            fetchPendingCheckouts();
        } else {
            alert(`拒绝失败: ${result.message}`);
        }
    } catch (error) {
        console.error('拒绝退房失败:', error);
        alert('拒绝退房失败，请稍后重试');
    }
} 

// 获取可用房间选项
async function getRoomOptions(currentRoom) {
    try {
        const response = await fetch('http://localhost:5000/api/rooms/status');
        const rooms = await response.json();
        
        let options = '<option value="without">无房间</option>';
        rooms.forEach(room => {
            if (room.status === 'available' || room.id === currentRoom) {
                options += `<option value="${room.id}" ${
                    room.id === currentRoom ? 'selected' : ''
                }>${room.id}房间</option>`;
            }
        });
        return options;
    } catch (error) {
        console.error('获取房间选项失败:', error);
        return '<option value="without">无房间</option>';
    }
}

// 保存用户编辑
async function saveUserEdit(username) {
    try {
        const role = document.getElementById('editRole').value;
        const room = document.getElementById('editRoom').value;
        const password = document.getElementById('editPassword').value;

        const response = await fetch('http://localhost:5000/api/users/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                role,
                room_id: room,
                password: password || undefined  // 如果密码为空，则不更新密码
            })
        });

        const result = await response.json();
        if (result.success) {
            alert('用户信息更新成功');
            cancelEdit();
            loadUsers();  // 刷新用户列表
        } else {
            alert(`更新失败: ${result.message}`);
        }
    } catch (error) {
        console.error('保存用户编辑失败:', error);
        alert('保存失败，请稍后重试');
    }
}

// 取消编辑
function cancelEdit() {
    const overlay = document.querySelector('.edit-overlay');
    if (overlay) {
        overlay.remove();
    }
} 
                
                // 更新传感器数据
async function updateSensorData(roomId, sensorDataId) {
    if (!roomId || !sensorDataId) {
        console.error('缺少必要参数:', { roomId, sensorDataId });
        return;
    }

    try {
        console.log(`正在更新房间 ${roomId} 的传感器数据`);
        const response = await fetch(`http://localhost:5000/api/sensor-data/${roomId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log(`房间 ${roomId} 的传感器数据:`, data);
        
        // 使用ID选择器查找传感器数据容器
        const sensorData = document.getElementById(sensorDataId);
        if (!sensorData) {
            console.error(`找不到房间 ${roomId} 的传感器数据元素 (ID: ${sensorDataId})`);
            return;
        }

        if (data.success) {
            // 更新温度
            const tempElement = sensorData.querySelector('.temperature');
            if (tempElement && data.temperature !== null) {
                tempElement.textContent = data.temperature.toFixed(1);
            }
            
            // 更新湿度
            const humidElement = sensorData.querySelector('.humidity');
            if (humidElement && data.humidity !== null) {
                humidElement.textContent = data.humidity.toFixed(1);
            }
            
            // 更新烟雾状态
            const smokeElement = sensorData.querySelector('.smoke');
            if (smokeElement) {
                if (data.smoke_alert) {
                    smokeElement.textContent = '警报';
                    smokeElement.style.color = 'red';
                } else {
                    smokeElement.textContent = '正常';
                    smokeElement.style.color = 'green';
                }
            }
        }
    } catch (error) {
        console.error(`更新房间 ${roomId} 传感器数据失败:`, error);
    }
}

// 更新统计房间选择器
async function updateStatsRoomSelect() {
    try {
        const select = document.getElementById('statsRoomSelect');
        if (!select) {
            console.log('找不到房间选择器，可能在其他页面');
            return;
        }

        const response = await fetch('http://localhost:5000/api/rooms/status');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const rooms = await response.json();
        select.innerHTML = '<option value="">请选择房间</option>';
        
        rooms.forEach(room => {
            const option = document.createElement('option');
            option.value = room.room_id || room.Room_ID;
            option.textContent = `${room.room_id || room.Room_ID}房间`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('加载房间列表失败:', error);
    }
}

// 更新服务请求列表
async function updateServiceRequests() {
    try {
        const requestsList = document.getElementById('serviceRequests');
        if (!requestsList) {
            console.error('找不到服务请求列表容器 (id: serviceRequests)');
            return;
        }

        const response = await fetch('http://localhost:5000/api/service-requests');
        const data = await response.json();
        
        // 获取是否显示已完成的服务
        const showCompleted = document.getElementById('showCompleted')?.checked || false;
        
        // 过滤请求
        const filteredRequests = data.filter(request => 
            showCompleted || request.status === 'pending'
        );
        
        if (filteredRequests.length === 0) {
            requestsList.innerHTML = '<p class="no-requests">暂无服务请求</p>';
                return;
            }

        requestsList.innerHTML = '';
        filteredRequests.forEach(request => {
            const requestElement = document.createElement('div');
            requestElement.className = `service-request-item ${request.status}`;
            requestElement.innerHTML = `
                <div class="request-info">
                    <p>房间号: ${request.room_id}</p>
                    <p>用户: ${request.username}</p>
                    <p>时间: ${new Date(request.timestamp).toLocaleString()}</p>
                    <p>状态: ${getStatusText(request.status)}</p>
                </div>
                ${request.status === 'pending' ? `
                    <div class="request-actions">
                        <button onclick="handleServiceRequest('${request.id}', 'complete')" class="complete-btn">完成</button>
                        <button onclick="handleServiceRequest('${request.id}', 'reject')" class="reject-btn">拒绝</button>
                    </div>
                ` : ''}
            `;
            requestsList.appendChild(requestElement);
        });
    } catch (error) {
        console.error('获取服务请求失败:', error);
        const requestsList = document.getElementById('serviceRequests');
        if (requestsList) {
            requestsList.innerHTML = '<p class="error">获取服务请求失败，请刷新页面重试</p>';
        }
    }
} 

// 获取服务类型文本
function getServiceTypeText(type) {
    const typeMap = {
        'cleaning': '清洁服务',
        'maintenance': '维修服务',
        'food': '餐饮服务',
        'other': '其他服务'
    };
    return typeMap[type] || type;
}

// 获取状态文本
function getStatusText(status) {
    const statusMap = {
        'pending': '待处理',
        'completed': '已完成',
        'rejected': '已拒绝'
    };
    return statusMap[status] || status;
}

// 更新退房申请列表
async function updateCheckoutRequests() {
    try {
        const response = await fetch('http://localhost:5000/api/checkout-requests');
        const data = await response.json();
        
        const requestsList = document.getElementById('checkoutRequests');
        if (!requestsList) return;
        
        if (data.length === 0) {
            requestsList.innerHTML = '<tr><td colspan="4">暂无退房申请</td></tr>';
            return;
        }
        
        requestsList.innerHTML = data.map(request => `
            <tr>
                <td>${request.room_id}</td>
                <td>${request.customer}</td>
                <td>${new Date(request.check_out).toLocaleString()}</td>
                <td>
                    <button onclick="handleCheckout('${request.room_id}', '${request.customer}', 'approve')" class="approve-btn">批准</button>
                    <button onclick="handleCheckout('${request.room_id}', '${request.customer}', 'reject')" class="reject-btn">拒绝</button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('获取退房申请失败:', error);
        const requestsList = document.getElementById('checkoutRequests');
        if (requestsList) {
            requestsList.innerHTML = '<tr><td colspan="4">获取退房申请失败</td></tr>';
        }
    }
} 

// 查询传感器历史数据
async function querySensorHistory() {
    try {
        const historyContainer = document.getElementById('sensorHistory');
        if (!historyContainer) {
            console.error('找不到历史数据容器元素 (id: sensorHistory)');
            alert('页面缺少必要的显示元素，请联系管理员');
            return;
        }

        const roomSelect = document.getElementById('monitorRoomSelect');
        if (!roomSelect) {
            throw new Error('找不到房间选择器');
        }
        
        const roomId = roomSelect.value;
        console.log('Selected room:', roomId, 'Select element:', roomSelect);
        
        if (!roomId || roomId === '') {
            alert('请选择一个房间');
            return;
        }

    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;

        if (!startDate || !endDate) {
            alert('请选择开始和结束日期');
            return;
        }

        // 显示加载状态
        historyContainer.innerHTML = '<p>加载中...</p>';

        console.log(`Fetching history for room ${roomId} from ${startDate} to ${endDate}`);

        const response = await fetch(`http://localhost:5000/api/sensor-history?room_id=${roomId}&start_date=${startDate}&end_date=${endDate}`);
        const data = await response.json();
        
        console.log('Response data:', data);

        // 确保数据是数组
        const history = Array.isArray(data) ? data : (data.data || []);
        if (history.length === 0) {
            historyContainer.innerHTML = '<p>该时间段内无数据</p>';
            return;
        }

        // 按类型分组数据
        const groupedData = {
            temperature: [],
            humidity: [],
            smoke: []
        };

        // 确保每个记录都有正确的格式
        history.forEach(record => {
            if (record && record.type && typeof record.value !== 'undefined' && record.timestamp) {
                if (groupedData[record.type]) {
                    groupedData[record.type].push({
                        value: parseFloat(record.value),
                        timestamp: new Date(record.timestamp).toLocaleString()
                    });
                }
            }
        });

        // 生成显示内容
        let html = '<div class="history-data">';
        
        // 温度数据
        if (groupedData.temperature.length > 0) {
            html += '<div class="sensor-group"><h4>温度记录</h4>';
            html += '<table><thead><tr><th>时间</th><th>温度(°C)</th></tr></thead><tbody>';
            groupedData.temperature.forEach(record => {
                html += `<tr><td>${record.timestamp}</td><td>${record.value.toFixed(1)}</td></tr>`;
            });
            html += '</tbody></table></div>';
        }

        // 湿度数据
        if (groupedData.humidity.length > 0) {
            html += '<div class="sensor-group"><h4>湿度记录</h4>';
            html += '<table><thead><tr><th>时间</th><th>湿度(%)</th></tr></thead><tbody>';
            groupedData.humidity.forEach(record => {
                html += `<tr><td>${record.timestamp}</td><td>${record.value.toFixed(1)}</td></tr>`;
            });
            html += '</tbody></table></div>';
        }

        // 烟雾数据
        if (groupedData.smoke.length > 0) {
            html += '<div class="sensor-group"><h4>烟雾记录</h4>';
            html += '<table><thead><tr><th>时间</th><th>状态</th></tr></thead><tbody>';
            groupedData.smoke.forEach(record => {
                const status = record.value > 100 ? '警报' : '正常';
                const statusClass = record.value > 100 ? 'alert' : 'normal';
                html += `<tr><td>${record.timestamp}</td><td class="${statusClass}">${status}</td></tr>`;
            });
            html += '</tbody></table></div>';
        }

        if (html === '<div class="history-data">') {
            html += '<p>没有有效的传感器数据</p>';
        }

        html += '</div>';
        historyContainer.innerHTML = html;

    } catch (error) {
        console.error('查询传感器历史数据失败:', error);
        const historyContainer = document.getElementById('sensorHistory');
        if (historyContainer) {
            historyContainer.innerHTML = `<p class="error">查询失败: ${error.message}</p>`;
        } else {
            alert('查询失败: ' + error.message);
        }
    }
}

// 更新传感器数据统计
async function updateDailyStats() {
    try {
        const roomId = document.getElementById('statsRoomSelect').value;
        const date = document.getElementById('statsDate').value;

        if (!roomId || !date) {
            alert('请选择房间和日期');
        return;
    }

        console.log(`获取房间 ${roomId} 在 ${date} 的传感器数据`);

        // 获取当天的传感器数据
        const response = await fetch(`http://localhost:5000/api/sensor-history?room_id=${roomId}&start_date=${date}&end_date=${date}`);
        const data = await response.json();

        if (!Array.isArray(data) || data.length === 0) {
            document.getElementById('statsDisplay').innerHTML = '<p>该日期无数据</p>';
            return;
        }

        // 按时间排序数据
        const sortedData = data.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

        // 准备图表数据
        const timestamps = [];
        const temperatures = [];
        const humidities = [];
        const smokeAlerts = [];
        let currentHour = -1;
        let alertCount = 0;

        sortedData.forEach(record => {
            const time = new Date(record.timestamp);
            const hour = time.getHours();
            
            // 如果是新的小时，添加之前的报警计数并重置
            if (hour !== currentHour && currentHour !== -1) {
                timestamps.push(new Date(time.setMinutes(0)));
                smokeAlerts.push(alertCount);
                alertCount = 0;
            }
            currentHour = hour;

            if (record.type === 'temperature') {
                temperatures.push(parseFloat(record.value));
            } else if (record.type === 'humidity') {
                humidities.push(parseFloat(record.value));
            } else if (record.type === 'smoke' && parseFloat(record.value) > 750) {
                alertCount++;
            }
        });

        // 添加最后一个小时的报警计数
        if (currentHour !== -1) {
            smokeAlerts.push(alertCount);
        }

    // 创建图表
        const ctx = document.createElement('canvas');
        document.getElementById('statsDisplay').innerHTML = '';
        document.getElementById('statsDisplay').appendChild(ctx);

        new Chart(ctx, {
        type: 'line',
        data: {
            labels: timestamps,
            datasets: [
                {
                    label: '温度 (°C)',
                    data: temperatures,
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y'
                },
                {
                    label: '湿度 (%)',
                    data: humidities,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y'
                    },
                    {
                        label: '烟雾报警次数',
                    data: smokeAlerts,
                    borderColor: 'rgb(255, 159, 64)',
                    backgroundColor: 'rgba(255, 159, 64, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                            unit: 'hour',
                        displayFormats: {
                                hour: 'HH:mm'
                        }
                    },
                    title: {
                        display: true,
                        text: '时间'
                    }
                },
                y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                    title: {
                        display: true,
                            text: '温度/湿度'
                }
            },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                title: {
                    display: true,
                            text: '报警次数'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: `房间 ${roomId} - ${date} 传感器数据统计`
                }
            }
        }
    });

    } catch (error) {
        console.error('更新传感器数据统计失败:', error);
        document.getElementById('statsDisplay').innerHTML = `
            <p class="error">获取数据失败: ${error.message}</p>
        `;
    }
}


