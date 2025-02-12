// MQTT客户端类
class MQTTClient {
    constructor() {
        // MQTT配置
        this.HOST = 'bemfa.com';
        this.PORT = 9501;
        this.CLIENT_ID = 'e895e3bb902037cbb463b2a41bac2d69';  // 巴法云密钥
        
        // 定义传感器主题
        this.TOPICS = {
            temperature: 'hotel101temp001',  // 温度传感器主题
            humidity: 'hotel101humi001',     // 湿度传感器主题
            smoke: 'hotel101smoke001'        // 烟雾传感器主题
        };
        
        this.client = null;
        this.isConnected = false;
        
        // 存储最新的传感器数据
        this.sensorData = {
            temperature: null,
            humidity: null,
            smoke: null
        };
        
        // 添加定时器ID
        this.updateInterval = null;
        
        // 添加最后更新时间
        this.lastUpdate = {
            temperature: null,
            humidity: null,
            smoke: null
        };

        // 自动连接
        this.connect();
    }

    connect() {
        try {
            console.log('正在连接到巴法云MQTT服务器...');
            
            // 构建连接URL
            const connectUrl = `ws://${this.HOST}:${this.PORT}`;
            console.log('连接URL:', connectUrl);

            // MQTT连接选项
            const options = {
                clientId: `mqtt_${Math.random().toString(16).slice(3)}`, // 随机客户端ID
            clean: true,
            connectTimeout: 4000,
                username: this.CLIENT_ID,  // 使用巴法云密钥作为用户名
                password: this.CLIENT_ID,  // 使用巴法云密钥作为密码
                reconnectPeriod: 1000,
            };

            // 创建MQTT客户端
            this.client = mqtt.connect(connectUrl, options);

            // 连接成功回调
            this.client.on('connect', () => {
                console.log('已成功连接到巴法云MQTT服务器');
                this.isConnected = true;

                // 订阅所有主题
                Object.values(this.TOPICS).forEach(topic => {
                    this.client.subscribe(topic, (err) => {
                        if (!err) {
                            console.log(`已订阅主题: ${topic}`);
                            // 发送获取数据的请求
                            this.client.publish(topic, 'get');
                        } else {
                            console.error(`订阅主题失败: ${topic}`, err);
                        }
                    });
                });
            });

            // 连接失败回调
            this.client.on('error', (error) => {
                console.error('MQTT连接错误:', error);
                this.isConnected = false;
            });

            // 断开连接回调
            this.client.on('close', () => {
                console.log('MQTT连接已断开');
                this.isConnected = false;
            });

            // 重连回调
            this.client.on('reconnect', () => {
                console.log('正在尝试重新连接到巴法云...');
            });

            // 收到消息回调
            this.client.on('message', (topic, message) => {
                const msg = message.toString();
                console.log(`收到消息 - 主题: ${topic}, 数据: ${msg}`);
                this.handleMessage(topic, message);
            });

        } catch (error) {
            console.error('MQTT连接初始化失败:', error);
            this.isConnected = false;
        }
    }

    // 启动定时更新
    startAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        // 每10秒获取一次数据
        this.updateInterval = setInterval(() => {
            this.requestSensorData();
        }, 10000);
    }

    // 停止定时更新
    stopAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    // 请求传感器数据
    requestSensorData() {
        if (!this.isConnected) return;
        
        Object.values(this.TOPICS).forEach(topic => {
            this.client.publish(topic, 'get');  // 发送获取数据的请求
        });
    }

    // 处理接收到的消息
    async handleMessage(topic, message) {
        try {
            const msg = message.toString();
            console.log('----------------------------------------');
            console.log('收到巴法云消息:');
            console.log('主题:', topic);
            console.log('原始数据:', msg);

            // 解析数据
            const valueMatch = msg.match(/数值[：:]\s*(\d+\.?\d*)/);
            if (!valueMatch) {
                console.error('数据格式错误，无法解析数值');
                return;
            }

            const value = parseFloat(valueMatch[1]);
            if (isNaN(value)) {
                console.error('无效的数值:', valueMatch[1]);
                return;
            }

            // 准备保存的数据
            const saveData = {
                room_id: '101',
                type: this.getTypeFromTopic(topic),
                value: value,
                timestamp: new Date().toISOString().slice(0, 19).replace('T', ' ')
            };

            console.log('准备保存的数据:', saveData);

            // 发送到服务器
            const response = await fetch('http://localhost:5000/api/sensor-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(saveData)
            });

            const result = await response.json();
            console.log('服务器响应:', result);

            if (!result.success) {
                throw new Error(result.message);
            }

            // 更新显示
            this.sensorData[saveData.type] = value;
            this.updateSensorDisplay();
            console.log('数据保存成功');
            console.log('----------------------------------------');

        } catch (error) {
            console.error('数据处理失败:', error);
        }
    }

    // 根据主题确定传感器类型
    getTypeFromTopic(topic) {
        switch (topic) {
            case 'hotel101temp001':
                return 'temperature';
            case 'hotel101humi001':
                return 'humidity';
            case 'hotel101smoke001':
                return 'smoke';
            default:
                throw new Error('未知的主题: ' + topic);
        }
    }

    // 更新传感器显示
    updateSensorDisplay() {
        try {
            const tempElement = document.querySelector('.sensor-value.temperature');
            const humidElement = document.querySelector('.sensor-value.humidity');
            const smokeElement = document.querySelector('.sensor-value.smoke');

            if (tempElement && this.sensorData.temperature !== null) {
                tempElement.textContent = this.sensorData.temperature.toFixed(1);
            }
            if (humidElement && this.sensorData.humidity !== null) {
                humidElement.textContent = this.sensorData.humidity.toFixed(1);
            }
            if (smokeElement && this.sensorData.smoke !== null) {
                const isAlert = this.sensorData.smoke > 100;
                smokeElement.textContent = isAlert ? '警报' : '正常';
                smokeElement.style.color = isAlert ? 'red' : 'green';
            }
        } catch (error) {
            console.error('更新显示失败:', error);
        }
    }

    // 手动刷新数据
    async refreshData() {
        try {
            if (!this.isConnected) {
                console.log('MQTT未连接，正在重新连接...');
                this.connect();
                await new Promise(resolve => setTimeout(resolve, 1000));
            }

            console.log('正在请求最新数据...');
            Object.values(this.TOPICS).forEach(topic => {
                this.client.publish(topic, 'get');
                console.log(`已发送请求到主题: ${topic}`);
            });

            // 等待数据更新
            await new Promise(resolve => setTimeout(resolve, 2000));
            return this.sensorData;
        } catch (error) {
            console.error('刷新数据失败:', error);
            throw error;
        }
    }

    // 处理烟雾警报
    handleSmokeAlert(roomId) {
        console.log(`烟雾警报! 房间: ${roomId}`);
        // 这里可以添加警报处理逻辑，比如：
        // - 发送警报到服务器
        // - 触发声光警报
        // - 通知管理员等
    }

    // 发送消息
    publish(topic, message) {
        if (this.isConnected && this.client) {
            this.client.publish(topic, message.toString(), (err) => {
                if (err) {
                    console.error('Publish error:', err);
                } else {
                    console.log(`Message published to ${topic}`);
                }
            });
        } else {
            console.error('MQTT client not connected');
        }
    }

    // 断开连接
    disconnect() {
        if (this.client) {
            this.client.end();
            this.isConnected = false;
            console.log('MQTT已断开连接');
        }
    }
}

// 创建并导出MQTT客户端实例
const mqttClient = new MQTTClient();
export default mqttClient; 