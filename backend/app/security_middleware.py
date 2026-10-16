from starlette.responses import JSONResponse

from app.security import settings


class SecurityHeaders:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def secure_send(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend([
                    (b"cache-control", b"no-store"),
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"x-frame-options", b"DENY"),
                    (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'; base-uri 'none'"),
                ])
                if settings().production:
                    headers.append((b"strict-transport-security", b"max-age=31536000"))
                message["headers"] = headers
            await send(message)

        if settings().production and scope.get("scheme") != "https":
            return await JSONResponse({"detail": "HTTPS is required"}, 400)(scope, receive, secure_send)
        if scope["method"] in {"POST", "PATCH", "PUT", "DELETE"}:
            headers = dict(scope["headers"])
            if headers.get(b"content-type", b"").split(b";")[0].strip().lower() != b"application/json":
                return await JSONResponse({"detail": "Use application/json"}, 415)(scope, receive, secure_send)
            body = b""
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                body += message.get("body", b"")
                if len(body) > 16384:
                    return await JSONResponse({"detail": "Request body too large"}, 413)(scope, receive, secure_send)
                if not message.get("more_body", False):
                    break
            delivered = False

            async def buffered_receive():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": body, "more_body": False}
                return await receive()

            return await self.app(scope, buffered_receive, secure_send)
        return await self.app(scope, receive, secure_send)
