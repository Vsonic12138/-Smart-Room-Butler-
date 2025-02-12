# 智慧客房管家 (Smart Room Butler)

一个结合物联网技术的智能酒店房间管理系统，提供实时监控、智能预警和便捷管理功能。

## 功能特点

- 🏨 房间管理
  - 房间状态实时监控
  - 入住/退房管理
  - 预订管理
  
- 🔔 智能监控
  - 温度实时监测
  - 湿度实时监测
  - 烟雾报警系统
  
- 👥 用户管理
  - 多角色权限控制
  - 用户注册与审核
  - 密码重置
  
- 🛎️ 服务请求
  - 客户服务申请
  - 请求状态追踪
  - 服务响应处理

## 技术架构

### 后端技术
- Python Flask 框架
- MQTT 物联网通信
- CSV 数据存储
- RESTful API

### 前端技术
- 原生 JavaScript
- Chart.js 数据可视化
- WebSocket 实时通信
- 响应式设计

### 物联网集成
- MQTT 协议
- 巴法云平台对接
- 实时数据采集
- 智能预警系统

## 目录结构smart-room-butler

```plaintext
smart-room-butler
├── app.py        # Flask应用主文件
├── run.py        # 应用程序入口点
├── README.md     # 项目说明文档
│
├── config/ # 配置文件目录
│   ├── init.py
│   ├── development.py # 开发环境配置
│   ├── production.py # 生产环境配置
│   └── mqtt_config.py # MQTT配置
│
├── server/ # 后端核心处理器
│   ├── init.py
│   ├── mqtt_client.py # MQTT客户端
│   ├── sensor_handler.py # 传感器处理
│   ├── alert_handler.py # 警报处理
│   ├── room_handler.py # 房间管理
│   ├── user_handler.py # 用户管理
│   ├── data_handler.py # 数据处理
│   └── app.py # 服务器应用
│
├── services/ # 业务逻辑服务
│   ├── init.py
│   ├── mqtt_service.py
│   ├── user_service.py
│   ├── room_service.py
│   └── sensor_service.py
│
├── handlers/ # API处理程序
│   ├── init.py
│   ├── user_handler.py
│   ├── room_handler.py
│   └── notification_handler.py
│
├── utils/ # 工具函数
│   ├── init.py
│   └── csv_helper.py
│
├── static/ # 静态文件
│   ├── css/
│   │   ├── style.css
│   │   └── admin.css
│   ├── js/
│   │   ├── login.js
│   │   ├── admin.js
│   │   └── chart.js
│   ├── html/
│   │   ├── login.html
│   │   ├── admin.html
│   │   └── register.html
│   └── images/
│
├── data/ # 数据文件
│   ├── hotel_login_data.csv
│   ├── hotel_rooms.csv
│   ├── hotel_bookings.csv
│   ├── hotel_history.csv
│   ├── hotel_room_data.csv
│   ├── admin_accounts.csv
│   ├── pending_users.csv
│   ├── alerts.csv
│   └── sensor_history.csv
│
├── docs/ # 文档
│   ├── architecture.md
│   ├── mqtt_workflow.md
│   └── admin_login_workflow.md
│
└── scripts/ # 脚本工具
    └── init_admin.py # 初始化管理员账号

