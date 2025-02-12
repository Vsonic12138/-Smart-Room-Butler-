# MQTT服务工作流程文档

## 1. 组件架构

### 1.1 核心组件

1. **MQTT服务 (services/mqtt_service.py)**
   ```python
   class MQTTService:
       def __init__(self):
           self.client = mqtt.Client(
               client_id=MQTT_CONFIG['CLIENT_ID'],
               callback_api_version=mqtt.CallbackAPIVersion.VERSION1
           )
           
           self.sensor_service = SensorService(
               data_dir=data_dir,
               csv_filename=DATA_CONFIG['CSV_FILENAME'],
               csv_fields=DATA_CONFIG['FIELDS'],
               notification_url=NOTIFICATION_CONFIG['URL']
           )
           
           self.setup_callbacks()
           self.is_running = False
           self.should_reconnect = True
           self.message_lock = threading.Lock()
   ```

2. **传感器服务 (services/sensor_service.py)**
   ```python
   class SensorService:
       def __init__(self, data_dir, csv_filename, csv_fields, notification_url):
           self.csv_helper = CSVHelper(data_dir, csv_filename, csv_fields)
           self.sensor_cache = {}
           self.notification_url = notification_url
           
       def process_sensor_data(self, room_id: str, sensor_type: str, value: float):
           if room_id not in self.sensor_cache:
               self.sensor_cache[room_id] = {
                   'temperature': None,
                   'humidity': None,
                   'smoke': None,
                   'timestamp': None
               }
           
           self.sensor_cache[room_id][sensor_type] = value
           self.sensor_cache[room_id]['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
   ```

3. **MQTT配置 (config/mqtt_config.py)**
   ```python
   MQTT_CONFIG = {
       'HOST': 'bemfa.com',
       'PORT': 9501,
       'CLIENT_ID': 'b79104dad1352b06548fcf4b319a65a0',
       'KEEP_ALIVE': 60
   }

   SENSOR_TOPICS = {
       'temperature': 'hotel101temp001',
       'humidity': 'hotel101humi001',
       'smoke': 'hotel101smoke001'
   }
   ```

4. **应用入口 (app.py)**
   ```python
   def main():
       app = create_app()
       if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
           mqtt_service.start()
           signal.signal(signal.SIGINT, handle_exit)
           signal.signal(signal.SIGTERM, handle_exit)
           atexit.register(mqtt_service.stop)
   ```

## 2. 工作流程

### 2.1 启动流程

1. **服务初始化**
   ```
   创建MQTT客户端 -> 设置回调 -> 初始化服务 -> 启动连接
   ```
   - 创建MQTT客户端实例
   - 配置回调函数
   - 初始化传感器服务
   - 启动重连监控线程

2. **连接建立**
   ```python
   def start(self):
       self.client.username_pw_set("", "")  # 巴法云不需要认证
       self.client.connect(
           MQTT_CONFIG['HOST'],
           MQTT_CONFIG['PORT'],
           MQTT_CONFIG['KEEP_ALIVE']
       )
       self.client.loop_start()
   ```

### 2.2 订阅流程

1. **主题订阅**
   ```python
   def on_connect(self, client, userdata, flags, rc):
       if rc == 0:
           for topic in SENSOR_TOPICS.values():
               client.subscribe(topic)
               logger.info(f"已订阅主题: {topic}")
   ```

2. **订阅确认**
   ```python
   def on_subscribe(self, client, userdata, mid, granted_qos):
       logger.info(f"订阅成功 - 消息ID: {mid}, QoS: {granted_qos}")
   ```

### 2.3 消息处理流程

1. **消息接收**
   ```python
   def on_message(self, client, userdata, msg):
       with self.message_lock:
           topic = msg.topic
           payload = msg.payload.decode('utf-8').strip()
           sensor_type = self.get_sensor_type(topic)
           
           try:
               value = float(payload)
               data = self.sensor_service.process_sensor_data(
                   room_id='101',
                   sensor_type=sensor_type,
                   value=value
               )
   ```

2. **数据处理**
   ```python
   def process_sensor_data(self, room_id, sensor_type, value):
       # 更新缓存
       self.sensor_cache[room_id][sensor_type] = value
       self.sensor_cache[room_id]['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
       
       # 检查数据完整性
       if all(self.sensor_cache[room_id][key] is not None for key in ['temperature', 'humidity', 'smoke']):
           data = {
               'Room_ID': room_id,
               'Temperature': self.sensor_cache[room_id]['temperature'],
               'Humidity': self.sensor_cache[room_id]['humidity'],
               'Smoke': self.sensor_cache[room_id]['smoke'],
               'Timestamp': self.sensor_cache[room_id]['timestamp']
           }
           self.csv_helper.append_row(data)
   ```

### 2.4 数据存储流程

1. **CSV文件存储**
   ```python
   def append_row(self, data: Dict):
       formatted_data = {k: str(v) if v is not None else '' for k, v in data.items()}
       with open(self.filepath, 'a', newline='', encoding='utf-8') as f:
           writer = csv.DictWriter(f, fieldnames=self.fieldnames)
           writer.writerow(formatted_data)
   ```

2. **数据缓存管理**
   ```python
   def get_latest_sensor_data(self, room_id: Optional[str] = None):
       if room_id and room_id in self.sensor_cache:
           return {
               'Room_ID': room_id,
               **self.sensor_cache[room_id]
           }
   ```

### 2.5 异常处理流程

1. **重连机制**
   ```python
   def start_reconnect_thread(self):
       def reconnect_job():
           while not self.stop_event.is_set() and self.should_reconnect:
               if not self.client.is_connected():
                   logger.info("MQTT连接断开，尝试重连...")
                   try:
                       self.client.reconnect()
                   except Exception as e:
                       logger.error(f"重连失败: {e}")
   ```

2. **错误处理**
   ```python
   @retry_on_failure(max_retries=3)
   def send_notification(self, room_id: str, is_alert: bool, smoke_value: float):
       try:
           payload = {
               'room_id': room_id,
               'status': 'ALERT' if is_alert else 'NORMAL',
               'smoke_value': smoke_value,
               'timestamp': datetime.now().isoformat()
           }
           response = requests.post(self.notification_url, json=payload, timeout=5)
   ```

### 2.6 关闭流程

1. **优雅关闭**
   ```python
   def stop(self):
       with self.message_lock:
           self.is_stopping = True
           self.should_reconnect = False
           self.stop_event.set()
           
           for topic in SENSOR_TOPICS.values():
               self.client.unsubscribe(topic)
           
           self.client.loop_stop()
           self.client.disconnect()
   ```

## 3. 数据结构

### 3.1 传感器数据格式

CSV文件格式：
```
Room_ID, Temperature, Humidity, Smoke, Timestamp
101, 25.5, 60.0, 0.0, 2024-02-13 01:23:45
```

### 3.2 消息格式

1. **温度消息**
   ```
   主题: hotel101temp001
   数据: 25.5
   ```

2. **湿度消息**
   ```
   主题: hotel101humi001
   数据: 60.0
   ```

3. **烟雾消息**
   ```
   主题: hotel101smoke001
   数据: 0.0
   ```

## 4. 监控和维护

### 4.1 日志记录

1. **连接日志**
   - MQTT连接状态
   - 订阅确认信息
   - 重连尝试记录
   - 错误信息

2. **数据日志**
   - 接收的消息
   - 处理的数据
   - 存储操作
   - 异常情况

### 4.2 异常监控

1. **连接监控**
   - 连接状态检查
   - 自动重连机制
   - 超时处理
   - 错误恢复

2. **数据监控**
   - 数据完整性检查
   - 阈值监控
   - 警报触发
   - 异常数据处理 