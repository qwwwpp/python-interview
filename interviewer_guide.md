# 面试官指南

## 埋的坑清单

### 环境问题（任务0）

1. **docker-compose.yml - 端口映射错误**
   - 错误：`5433:5432`（应该是 `5432:5432`）
   - 现象：PostgreSQL启动正常，但代码无法连接
   - 观察点：候选人是否能通过错误信息定位到端口问题

2. **database.py - 端口配置错误**
   - 错误：连接 `localhost:5432`
   - 正确：应该连接 `localhost:5433`（即使修正了docker-compose）
   - 或者：同时修正docker-compose和database.py都用5432

3. **models.py - 表名拼写错误**
   - 错误：`acess_logs`（缺少c）
   - 正确：`access_logs`
   - 现象：运行时会报表不存在的错误

4. **requirements.txt - 缺少依赖**
   - 缺少：`psycopg2-binary`（PostgreSQL驱动）
   - 缺少：`python-multipart`（文件上传）
   - 现象：导入错误或运行时错误

5. **main.py - 缺少CORS配置**（可选）
   - 如果候选人要写前端，会遇到跨域问题

6. **sample_logs.txt - 混入错误格式**
   - 缺少字段、时间格式错误、完全无效的行
   - 测试候选人的错误处理能力

---

## 任务1参考答案：日志导入

```python
@app.post("/api/logs/import")
async def import_logs(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    content = await file.read()
    lines = content.decode('utf-8').split('\n')
    
    success_count = 0
    error_count = 0
    errors = []
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        try:
            # 解析日志行
            parts = [p.strip() for p in line.split('|')]
            if len(parts) != 5:
                raise ValueError(f"字段数量不正确: {len(parts)}")
            
            # 解析各字段
            timestamp_str, user_id, path, response_time_str, status_code_str = parts
            
            # 解析时间
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            # 解析响应时间（移除ms后缀）
            response_time = float(response_time_str.replace('ms', ''))
            
            # 解析状态码
            status_code = int(status_code_str)
            
            # 创建记录
            log = AccessLog(
                timestamp=timestamp,
                user_id=user_id,
                path=path,
                response_time=response_time,
                status_code=status_code
            )
            db.add(log)
            success_count += 1
            
        except Exception as e:
            error_count += 1
            errors.append(f"第{line_num}行错误: {str(e)}")
    
    db.commit()
    
    return {
        "success": success_count,
        "errors": error_count,
        "error_details": errors[:10]  # 只返回前10个错误
    }
```

**评分点**：
- ✅ 能正确读取文件内容
- ✅ 逐行解析，处理分隔符
- ✅ 跳过注释和空行
- ✅ 正确解析各字段（时间、响应时间格式）
- ✅ 异常处理和错误统计
- ⭐ 加分：批量插入优化（`db.bulk_insert_mappings`）

---

## 任务2参考答案：基础统计

```python
from sqlalchemy import func

@app.get("/api/stats/summary")
def get_summary_stats(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AccessLog)
    
    # 时间范围过滤
    if start_time:
        query = query.filter(AccessLog.timestamp >= datetime.fromisoformat(start_time))
    if end_time:
        query = query.filter(AccessLog.timestamp <= datetime.fromisoformat(end_time))
    
    # 总请求数
    total_requests = query.count()
    
    # 独立用户数
    unique_users = query.with_entities(
        func.count(func.distinct(AccessLog.user_id))
    ).scalar()
    
    # 平均响应时间
    avg_response_time = query.with_entities(
        func.avg(AccessLog.response_time)
    ).scalar() or 0
    
    # 错误率
    error_count = query.filter(AccessLog.status_code >= 400).count()
    error_rate = error_count / total_requests if total_requests > 0 else 0
    
    # 热门路径（Top 5）
    top_paths = db.query(
        AccessLog.path,
        func.count(AccessLog.id).label('count')
    ).group_by(AccessLog.path).order_by(func.count(AccessLog.id).desc()).limit(5).all()
    
    return {
        "total_requests": total_requests,
        "unique_users": unique_users,
        "avg_response_time": round(avg_response_time, 2),
        "error_rate": round(error_rate, 4),
        "top_paths": [{"path": p, "count": c} for p, c in top_paths]
    }
```

**评分点**：
- ✅ 使用SQL聚合函数（不是读到内存计算）
- ✅ 正确处理时间范围过滤
- ✅ 各项指标计算正确
- ⭐ 加分：考虑空数据的边界情况

---

## 任务3参考答案：滑动窗口

```python
from sqlalchemy import func, cast, String

@app.get("/api/stats/realtime")
def get_realtime_stats(
    window_minutes: int = 5,
    db: Session = Depends(get_db)
):
    # 计算窗口起始时间
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=window_minutes)
    
    # 按分钟分组统计
    # 使用date_trunc截断到分钟级别
    results = db.query(
        func.date_trunc('minute', AccessLog.timestamp).label('minute'),
        func.count(AccessLog.id).label('requests'),
        func.sum(
            func.cast(AccessLog.status_code >= 400, Integer)
        ).label('errors')
    ).filter(
        AccessLog.timestamp >= start_time,
        AccessLog.timestamp <= end_time
    ).group_by(
        func.date_trunc('minute', AccessLog.timestamp)
    ).order_by('minute').all()
    
    data_points = []
    for minute, requests, errors in results:
        error_rate = errors / requests if requests > 0 else 0
        data_points.append({
            "timestamp": minute.strftime('%Y-%m-%d %H:%M:%S'),
            "requests": requests,
            "error_rate": round(error_rate, 4)
        })
    
    return {
        "window_minutes": window_minutes,
        "start_time": start_time.strftime('%Y-%m-%d %H:%M:%S'),
        "end_time": end_time.strftime('%Y-%m-%d %H:%M:%S'),
        "data_points": data_points
    }
```

**评分点**：
- ✅ 正确计算时间窗口
- ✅ 使用date_trunc或类似函数按分钟分组
- ✅ 一次查询完成统计（不是多次查询）
- ⭐ 加分：考虑时区问题
- ⭐ 加分：处理空白分钟（补全数据）

---

## 任务4参考答案：用户路径分析

```python
from collections import defaultdict

# 定义购买流程
PURCHASE_STAGES = {
    "product_browsing": ["/product/"],
    "add_to_cart": ["/cart/add"],
    "checkout": ["/checkout"],
    "payment": ["/payment"]
}

def analyze_session(logs):
    """分析单个会话"""
    path_sequence = [log.path for log in logs]
    
    # 判断是否完成购买
    has_product = any("/product/" in p for p in path_sequence)
    has_cart = any("/cart/add" in p for p in path_sequence)
    has_checkout = any("/checkout" in p for p in path_sequence)
    
    completed_purchase = has_product and has_cart and has_checkout
    
    # 判断中断点
    drop_off_point = None
    if not completed_purchase:
        if not has_product:
            drop_off_point = "no_browsing"
        elif not has_cart:
            drop_off_point = "product_browsing"
        elif not has_checkout:
            drop_off_point = "cart_abandonment"
    
    return {
        "start_time": logs[0].timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        "path_sequence": path_sequence,
        "completed_purchase": completed_purchase,
        "drop_off_point": drop_off_point
    }

@app.get("/api/users/{user_id}/journey")
def get_user_journey(user_id: str, db: Session = Depends(get_db)):
    # 查询用户所有访问记录
    logs = db.query(AccessLog).filter(
        AccessLog.user_id == user_id
    ).order_by(AccessLog.timestamp).all()
    
    if not logs:
        raise HTTPException(status_code=404, detail="用户未找到")
    
    # 按会话分组（超过30分钟算新会话）
    sessions = []
    current_session = [logs[0]]
    
    for log in logs[1:]:
        time_gap = (log.timestamp - current_session[-1].timestamp).total_seconds()
        if time_gap > 1800:  # 30分钟
            sessions.append(analyze_session(current_session))
            current_session = [log]
        else:
            current_session.append(log)
    
    # 处理最后一个会话
    if current_session:
        sessions.append(analyze_session(current_session))
    
    return {
        "user_id": user_id,
        "total_sessions": len(sessions),
        "sessions": sessions
    }
```

**评分点**：
- ✅ 正确查询和排序用户访问记录
- ✅ 会话划分逻辑合理（时间间隔）
- ✅ 购买流程识别正确
- ✅ 能标记中断点
- ⭐ 加分：OOD设计（定义Session类、State Pattern）
- ⭐ 加分：考虑更复杂的流程（重复访问、回退等）

---

## 任务5：性能优化提示

### 索引优化
```sql
-- 已有索引：id, timestamp, user_id
-- 建议添加：
CREATE INDEX idx_status_code ON access_logs(status_code);
CREATE INDEX idx_path ON access_logs(path);
CREATE INDEX idx_user_timestamp ON access_logs(user_id, timestamp);
```

### 批量插入优化
```python
# 使用bulk_insert_mappings代替逐条add
logs_data = [...]
db.bulk_insert_mappings(AccessLog, logs_data)
```

### 缓存（可选）
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_stats(start_time, end_time):
    # 缓存统计结果
    pass
```

---

## 观察要点记录表

| 维度 | 优秀表现 | 一般表现 | 需改进 |
|-----|---------|---------|--------|
| 代码阅读 | 快速定位关键代码，理解项目结构 | 能找到相关文件，但需要时间 | 漫无目的地浏览 |
| 调试能力 | 系统性排查，看日志、加print、查文档 | 尝试修改但不确定原因 | 反复试错，没有章法 |
| 搜索技能 | 精准关键词，快速找到答案 | 搜索但结果不理想 | 不知道搜什么 |
| AI使用 | 提问清晰，验证答案，理解原理 | 直接复制代码，部分理解 | 盲目粘贴，不测试 |
| 算法思维 | 考虑时间复杂度，选择合适数据结构 | 能实现但未优化 | 暴力解法或错误 |
| 代码质量 | 清晰命名，适当注释，异常处理 | 能跑但不够优雅 | 混乱、无异常处理 |
| 工具使用 | 熟练使用git/docker或快速学会 | 基本操作但不熟练 | 需要详细指导 |
| 沟通能力 | 主动说明思路，及时提问 | 基本能表达 | 埋头苦干，不沟通 |

---

## 时间分配建议

- **30分钟**：任务0（环境修复）+ 任务1（日志导入）
- **20分钟**：任务2（基础统计）
- **20分钟**：任务3或任务4任选其一
- **10分钟**：讨论和总结

**总时长**：60-90分钟

---

## 常见反模式

❌ **过度使用正则表达式**
- 对于简单的分隔符解析，`split('|')` 足够
- 候选人一上来就写复杂正则说明缺乏工程判断

❌ **全部读入内存**
```python
# 不好
all_logs = db.query(AccessLog).all()
for log in all_logs:  # 如果有百万条数据会爆内存
    ...

# 好
query.count()  # 用SQL统计
```

❌ **忽略错误处理**
```python
# 不好
timestamp = datetime.strptime(parts[0], '%Y-%m-%d %H:%M:%S')  # 如果格式错误会crash

# 好
try:
    timestamp = datetime.strptime(parts[0], '%Y-%m-%d %H:%M:%S')
except ValueError:
    error_count += 1
    continue
```

❌ **盲目相信AI回答**
- 直接复制ChatGPT代码不测试
- 不理解代码就提交

---

## 加分项

✨ **主动发现隐藏问题**
- "我注意到这里没有索引，查询可能会很慢"
- "这个表名好像拼错了"

✨ **提出改进建议**
- "我们可以用异步IO加速文件读取"
- "建议加上数据验证和日志记录"

✨ **写测试**
```python
def test_import_logs():
    # 自己写单元测试
    pass
```

✨ **考虑生产环境**
- "如果日志文件很大怎么办？"
- "并发请求会不会有问题？"
