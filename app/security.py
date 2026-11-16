import bcrypt


def hash_password(password: str) -> str:
    data = password.encode("utf-8")[:72]
    return bcrypt.hashpw(data, bcrypt.gensalt()).decode("utf-8")


def check_password(password: str, password_hash: str) -> bool:
    data = password.encode("utf-8")[:72]
    try:
        return bcrypt.checkpw(data, password_hash.encode("utf-8"))
    except ValueError:
        return False
