from fastapi import Request

def get_client_ip(request: Request) -> str:
    # Cloudflare
    if cf_ip := request.headers.get("CF-Connecting-IP"):
        return cf_ip.strip()

    # Caddy / Nginx / HAProxy
    if xff := request.headers.get("X-Forwarded-For"):
        # может быть список IP через запятую
        return xff.split(",")[0].strip()

    if real_ip := request.headers.get("X-Real-IP"):
        return real_ip.strip()

    # Фоллбек — IP ближайшего прокси (например, 127.0.0.1 при docker-compose)
    return request.client.host
