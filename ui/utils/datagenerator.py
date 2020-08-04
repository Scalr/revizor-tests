import uuid
import random
import string
import typing as tp


def generate_name(prefix: str = '', length: int = 12) -> str:
    if prefix:
        length -= 1
    name = ''.join(random.choice(string.ascii_lowercase) for _ in range(length - len(prefix)))
    if prefix:
        return f"{prefix}-{name}"
    return name


def generate_uuid() -> str:
    return str(uuid.uuid4())


