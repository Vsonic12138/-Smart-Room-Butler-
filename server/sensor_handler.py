import csv
import os
from datetime import datetime, time
from statistics import mean
from pathlib import Path

class SensorHandler:
    # 添加常量定义
    SMOKE_THRESHOLD = 750  # 烟雾报警阈值
    
    def __init__(self, root_dir=None):
        # 使用传入的root_dir或自动检测
        if root_dir is None:
            root_dir = Path(__file__).resolve().parent.parent
        else:
            root_dir = Path(root_dir)
            
        # 设置文件路径
        self.room_data_file = root_dir / 'hotel_room_data.csv'
        self.history_file = root_dir / 'data' / 'sensor_history.csv'
        
        # 确保文件存在
        self.ensure_files_exist()
        
    def ensure_files_exist(self):
        """确保必要的文件存在"""
        # 传感器数据文件
        if not self.room_data_file.exists():
            with open(self.room_data_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Room_ID', 'Type', 'Value', 'Timestamp'])
        
        # 确保历史数据目录存在
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 历史数据文件
        if not self.history_file.exists():
            with open(self.history_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['room_id', 'timestamp', 'type', 'value'])

    def save_sensor_data(self, room_id, sensor_type, value):
        """保存传感器数据"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 确保文件存在
            if not os.path.exists(self.room_data_file):
                with open(self.room_data_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Room_ID', 'Type', 'Value', 'Timestamp'])
            
            # 添加新数据
            with open(self.room_data_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([room_id, sensor_type, value, timestamp])
            
            print(f"保存传感器数据: 房间={room_id}, 类型={sensor_type}, 值={value}, 时间={timestamp}")
            return True
            
        except Exception as e:
            print(f"保存传感器数据失败: {e}")
            return False

    def get_daily_averages(self, room_id, date_str):
        """计算指定房间和日期的日间和夜间平均温湿度"""
        try:
            # 转换日期字符串为日期对象
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # 存储温湿度数据
            day_temps = []
            day_humids = []
            night_temps = []
            night_humids = []
            
            with open(self.room_data_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 解析数据时间
                    data_time = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
                    
                    # 检查是否是目标日期和房间
                    if (data_time.date() == target_date and 
                        row['room_id'] == room_id):
                        
                        # 获取温度和湿度值
                        temp = float(row['temperature'])
                        humid = float(row['humidity'])
                        
                        # 判断是白天还是夜晚 (6:00-18:00为白天)
                        if time(6, 0) <= data_time.time() < time(18, 0):
                            day_temps.append(temp)
                            day_humids.append(humid)
                        else:
                            night_temps.append(temp)
                            night_humids.append(humid)
            
            # 计算平均值
            result = {
                'day': {
                    'temperature': round(sum(day_temps) / len(day_temps), 1) if day_temps else None,
                    'humidity': round(sum(day_humids) / len(day_humids), 1) if day_humids else None
                },
                'night': {
                    'temperature': round(sum(night_temps) / len(night_temps), 1) if night_temps else None,
                    'humidity': round(sum(night_humids) / len(night_humids), 1) if night_humids else None
                }
            }
            
            print(f"计算结果 - 房间{room_id}, 日期{date_str}:")
            print(f"白天: 温度{result['day']['temperature']}°C, 湿度{result['day']['humidity']}%")
            print(f"夜晚: 温度{result['night']['temperature']}°C, 湿度{result['night']['humidity']}%")
            
            return result
            
        except Exception as e:
            print(f"计算日均值时出错: {str(e)}")
            return {
                'day': {'temperature': None, 'humidity': None},
                'night': {'temperature': None, 'humidity': None}
            }

    def get_sensor_history(self, room_id, start_date=None, end_date=None):
        """获取指定房间的传感器历史数据"""
        try:
            history = []
            with open(self.history_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['room_id'] == room_id:
                        try:
                            timestamp = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
                            if start_date and timestamp < datetime.strptime(start_date, '%Y-%m-%d'):
                                continue
                            if end_date and timestamp > datetime.strptime(end_date, '%Y-%m-%d'):
                                continue
                            
                            history.append({
                                'type': row['type'],
                                'value': float(row['value']),
                                'timestamp': row['timestamp']
                            })
                        except (ValueError, TypeError) as e:
                            print(f"处理数据行时出错: {e}")
                            continue
                        
            return {'success': True, 'data': history}
        except Exception as e:
            print(f"获取传感器历史数据失败: {e}")
            return {'success': False, 'message': str(e)}

    def get_recent_history(self, room_id=None):
        """获取最近的传感器数据"""
        try:
            if not os.path.exists(self.room_data_file):
                return []

            with open(self.room_data_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = list(reader)
                
            # 如果指定了房间号，只返回该房间的数据
            if room_id:
                data = [row for row in data if row['Room_ID'] == room_id]

            # 按时间戳排序，获取每种类型的最新数据
            latest_data = {}
            for row in reversed(data):
                sensor_type = row['Type']
                if sensor_type not in latest_data:
                    try:
                        value = float(row['Value'])  # 尝试转换为浮点数
                        latest_data[sensor_type] = {
                            'type': sensor_type,
                            'value': value,
                            'timestamp': row['Timestamp']
                        }
                    except (ValueError, TypeError):
                        # 如果转换失败，直接使用原始值
                        latest_data[sensor_type] = {
                            'type': sensor_type,
                            'value': row['Value'],
                            'timestamp': row['Timestamp']
                        }

            return list(latest_data.values())

        except Exception as e:
            print(f"获取传感器数据失败: {e}")
            return []

    def get_recent_data(self, room_id=None, limit=3):
        """获取最近的传感器数据记录"""
        try:
            with open(self.room_data_file, 'r') as f:
                reader = csv.DictReader(f)
                # 读取所有数据
                all_data = list(reader)
                
                # 按房间号过滤（如果指定了房间号）
                if room_id:
                    all_data = [row for row in all_data if row['room_id'] == room_id]
                
                # 按时间戳排序
                all_data.sort(key=lambda x: datetime.strptime(x['timestamp'], '%Y-%m-%d %H:%M:%S'), reverse=True)
                
                # 获取最近的记录
                recent_data = all_data[:limit]
                
                # 格式化数据
                formatted_data = []
                for row in recent_data:
                    formatted_data.append({
                        'timestamp': row['timestamp'],
                        'room_id': row['room_id'],
                        'temperature': float(row['temperature']) if row['temperature'] else None,
                        'humidity': float(row['humidity']) if row['humidity'] else None,
                        'smoke': row['smoke'] == '1'
                    })
                
                return formatted_data
                
        except Exception as e:
            print(f"获取最近数据失败: {str(e)}")
            return []

    def get_latest_sensor_data(self, room_id):
        """获取指定房间的最新传感器数据"""
        try:
            print(f"Getting sensor data for room {room_id}")
            if not os.path.exists(self.room_data_file):
                print(f"Data file not found: {self.room_data_file}")
                return {'temperature': None, 'humidity': None, 'smoke': False}
            
            with open(self.room_data_file, 'r') as f:
                reader = csv.DictReader(f)
                room_data = []
                for row in reader:
                    if row['room_id'] == str(room_id):
                        room_data.append(row)
                
                if not room_data:
                    return {
                        'temperature': None,
                        'humidity': None,
                        'smoke': False
                    }
                
                # 获取最新数据
                latest_data = max(room_data, 
                                key=lambda x: datetime.strptime(x['timestamp'], '%Y-%m-%d %H:%M:%S'))
                
                try:
                    smoke_value = float(latest_data['smoke'])
                    return {
                        'temperature': float(latest_data['temperature']),
                        'humidity': float(latest_data['humidity']),
                        'smoke': smoke_value,  # 返回具体数值
                        'smoke_alert': smoke_value > self.SMOKE_THRESHOLD  # 添加警报状态
                    }
                except (ValueError, TypeError) as e:
                    print(f"Error converting sensor values: {e}")
                    return {
                        'temperature': None,
                        'humidity': None,
                        'smoke': 0,
                        'smoke_alert': False
                    }
                  
        except Exception as e:
            print(f"获取最新传感器数据失败: {str(e)}")
            return {
                'temperature': None,
                'humidity': None,
                'smoke': 0,
                'smoke_alert': False
            } 