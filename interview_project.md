# 日志分析系统面试项目

## 项目背景
你需要为一个电商网站构建一个简单的日志分析API服务。系统需要接收访问日志，存储到数据库，并提供统计分析接口。

## 环境要求
- Python 3.9+
- Docker & Docker Compose
- 任何你喜欢的编辑器/IDE

## 快速开始

### 1. 克隆并启动项目
```bash
git clone <repo-url>
cd log-analytics-interview
docker-compose up -d
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 运行服务
```bash
python main.py
```

服务将在 `http://localhost:8000` 启动

### 4. 测试API
访问 `http://localhost:8000/docs` 查看API文档

## 项目结构
```
log-analytics-interview/
├── main.py              # 主程序入口
├── models.py            # 数据库模型
├── database.py          # 数据库连接
├── requirements.txt     # Python依赖
├── docker-compose.yml   # Docker配置
├── sample_logs.txt      # 示例日志数据
├── test_data.py         # 测试数据生成脚本
└── README.md           # 本文件
```

## 任务列表

### 任务0：修复环境问题（必做）
运行 `docker-compose up` 和 `python main.py`，你会遇到一些问题。请修复它们使服务正常启动。

**提示**：注意观察错误信息，可能涉及端口冲突、数据库连接等。

---

### 任务1：实现日志导入API（必做）
完善 `POST /api/logs/import` 接口，从上传的日志文件中解析数据并存入数据库。

**日志格式示例**：
```
2024-01-15 10:23:45 | user_1001 | /product/12345 | 250ms | 200
2024-01-15 10:24:10 | user_1002 | /cart/add | 180ms | 200
2024-01-15 10:24:15 | user_1001 | /checkout | 1200ms | 500
```

格式说明：`时间戳 | 用户ID | 访问路径 | 响应时间 | HTTP状态码`

**要求**：
- 解析日志文件并存储到 `access_logs` 表
- 处理格式错误的行（跳过并记录错误数）
- 返回导入统计信息

**评估点**：
- 文件处理能力
- 字符串解析（是否过度使用正则？）
- 错误处理

---

### 任务2：实现基础统计API（必做）
实现 `GET /api/stats/summary` 接口，返回以下统计数据：

```json
{
  "total_requests": 10000,
  "unique_users": 523,
  "avg_response_time": 350.5,
  "error_rate": 0.023,
  "top_paths": [
    {"path": "/product/12345", "count": 450},
    {"path": "/cart/add", "count": 320}
  ]
}
```

**要求**：
- 使用SQL查询实现（不要全部读到内存）
- 支持按时间范围过滤（可选参数 `start_time`, `end_time`）

**评估点**：
- SQL能力
- 数据聚合思路
- 性能意识

---

### 任务3：实现滑动窗口实时监控（选做，算法重点）
实现 `GET /api/stats/realtime` 接口，计算最近N分钟的请求速率和错误率。

**要求**：
- 支持参数：`window_minutes`（窗口大小，默认5分钟）
- 按每分钟分组统计
- 使用滑动窗口算法优化查询

**返回示例**：
```json
{
  "window_minutes": 5,
  "data_points": [
    {"timestamp": "2024-01-15 10:20:00", "requests": 120, "error_rate": 0.02},
    {"timestamp": "2024-01-15 10:21:00", "requests": 135, "error_rate": 0.01},
    ...
  ]
}
```

**评估点**：
- 时间窗口处理能力
- 算法选择（暴力 vs 优化）
- 边界条件处理

---

### 任务4：用户行为路径分析（选做，OOD重点）
实现 `GET /api/users/{user_id}/journey` 接口，分析用户的访问路径。

**要求**：
- 返回用户的访问序列
- 识别"完整购买流程"：浏览商品 → 加入购物车 → 结账
- 标记出"中断点"（用户在哪一步离开）

**返回示例**：
```json
{
  "user_id": "user_1001",
  "sessions": [
    {
      "start_time": "2024-01-15 10:23:45",
      "path_sequence": ["/product/123", "/cart/add", "/checkout"],
      "completed_purchase": true
    },
    {
      "start_time": "2024-01-15 14:10:00",
      "path_sequence": ["/product/456", "/product/789"],
      "completed_purchase": false,
      "drop_off_point": "product_browsing"
    }
  ]
}
```

**评估点**：
- 状态机/工作流设计
- 面向对象设计
- 业务逻辑抽象

---

### 任务5：性能优化（选做，进阶）
当前系统在大数据量下可能会有性能问题。

**要求**：
- 为 `access_logs` 表添加合适的索引
- 实现查询结果缓存（Redis或内存）
- 优化慢查询

**评估点**：
- 数据库优化意识
- 缓存策略
- 性能分析能力

---

## 评分标准

### 基础分（60分）
- 任务0：修复环境问题（10分）
- 任务1：日志导入（25分）
- 任务2：基础统计（25分）

### 进阶分（40分）
- 任务3：滑动窗口（15分）
- 任务4：用户路径分析（15分）
- 任务5：性能优化（10分）

### 加分项
- 代码结构清晰，遵循最佳实践
- 主动添加单元测试
- 良好的错误处理和日志记录
- 主动发现并修复未列出的bug

## 注意事项
1. **允许使用任何资源**：Google、ChatGPT、Claude、Stack Overflow等
2. **鼓励提问**：遇到不清楚的地方可以随时问面试官
3. **思路比结果重要**：即使没完成，清晰的解题思路也会得分
4. **时间管理**：建议先完成必做任务，再挑选感兴趣的选做任务

## 故意埋的坑（面试官参考）
1. **docker-compose.yml**：数据库端口映射错误
2. **database.py**：数据库URL拼接错误
3. **models.py**：表名拼写错误导致查询失败
4. **main.py**：缺少CORS配置导致前端无法调用
5. **sample_logs.txt**：混入了一些格式错误的行
6. **requirements.txt**：缺少必要的依赖包

## 面试官观察点
- [ ] 如何阅读和理解现有代码？
- [ ] 遇到错误时的调试流程？
- [ ] 如何使用搜索引擎/AI工具？
- [ ] 是否先看数据再写代码？
- [ ] 是否考虑边界情况和异常处理？
- [ ] SQL写法是否高效？
- [ ] 代码风格和可读性
- [ ] 沟通能力和问题意识
