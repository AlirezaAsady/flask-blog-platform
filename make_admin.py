from models import session, User
from log_setup import get_logger

logger = get_logger("make_admin")

try:
    user_id = int(input("user id to promote: "))
except (ValueError, TypeError):
    logger.warning("Invalid input for user_id")
    print("Invalid input, please enter a number")
else:
    user = session.query(User).filter(User.id == user_id).one_or_none()

    if user:
        try:
            user.is_admin = True
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("Error in make_admin: %s", e)
            print("Error")
        else:
            admin_count = session.query(User).filter(User.is_admin == True).count()
            logger.info(
                "User promoted to admin (user_id=%s, username=%s). Total admins now: %s",
                user.id,
                user.username,
                admin_count,
            )
            print(f"{user.username} is now admin. Total admins: {admin_count}")
    else:
        logger.warning("Attempted to promote non-existent user_id=%s", user_id)
        print("user not found")
