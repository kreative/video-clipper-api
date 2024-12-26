from src.models import User
from src.utils.resiliance import retry_on_db_error


@retry_on_db_error
def get_user_by_id(user_id: int) -> User:
    if not user_id:
        return None

    return User.query.get(user_id)


def update_user(user_id, markdown_template, prompt):
    user = get_user_by_id(user_id)

    if not user:
        raise ValueError("User not found")

    user.markdown_template = markdown_template
    user.prompt = prompt

    db.session.commit()

    return user


def onboard_new_user(ksn):
    new_user = User(
        id=ksn,
        prompt="",
        markdown_template="",
    )

    db.session.add(new_user)
    db.session.commit()

    return new_user
