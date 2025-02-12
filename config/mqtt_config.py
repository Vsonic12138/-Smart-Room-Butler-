"""MQTT配置文件"""

# MQTT服务器配置
MQTT_CONFIG = {
    'HOST': 'bemfa.com',
    'PORT': 9501,
    'CLIENT_ID': 'b79104dad1352b06548fcf4b319a65a0',  # 巴法云密钥
    'KEEP_ALIVE': 60
}

# 传感器主题配置
SENSOR_TOPICS = {
    'temperature': 'hotel101temp001',
    'humidity': 'hotel101humi001',
    'smoke': 'hotel101smoke001'
}

# 数据存储配置
DATA_CONFIG = {
    'CSV_FILENAME': 'hotel_room_data.csv',
    'FIELDS': ['Room_ID', 'Temperature', 'Humidity', 'Smoke', 'Timestamp']
}

# 传感器阈值配置
SENSOR_THRESHOLDS = {
    'temperature': {'min': 15, 'max': 30},
    'humidity': {'min': 20, 'max': 80},
    'smoke': {'min': 0, 'max': 100}
}

# 通知配置
NOTIFICATION_CONFIG = {
    'URL': 'http://localhost:5000/api/notifications'  # 默认使用本地测试URL
} 