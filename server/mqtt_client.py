import paho.mqtt.client as mqtt
import json
import csv
from datetime import datetime
import os

# 配置数据存储路径
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
CSV_FILE = 'hotel_room_data.csv'
CSV_PATH = os.path.join(DATA_DIR, 'hotel_room_data.csv')

# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)

class MQTTClient:
    def __init__(self):
        # MQTT配置
        self.HOST = "bemfa.com"
        self.PORT = 9501
        self.CLIENT_ID = "b79104dad1352b06548fcf4b319a65a0"  # 巴法云密钥
        
        # 传感器主题
        self.TOPICS = {
            'temperature': 'hotel101temp001',
            'humidity': 'hotel101humi001',
            'smoke': 'hotel101smoke001'
        }
        
        # 初始化MQTT客户端
        self.client = mqtt.Client(client_id=self.CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
        self.setup_client()
        self.is_running = False  # 运行状态标志
        self.update_timer = None  # 定时器
        self.last_values = {
            'temperature': None,
            'humidity': None,
            'smoke': None
        }
        
    def setup_client(self):
        """设置MQTT客户端回调"""
        try:
            print("\n=== MQTT客户端配置开始 ===")
            print(f"服务器: {self.HOST}:{self.PORT}")
            print(f"客户端ID: {self.CLIENT_ID}")
            print(f"订阅主题: {list(self.TOPICS.values())}")
            
            # 设置回调函数
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_subscribe = self.on_subscribe
            self.client.on_disconnect = self.on_disconnect
            
            print("已设置所有回调函数")
            
            # 巴法云不需要用户名和密码
            self.client.username_pw_set("", "")
            
            # 连接服务器
            print("正在连接到巴法云...")
            self.client.connect(self.HOST, self.PORT, 60)
            print("=== MQTT客户端配置完成 ===\n")
            
        except Exception as e:
            print(f"MQTT客户端配置失败: {e}")
            raise

    def start(self):
        """启动MQTT客户端"""
        try:
            if self.is_running:
                print("MQTT客户端已经在运行")
                return
                
            print("\n=== 启动MQTT客户端 ===")
            # 启动MQTT循环
            self.client.loop_start()
            self.is_running = True
            print("MQTT客户端后台线程已启动")
            print("等待接收消息...\n")
            
        except Exception as e:
            print(f"启动MQTT客户端失败: {e}")
            raise

    def stop(self):
        """停止MQTT客户端"""
        try:
            if not self.is_running:
                print("MQTT客户端已经停止")
                return
                
            print("\n=== 停止MQTT客户端 ===")
            # 停止MQTT客户端
            self.client.loop_stop()
            self.client.disconnect()
            self.is_running = False
            print("MQTT客户端已停止\n")
            
        except Exception as e:
            print(f"停止MQTT客户端失败: {e}")

    def on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        print("\n=== MQTT连接状态 ===")
        if rc == 0:
            print("成功连接到巴法云")
            print("开始订阅主题...")
            # 订阅所有主题
            for topic in self.TOPICS.values():
                client.subscribe(topic)
                print(f"已订阅主题: {topic}")
        else:
            print(f"连接失败，错误码: {rc}")
            # 错误码说明
            rc_codes = {
                1: "协议版本错误",
                2: "无效的客户端标识",
                3: "服务器无法使用",
                4: "用户名或密码错误",
                5: "未授权"
            }
            print(f"错误原因: {rc_codes.get(rc, '未知错误')}")
        print("="*30 + "\n")

    def on_message(self, client, userdata, msg):
        """消息接收回调"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8').strip()

            print("\n" + "="*50)
            print("收到MQTT消息:")
            print(f"主题: {topic}")
            print(f"原始数据: {payload}")
            print("="*50)

            # 1. 获取传感器类型
            sensor_type = None
            if topic == 'hotel101temp001':
                sensor_type = 'temperature'
            elif topic == 'hotel101humi001':
                sensor_type = 'humidity'
            elif topic == 'hotel101smoke001':
                sensor_type = 'smoke'
            else:
                print(f"未知的主题: {topic}")
                return

            # 2. 处理数值消息
            try:
                value = float(payload)
                
                print("\n传感器数据解析结果:")
                print("-"*30)
                print(f"房间号: 101")
                print(f"传感器类型: {sensor_type}")
                print(f"数值: {value}")
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"时间: {current_time}")
                print("-"*30)

                # 3. 准备保存的数据
                data = {
                    'Room_ID': '101',
                    'Type': sensor_type,
                    'Value': str(value),
                    'Timestamp': current_time
                }

                # 4. 保存数据
                self.save_to_csv(data)

            except ValueError:
                print(f"警告: 收到非数值消息: {payload}")
                print("="*50)

        except Exception as e:
            print(f"错误: 处理MQTT消息失败: {e}")
            print("="*50)

    def on_subscribe(self, client, userdata, mid, granted_qos):
        """订阅回调"""
        print("\n=== MQTT订阅状态 ===")
        print(f"消息ID: {mid}")
        print(f"QoS等级: {granted_qos}")
        print("订阅成功")
        print("="*30 + "\n")

    def on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        print("\n=== MQTT连接断开 ===")
        if rc != 0:
            print(f"意外断开连接，错误码: {rc}")
            print("尝试重新连接...")
            self.client.reconnect()
        else:
            print("正常断开连接")
        print("="*30 + "\n")

    def get_sensor_type(self, topic):
        """根据主题获取传感器类型"""
        for sensor_type, t in self.TOPICS.items():
            if t == topic:
                return sensor_type
        return 'unknown'

    def save_to_csv(self, data):
        """保存数据到CSV文件"""
        try:
            csv_path = CSV_PATH
            file_exists = os.path.exists(csv_path)
            
            print("\n开始保存数据到CSV:")
            print("-"*30)
            print(f"文件路径: {csv_path}")
            
            # 确保数据目录存在
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            
            # 确保数据格式正确
            save_data = {
                'Room_ID': str(data['Room_ID']),
                'Type': str(data['Type']),
                'Value': str(data['Value']),
                'Timestamp': str(data['Timestamp'])
            }
            
            with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Type', 'Value', 'Timestamp'])
                if not file_exists:
                    writer.writeheader()
                    print("创建新的CSV文件并写入表头")
                writer.writerow(save_data)
                
                print("\n数据保存成功:")
                print(f"- 房间: {save_data['Room_ID']}")
                print(f"- 类型: {save_data['Type']}")
                print(f"- 数值: {save_data['Value']}")
                print(f"- 时间: {save_data['Timestamp']}")
            
            print("-"*30 + "\n")
                
        except Exception as e:
            print(f"错误: 保存数据失败: {e}")
            print(f"尝试保存的数据: {data}")
            print("-"*30 + "\n")

# 创建MQTT客户端实例
mqtt_client = MQTTClient()