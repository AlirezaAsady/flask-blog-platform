from sqlalchemy import create_engine, Column, Integer, String, select, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
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


# -------------------* USERS *-------------------------
# ---------------- users: list_all --------------------
def get_all_users__db():
    stmt = select(User.id, User.firstname, User.lastname, User.age)
    try:
        result = session.execute(stmt).all()
    except Exception as e:
        return False, f"Failed to fetch users: {e}", None
    else:
        return True, "users loaded successfully", result


# ---------------- users: create ----------------------
def create_user__db(username, password, firstname=None, lastname=None, age=None):
    try:
        new_emp = User(
            username=username,
            password=generate_password_hash(password),
            firstname=firstname,
            lastname=lastname,
            age=age,
        )
        session.add(new_emp)
        session.commit()
        return True, "Registration successful"
    except IntegrityError:
        session.rollback()
        return False, "This username is already taken"
    except Exception as e:
        session.rollback()
        return False, "Something went wrong, please try again"


# ---------------- users: login -----------------------
def login_user__db(username, password):
    stmt = select(User).where(User.username == username)
    result = session.execute(stmt).scalar_one_or_none()

    if result is None:
        return False, "Invalid username or password", None

    if check_password_hash(result.password, password):
        return True, "Login successful", result.id
    else:
        return False, "Invalid username or password", None
