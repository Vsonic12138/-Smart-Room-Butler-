"""CSV文件操作工具类"""
import csv
import os
from datetime import datetime
from typing import Dict, List, Optional

class CSVHelper:
    def __init__(self, data_dir: str, filename: str, fieldnames: List[str]):
        """
        初始化CSV工具类
        
        Args:
            data_dir: 数据目录路径
            filename: CSV文件名
            fieldnames: CSV文件字段名列表
        """
        self.data_dir = data_dir
        self.filename = filename
        self.fieldnames = fieldnames
        self.filepath = os.path.join(data_dir, filename)
        
        # 确保数据目录存在
        os.makedirs(data_dir, exist_ok=True)
        
        # 如果文件不存在，创建文件并写入表头
        if not os.path.exists(self.filepath):
            self.write_header()
    
    def write_header(self) -> None:
        """写入CSV文件表头"""
        with open(self.filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()
    
    def append_row(self, data: Dict) -> None:
        """
        追加一行数据到CSV文件
        
        Args:
            data: 要写入的数据字典
        """
        try:
            # 确保所有字段都是字符串类型
            formatted_data = {k: str(v) if v is not None else '' for k, v in data.items()}
            
            with open(self.filepath, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writerow(formatted_data)
                
        except Exception as e:
            print(f"Error writing to CSV: {e}")
            raise
    
    def read_all(self) -> List[Dict]:
        """
        读取CSV文件中的所有数据
        
        Returns:
            所有数据记录的列表
        """
        try:
            if not os.path.exists(self.filepath):
                return []
                
            with open(self.filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
                
        except Exception as e:
            print(f"Error reading from CSV: {e}")
            return []
            
    def delete_row(self, condition: Dict) -> bool:
        """
        删除符合条件的行
        
        Args:
            condition: 删除条件，如 {'Username': 'test'}
            
        Returns:
            bool: 是否成功删除
        """
        try:
            if not os.path.exists(self.filepath):
                return False
                
            # 读取所有数据
            rows = self.read_all()
            if not rows:
                return False
                
            # 过滤出不符合条件的行
            new_rows = []
            found = False
            for row in rows:
                matches = all(row.get(k) == str(v) for k, v in condition.items())
                if not matches:
                    new_rows.append(row)
                else:
                    found = True
                    
            if not found:
                return False
                
            # 重写文件
            with open(self.filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()
                writer.writerows(new_rows)
                
            return True
            
        except Exception as e:
            print(f"Error deleting from CSV: {e}")
            return False
    
    def read_latest_data(self, room_id: Optional[str] = None) -> Optional[Dict]:
        """
        读取最新的传感器数据
        
        Args:
            room_id: 房间号（可选）
            
        Returns:
            最新的数据记录
        """
        try:
            if not os.path.exists(self.filepath):
                return None
                
            with open(self.filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                if not rows:
                    return None
                    
                # 过滤数据
                if room_id:
                    rows = [r for r in rows if r['Room_ID'] == room_id]
                    
                if not rows:
                    return None
                    
                # 返回最新的记录
                latest = rows[-1]
                
                # 转换数值类型
                for field in ['Temperature', 'Humidity', 'Smoke']:
                    if field in latest and latest[field]:
                        latest[field] = float(latest[field])
                    else:
                        latest[field] = None
                        
                return latest
                
        except Exception as e:
            print(f"Error reading from CSV: {e}")
            raise 