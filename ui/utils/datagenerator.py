import uuid
import random
import string
import typing as tp


def generate_name(prefix: str = '', length: int = 12) -> str:
    return prefix + ''.join(random.choice(string.ascii_lowercase) for _ in range(length - len(prefix)))


def generate_uuid() -> str:
    return str(uuid.uuid4())


