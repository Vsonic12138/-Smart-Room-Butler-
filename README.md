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

## 目录结构smart-room-butler/
├── server/ # 服务器端核心代码
│ ├── app.py # 应用主入口
│ ├── room_handler.py # 房间管理
│ ├── user_handler.py # 用户管理
│ └── mqtt_client.py # MQTT客户端
├── services/ # 业务服务层
│ ├── mqtt_service.py # MQTT服务
│ ├── user_service.py # 用户服务
│ └── sensor_service.py # 传感器服务
├── static/ # 静态资源
│ ├── css/ # 样式文件
│ ├── js/ # JavaScript文件
│ └── html/ # HTML页面
├── config/ # 配置文件
├── data/ # 数据存储
└── docs/ # 文档
