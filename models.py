from sqlalchemy import create_engine, Column, Integer, String, select, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from log_setup import get_logger

logger = get_logger("models")

# ----------------*** Database Setup ***--------------
# ---------------- app: database_connection -----------
# اتصال به یک فایل SQLite (اگر فایل وجود نداشته باشه، ساخته می‌شه)
engine = create_engine(
    "sqlite:///database.db",
    connect_args={"check_same_thread": False},  # only for sqlite
    echo=True,
)

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


# ----------------------------------------------------

# ----------------*** Session Setup ***---------------
# ---------------- app: database_session --------------
# ساخت جدول‌ها در دیتابیس (فقط اگر وجود نداشته باشن)
Base.metadata.create_all(engine)

# ساخت session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

# -----------------------------------------------------


# ---------------- users: list_all --------------------
def get_all_users__db():
    stmt = select(User.id, User.firstname, User.lastname, User.age)
    try:
        result = session.execute(stmt).all()
    except Exception as e:
        return False, f"Failed to fetch users: {e}", None
    else:
        return True, "users loaded successfully", result
