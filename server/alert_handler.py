import csv
import os
from datetime import datetime
from pathlib import Path

class AlertHandler:
    def __init__(self, root_dir=None):
        # 使用传入的root_dir或自动检测
        if root_dir is None:
            root_dir = Path(__file__).resolve().parent.parent
        else:
            root_dir = Path(root_dir)
            
        # 设置文件路径
        self.alerts_file = root_dir / 'data' / 'alerts.csv'
        
        # 确保文件存在
        self.ensure_files_exist()
    
    def ensure_files_exist(self):
        """确保必要的文件存在"""
        # 确保目录存在
        self.alerts_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 警报记录文件
        if not self.alerts_file.exists():
            with open(self.alerts_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['room_id', 'timestamp', 'type', 'level'])
    
    def save_smoke_alert(self, room_id, timestamp, value):
        """记录烟雾警报"""
        with open(self.alerts_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, room_id, 'smoke', value])
    
    def get_alerts(self, start_date=None, end_date=None):
        """获取警报历史"""
        alerts = []
        with open(self.alerts_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                timestamp = datetime.fromisoformat(row['timestamp'])
                if start_date and timestamp < datetime.fromisoformat(start_date):
                    continue
                if end_date and timestamp > datetime.fromisoformat(end_date):
                    continue
                alerts.append(row)
        return alerts 