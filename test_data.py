"""
生成更多测试数据的脚本
运行后可以产生大量日志用于测试性能优化
"""
import random
from datetime import datetime, timedelta

PATHS = [
    "/product/12345", "/product/67890", "/product/11111", 
    "/product/22222", "/product/33333", "/product/44444",
    "/cart/add", "/cart/remove", "/cart/view",
    "/checkout", "/payment", "/order/confirm",
    "/user/profile", "/user/orders", "/search"
]

STATUS_CODES = [200, 200, 200, 200, 200, 200, 200, 200, 404, 500, 503]

def generate_logs(num_logs=10000, output_file="large_test_logs.txt"):
    """生成大量测试日志"""
    start_time = datetime(2024, 1, 15, 10, 0, 0)
    
    with open(output_file, 'w') as f:
        for i in range(num_logs):
            timestamp = start_time + timedelta(seconds=i*2)
            user_id = f"user_{random.randint(1000, 1100)}"
            path = random.choice(PATHS)
            response_time = random.randint(50, 2000)
            status_code = random.choice(STATUS_CODES)
            
            log_line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {user_id} | {path} | {response_time}ms | {status_code}\n"
            f.write(log_line)
            
            # 偶尔插入一些错误格式的行
            if random.random() < 0.001:
                f.write("# ERROR LINE\n")
    
    print(f"生成了 {num_logs} 条日志到 {output_file}")

if __name__ == "__main__":
    generate_logs(10000)