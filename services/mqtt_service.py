"""MQTT服务类"""
import paho.mqtt.client as mqtt
from datetime import datetime
from typing import Dict, Optional
import os
import threading
import time
from config.mqtt_config import MQTT_CONFIG, SENSOR_TOPICS, DATA_CONFIG, NOTIFICATION_CONFIG
from services.sensor_service import SensorService
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MQTTService:
    def __init__(self):
        """初始化MQTT服务"""
        # 创建MQTT客户端
        self.client = mqtt.Client(
            client_id=MQTT_CONFIG['CLIENT_ID'],
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1
        )
        
        # 创建传感器服务
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        self.sensor_service = SensorService(
            data_dir=data_dir,
            csv_filename=DATA_CONFIG['CSV_FILENAME'],
            csv_fields=DATA_CONFIG['FIELDS'],
            notification_url=NOTIFICATION_CONFIG['URL']
        )
        
        # 设置MQTT回调
        self.setup_callbacks()
        
        # 运行状态标志
        self.is_running = False
        
        # 重连标志
        self.should_reconnect = True
        
        # 重连线程
        self.reconnect_thread = None
        
        # 停止标志
        self.is_stopping = False
        
        # 消息处理锁
        self.message_lock = threading.Lock()
        
        # 停止事件
        self.stop_event = threading.Event()
        
    def setup_callbacks(self):
        """设置MQTT回调函数"""
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        self.client.on_disconnect = self.on_disconnect
        
    def start(self):
        """启动MQTT服务"""
        try:
            if self.is_running:
                logger.info("MQTT服务已经在运行")
                return
                
            logger.info("=== 启动MQTT服务 ===")
            # 重置停止事件
            self.stop_event.clear()
            self.is_stopping = False
            
            # 连接MQTT服务器
            self.should_reconnect = True
            self.client.username_pw_set("", "")  # 巴法云不需要用户名和密码
            self.client.connect(
                MQTT_CONFIG['HOST'],
                MQTT_CONFIG['PORT'],
                MQTT_CONFIG['KEEP_ALIVE']
            )
            
            # 启动MQTT循环
            self.client.loop_start()
            self.is_running = True
            logger.info("MQTT服务启动成功")
            
            # 启动重连线程
            self.start_reconnect_thread()
            
        except Exception as e:
            logger.error(f"启动MQTT服务失败: {e}")
            raise
            
    def stop(self):
        """停止MQTT服务"""
        try:
            if not self.is_running:
                logger.info("MQTT服务已经停止")
                return
                
            with self.message_lock:
                # 设置停止标志
                self.is_stopping = True
                self.is_running = False
                self.should_reconnect = False
                
                # 设置停止事件
                self.stop_event.set()
                
                logger.info("=== 停止MQTT服务 ===")
                
                # 等待一小段时间，确保没有新的消息处理
                time.sleep(0.5)
                
                # 取消所有订阅
                for topic in SENSOR_TOPICS.values():
                    self.client.unsubscribe(topic)
                    logger.info(f"已取消订阅主题: {topic}")
                
                # 等待重连线程结束
                if self.reconnect_thread and self.reconnect_thread.is_alive():
                    logger.info("等待重连线程结束...")
                    self.reconnect_thread.join(timeout=5)
                    if self.reconnect_thread.is_alive():
                        logger.warning("重连线程未能在超时时间内结束")
                
                # 停止MQTT循环
                logger.info("正在停止MQTT循环...")
                self.client.loop_stop()
                
                # 断开连接
                logger.info("正在断开MQTT连接...")
                self.client.disconnect()
                
                logger.info("MQTT服务已停止")
            
        except Exception as e:
            logger.error(f"停止MQTT服务失败: {e}")
            
    def start_reconnect_thread(self):
        """启动重连线程"""
        def reconnect_job():
            while not self.stop_event.is_set() and self.should_reconnect:
                if not self.client.is_connected():
                    logger.info("MQTT连接断开，尝试重连...")
                    try:
                        self.client.reconnect()
                    except Exception as e:
                        logger.error(f"重连失败: {e}")
                # 使用事件等待，支持提前退出
                self.stop_event.wait(timeout=5)
                
        self.reconnect_thread = threading.Thread(target=reconnect_job)
        self.reconnect_thread.daemon = True
        self.reconnect_thread.start()
            
    def on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        if rc == 0 and not self.is_stopping:
            logger.info("成功连接到MQTT服务器")
            # 订阅所有主题
            for topic in SENSOR_TOPICS.values():
                client.subscribe(topic)
                logger.info(f"已订阅主题: {topic}")
        else:
            logger.error(f"连接失败，错误码: {rc}")
            
    def on_message(self, client, userdata, msg):
        """消息接收回调"""
        # 在获取锁之前就检查停止标志
        if self.is_stopping or self.stop_event.is_set():
            return
            
        # 尝试获取锁，如果获取不到就跳过这条消息
        if not self.message_lock.acquire(blocking=False):
            return
            
        try:
            # 再次检查停止标志
            if self.is_stopping or self.stop_event.is_set():
                return
                
            topic = msg.topic
            payload = msg.payload.decode('utf-8').strip()
            
            logger.info(f"收到消息: topic={topic}, payload={payload}")
            
            # 获取传感器类型
            sensor_type = self.get_sensor_type(topic)
            if sensor_type == 'unknown':
                logger.warning(f"未知的主题: {topic}")
                return
                
            try:
                # 解析数值
                value = float(payload)
                
                # 处理传感器数据
                data = self.sensor_service.process_sensor_data(
                    room_id='101',  # 目前固定为101房间
                    sensor_type=sensor_type,
                    value=value
                )
                
                logger.info(f"数据已保存: {data}")
                
                # 只对烟雾传感器进行阈值检查
                if sensor_type == 'smoke' and not self.is_stopping:
                    result = self.sensor_service.check_smoke_level(data)
                    if result is None:
                        logger.warning("烟雾数据处理失败")
                    
            except ValueError:
                logger.warning(f"警告: 收到非数值消息: {payload}")
                
        except Exception as e:
            logger.error(f"处理MQTT消息失败: {e}")
        finally:
            self.message_lock.release()
            
    def on_subscribe(self, client, userdata, mid, granted_qos):
        """订阅回调"""
        if not self.is_stopping:
            logger.info(f"订阅成功 - 消息ID: {mid}, QoS: {granted_qos}")
        
    def on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        if rc != 0 and not self.is_stopping:
            logger.error(f"意外断开连接，错误码: {rc}")
        else:
            logger.info("正常断开连接")
            
    def get_sensor_type(self, topic: str) -> str:
        """根据主题获取传感器类型"""
        for sensor_type, t in SENSOR_TOPICS.items():
            if t == topic:
                return sensor_type
        return 'unknown'

# 创建MQTT服务实例
mqtt_service = MQTTService() 