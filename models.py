from sqlalchemy import Column, Integer, String, DateTime, Float
from database import Base


class AccessLog(Base):
    """
    访问日志模型
    存储网站访问日志信息
    """
    __tablename__ = "acess_logs" 

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    path = Column(String, nullable=False)
    response_time = Column(Float, nullable=False)
    status_code = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<AccessLog(id={self.id}, user_id={self.user_id}, path={self.path}, status={self.status_code})>"

