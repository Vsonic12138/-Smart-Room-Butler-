# type: ignore
import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify, g, send_from_directory, redirect
from server.user_handler import UserHandler
from server.sensor_handler import SensorHandler
from server.alert_handler import AlertHandler
from server.room_handler import RoomHandler
from server.service_handler import ServiceHandler
from flask_cors import CORS
from werkzeug.serving import WSGIRequestHandler
import csv
import atexit
from server.mqtt_client import mqtt_client
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

# 获取项目根目录的绝对路径
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))


# 创建Flask应用，配置静态文件目录
app = Flask(__name__, 
           static_folder=str(ROOT_DIR / 'static'),  # 使用static目录作为静态文件目录
           static_url_path='/static')  # 设置静态文件URL前缀

# 配置 CORS，允许所有路由
CORS(app, resources={
    r"/*": {
        "origins": ["*", "null"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Range", "X-Content-Range"],
        "supports_credentials": True
    }
})

# 添加根路由
@app.route('/')
def index():
    return redirect('/static/html/login.html')

# 添加登录页面路由
@app.route('/login')
def login_page():
    return redirect('/static/html/login.html')

# 添加注册页面路由
@app.route('/register')
def register_page():
    return redirect('/static/html/register.html')

# 修改HTML文件路由
@app.route('/<path:filename>')
def serve_static(filename):
    print(f"\n请求文件: {filename}")
    if filename.endswith('.html'):
        # 重定向到正确的静态文件URL
        return app.send_static_file(f'html/{filename}')
    return app.send_static_file(filename)

# 开发环境的基本配置
app.config['SECRET_KEY'] = 'dev'

# 初始化处理器，传入根目录路径
user_handler = UserHandler(root_dir=ROOT_DIR)
sensor_handler = SensorHandler(root_dir=ROOT_DIR)
alert_handler = AlertHandler(root_dir=ROOT_DIR)
room_handler = RoomHandler(root_dir=ROOT_DIR)
service_handler = ServiceHandler(root_dir=ROOT_DIR)

# 创建定时任务调度器
scheduler = BackgroundScheduler()

def save_hourly_sensor_data():
    """每小时保存传感器数据"""
    try:
        print("\n执行每小时传感器数据保存任务")
        current_time = datetime.now()
        
        # 使用绝对路径
        room_data_file = ROOT_DIR / 'hotel_room_data.csv'
        history_file = ROOT_DIR / 'data' / 'sensor_history.csv'
        
        # 读取最新的传感器数据
        with open(room_data_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            latest_data = {}
            for row in reader:
                room_id = row['Room_ID']
                data_type = row['Type']
                if room_id not in latest_data:
                    latest_data[room_id] = {}
                latest_data[room_id][data_type] = {
                    'value': row['Value'],
                    'timestamp': row['Timestamp']
                }
        
        # 确保目录存在
        history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存到历史数据文件
        with open(history_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # 如果文件为空，写入表头
            if f.tell() == 0:
                writer.writerow(['room_id', 'timestamp', 'type', 'value'])
            
            # 写入每个房间的数据
            for room_id, sensors in latest_data.items():
                timestamp = current_time.strftime('%Y-%m-%d %H:00:00')
                for sensor_type, data in sensors.items():
                    writer.writerow([
                        room_id,
                        timestamp,
                        sensor_type.lower(),
                        data['value']
                    ])
        
        print(f"已保存 {len(latest_data)} 个房间的传感器数据")
        
    except Exception as e:
        print(f"保存每小时传感器数据失败: {e}")

# 添加定时任务
scheduler.add_job(
    save_hourly_sensor_data, 
    'cron', 
    hour='*',
    minute='0',
    second='0'
)

@app.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')
        
        print(f"\n收到登录请求:")
        print(f"- 用户名: {username}")
        print(f"- 角色: {role}")
        
        result = user_handler.verify_user(username, password, role)
        print(f"验证结果: {result}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"处理登录请求失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    room_id = data.get('roomId')
    
    success, message = user_handler.register_user(username, password, room_id)
    return jsonify({
        'success': success,
        'message': message
    })

@app.route('/api/pending-users', methods=['GET'])
def get_pending_users():
    try:
        print("Fetching pending users...")  # 添加调试日志
        users = user_handler.get_pending_users()
        print(f"Found {len(users)} pending users")  # 添加调试日志
        return jsonify(users)
    except Exception as e:
        print(f"Error getting pending users: {str(e)}")  # 添加错误日志
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/approve', methods=['POST'])
def approve_user():
    """审核通过用户注册"""
    data = request.get_json()
    username = data.get('username')
    
    if not username:
        return jsonify({'success': False, 'message': '缺少用户名'})
    
    try:
        result = user_handler.approve_user(username)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/sensor-data', methods=['POST'])
def save_sensor_data():
    """保存传感器数据到CSV文件"""
    try:
        data = request.get_json()
        print('接收到的数据:', data)
        
        if not data:
            raise ValueError("没有接收到数据")
            
        # 准备保存的数据
        save_data = {
            'Room_ID': str(data.get('room_id', '')),
            'Type': str(data.get('type', '')),
            'Value': str(data.get('value', '')),  # 直接保存为字符串
            'Timestamp': str(data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        }

        # 保存数据
        csv_path = os.path.abspath('hotel_room_data.csv')
        file_exists = os.path.exists(csv_path)
        
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Type', 'Value', 'Timestamp'])
            if not file_exists:
                writer.writeheader()
            writer.writerow(save_data)
            print(f"数据已保存: {save_data}")

        return jsonify({
            'success': True,
            'message': '数据保存成功',
            'data': save_data
        })

    except Exception as e:
        error_msg = f'保存数据失败: {str(e)}'
        print(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500

@app.route('/api/sensor-history', methods=['GET'])
def get_sensor_history():
    """获取传感器历史数据"""
    try:
        room_id = request.args.get('room_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        print(f"\n获取传感器历史数据:")
        print(f"- 房间: {room_id}")
        print(f"- 开始日期: {start_date}")
        print(f"- 结束日期: {end_date}")
        
        if not all([room_id, start_date, end_date]):
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
            
        # 从 CSV 文件读取历史数据
        history_data = []
        try:
            with open('data/sensor_history.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 检查是否属于指定房间和时间范围
                    if (row['room_id'] == room_id and 
                        start_date <= row['timestamp'].split()[0] <= end_date):
                        history_data.append({
                            'timestamp': row['timestamp'],
                            'type': row['type'],
                            'value': float(row['value'])
                        })
        except FileNotFoundError:
            print("历史数据文件不存在，创建新文件")
            # 创建文件并写入表头
            with open('data/sensor_history.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['room_id', 'timestamp', 'type', 'value'])
        
        print(f"找到 {len(history_data)} 条记录")
        return jsonify(history_data)
        
    except Exception as e:
        print(f"获取传感器历史数据失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/smoke-alert', methods=['POST'])
def handle_smoke_alert():
    data = request.get_json()
    room_id = data.get('room_id')
    timestamp = data.get('timestamp')
    
    try:
        alert_handler.save_smoke_alert(room_id, timestamp, 'high')
        # 这里可以添加其他警报处理逻辑，如发送短信、邮件等
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    alerts = alert_handler.get_alerts(start_date, end_date)
    return jsonify(alerts)

@app.route('/api/reset-password-request', methods=['POST'])
def reset_password_request():
    data = request.get_json()
    username = data.get('username')
    reason = data.get('reason')
    
    try:
        user_handler.create_reset_request(username, reason)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/pending-resets', methods=['GET'])
def get_pending_resets():
    resets = user_handler.get_pending_resets()
    return jsonify(resets)

@app.route('/api/approve-reset', methods=['POST'])
def approve_reset():
    data = request.get_json()
    username = data.get('username')
    new_password = data.get('new_password')
    
    try:
        user_handler.reset_password(username, new_password)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/rooms/status', methods=['GET'])
def get_rooms_status():
    """获取所有房间状态"""
    try:
        rooms = room_handler.get_room_status()
        if not rooms:
            return jsonify([]), 404
        return jsonify(rooms)
    except Exception as e:
        print(f"获取房间状态失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/rooms/checkout/request', methods=['POST'])
def request_room_checkout():
    """客户申请退房"""
    try:
        data = request.get_json()
        username = data.get('username')
        room_id = data.get('room_id')
        
        print(f"收到退房申请 - 用户: {username}, 房间: {room_id}")
        
        if not username or not room_id:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
        
        success, message = room_handler.request_checkout(room_id, username)
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        print(f"处理退房申请失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/rooms/checkout/reject', methods=['POST'])
def reject_checkout():
    """拒绝退房申请"""
    try:
        data = request.get_json()
        username = data.get('username')
        room_id = data.get('room_id')
        
        if not username or not room_id:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
            
        success, message = room_handler.handle_checkout_request(username, room_id, 'reject')
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        print(f"处理退房拒绝失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/rooms/checkout/approve', methods=['POST'])
def approve_checkout():
    """批准退房申请"""
    try:
        data = request.get_json()
        username = data.get('username')
        room_id = data.get('room_id')
        
        if not username or not room_id:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
            
        success, message = room_handler.handle_checkout_request(username, room_id, 'approve')
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        print(f"处理退房批准失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/rooms/book', methods=['POST'])
def book_room():
    data = request.get_json()
    room_id = data.get('room_id')
    customer = data.get('customer')
    
    try:
        room_handler.book_room(room_id, customer)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/daily-averages', methods=['GET'])
def get_daily_averages():
    room_id = request.args.get('room_id')
    date = request.args.get('date')
    
    try:
        averages = sensor_handler.get_daily_averages(room_id, date)
        return jsonify(averages)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test', methods=['GET'])
def test_connection():
    return jsonify({
        'status': 'ok',
        'message': '服务器连接正常'
    })

@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    """获取所有房间列表"""
    try:
        rooms = room_handler.get_room_status()
        if not rooms:
            return jsonify({'error': 'No rooms found'}), 404
        return jsonify(rooms)
    except Exception as e:
        print(f"Error getting rooms: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/rooms/delete/<room_id>', methods=['DELETE'])
def delete_room(room_id):
    """删除房间"""
    try:
        result = room_handler.delete_room(room_id)
        return jsonify(result)
    except Exception as e:
        print(f"删除房间失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/rooms/add', methods=['POST'])
def add_room():
    """添加新房间"""
    try:
        data = request.get_json()
        room_id = data.get('room_id')
        if not room_id:
            return jsonify({'success': False, 'message': '房间号不能为空'}), 400

        success, message = room_handler.add_room(room_id)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        print(f"添加房间失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    """获取所有用户"""
    try:
        users = []
        with open(user_handler.users_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            users = list(reader)
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/add', methods=['POST'])
def add_user():
    """添加新用户"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')
        room_id = data.get('room_id')
        
        print(f"\n添加新用户:")
        print(f"- 用户名: {username}")
        print(f"- 角色: {role}")
        print(f"- 房间: {room_id}")
        
        # 验证必要参数
        if not all([username, password, role]):
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
            
        # 检查用户名是否已存在
        with open('hotel_login_data.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if any(row['Username'] == username for row in reader):
                return jsonify({
                    'success': False,
                    'message': '用户名已存在'
                })
        
        # 添加新用户到 hotel_login_data.csv
        with open('hotel_login_data.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['Username', 'Password', 'Role', 'Room_ID'])
            writer.writerow({
                'Username': username,
                'Password': password,  # 直接使用明文密码
                'Role': role,
                'Room_ID': room_id or 'without'
            })
        
        # 如果是客户且分配了房间，更新房间状态
        if role == 'Customer' and room_id and room_id != 'without':
            with open('hotel_rooms.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rooms = list(reader)
                
            for room in rooms:
                if room['Room_ID'] == room_id:
                    room['Status'] = 'assigned'
                    room['Customer'] = username
                    break
                    
            with open('hotel_rooms.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Status', 'Customer', 'Check_in'])
                writer.writeheader()
                writer.writerows(rooms)
        
        print(f"用户 {username} 添加成功")
        return jsonify({
            'success': True,
            'message': '用户添加成功'
        })
        
    except Exception as e:
        print(f"添加用户失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/users/update', methods=['POST'])
def update_user():
    """更新用户信息"""
    try:
        data = request.get_json()
        username = data.get('username')
        role = data.get('role')
        room_id = data.get('room_id')
        password = data.get('password')  # 可选参数
        
        if not username or not role:
            return jsonify({'success': False, 'message': '缺少必要参数'})

        # 获取用户当前的房间信息
        current_room = None
        with open(user_handler.users_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Username'] == username:
                    current_room = row['Room_ID']
                    break

        # 如果分配了新房间
        if room_id != 'without' and room_id != current_room:
            result = room_handler.assign_room(room_id, username)
            if not result['success']:
                return jsonify(result)

        # 更新用户信息
        result = user_handler.update_user(username, role, room_id, password)
        return jsonify(result)
        
    except Exception as e:
        print(f"更新用户失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users/delete', methods=['POST'])
def delete_user():
    """删除用户"""
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({
                'success': False,
                'message': '缺少用户名'
            }), 400
            
        print(f"\n删除用户: {username}")
        
        # 读取所有用户
        users = []
        user_found = False
        user_room = None
        
        # 从 hotel_login_data.csv 中删除用户并获取房间信息
        with open('hotel_login_data.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Username'] == username:
                    user_found = True
                    user_room = row['Room_ID']
                    continue
                users.append(row)
        
        if not user_found:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            })
            
        # 写回用户数据
        with open('hotel_login_data.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['Username', 'Password', 'Role', 'Room_ID'])
            writer.writeheader()
            writer.writerows(users)
            
        print(f"已从用户数据中删除用户 {username}")
        
        # 更新房间状态
        if user_room and user_room != 'without':
            print(f"更新房间 {user_room} 的状态")
            rooms = []
            room_updated = False
            
            with open('hotel_rooms.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Room_ID'] == user_room and row['Customer'] == username:
                        print(f"重置房间 {user_room} 状态")
                        row['Status'] = 'available'
                        row['Customer'] = ''
                        row['Check_in'] = ''
                        room_updated = True
                    rooms.append(row)
            
            if room_updated:
                with open('hotel_rooms.csv', 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=['Room_ID', 'Status', 'Customer', 'Check_in'])
                    writer.writeheader()
                    writer.writerows(rooms)
                print(f"房间 {user_room} 状态已更新")
            else:
                print(f"未找到需要更新的房间记录")
        
        print(f"用户 {username} 删除成功")
        return jsonify({
            'success': True,
            'message': '用户删除成功'
        })
        
    except Exception as e:
        print(f"删除用户失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/verify-session', methods=['POST'])
def verify_session():
    """验证用户会话"""
    data = request.get_json()
    username = data.get('username')
    role = data.get('role')
    
    if not username or not role:
        return jsonify({'success': False, 'message': '缺少必要参数'})
    
    try:
        # 验证用户是否存在且角色匹配
        with open(user_handler.users_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Username'] == username and row['Role'] == role:
                    return jsonify({'success': True})
            return jsonify({'success': False, 'message': '用户信息验证失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/reject-reset', methods=['POST'])
def reject_reset():
    data = request.get_json()
    username = data.get('username')
    try:
        user_handler.reject_reset_request(username)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/sensor-upload', methods=['POST'])
def upload_sensor_data():
    """接收来自巴法云的传感器数据"""
    try:
        data = request.get_json()
        room_id = data.get('room_id')
        sensor_type = data.get('type')
        value = data.get('value')
        
        sensor_handler.save_sensor_data(room_id, sensor_type, value)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/mqtt-data', methods=['POST'])
def handle_mqtt_data():
    """处理MQTT传感器数据"""
    try:
        data = request.get_json()
        room_id = data.get('room_id')
        temperature = data.get('temperature')
        humidity = data.get('humidity')
        smoke = data.get('smoke')
        
        if temperature is not None:
            sensor_handler.save_sensor_data(room_id, 'temperature', temperature)
        if humidity is not None:
            sensor_handler.save_sensor_data(room_id, 'humidity', humidity)
        if smoke is not None:
            sensor_handler.save_sensor_data(room_id, 'smoke', smoke)
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/recent-data', methods=['GET'])
def get_recent_data():
    """获取最近的传感器数据"""
    try:
        data = sensor_handler.get_recent_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/room', methods=['GET'])
def get_user_room():
    """获取用户的房间信息"""
    username = request.args.get('username')
    if not username:
        return jsonify({'success': False, 'message': '缺少用户名参数'})
        
    try:
        result = user_handler.get_user_room(username)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/sensor-data', methods=['GET'])
def get_sensor_data():
    """获取传感器数据，需要验证用户权限"""
    room_id = request.args.get('room_id')
    username = request.args.get('username')
    
    if not room_id or not username:
        return jsonify({
            'success': False,
            'message': '缺少必要参数'
        })
    
    try:
        # 验证用户是否有权限访问该房间数据
        with open(user_handler.users_file, 'r') as f:
            reader = csv.DictReader(f)
            user_found = False
            for row in reader:
                if row['Username'] == username:
                    user_found = True
                    if row['Role'] == 'Admin' or row['Room_ID'] == room_id:
                        # 管理员可以访问所有房间，普通用户只能访问自己的房间
                        data = sensor_handler.get_latest_sensor_data(room_id)
                        return jsonify({
                            'success': True,
                            **data
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'message': '无权访问该房间数据'
                        })
            
            if not user_found:
                return jsonify({
                    'success': False,
                    'message': '用户不存在'
                })
                
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/service-request', methods=['POST'])
def create_service_request():
    data = request.get_json()
    try:
        result = service_handler.create_request(
            data.get('username'),
            data.get('room_id'),
            data.get('timestamp')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/service-requests', methods=['GET'])
def get_service_requests():
    """获取所有服务请求"""
    try:
        requests = service_handler.get_pending_requests()
        return jsonify(requests)
    except Exception as e:
        print(f"Error getting service requests: {str(e)}")
        return jsonify([])

@app.route('/api/complete-service', methods=['POST'])
def complete_service_request():
    data = request.get_json()
    try:
        result = service_handler.complete_request(data.get('request_id'))
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/rooms/checkin', methods=['POST'])
def check_in():
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({'success': False, 'message': '缺少用户名'}), 400
        
        result = user_handler.check_in_room(username)
        return jsonify(result)
        
    except Exception as e:
        print(f"处理入住请求失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/rooms/checkout/pending', methods=['GET'])
def get_pending_checkouts():
    """获取待审核的退房申请"""
    try:
        checkouts = room_handler.get_pending_checkouts()
        return jsonify(checkouts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rooms/checkout/reject', methods=['POST'])
def reject_room_checkout():
    """拒绝退房申请"""
    data = request.get_json()
    room_id = data.get('room_id')
    username = data.get('username')
    
    if not room_id or not username:
        return jsonify({'success': False, 'message': '缺少必要参数'})
    
    result = room_handler.reject_checkout(room_id, username)
    return jsonify(result)

@app.route('/api/sensor-data/<room_id>', methods=['GET'])
def get_room_sensor_data(room_id):
    """获取指定房间的最新传感器数据"""
    try:
        latest_data = {
            'temperature': None,
            'humidity': None,
            'smoke': None,
            'success': True
        }

        # 确保文件存在
        if not os.path.exists('hotel_room_data.csv'):
            return jsonify(latest_data)

        # 从CSV文件读取最新数据
        with open('hotel_room_data.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or 'Room_ID' not in reader.fieldnames:
                raise ValueError('CSV文件格式不正确')
                
            rows = list(reader)
            for row in reversed(rows):  # 从后向前读取，获取最新数据
                if row['Room_ID'] == room_id:
                    sensor_type = row['Type'].lower()
                    if sensor_type in latest_data and latest_data[sensor_type] is None:
                        try:
                            latest_data[sensor_type] = float(row['Value'])
                        except (ValueError, TypeError):
                            print(f"无效的传感器数据: {row['Value']}")
                            continue

                    # 如果所有传感器数据都已找到，就退出循环
                    if all(v is not None for k, v in latest_data.items() if k != 'success'):
                        break

        print(f"房间 {room_id} 的最新传感器数据: {latest_data}")  # 添加调试日志
        return jsonify(latest_data)
    except Exception as e:
        print(f"获取传感器数据失败: {str(e)}")  # 添加调试日志
        return jsonify({
            'success': False,
            'message': str(e)
        })

@app.route('/api/rooms/available', methods=['GET'])
def get_available_rooms():
    """获取所有可用房间"""
    try:
        print("\n获取可用房间列表")
        available_rooms = []
        
        # 读取所有房间状态
        with open('hotel_rooms.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 只返回状态为 available 的房间
                if row['Status'] == 'available':
                    available_rooms.append({
                        'Room_ID': row['Room_ID'],
                        'Status': row['Status']
                    })
        
        print(f"找到 {len(available_rooms)} 个可用房间")
        return jsonify(available_rooms)
        
    except Exception as e:
        print(f"获取可用房间列表失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/service-requests/handle', methods=['POST', 'OPTIONS'])
def handle_service_request():
    """处理服务请求"""
    # 处理 OPTIONS 请求
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        action = data.get('action')
        
        if not request_id or not action:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
            
        result = service_handler.handle_request(request_id, action)
        return jsonify(result)
        
    except Exception as e:
        print(f"处理服务请求失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/room-stats/daily/<date>', methods=['GET'])
def get_daily_stats(date):
    """获取指定日期的日均值统计"""
    try:
        print(f"\n开始获取日期 {date} 的统计数据...")
        
        # 解析日期
        target_date = datetime.strptime(date, '%Y-%m-%d')
        current_date = datetime.now()
        
        # 如果是当天，使用当前时间作为结束时间
        is_today = (target_date.date() == current_date.date())
        end_time = current_date if is_today else (target_date + timedelta(days=1))
        
        print(f"目标日期: {target_date}, 结束时间: {end_time}")
        
        # 读取房间数据
        day_temps = []
        day_humids = []
        night_temps = []
        night_humids = []
        
        try:
            with open('hotel_room_data.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        timestamp = datetime.strptime(row['Timestamp'], '%Y-%m-%d %H:%M:%S')
                        # 只处理目标日期的数据
                        if target_date <= timestamp < end_time:
                            hour = timestamp.hour
                            value = float(row['Value'])
                            
                            print(f"处理数据: 时间={timestamp}, 类型={row['Type']}, 值={value}")
                            
                            # 区分日间和夜间数据
                            if 6 <= hour < 18:  # 日间 6:00-18:00
                                if row['Type'] == 'temperature':
                                    day_temps.append(value)
                                elif row['Type'] == 'humidity':
                                    day_humids.append(value)
                            else:  # 夜间 18:00-6:00
                                if row['Type'] == 'temperature':
                                    night_temps.append(value)
                                elif row['Type'] == 'humidity':
                                    night_humids.append(value)
                    except Exception as e:
                        print(f"处理行数据失败: {e}, 行数据: {row}")
                        continue
                        
            print(f"收集到的数据:")
            print(f"日间温度数据: {len(day_temps)} 条")
            print(f"日间湿度数据: {len(day_humids)} 条")
            print(f"夜间温度数据: {len(night_temps)} 条")
            print(f"夜间湿度数据: {len(night_humids)} 条")
            
        except Exception as e:
            print(f"读取房间数据文件失败: {e}")
            raise
        
        # 计算平均值（分别计算每个指标）
        stats = {
            'day': {
                'temperature': round(sum(day_temps) / len(day_temps), 1) if day_temps else None,
                'humidity': round(sum(day_humids) / len(day_humids), 1) if day_humids else None
            },
            'night': {
                'temperature': round(sum(night_temps) / len(night_temps), 1) if night_temps else None,
                'humidity': round(sum(night_humids) / len(night_humids), 1) if night_humids else None
            },
            'data_points': {
                'day': {
                    'temperature': len(day_temps),
                    'humidity': len(day_humids)
                },
                'night': {
                    'temperature': len(night_temps),
                    'humidity': len(night_humids)
                }
            }
        }
        
        print(f"统计结果: {stats}")
        return jsonify(stats)
        
    except Exception as e:
        print(f"获取日均值统计失败: {e}")
        return jsonify({'error': str(e)}), 500

# 修改MQTT客户端初始化逻辑
mqtt_started = False

def init_mqtt():
    """初始化MQTT服务"""
    global mqtt_started
    if not mqtt_started:
        print("\n=== 初始化MQTT服务 ===")
        try:
            mqtt_client.start()
            mqtt_started = True
            print("MQTT服务启动成功")
        except Exception as e:
            print(f"MQTT服务启动失败: {e}")
        print("="*30 + "\n")

@app.before_request
def before_request():
    """每个请求前检查MQTT客户端状态"""
    global mqtt_started
    if not mqtt_started:
        init_mqtt()

# 在应用关闭时清理资源
def cleanup():
    global mqtt_started
    if mqtt_started:
        mqtt_client.stop()
    if scheduler.running:
        scheduler.shutdown()

atexit.register(cleanup)

if __name__ == '__main__':
    # 初始化MQTT服务
    init_mqtt()
    
    # 启动调度器
    if not scheduler.running:
        scheduler.start()
        print("调度器已启动")
    
    try:
        app.run(
            debug=True,
            host='127.0.0.1',
            port=5000,
            threaded=True
        )
    finally:
        cleanup() 