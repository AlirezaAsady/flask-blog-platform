from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    select,
    Text,
    DateTime,
    ForeignKey,
    Table,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
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

    a_profile = relationship(
        "Profile", back_populates="a_user", uselist=False, cascade="all, delete-orphan"
    )
    a_posts = relationship(
        "Post", back_populates="a_user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<user id= {self.id}: username= {self.username} firstname= {self.firstname} lastname= {self.lastname} age= {self.age}>"


# ---------------- models: profile --------------------
class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True)
    bio = Column(Text)
    avatar_url = Column(String(255))

    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    a_user = relationship("User", back_populates="a_profile")


# ---------------# models: post_tags #-----------------
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.post_id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


# ---------------- models: tag ------------------------
class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)

    a_posts = relationship("Post", secondary=post_tags, back_populates="a_tags")


# ---------------- models: post -----------------------
class Post(Base):
    __tablename__ = "posts"

    post_id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    a_user = relationship("User", back_populates="a_posts")
    a_tags = relationship("Tag", secondary=post_tags, back_populates="a_posts")

    def __repr__(self):
        return f"<post id= {self.post_id}: title= {self.title} content= {self.content} created_at= {self.created_at}>"


# ----------------------------------------------------

# ----------------*** Session Setup ***---------------
# ---------------- app: database_session --------------
Base.metadata.create_all(engine)

# ساخت session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

# -----------------------------------------------------


# -------------------* USERS *-------------------------
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


# ---------------- users: list_all --------------------
def get_all_users__db():
    stmt = select(User.id, User.firstname, User.lastname, User.age)
    try:
        result = session.execute(stmt).all()
    except Exception as e:
        return False, f"Failed to fetch users: {e}", None
    else:
        return True, "users loaded successfully", result


# ---------------- users: delete ----------------------
def delete_user__db(uid):
    try:
        user = session.query(User).filter(User.id == uid).one_or_none()
        if not user:
            return False, "کاربر پیدا نشد"

        session.delete(user)
        session.commit()
        return True, "User deleted successfully"
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
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


# ---------------- users: show_one --------------------
def get_user_by_id__db(uid):
    stmt = select(User).where(User.id == uid)
    result = session.execute(stmt).scalar_one_or_none()
    if result is None:
        return False, "user not fond", None
    else:
        return True, "Login user data successful", result


# ---------------- users: update ----------------------
def update_user__db(uid, username, password, firstname=None, lastname=None, age=None):
    stmt = select(User).where(User.id == uid)
    result = session.execute(stmt).scalar_one_or_none()
    if result is None:
        return False, "user not found", None

    try:
        result.username = username
        if password:
            result.password = generate_password_hash(password)
        result.firstname = firstname
        result.lastname = lastname
        result.age = age
        session.commit()
        return True, "update successful", result
    except IntegrityError:
        session.rollback()
        return False, "This username is already taken", None
    except Exception as e:
        session.rollback()
        return False, "Something went wrong, please try again", None


# -----------------------------------------------------


# -------------------* PROFILE *-----------------------
# ---------------- profile: create --------------------
def create_profile__db(uid, bio=None, avatar_url=None):
    try:
        new_profile = Profile(bio=bio, avatar_url=avatar_url, user_id=uid)
        session.add(new_profile)
        session.commit()
        return True, "Create profile successful"
    except IntegrityError as e:
        session.rollback()
        print(f"Error: {e}")
        return False, "شما از قبل پروفایل دارید"
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        return False, "Something went wrong, please try again"


# ---------------- profile: get -----------------------
def get_profile__db(uid):
    try:
        profile = session.query(Profile).filter(Profile.user_id == uid).one_or_none()
        if not profile:
            return True, "پروفایلی ندارید", None
        return True, "load_profile successful", profile
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        return False, "Something went wrong, please try again", None


# ---------------- profile: update --------------------
def update_profile__db(uid, bio=None, avatar_url=None):
    success, message, profile = get_profile__db(uid)
    if not success:
        return False, message, None

    try:
        if bio:
            profile.bio = bio
        if avatar_url:
            profile.avatar_url = avatar_url

        if bio or avatar_url:
            session.commit()
            return True, "update_profile successful"

        return False, "update_profile Not successful"
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        return False, "Something went wrong, please try again"


# -----------------------------------------------------


# -------------------* POSTS *-------------------------
# ---------------- posts: create ---------------------
def create_post__db(uid, title, content):
    try:
        new_post = Post(
            user_id=uid,
            title=title,
            content=content,
        )
        session.add(new_post)
        session.commit()
        return True, "create post successful", new_post
    except Exception as e:
        session.rollback()
        print(f"Error creating post: {e}")
        return False, "Something went wrong, please try again", None


# ---------------- posts: list_by_user ----------------
def get_posts_by_user__db(uid):
    try:
        posts = session.query(Post).filter(Post.user_id == uid).all()
        return True, "Load_post successful", posts
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        return False, "Something went wrong, please try again", None


# ---------------- posts: delete ----------------------
def delete_post__db(pid, uid):
    try:
        post = (
            session.query(Post).filter(Post.post_id == pid, Post.user_id == uid).first()
        )
        if not post:
            return False, "پست یافت نشد یا متعلق به شما نیست"
        session.delete(post)
        session.commit()
        return True, "delete post successful"
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        return False, "Something went wrong, please try again"


# ---------------- posts: update ----------------------
def update_post__db(pid, uid, title, content):
    try:
        post = (
            session.query(Post).filter(Post.post_id == pid, Post.user_id == uid).first()
        )
        if not post:
            return False, "پست یافت نشد یا متعلق به شما نیست"
        post.title = title
        post.content = content
        session.commit()
        return True, "update post successful"
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        return False, "Something went wrong, please try again"


# ---------------- posts: list_all --------------------
def get_all_posts__db(title_filter=None, user_filter=None):
    try:
        query = session.query(Post)

        if user_filter:
            query = query.join(User)

        conditions = []
        if title_filter:
            conditions.append(Post.title.ilike(f"%{title_filter}%"))
        if user_filter:
            conditions.append(User.username.ilike(f"%{user_filter}%"))

        if conditions:
            query = query.filter(*conditions)

        posts = query.order_by(Post.created_at.desc()).all()
        return True, "All posts loaded successfully", posts
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        return False, "Something went wrong, please try again", None


# -----------------------------------------------------


# --------------------* Tag *--------------------------
# ------------------ Tag: create ----------------------
def get_or_create_tag__db(tag_name):
    try:
        tag = session.query(Tag).filter(Tag.name == tag_name).one_or_none()
        if tag:
            return tag

        try:
            new_tag = Tag(name=tag_name)
            session.add(new_tag)
            session.flush()
            return new_tag
        except IntegrityError:
            session.rollback()
            return session.query(Tag).filter(Tag.name == tag_name).one()

    except Exception as e:
        session.rollback()
        logger.error(f"Error in get_or_create_tag__db(tag_name={tag_name}): {e}")
        return None


def add_tag_to_post__db(post_id, tag_name):
    try:
        post = session.query(Post).filter(Post.post_id == post_id).one_or_none()
        if not post:
            return False, "پست پیدا نشد"

        tag = get_or_create_tag__db(tag_name)
        if not tag:
            return False, "خطا در ساخت یا پیدا کردن تگ"

        if tag not in post.a_tags:
            post.a_tags.append(tag)
            session.commit()
            return True, "تگ با موفقیت اضافه شد"

        return True, "این تگ از قبل روی این پست وجود دارد"

    except Exception as e:
        session.rollback()
        logger.error(
            f"Error in add_tag_to_post__db(post_id={post_id}, tag_name={tag_name}): {e}"
        )
        return False, "Something went wrong, please try again"


def get_posts_by_tag__db(tag_name):
    try:
        tag = session.query(Tag).filter(Tag.name == tag_name).one_or_none()
        if not tag:
            return True, "تگی با این نام پیدا نشد", []

        return True, "Posts loaded successfully", tag.a_posts

    except Exception as e:
        session.rollback()
        logger.error(f"Error in get_posts_by_tag__db(tag_name={tag_name}): {e}")
        return False, "Something went wrong, please try again", None
