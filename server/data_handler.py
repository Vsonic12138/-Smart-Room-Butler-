import csv
import os
from datetime import datetime

class DataHandler:
    def __init__(self):
        self.data_dir = 'data'
        self.ensure_data_directory()

    def ensure_data_directory(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def save_sensor_data(self, topic, value):
        filename = f"{self.data_dir}/{topic}_{datetime.now().strftime('%Y%m')}.csv"
        
        # 检查文件是否存在，如果不存在则创建表头
        file_exists = os.path.exists(filename)
        
        with open(filename, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['timestamp', 'value'])
            writer.writerow([datetime.now().isoformat(), value])

    def get_sensor_history(self, topic, start_date=None, end_date=None):
        data = []
        filename = f"{self.data_dir}/{topic}_{datetime.now().strftime('%Y%m')}.csv"
        
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
        
        return data 