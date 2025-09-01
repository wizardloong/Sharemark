import hashlib

def get_user_hash(ip: str, userAgent: str) -> str:
    """Создаём уникальный хэш для пользователя на основе IP и User-Agent"""
    raw = f"{ip}:{userAgent}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
