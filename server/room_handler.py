import csv
import os
from datetime import datetime
from pathlib import Path

class RoomHandler:
    def __init__(self, root_dir=None):
        # 使用传入的root_dir或自动检测
        if root_dir is None:
            root_dir = Path(__file__).resolve().parent.parent
        else:
            root_dir = Path(root_dir)
            
        # 设置文件路径
        self.rooms_file = root_dir / 'hotel_rooms.csv'
        self.users_file = root_dir / 'hotel_login_data.csv'
        self.bookings_file = root_dir / 'hotel_bookings.csv'
        self.history_file = root_dir / 'hotel_history.csv'
        self.room_data_file = root_dir / 'hotel_room_data.csv'
        self.service_file = root_dir / 'service_requests.csv'
        
        print(f"\n初始化文件路径:")
        print(f"- 历史记录文件: {self.history_file}")
        print(f"- 预订记录文件: {self.bookings_file}")
        print(f"- 房间信息文件: {self.rooms_file}")
        
        # 确保所有文件存在
        self.ensure_files()
    
    def ensure_files(self):
        """确保所有必要的文件存在并具有正确的格式"""
        try:
            # 历史记录文件
            if not os.path.exists(self.history_file):
                print(f"创建历史记录文件: {self.history_file}")
                with open(self.history_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Room_ID', 'Customer', 'Check_in', 'Check_out', 'Status'])
                print("历史记录文件创建成功")

            # 预订记录文件
            if not os.path.exists(self.bookings_file):
                with open(self.bookings_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Room_ID', 'Customer', 'Check_in', 'Check_out', 'Status'])
            
            # 房间基本信息文件
            if not os.path.exists(self.rooms_file):
                with open(self.rooms_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Room_ID', 'Status', 'Customer', 'Check_in'])
                    # 初始化默认房间
                    writer.writerow(['101', 'available', '', ''])
                    writer.writerow(['102', 'available', '', ''])
                    writer.writerow(['103', 'available', '', ''])

            # 房间数据文件
            if not os.path.exists(self.room_data_file):
                with open(self.room_data_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Room_ID', 'Type', 'Value', 'Timestamp'])

            # 服务请求文件
            if not os.path.exists(self.service_file):
                with open(self.service_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Request_ID', 'Room_ID', 'Customer', 'Type', 'Status', 'Timestamp'])

        except Exception as e:
            print(f"确保文件存在时出错: {e}")
            raise

    def sync_room_status(self):
        """同步所有文件中的房间状态"""
        try:
            # 从用户数据获取房间分配信息
            room_assignments = {}
            with open(self.users_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Room_ID'] != 'without':
                        room_assignments[row['Room_ID']] = {
                            'username': row['Username'],
                            'has_room': True
                        }

            # 从预订记录获取状态
            with open(self.bookings_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    room_id = row['Room_ID']
                    if room_id in room_assignments:
                        if row['Status'] == 'occupied':
                            room_assignments[room_id]['status'] = 'occupied'
                            room_assignments[room_id]['check_in'] = row['Check_in']
                        elif row['Status'] == 'pending_checkout':
                            room_assignments[room_id]['status'] = 'pending_checkout'
                        elif row['Status'] == 'completed':
                            room_assignments[room_id]['status'] = 'assigned'

            # 更新房间状态文件
            rooms = []
            with open(self.rooms_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                existing_rooms = {row['Room_ID'] for row in reader}

            for room_id in existing_rooms:
                room = {
                    'Room_ID': room_id,
                    'Status': 'available',
                    'Customer': '',
                    'Check_in': ''
                }
                if room_id in room_assignments:
                    assignment = room_assignments[room_id]
                    if 'status' in assignment:
                        room['Status'] = assignment['status']
                        if assignment['status'] == 'occupied':
                            room['Check_in'] = assignment['check_in']
                    else:
                        room['Status'] = 'assigned'
                    room['Customer'] = assignment['username']
                rooms.append(room)

            # 写回房间状态
            with open(self.rooms_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Status', 'Customer', 'Check_in'])
                writer.writeheader()
                writer.writerows(rooms)

            # 更新历史记录
            completed_bookings = []
            with open(self.bookings_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Status'] == 'completed':
                        completed_bookings.append(row)

            with open(self.history_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Customer', 'Check_in', 'Check_out', 'Status'])
                writer.writeheader()
                writer.writerows(completed_bookings)

            return True
        except Exception as e:
            print(f"同步房间状态失败: {str(e)}")
            return False

    def update_room_status(self):
        """更新房间状态并同步所有文件"""
        try:
            result = self.sync_room_status()
            if not result:
                raise Exception("同步房间状态失败")
            return True
        except Exception as e:
            print(f"更新房间状态失败: {str(e)}")
            return False

    def get_room_status(self):
        """获取所有房间状态"""
        try:
            rooms = []
            seen_rooms = set()  # 用于跟踪已处理的房间
            
            # 读取房间信息
            with open(self.rooms_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    room_id = row['Room_ID']
                    # 如果房间已经处理过，跳过
                    if room_id in seen_rooms:
                        continue
                        
                    seen_rooms.add(room_id)
                    # 获取最新的传感器数据
                    sensor_data = self.get_latest_sensor_data(room_id)
                    
                    rooms.append({
                        'room_id': room_id,
                        'status': row['Status'],
                        'customer': row['Customer'],
                        'check_in': row['Check_in'],
                        'temperature': sensor_data.get('temperature'),
                        'humidity': sensor_data.get('humidity'),
                        'smoke': sensor_data.get('smoke')
                    })
            return rooms
        except Exception as e:
            print(f"获取房间状态失败: {e}")
            return []

    def get_latest_sensor_data(self, room_id):
        """获取房间最新的传感器数据"""
        try:
            latest_data = {}
            with open(self.room_data_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                # 倒序遍历找到最新的数据
                for row in reversed(rows):
                    if row['Room_ID'] == room_id:
                        sensor_type = row['Type']
                        if sensor_type not in latest_data:
                            try:
                                value = float(row['Value'])
                                # 对于烟雾数据，添加警报状态
                                if sensor_type == 'smoke':
                                    latest_data[sensor_type] = {
                                        'value': value,
                                        'alert': value >= 750
                                    }
                                else:
                                    latest_data[sensor_type] = value
                            except (ValueError, TypeError):
                                latest_data[sensor_type] = None
                        
                        # 如果所有类型的数据都找到了，就停止搜索
                        if all(k in latest_data for k in ['temperature', 'humidity', 'smoke']):
                            break
                            
            return latest_data
        except Exception as e:
            print(f"获取传感器数据失败: {e}")
            return {}

    def handle_checkout_request(self, username, room_id, action):
        """处理退房申请"""
        try:
            # 读取预订数据
            bookings = []
            with open(self.bookings_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                bookings = list(reader)

            # 查找对应的预订记录
            booking = None
            for b in bookings:
                if (b['Room_ID'] == room_id and 
                    b['Customer'] == username and 
                    b['Status'] == 'pending_checkout'):
                    booking = b
                    break

            if not booking:
                return False, "未找到对应的退房申请"

            # 更新预订状态
            if action == 'approve':
                # 批准退房
                booking['Status'] = 'available'
                booking['Customer'] = ''
                booking['Check_in'] = ''
                booking['Check_out'] = ''
            elif action == 'reject':
                # 拒绝退房，恢复为已入住状态
                booking['Status'] = 'occupied'
                booking['Check_out'] = ''
            else:
                return False, "无效的操作"

            # 保存更新后的预订数据
            with open(self.bookings_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Customer', 'Check_in', 'Check_out', 'Status'])
                writer.writeheader()
                writer.writerows(bookings)

            return True, f"退房申请已{action == 'approve' and '批准' or '拒绝'}"

        except Exception as e:
            print(f"处理退房申请失败: {e}")
            return False, str(e)

    def get_pending_checkouts(self):
        """获取待处理的退房申请"""
        try:
            pending = []
            with open(self.bookings_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Status'] == 'pending_checkout':
                        pending.append({
                            'room_id': row['Room_ID'],
                            'username': row['Customer'],
                            'request_time': row['Check_out']
                        })
            return pending
        except Exception as e:
            print(f"获取退房申请失败: {e}")
            return []

    def check_in(self, username, timestamp):
        """客户入住"""
        try:
            # 获取用户的房间号
            room_id = None
            with open(self.users_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Username'] == username:
                        room_id = row['Room_ID']
                        break

            if not room_id or room_id == 'without':
                return {'success': False, 'message': '用户未分配房间'}

            # 更新房间入住时间
            rooms = []
            with open(self.rooms_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Room_ID'] == room_id:
                        row['Check_in'] = timestamp
                    rooms.append(row)

            with open(self.rooms_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Status', 'Customer', 'Check_in'])
                writer.writeheader()
                writer.writerows(rooms)

            return {'success': True, 'message': '入住成功'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def add_room(self, room_id):
        """添加新房间"""
        try:
            # 检查房间是否已存在
            with open(self.rooms_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                existing_rooms = {row['Room_ID'] for row in reader}
                
            if room_id in existing_rooms:
                return False, "房间已存在"

            # 添加新房间
            with open(self.rooms_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Status', 'Customer', 'Check_in'])
                writer.writerow({
                    'Room_ID': room_id,
                    'Status': 'available',
                    'Customer': '',
                    'Check_in': ''
                })
            return True, "房间添加成功"
        except Exception as e:
            print(f"添加房间失败: {e}")
            return False, str(e)

    def delete_room(self, room_id):
        """删除房间"""
        try:
            print(f"\n删除房间: {room_id}")
            
            # 检查房间是否存在且为空闲状态
            rooms = []
            room_found = False
            room_available = False
            
            with open(self.rooms_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Room_ID'] == room_id:
                        room_found = True
                        if row['Status'] == 'available':
                            room_available = True
                            continue
                    rooms.append(row)
            
            if not room_found:
                print("房间不存在")
                return {'success': False, 'message': '房间不存在'}
            
            if not room_available:
                print("只能删除空闲状态的房间")
                return {'success': False, 'message': '只能删除空闲状态的房间'}
            
            # 写回文件
            with open(self.rooms_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Status', 'Customer', 'Check_in'])
                writer.writeheader()
                writer.writerows(rooms)
            
            print(f"房间 {room_id} 已删除")
            return {'success': True, 'message': '房间删除成功'}
            
        except Exception as e:
            print(f"删除房间失败: {e}")
            return {'success': False, 'message': str(e)}

    def is_room_available(self, room_id):
        """检查房间是否可用"""
        try:
            with open(self.rooms_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Room_ID'] == room_id:
                        # 检查房间状态
                        if row['Status'] != 'available':
                            return False
                        # 检查是否有客户
                        if row['Customer']:
                            return False
                        return True
                # 如果没找到房间
                return False
            
        except Exception as e:
            print(f"检查房间可用性失败: {e}")
            return False

    def get_available_rooms(self):
        """获取所有可用房间"""
        try:
            available_rooms = []
            with open(self.rooms_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 只返回状态为可用且没有客户的房间
                    if row['Status'] == 'available' and not row['Customer']:
                        available_rooms.append({
                            'Room_ID': row['Room_ID'],
                            'Status': row['Status']
                        })
            return available_rooms
        except Exception as e:
            print(f"获取可用房间失败: {e}")
            raise

    def assign_room(self, room_id, username):
        """分配房间给用户"""
        try:
            # 检查房间是否可用
            room_status = None
            with open(self.rooms_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Room_ID'] == room_id:
                        room_status = row['Status']
                        break

            if room_status != 'available':
                return {'success': False, 'message': '房间不可用'}

            # 更新房间状态
            rooms = []
            with open(self.rooms_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Room_ID'] == room_id:
                        row['Status'] = 'assigned'
                        row['Customer'] = username
                    rooms.append(row)

            with open(self.rooms_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Status', 'Customer', 'Check_in'])
                writer.writeheader()
                writer.writerows(rooms)

            # 更新预订记录
            with open(self.bookings_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Customer', 'Check_in', 'Check_out', 'Status'])
                writer.writerow({
                    'Room_ID': room_id,
                    'Customer': username,
                    'Check_in': '',
                    'Check_out': '',
                    'Status': 'assigned'
                })

            return {'success': True, 'message': '房间分配成功'}
        except Exception as e:
            print(f"分配房间失败: {str(e)}")
            return {'success': False, 'message': str(e)}

    def request_checkout(self, room_id, username):
        """客户申请退房"""
        try:
            print(f"\n开始处理退房申请: 房间={room_id}, 用户={username}")
            # 读取预订数据
            bookings = []
            found = False
            request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with open(self.bookings_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if (row['Room_ID'] == room_id and 
                        row['Customer'] == username and 
                        row['Status'] == 'occupied'):
                        # 更新状态为待退房，并记录申请时间
                        row['Status'] = 'pending_checkout'
                        row['Check_out'] = request_time  # 添加退房申请时间
                        found = True
                    bookings.append(row)

            if not found:
                print("未找到对应的入住记录")
                return False, "未找到对应的入住记录"

            # 保存更新后的预订数据
            with open(self.bookings_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Customer', 'Check_in', 'Check_out', 'Status'])
                writer.writeheader()
                writer.writerows(bookings)

            print(f"退房申请已提交，申请时间: {request_time}")
            return True, "退房申请已提交"

        except Exception as e:
            print(f"申请退房失败: {e}")
            return False, str(e)

    def approve_checkout(self, room_id, username):
        """审核通过退房申请"""
        try:
            print(f"\n开始处理退房审核: 房间={room_id}, 用户={username}")
            check_out_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 1. 从 hotel_bookings.csv 读取入住记录
            booking_record = None
            remaining_bookings = []
            
            print(f"读取预订记录文件: {self.bookings_file}")
            with open(self.bookings_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if (row['Room_ID'] == room_id and 
                        row['Customer'] == username and 
                        row['Status'] == 'pending_checkout'):
                        booking_record = row.copy()
                    else:
                        remaining_bookings.append(row)
            
            if not booking_record:
                print("未找到待审核的退房申请")
                return {'success': False, 'message': '未找到待审核的退房申请'}
            
            print(f"找到预订记录: {booking_record}")
            
            # 2. 保存到历史记录
            print(f"准备保存历史记录到: {self.history_file}")
            history_record = {
                'Room_ID': room_id,
                'Customer': username,
                'Check_in': booking_record['Check_in'],
                'Check_out': check_out_time,
                'Status': 'completed'
            }
            
            # 确保历史记录文件存在
            if not os.path.exists(self.history_file):
                print("历史记录文件不存在，正在创建...")
                with open(self.history_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Room_ID', 'Customer', 'Check_in', 'Check_out', 'Status'])
                print("历史记录文件创建成功")
            
            # 添加历史记录
            print("正在写入历史记录...")
            try:
                with open(self.history_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Customer', 'Check_in', 'Check_out', 'Status'])
                    writer.writerow(history_record)
                    print(f"历史记录已保存: {history_record}")
            except Exception as e:
                print(f"写入历史记录失败: {e}")
                raise Exception(f"保存历史记录失败: {e}")
            
            # 3. 更新 hotel_bookings.csv
            print("更新预订记录...")
            with open(self.bookings_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Customer', 'Check_in', 'Check_out', 'Status'])
                writer.writeheader()
                writer.writerows(remaining_bookings)
                writer.writerow({
                    'Room_ID': room_id,
                    'Customer': '',
                    'Check_in': '',
                    'Check_out': '',
                    'Status': 'available'
                })
            
            # 4. 更新房间状态
            print("更新房间状态...")
            rooms = []
            with open(self.rooms_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Room_ID'] == room_id:
                        row['Status'] = 'available'
                        row['Customer'] = ''
                        row['Check_in'] = ''
                    rooms.append(row)
            
            with open(self.rooms_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Status', 'Customer', 'Check_in'])
                writer.writeheader()
                writer.writerows(rooms)
            
            print(f"退房审核完成: 房间={room_id}, 用户={username}, 退房时间={check_out_time}")
            return {'success': True, 'message': '退房成功'}
            
        except Exception as e:
            print(f"处理退房审核失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)} 