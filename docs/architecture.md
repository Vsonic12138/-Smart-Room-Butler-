# 酒店管理系统架构文档

## 1. 系统概述

本系统是一个基于Python Flask的酒店管理系统,集成了用户管理、房间管理、传感器监控等功能。系统采用前后端分离架构,后端使用RESTful API提供服务,前端使用HTML/CSS/JavaScript实现。

## 2. 系统架构

### 2.1 技术栈

- 后端: Python Flask
- 前端: HTML/CSS/JavaScript
- 数据存储: CSV文件
- 实时通信: MQTT协议
- 定时任务: APScheduler

### 2.2 项目结构

```
hotel_management/
├── run.py                 # 应用程序入口点
├── app.py                 # Flask应用主文件
├── config/               # 配置文件目录
│   ├── __init__.py
│   ├── development.py    # 开发环境配置
│   └── production.py     # 生产环境配置
├── services/           # 业务逻辑服务目录
│   ├── __init__.py
│   ├── user_service.py
│   ├── room_service.py
│   └── sensor_service.py
├── handlers/           # API处理程序目录
│   ├── __init__.py
│   ├── user_handler.py
│   ├── room_handler.py
│   └── sensor_handler.py
├── utils/             # 工具函数目录
│   ├── __init__.py
│   ├── csv_helper.py
│   └── mqtt_helper.py
├── static/           # 静态html文件目录
│   ├── css/
│   ├── js/
│   └── images/
└── data/            # 数据文件目录
    ├── hotel_login_data.csv
    └── ...
```

### 2.3 核心模块

1. **用户管理模块 (UserHandler)**
   - 用户注册与登录
   - 用户审核
   - 密码重置
   - 用户权限管理

2. **房间管理模块 (RoomHandler)**
   - 房间状态管理
   - 入住/退房处理
   - 房间分配
   - 预订管理

3. **传感器管理模块 (SensorHandler)**
   - 传感器数据采集
   - 数据存储
   - 实时监控
   - 历史数据查询

4. **MQTT客户端模块 (MQTTClient)**
   - 连接MQTT服务器
   - 订阅传感器主题
   - 处理传感器数据
   - 数据持久化

5. **服务请求模块 (ServiceHandler)**
   - 处理客户服务请求
   - 跟踪服务状态
   - 服务完成确认

6. **警报处理模块 (AlertHandler)**
   - 监控异常数据
   - 触发警报
   - 警报记录管理

### 2.4 数据存储

系统使用CSV文件进行数据持久化存储:

1. **用户相关**
   - `hotel_login_data.csv`: 用户账号信息
   - `pending_users.csv`: 待审核用户
   - `reset_requests.csv`: 密码重置请求

2. **房间相关**
   - `hotel_rooms.csv`: 房间基本信息
   - `hotel_bookings.csv`: 预订记录
   - `hotel_history.csv`: 历史记录

3. **传感器相关**
   - `hotel_room_data.csv`: 实时传感器数据
   - `sensor_history.csv`: 传感器历史数据

4. **服务相关**
   - `service_requests.csv`: 服务请求记录
   - `alerts.csv`: 警报记录

## 3. 工作流程

### 3.1 用户注册流程

1. 用户提交注册信息
   - 前端通过register.html页面收集用户信息
   - 发送POST请求到/api/register接口

2. 系统验证信息完整性
   - 后端UserHandler验证用户名是否已存在
   - 检查密码强度和其他必填信息

3. 将用户信息保存到待审核列表
   - 数据存储到pending_users.csv文件
   - 包含字段:Username、Password、Room_ID、Timestamp

4. 管理员审核
   - 管理员通过admin.html页面查看待审核列表
   - 待审核数据从pending_users.csv读取
   - 管理员可以选择通过或拒绝

5. 审核通过后创建正式账号
   - 从pending_users.csv删除该条记录
   - 将用户信息写入hotel_login_data.csv
   - 包含字段:Username、Password、Role、Room_ID
   - 如果分配了房间,同时更新hotel_rooms.csv

### 3.2 房间管理流程

1. 客户预订房间
   - 通过customer.html页面选择房间
   - 发送预订请求到后端

2. 系统检查房间可用性
   - 从hotel_rooms.csv读取房间状态
   - 检查房间是否处于可预订状态

3. 确认预订并更新房间状态
   - 在hotel_bookings.csv创建预订记录
   - 更新hotel_rooms.csv中房间状态
   - 字段包括:Room_ID、Customer、Check_in、Status

4. 客户入住时更新房间状态
   - 更新hotel_rooms.csv中Status为"occupied"
   - 记录入住时间Check_in
   - 关联房间与用户信息

5. 退房时进行结算并释放房间
   - 更新hotel_rooms.csv中Status为"available"
   - 清除房间关联的用户信息
   - 将预订记录从hotel_bookings.csv移动到hotel_history.csv

### 3.3 传感器监控流程

1. MQTT客户端订阅传感器主题
   - 订阅temperature、humidity、smoke三个主题
   - 主题格式:hotel{房间号}{传感器类型}

2. 接收传感器实时数据
   - MQTTClient接收传感器发送的数据
   - 解析主题获取房间号和传感器类型

3. 解析并存储数据
   - 将数据写入hotel_room_data.csv
   - 字段包括:Room_ID、Type、Value、Timestamp
   - 每小时自动将数据归档到sensor_history.csv

4. 检查数据是否超过阈值
   - 检查温度、湿度、烟雾值是否超出预设范围
   - 阈值配置在系统配置文件中

5. 必要时触发警报
   - 异常数据写入alerts.csv
   - 字段包括:Room_ID、Type、Value、Level、Timestamp
   - 通过WebSocket推送警报到前端

### 3.4 服务请求流程

1. 客户提交服务请求
   - 通过customer.html页面提交请求
   - 发送POST请求到服务接口

2. 系统记录请求信息
   - 将请求写入service_requests.csv
   - 字段包括:Request_ID、Room_ID、Customer、Type、Status、Timestamp

3. 服务人员接收并处理请求
   - 管理员通过admin.html页面查看请求列表
   - 从service_requests.csv读取未处理的请求
   - 分配服务人员处理

4. 更新请求状态
   - 在service_requests.csv中更新请求状态
   - 状态包括:pending、processing、completed

5. 完成服务后确认
   - 服务人员完成服务后更新状态为completed
   - 系统通知客户服务完成
   - 客户可以评价服务质量

## 4. 安全机制

1. 用户认证
   - 密码加密存储
   - 会话管理
   - 权限控制

2. 数据安全
   - 数据备份
   - 访问控制
   - 输入验证

3. 系统监控
   - 错误日志
   - 操作审计
   - 异常检测

## 5. 扩展性考虑

1. 模块化设计
   - 各模块独立封装
   - 接口统一规范
   - 便于功能扩展

2. 数据存储优化
   - 可迁移到关系型数据库
   - 支持数据分析
   - 历史数据归档

3. 性能优化
   - 缓存机制
   - 异步处理
   - 批量操作

## 6. 注意事项

1. 数据一致性
   - 确保各个CSV文件之间的数据同步
   - 定期检查数据完整性
   - 处理并发访问

2. 错误处理
   - 完善的异常处理机制
   - 用户友好的错误提示
   - 系统状态恢复

3. 维护建议
   - 定期数据备份
   - 日志监控
   - 系统升级计划

## 7. 前端架构

### 7.1 页面结构

1. **登录相关页面**
   - `login.html`: 用户登录页面
   - `register.html`: 用户注册页面
   - `forgot-password.html`: 密码重置页面

2. **管理员页面 (admin.html)**
   - 用户管理模块
     * 用户列表
     * 添加/编辑用户
     * 待审核用户管理
     * 密码重置请求处理
   - 房间管理模块
     * 房间状态监控
     * 传感器数据分析
     * 房间添加/删除
   - 服务请求管理
     * 查看服务请求
     * 处理服务请求

3. **客户页面 (customer.html)**
   - 房间信息显示
   - 传感器数据监控
   - 服务请求功能
   - 入住/退房操作

### 7.2 技术实现

1. **UI框架与库**
   - 原生HTML/CSS/JavaScript
   - Chart.js用于数据可视化
   - MQTT.js用于实时数据通信

2. **页面交互**
   - AJAX异步请求
   - WebSocket实时通信
   - 动态DOM操作

3. **数据展示**
   - 实时传感器数据更新
   - 图表展示
   - 表格数据展示

### 7.3 前后端通信

1. **API调用**
   - RESTful API接口
   - JSON数据格式
   - HTTP请求方法(GET/POST/PUT/DELETE)

2. **实时通信**
   - MQTT协议
   - WebSocket连接
   - 服务器推送

3. **数据同步**
   - 定时轮询
   - 事件驱动更新
   - 状态管理

### 7.4 用户体验

1. **响应式设计**
   - 适配不同设备
   - 流畅的页面切换
   - 友好的操作反馈

2. **错误处理**
   - 用户输入验证
   - 错误提示
   - 异常状态处理

3. **安全性**
   - 登录状态维护
   - 权限控制
   - 数据加密传输

