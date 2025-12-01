import datetime
import importlib
import json
import os
import pkgutil
import time
from starlette.middleware.base import BaseHTTPMiddleware

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from common.settings import settings

app = FastAPI(title="Functions Hub", version="1.0.0")

@app.get("/health")
def health():
    return {"ok": True, "env": settings.APP_ENV}

def _iter_subpackages(root_pkg_name: str):
    """Yield package names (one level) under root."""
    pkg = importlib.import_module(root_pkg_name)
    for sub in pkgutil.iter_modules(pkg.__path__):
        if sub.ispkg:
            yield sub.name

def _load_func_config(func_dir: str):
    """Читает func.yaml, если есть. Возвращает dict."""
    cfg_path = os.path.join(func_dir, "func.yaml")

    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    else:
        cfg = {}

    # defaults
    fname = os.path.basename(func_dir)
    cfg.setdefault("name", fname)
    cfg.setdefault("expose_http", True)

    return cfg

def _resolve_callable(mod):
    """Return callable(event, ctx) for run() or handler()."""
    if hasattr(mod, "run"):
        return getattr(mod, "run")
    if hasattr(mod, "handler"):
        def call(event, ctx, _m=mod):
            # YC-style shim
            res = _m.handler(event, None)
            # normalize
            if isinstance(res, dict) and "statusCode" in res and "body" in res:
                return {"ok": (res.get("statusCode", 200) < 300), "raw": res}
            return res
        return call
    raise AttributeError("Neither run(event, ctx) nor handler(event, context) found")

# def _should_expose(mod):
#     """Optional per-function flag (default True)."""
#     # If module defines EXPOSE_HTTP explicitly, honor it; otherwise True
#     return getattr(mod, "EXPOSE_HTTP", True)

# Register HTTP routes from web_functions/*
try:
    for fname in _iter_subpackages("functions"):
        func_dir = os.path.join("functions", fname)
        cfg = _load_func_config(func_dir)
        if not cfg.get("expose_http", True):
            print(f"🚫 HTTP disabled for {fname}")
            continue

        mod = importlib.import_module(f"functions.{fname}.main")

        # if not _should_expose(mod):
        #     continue
        call = _resolve_callable(mod)

        async def endpoint(request: Request, _call=call, _fname=fname):
            started = time.time()
            try:
                content_type = request.headers.get("content-type", "")
                if content_type.startswith("application/json"):
                    body = await request.json()
                else:
                    # allow empty or form-encoded bodies
                    try:
                        body = await request.json()
                    except Exception:
                        body = {}
                print(json.dumps({
                    "ts": datetime.datetime.utcnow().isoformat(),
                    "type": "function_http_start",
                    "function": _fname,
                    "body": body
                }))
                ctx = {"source": "http", "function": _fname}
                result = _call(body, ctx) or {"ok": True}
                took = round((time.time() - started) * 1000)
                print(json.dumps({
                    "ts": datetime.datetime.utcnow().isoformat(),
                    "type": "function_http_end",
                    "function": _fname,
                    "took_ms": took,
                    "result": result
                }))
                if isinstance(result, dict):
                    result.setdefault("took_ms", took)
                return JSONResponse(result)
            except Exception as e:
                print(json.dumps({
                    "ts": datetime.datetime.utcnow().isoformat(),
                    "type": "function_http_error",
                    "function": _fname,
                    "error": str(e)
                }))
                return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

        app.add_api_route(f"/f/{fname}", endpoint, methods=["POST"], name=fname)

except Exception as e:
    # web_functions пакета может не быть при первом старте — это ок
    print(e)
    pass


class LogRequestsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        body = await request.body()
        print(f"[HTTP-IN] {request.url.path} body={body.decode('utf-8')}")

        response = await call_next(request)
        took = int((time.time() - start) * 1000)

        print(f"[HTTP-OUT] {request.url.path} status={response.status_code} took={took}ms")

        return response


app.add_middleware(LogRequestsMiddleware)