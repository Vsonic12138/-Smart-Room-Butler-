import csv
import os
from datetime import datetime
import uuid
from pathlib import Path

class ServiceHandler:
    def __init__(self, root_dir=None):
        # 使用传入的root_dir或自动检测
        if root_dir is None:
            root_dir = Path(__file__).resolve().parent.parent
        else:
            root_dir = Path(root_dir)
            
        # 设置文件路径
        self.service_file = root_dir / 'service_requests.csv'
        
        # 确保文件存在
        self.ensure_files_exist()
    
    def ensure_files_exist(self):
        """确保必要的文件存在"""
        # 服务请求文件
        if not self.service_file.exists():
            with open(self.service_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['request_id', 'username', 'room_id', 'timestamp', 'status'])
            print(f"Created new service requests file at {self.service_file}")
    
    def create_request(self, username, room_id, timestamp):
        try:
            request_id = str(uuid.uuid4())
            with open(self.service_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([request_id, room_id, username, timestamp, 'pending'])
            print(f"Created new service request: ID={request_id}, User={username}, Room={room_id}")
            return {'success': True, 'request_id': request_id}
        except Exception as e:
            print(f"Error creating service request: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def get_pending_requests(self):
        """获取所有服务请求（包括已完成的）"""
        try:
            requests = []
            with open(self.service_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                if not fieldnames or not all(field in fieldnames 
                    for field in ['id', 'room_id', 'username', 'timestamp', 'status']):
                    print(f"Invalid CSV format. Expected fields: id, room_id, username, timestamp, status")
                    print(f"Found fields: {fieldnames}")
                    return []
                
                for row in reader:
                    try:
                        requests.append({
                            'id': row.get('id', ''),
                            'room_id': row.get('room_id', ''),
                            'username': row.get('username', ''),
                            'timestamp': row.get('timestamp', ''),
                            'status': row.get('status', 'pending')
                        })
                    except Exception as e:
                        print(f"Error processing row: {row}")
                        print(f"Error details: {str(e)}")
                        continue
            return requests
        except Exception as e:
            print(f"获取服务请求失败: {str(e)}")
            return []
    
    def complete_request(self, request_id):
        try:
            rows = []
            with open(self.service_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            with open(self.service_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'room_id', 'username', 'timestamp', 'status'])
                for row in rows:
                    if row['id'] == request_id:
                        row['status'] = 'completed'
                    writer.writerow([row['id'], row['room_id'], row['username'], 
                                  row['timestamp'], row['status']])
            return {'success': True}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def handle_request(self, request_id, action):
        """处理服务请求"""
        try:
            # 读取所有服务请求
            requests = []
            with open(self.service_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['id'] == request_id:
                        row['status'] = 'completed' if action == 'complete' else 'rejected'
                    requests.append(row)
            
            # 写回文件
            with open(self.service_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'room_id', 'username', 'timestamp', 'status'])
                writer.writeheader()
                writer.writerows(requests)
                
            return {
                'success': True,
                'message': '服务请求已处理'
            }
            
        except Exception as e:
            print(f"处理服务请求失败: {e}")
            return {
                'success': False,
                'message': str(e)
            } 