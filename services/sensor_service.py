"""传感器数据处理服务"""
from datetime import datetime
from typing import Dict, Optional, Any
from utils.csv_helper import CSVHelper
import os
from config.mqtt_config import SENSOR_THRESHOLDS
import logging
import requests
from functools import wraps
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def retry_on_failure(max_retries: int = 3, delay: int = 1):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"最大重试次数已达到: {str(e)}")
                        raise
                    logger.warning(f"尝试 {attempt + 1}/{max_retries} 失败: {str(e)}")
                    time.sleep(delay)
        return wrapper
    return decorator

class SensorService:
    def __init__(self, data_dir: str, csv_filename: str, csv_fields: list, notification_url: str, smoke_threshold: float = 800.0):
        """
        初始化传感器服务
        
        Args:
            data_dir: 数据目录路径
            csv_filename: CSV文件名
            csv_fields: CSV文件字段列表
            notification_url: 通知API的URL
            smoke_threshold: 烟雾阈值，默认800
        """
        self.csv_helper = CSVHelper(data_dir, csv_filename, csv_fields)
        
        # 数据缓存，用于存储最新的传感器数据
        self.sensor_cache = {}
        self.notification_url = notification_url
        self.smoke_threshold = smoke_threshold
        self.logger = logging.getLogger(__name__)
    
    def process_sensor_data(self, room_id: str, sensor_type: str, value: float) -> Dict:
        """
        处理传感器数据
        
        Args:
            room_id: 房间号
            sensor_type: 传感器类型
            value: 传感器值
            
        Returns:
            处理后的数据字典
        """
        # 更新缓存
        if room_id not in self.sensor_cache:
            self.sensor_cache[room_id] = {
                'temperature': None,
                'humidity': None,
                'smoke': None,
                'timestamp': None
            }
            
        # 更新对应的传感器值和时间戳
        self.sensor_cache[room_id][sensor_type] = value
        self.sensor_cache[room_id]['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 检查是否所有传感器数据都已收集
        cache = self.sensor_cache[room_id]
        if all(cache[key] is not None for key in ['temperature', 'humidity', 'smoke']):
            # 准备写入的数据
            data = {
                'Room_ID': room_id,
                'Temperature': cache['temperature'],
                'Humidity': cache['humidity'],
                'Smoke': cache['smoke'],
                'Timestamp': cache['timestamp']
            }
            
            # 写入CSV
            self.csv_helper.append_row(data)
            
            # 返回完整的数据记录
            return data
            
        # 如果数据不完整，返回当前缓存
        return {
            'Room_ID': room_id,
            'Temperature': cache['temperature'],
            'Humidity': cache['humidity'],
            'Smoke': cache['smoke'],
            'Timestamp': cache['timestamp']
        }
    
    def get_latest_sensor_data(self, room_id: Optional[str] = None) -> Dict:
        """
        获取最新的传感器数据
        
        Args:
            room_id: 房间号（可选）
            
        Returns:
            最新的传感器数据记录
        """
        # 如果指定了房间号且有缓存数据，优先返回缓存
        if room_id and room_id in self.sensor_cache:
            return {
                'Room_ID': room_id,
                **self.sensor_cache[room_id]
            }
            
        # 否则从CSV文件读取
        return self.csv_helper.read_latest_data(room_id)
    
    def check_sensor_thresholds(self, data: Dict) -> bool:
        """
        检查传感器数据是否超过阈值
        
        Args:
            data: 传感器数据
            
        Returns:
            如果任何一个传感器超过阈值返回True，否则返回False
        """
        for sensor_type, threshold in SENSOR_THRESHOLDS.items():
            value = data.get(sensor_type.capitalize())
            if value is not None:
                value = float(value)
                if value < threshold['min'] or value > threshold['max']:
                    return True
                    
        return False

    def validate_sensor_data(self, data: Dict[str, Any]) -> bool:
        """
        验证传感器数据的有效性
        
        Args:
            data: 传感器数据字典
        
        Returns:
            bool: 数据是否有效
        """
        required_fields = ['Room_ID', 'Smoke']
        return all(field in data for field in required_fields)

    @retry_on_failure(max_retries=3)
    def send_notification(self, room_id: str, is_alert: bool, smoke_value: float) -> bool:
        """
        发送通知到外部API
        
        Args:
            room_id: 房间号
            is_alert: 是否是警报
            smoke_value: 烟雾值
        
        Returns:
            bool: 发送是否成功
        """
        try:
            payload = {
                'room_id': room_id,
                'status': 'ALERT' if is_alert else 'NORMAL',
                'smoke_value': smoke_value,
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(
                self.notification_url,
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                self.logger.info(f"通知发送成功: {payload}")
                return True
            else:
                self.logger.error(f"通知发送失败: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"发送通知时发生错误: {str(e)}")
            raise

    def check_smoke_level(self, sensor_data: Dict[str, Any]) -> Optional[bool]:
        """
        检查烟雾水平并发送相应通知
        
        Args:
            sensor_data: 传感器数据字典
        
        Returns:
            Optional[bool]: 处理是否成功
        """
        try:
            # 验证数据
            if not self.validate_sensor_data(sensor_data):
                self.logger.error(f"无效的传感器数据: {sensor_data}")
                return None
                
            room_id = sensor_data['Room_ID']
            smoke_value = float(sensor_data['Smoke'])
            
            # 检查烟雾值
            is_alert = smoke_value > self.smoke_threshold
            
            # 发送通知
            notification_sent = self.send_notification(
                room_id=room_id,
                is_alert=is_alert,
                smoke_value=smoke_value
            )
            
            if notification_sent:
                status = "警报" if is_alert else "正常"
                self.logger.info(f"房间 {room_id} 烟雾状态: {status} (值: {smoke_value})")
            
            return notification_sent
            
        except Exception as e:
            self.logger.error(f"处理传感器数据时发生错误: {str(e)}")
            return None

    def process_mqtt_message(self, topic: str, payload: Dict[str, Any]) -> None:
        """
        处理MQTT消息
        
        Args:
            topic: MQTT主题
            payload: 消息内容
        """
        try:
            self.logger.info(f"收到MQTT消息: {topic} - {payload}")
            
            # 处理传感器数据
            result = self.check_smoke_level(payload)
            
            if result is None:
                self.logger.warning(f"消息处理失败: {topic}")
            
        except Exception as e:
            self.logger.error(f"处理MQTT消息时发生错误: {str(e)}") 