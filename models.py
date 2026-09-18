from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base

# ---------------- app: orm_base ----------------------
# create base class for declaring tables
Base = declarative_base()


# -------------------* MODELS *------------------------
# ---------------- models: user -----------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)

    firstname = Column(String(30), nullable=True)
    lastname = Column(String(50), nullable=True)
    age = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<user id= {self.id}: username= {self.username} firstname= {self.firstname} lastname= {self.lastname} age= {self.age}>"
