from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 数据库配置
DATABASE_URL = "postgresql://loguser:logpass@localhost:5432/logdb"

# 创建数据库引擎
engine = create_engine(DATABASE_URL)

# 创建SessionLocal类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base类
Base = declarative_base()


def get_db():
    """
    数据库依赖注入函数
    用于FastAPI的依赖注入系统
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

