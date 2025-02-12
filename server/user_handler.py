import csv
import os
from datetime import datetime
from pathlib import Path
from server.room_handler import RoomHandler

class UserHandler:
    def __init__(self, root_dir=None):
        # 使用传入的root_dir或自动检测
        if root_dir is None:
            root_dir = Path(__file__).resolve().parent.parent
        else:
            root_dir = Path(root_dir)
        
        # 使用Path对象处理文件路径
        self.users_file = root_dir / 'hotel_login_data.csv'
        self.pending_file = root_dir / 'pending_users.csv'
        self.rooms_file = root_dir / 'hotel_rooms.csv'
        
        # 确保文件存在
        self.ensure_files_exist()

    def ensure_files_exist(self):
        """确保必要的文件存在"""
        # 用户数据文件
        if not self.users_file.exists():
            with open(self.users_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Username', 'Password', 'Role', 'Room_ID'])
        
        # 待审核用户文件
        if not self.pending_file.exists():
            with open(self.pending_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Username', 'Password', 'Room_ID', 'Timestamp'])
        
        # 房间信息文件
        if not self.rooms_file.exists():
            with open(self.rooms_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Room_ID', 'Status', 'Customer', 'Check_in'])

    def register_user(self, username, password, room_id):
        """注册新用户"""
        try:
            # 检查用户名是否已存在
            with open(self.users_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Username'] == username:
                        return False, "用户名已存在"

            # 添加新用户，使用明文密码
            with open(self.users_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Username', 'Password', 'Role', 'Room_ID'])
                writer.writerow({
                    'Username': username,
                    'Password': password,  # 直接保存明文密码
                    'Role': 'Customer',
                    'Room_ID': room_id
                })
            return True, "注册成功，等待管理员审核"
        except Exception as e:
            print(f"注册用户失败: {e}")
            return False, str(e)

    def verify_user(self, username, password, role):
        """验证用户登录"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Username'] == username:
                        # 直接比较明文密码
                        if row['Password'] == password and row['Role'] == role:
                            return {
                                'success': True,
                                'role': row['Role'],
                                'room_id': row['Room_ID']
                            }
                        else:
                            return {
                                'success': False,
                                'message': '密码错误或角色不匹配'
                            }
                return {
                    'success': False,
                    'message': '用户不存在'
                }
        except Exception as e:
            print(f"验证用户失败: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def get_pending_users(self):
        """获取待审核的用户列表"""
        try:
            print(f"Reading pending users from: {self.pending_file}")
            
            # 如果文件不存在，创建它
            if not os.path.exists(self.pending_file):
                print("Creating new pending users file")
                with open(self.pending_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Username', 'Password', 'created_at', 'room_id'])
                return []
            
            # 读取待审核用户
            pending_users = []
            with open(self.pending_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pending_users.append({
                        'Username': row['Username'],
                        'created_at': row['created_at'],
                        'room_id': row.get('room_id', 'without')  # 添加房间号信息
                    })
                print(f"Found {len(pending_users)} pending users")
            
            return pending_users
            
        except Exception as e:
            print(f"Error reading pending users: {str(e)}")
            raise

    def approve_user(self, username):
        """审核通过用户"""
        try:
            pending_users = []
            approved_user = None
            room_id = None

            # 读取待审核用户
            with open(self.pending_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Username'] == username:
                        approved_user = row
                        # 获取用户选择的房间号
                        room_id = row.get('room_id', 'without')
                    else:
                        pending_users.append(row)

            if not approved_user:
                return {'success': False, 'message': '未找到待审核用户'}

            # 检查房间是否可用
            if room_id != 'without':
                with open(self.rooms_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    room_available = False
                    for row in reader:
                        if row['Room_ID'] == room_id and row['Status'] == 'available':
                            room_available = True
                            break
                    
                    if not room_available:
                        return {'success': False, 'message': '所选房间已被占用'}

            # 将审核通过的用户添加到用户文件
            with open(self.users_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    approved_user['Username'],
                    approved_user['Password'],
                    'Customer',  # 默认角色为客户
                    room_id  # 写入选择的房间号
                ])

            # 更新房间状态
            if room_id != 'without':
                rooms = []
                with open(self.rooms_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['Room_ID'] == room_id:
                            row['Status'] = 'occupied'
                            row['Customer'] = approved_user['Username']
                        rooms.append(row)

                with open(self.rooms_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Status', 'Customer', 'Check_in'])
                    writer.writeheader()
                    writer.writerows(rooms)

            # 更新待审核用户文件
            with open(self.pending_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Username', 'Password', 'created_at', 'room_id'])
                for user in pending_users:
                    writer.writerow([
                        user['Username'],
                        user['Password'],
                        user['created_at'],
                        user.get('room_id', 'without')
                    ])

            return {'success': True, 'message': '用户审核通过'}
        except Exception as e:
            print(f"Error in approve_user: {str(e)}")
            return {'success': False, 'message': str(e)}

    def create_reset_request(self, username, reason):
        """创建密码重置请求"""
        reset_file = 'data/password_resets.csv'
        
        if not os.path.exists(reset_file):
            with open(reset_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['username', 'reason', 'status', 'created_at'])
        
        with open(reset_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([username, reason, 'pending', datetime.now().isoformat()])

    def get_pending_resets(self):
        """获取待处理的密码重置请求"""
        reset_file = 'data/password_resets.csv'
        resets = []
        
        if os.path.exists(reset_file):
            with open(reset_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['status'] == 'pending':
                        resets.append(row)
        
        return resets

    def reset_user_password(self, username, new_password):
        """重置用户密码"""
        try:
            print(f"\n重置用户密码:")
            print(f"- 用户名: {username}")
            print(f"- 新密码: {new_password}")
            
            # 读取所有用户
            users = []
            user_found = False
            with open(self.users_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Username'] == username:
                        user_found = True
                        # 直接使用明文密码
                        row['Password'] = new_password
                    users.append(row)
            
            if not user_found:
                print("用户不存在")
                return False, '用户不存在'
            
            # 写回文件
            with open(self.users_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Username', 'Password', 'Role', 'Room_ID'])
                writer.writeheader()
                writer.writerows(users)
            
            print("密码重置成功")
            return True, '密码重置成功'
            
        except Exception as e:
            print(f"重置密码失败: {e}")
            return False, str(e)

    def get_available_rooms(self):
        """获取可用房间列表"""
        try:
            print("Getting available rooms...")
            
            # 获取所有房间的状态
            available_rooms = []
            with open(self.rooms_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 只返回状态为 available 的房间
                    if row['Status'] == 'available':
                        available_rooms.append(row['Room_ID'])
            
            print(f"Found {len(available_rooms)} available rooms: {available_rooms}")
            return available_rooms
            
        except Exception as e:
            print(f"Error getting available rooms: {str(e)}")
            return []

    def get_all_rooms(self):
        """获取所有房间及其状态"""
        rooms = {}
        # 读取所有房间
        with open(self.rooms_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rooms[row['room_number']] = {'status': 'available'}
        
        # 标记已占用的房间
        with open(self.users_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['room_id'] != 'without' and row['room_id'] in rooms:
                    rooms[row['room_id']]['status'] = 'occupied'
                    rooms[row['room_id']]['customer'] = row['Username']
        
        return rooms

    def add_room(self, room_number):
        """添加新房间"""
        # 检查房间号格式
        if not room_number.isdigit() or len(room_number) != 3:
            return False, '房间号必须是3位数字'
        
        # 检查房间是否已存在
        with open(self.rooms_file, 'r') as f:
            reader = csv.DictReader(f)
            if any(row['room_number'] == room_number for row in reader):
                return False, '房间号已存在'
        
        # 添加新房间
        with open(self.rooms_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([room_number, 'available'])
        
        return True, '房间添加成功'

    def delete_room(self, room_number):
        """删除房间"""
        try:
            # 检查房间是否存在
            room_exists = False
            with open(self.rooms_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rooms = list(reader)
                for room in rooms:
                    if room['Room_ID'] == room_number:
                        room_exists = True
                        # 检查房间是否被占用
                        if room['Status'] != 'available':
                            return {'success': False, 'message': '房间正在使用中，无法删除'}
                        break
        
            if not room_exists:
                return {'success': False, 'message': '房间不存在'}
        
            # 删除房间
            updated_rooms = [room for room in rooms if room['Room_ID'] != room_number]
        
            # 写回文件
            with open(self.rooms_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Status', 'Customer', 'Check_in'])
                writer.writeheader()
                writer.writerows(updated_rooms)
        
            # 同时更新 hotel_bookings.csv
            try:
                bookings = []
                with open('hotel_bookings.csv', 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    bookings = [row for row in reader if row['Room_ID'] != room_number]
            
                with open('hotel_bookings.csv', 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Customer', 'Check_in', 'Check_out', 'Status'])
                    writer.writeheader()
                    writer.writerows(bookings)
            except Exception as e:
                print(f"更新预订记录失败: {str(e)}")
        
            print(f"房间 {room_number} 已删除")
            return {'success': True, 'message': '房间删除成功'}
        
        except Exception as e:
            print(f"删除房间失败: {str(e)}")
            return {'success': False, 'message': str(e)}

    def get_all_users(self):
        """获取所有用户"""
        users = []
        with open(self.users_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                users.append({
                    'Username': row['Username'],
                    'Role': row['Role'],
                    'Password': row['Password'],
                    'room_id': row['room_id']
                })
            print(f"Found {len(users)} users")  # 添加调试信息
        return users

    def add_user(self, username, password, role='Customer', room_id=None):
        """添加新用户"""
        try:
            print(f"\n开始添加用户: username={username}, role={role}, room_id={room_id}")
            
            # 检查用户名是否已存在
            if self.user_exists(username):
                return False, '用户名已存在'
            
            # 直接使用明文密码，不再加密
            # hashed_password = self.hash_password(password)
            
            # 确定房间ID
            assigned_room = 'without'
            if room_id:
                # 检查房间是否可用
                if not self.room_handler.is_room_available(room_id):
                    return False, '该房间不可用'
                assigned_room = room_id
            
            # 写入用户数据
            with open(self.users_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([username, password, role, assigned_room])  # 使用明文密码
            
            # 如果分配了房间，更新房间状态
            if assigned_room != 'without':
                try:
                    # 更新房间状态
                    with open(self.rooms_file, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        rooms = list(reader)
                    
                    for room in rooms:
                        if room['Room_ID'] == assigned_room:
                            room['Status'] = 'assigned'
                            room['Customer'] = username
                            break
                    
                    with open(self.rooms_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Status', 'Customer', 'Check_in'])
                        writer.writeheader()
                        writer.writerows(rooms)
                    
                    print(f"房间 {assigned_room} 已分配给用户 {username}")
                except Exception as e:
                    print(f"更新房间状态失败: {e}")
                    self.delete_user(username)
                    return False, f'房间分配失败: {str(e)}'
            
            return True, '用户添加成功'
            
        except Exception as e:
            print(f"添加用户失败: {e}")
            return False, str(e)

    def user_exists(self, username):
        """检查用户名是否已存在"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return any(row['Username'] == username for row in reader)
        except Exception as e:
            print(f"检查用户名失败: {e}")
            return False

    def delete_user(self, username):
        """删除用户（用于回滚操作）"""
        try:
            rows = []
            with open(self.users_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = [row for row in reader if row['Username'] != username]
            
            with open(self.users_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Username', 'Password', 'Role', 'Room_ID'])
                writer.writeheader()
                writer.writerows(rows)
            
            print(f"用户删除成功: {username}")
            return True
            
        except Exception as e:
            print(f"删除用户失败: {e}")
            return False

    def update_user(self, username, role, room_id, password=None):
        """更新用户信息"""
        try:
            print(f"\n开始更新用户信息: username={username}, role={role}, room_id={room_id}")
            users = []
            user_found = False
            old_room_id = None
            
            # 读取所有用户
            with open(self.users_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Username'] == username:
                        user_found = True
                        old_room_id = row['Room_ID']  # 保存原房间号
                        # 更新用户信息
                        row['Role'] = role
                        row['Room_ID'] = room_id
                        if password:  # 如果提供了新密码
                            row['Password'] = password
                    users.append(row)
            
            if not user_found:
                return {'success': False, 'message': '未找到用户'}
            
            print(f"原房间: {old_room_id}, 新房间: {room_id}")
            
            # 如果房间发生变化
            if old_room_id != room_id:
                try:
                    # 1. 如果有原房间，将其状态设为可用
                    if old_room_id and old_room_id != 'without':
                        print(f"释放原房间: {old_room_id}")
                        # 更新房间状态
                        rooms = []
                        with open(self.rooms_file, 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                if row['Room_ID'] == old_room_id:
                                    row['Status'] = 'available'
                                    row['Customer'] = ''
                                    row['Check_in'] = ''
                                rooms.append(row)
                        
                        with open(self.rooms_file, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Status', 'Customer', 'Check_in'])
                            writer.writeheader()
                            writer.writerows(rooms)
                        
                        # 更新预订记录
                        bookings = []
                        with open('hotel_bookings.csv', 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                if row['Room_ID'] != old_room_id or row['Customer'] != username:
                                    bookings.append(row)
                        
                        with open('hotel_bookings.csv', 'w', newline='', encoding='utf-8') as f:
                            writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Customer', 'Check_in', 'Check_out', 'Status'])
                            writer.writeheader()
                            writer.writerows(bookings)
                            # 添加新的空闲记录
                            writer.writerow({
                                'Room_ID': old_room_id,
                                'Customer': '',
                                'Check_in': '',
                                'Check_out': '',
                                'Status': 'available'
                            })
                    
                    # 2. 如果分配了新房间，更新其状态
                    if room_id and room_id != 'without':
                        print(f"分配新房间: {room_id}")
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
                        
                        # 添加新的预订记录
                        with open('hotel_bookings.csv', 'a', newline='', encoding='utf-8') as f:
                            writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Customer', 'Check_in', 'Check_out', 'Status'])
                            writer.writerow({
                                'Room_ID': room_id,
                                'Customer': username,
                                'Check_in': '',
                                'Check_out': '',
                                'Status': 'assigned'
                            })
                    
                except Exception as e:
                    print(f"更新房间状态失败: {e}")
                    return {'success': False, 'message': f'更新房间状态失败: {str(e)}'}
            
            # 写回用户文件
            with open(self.users_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Username', 'Password', 'Role', 'Room_ID'])
                writer.writeheader()
                writer.writerows(users)
            
            print("用户信息更新成功")
            return {'success': True, 'message': '用户信息更新成功'}
            
        except Exception as e:
            print(f"更新用户信息失败: {e}")
            return {'success': False, 'message': str(e)}

    def reject_reset_request(self, username):
        """拒绝密码重置请求"""
        reset_file = 'data/password_resets.csv'
        resets = []
        
        with open(reset_file, 'r') as f:
            reader = csv.DictReader(f)
            resets = [row for row in reader if row['username'] != username]
        
        with open(reset_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['username', 'reason', 'status', 'created_at'])
            for reset in resets:
                writer.writerow([
                    reset['username'],
                    reset['reason'],
                    reset['status'],
                    reset['created_at']
                ]) 

    def get_user_room(self, username):
        """获取用户的房间信息"""
        try:
            # 获取用户的房间分配
            user_room = None
            with open(self.users_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Username'] == username:
                        user_room = row['Room_ID']
                        break

            if not user_room or user_room == 'without':
                return {'success': False, 'message': '用户没有分配房间'}

            # 获取房间状态
            with open(self.rooms_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Room_ID'] == user_room:
                        # 检查预订状态
                        booking_status = None
                        check_in_time = None
                        with open('hotel_bookings.csv', 'r', encoding='utf-8') as bf:
                            booking_reader = csv.DictReader(bf)
                            for booking in booking_reader:
                                if (booking['Room_ID'] == user_room and 
                                    booking['Customer'] == username):
                                    booking_status = booking['Status']
                                    check_in_time = booking['Check_in']
                                    break

                        return {
                            'success': True,
                            'room_id': user_room,
                            'status': '有客' if booking_status == 'occupied' else 
                                     '待退房' if booking_status == 'pending_checkout' else '空闲',
                            'check_in': check_in_time if booking_status == 'occupied' else None
                        }

            return {'success': False, 'message': '未找到房间信息'}

        except Exception as e:
            print(f"Error getting user room: {str(e)}")
            return {'success': False, 'message': str(e)}

    def check_in_room(self, username):
        """处理用户入住"""
        try:
            # 获取用户的房间信息
            user_room = None
            with open(self.users_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Username'] == username:
                        user_room = row['Room_ID']
                        break
            
            if not user_room or user_room == 'without':
                return {'success': False, 'message': '用户没有分配房间'}
            
            # 更新房间状态
            rooms = []
            check_in_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 更新 hotel_rooms.csv
            with open(self.rooms_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Room_ID'] == user_room:
                        row['Status'] = 'occupied'
                        row['Customer'] = username
                        row['Check_in'] = check_in_time
                    rooms.append(row)
            
            with open(self.rooms_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Status', 'Customer', 'Check_in'])
                writer.writeheader()
                writer.writerows(rooms)
            
            # 更新 hotel_bookings.csv
            with open('hotel_bookings.csv', 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Customer', 'Check_in', 'Check_out', 'Status'])
                writer.writerow({
                    'Room_ID': user_room,
                    'Customer': username,
                    'Check_in': check_in_time,
                    'Check_out': '',
                    'Status': 'occupied'
                })
            
            print(f"用户 {username} 入住房间 {user_room}, 时间: {check_in_time}")
            return {
                'success': True, 
                'message': '入住成功',
                'room_id': user_room,
                'check_in': check_in_time
            }
            
        except Exception as e:
            print(f"入住处理失败: {str(e)}")
            return {'success': False, 'message': str(e)}

    def approve_checkout(self, room_id, username):
        """审核通过退房申请"""
        try:
            check_out_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 更新 hotel_rooms.csv
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
            
            # 更新 hotel_bookings.csv
            bookings = []
            with open('hotel_bookings.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Room_ID'] == room_id and row['Customer'] == username:
                        row['Check_out'] = check_out_time
                        row['Status'] = 'completed'
                    bookings.append(row)
            
            with open('hotel_bookings.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Customer', 'Check_in', 'Check_out', 'Status'])
                writer.writeheader()
                writer.writerows(bookings)
            
            print(f"房间 {room_id} 的退房申请已通过，用户: {username}, 退房时间: {check_out_time}")
            return {'success': True, 'message': '退房成功'}
            
        except Exception as e:
            print(f"处理退房失败: {str(e)}")
            return {'success': False, 'message': str(e)}

    def approve_reset_request(self, username, new_password):
        """审核通过密码重置请求"""
        try:
            print(f"\n处理密码重置请求:")
            print(f"- 用户名: {username}")
            print(f"- 新密码: {new_password}")
            
            # 重置用户密码
            success, message = self.reset_user_password(username, new_password)
            if not success:
                return False, message
            
            # 更新密码重置请求状态
            resets = []
            with open('data/password_resets.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['username'] == username and row['status'] == 'pending':
                        row['status'] = 'approved'
                    resets.append(row)
            
            with open('data/password_resets.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['username', 'reason', 'status', 'created_at'])
                writer.writeheader()
                writer.writerows(resets)
            
            print("密码重置请求已处理")
            return True, '密码重置成功'
            
        except Exception as e:
            print(f"处理密码重置请求失败: {e}")
            return False, str(e) 