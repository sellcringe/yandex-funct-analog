import argparse
import json
import importlib
import sys
import datetime
import traceback


def log_json(event_name, **kwargs):
    """Structured JSON log compatible with Loki/Grafana."""
    print(json.dumps({
        "ts": datetime.datetime.utcnow().isoformat(),
        "event": event_name,
        **kwargs
    }))


def main():
    p = argparse.ArgumentParser(description="Run a function via CLI or CRON")
    p.add_argument("path", help="functions.<name> or web_functions.<name>")
    p.add_argument("--event", default="{}",
                   help="JSON string, e.g. '{\"id\":123}'")
    args = p.parse_args()

    # импорт функции
    try:
        mod = importlib.import_module(f"{args.path}.main")
    except ModuleNotFoundError:
        sys.exit(f"Module not found: {args.path}.main")

    # парсим event
    try:
        event = json.loads(args.event)
    except Exception as e:
        sys.exit(f"Invalid --event JSON: {e}")

    # определяем источник вызова (cron vs cli)
    source = "cron"

    ctx = {
        "source": source,
        "function": args.path
    }

    # 🔥 LOG: старт выполнения
    log_json("function_start", function=args.path, type=source)

    try:
        # основной вызов
        if hasattr(mod, "run"):
            result = mod.run(event, ctx)
        elif hasattr(mod, "handler"):
            result = mod.handler(event, None)
        else:
            raise RuntimeError("Neither run(event, ctx) nor handler(event, context) found")

        # LOG: успешное завершение
        log_json("function_end", function=args.path, result=result)

    except Exception as e:
        # LOG: ошибка
        log_json(
            "function_error",
            function=args.path,
            error=str(e),
            traceback=traceback.format_exc()
        )
        raise

    # равномерный вывод результата для CLI
    if not isinstance(result, dict):
        result = {"result": result}

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import os
    main()
