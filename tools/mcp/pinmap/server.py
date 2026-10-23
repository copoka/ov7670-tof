#!/usr/bin/env python3
"""pinmap MCP server — что и на каком пине висит (OMDAZZ / EP4CE6E22C8).

Локальный MCP-сервер (stdio, JSON-RPC 2.0), без внешних зависимостей.

Данные: pinmap.json рядом со скриптом (генерируется build_pinmap.py).
Переопределить путь: PINMAP_FILE=/path/to/pinmap.json.

Инструменты:
  pin_get(pin)                  — всё про один пин
  pin_list(device, kind, free, range)
  pin_free(range, count)        — валидные свободные I/O
  pin_check(assignments)        — конфликты/недопустимые пины для набора сигналов
  pin_suggest(role, range, count)
  stand_show()                  — текущая обвязка стенда

Ресурс: pinmap://current (JSON), pinmap://table (Markdown-таблица).
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import sys

VERSION = "0.1.0"
HERE = pathlib.Path(__file__).resolve().parent
DATA_FILE = pathlib.Path(os.environ.get("PINMAP_FILE", HERE / "pinmap.json"))

DEBUG = os.environ.get("PINMAP_DEBUG", "") not in ("", "0")


def log(*a) -> None:
    if DEBUG:
        print(*a, file=sys.stderr, flush=True)


class Data:
    def __init__(self, path: pathlib.Path) -> None:
        self.mtime = path.stat().st_mtime
        raw = json.loads(path.read_text())
        self.raw = raw
        self.pins: dict[int, dict] = {p["pin"]: p for p in raw["pins"]}
        self.devices: dict[str, dict] = raw.get("devices", {})

    def model(self, device: str) -> str:
        info = self.devices.get(device) or {}
        return info.get("model", "")

    # --- выборки -----------------------------------------------------------
    def free(self, include_optional: bool = False) -> list[dict]:
        """Свободные I/O. include_optional=True — разрешить пины, занятые
        только «опциональными» линиями (тач/SD монитора)."""
        out = []
        for p in self.pins.values():
            if p["kind"] != "io":
                continue
            blocking = [] if include_optional else p["stand"]
            if not blocking:
                out.append(p)
        return sorted(out, key=lambda p: p["pin"])

    @staticmethod
    def parse_range(spec: str | None) -> set[int] | None:
        if not spec:
            return None
        pins: set[int] = set()
        for part in re.split(r"[,;\s]+", spec.strip()):
            if not part:
                continue
            m = re.fullmatch(r"(\d+)\s*(?:\.\.|-|:)\s*(\d+)", part)
            if m:
                a, b = int(m.group(1)), int(m.group(2))
                pins.update(range(min(a, b), max(a, b) + 1))
            elif part.isdigit():
                pins.add(int(part))
            else:
                raise ValueError(f"не понимаю диапазон: {part!r}")
        return pins


DATA: Data | None = None


def data() -> Data:
    """Загрузить данные; перечитывать файл, если он изменился (build_pinmap.py)."""
    global DATA
    try:
        mtime = DATA_FILE.stat().st_mtime
    except OSError:
        mtime = None
    if DATA is None or (mtime is not None and mtime != DATA.mtime):
        DATA = Data(DATA_FILE)
    return DATA


# ---------------------------------------------------------------------------
# форматирование
# ---------------------------------------------------------------------------
def fmt_stand(p: dict) -> str:
    if not p["stand"]:
        return "—"
    out = []
    for s in sorted(p["stand"], key=lambda s: s["device"]):
        mark = " (опц.)" if s.get("optional") else ""
        out.append(f"{s['device']}.{s['signal']}{mark}")
    return ", ".join(out)


def table(rows: list[dict], with_board: bool = True) -> str:
    head = f"{'PIN':>4}  {'ТИП':<7} {'БАНК':>4}  {'НА ПЛАТЕ':<22} НА СТЕНДЕ"
    lines = [head, "-" * len(head)]
    for p in rows:
        bank = "" if p["bank"] is None else str(p["bank"])
        board = p["board"] or ""
        if not with_board:
            board = ""
        lines.append(f"{p['pin']:>4}  {p['kind']:<7} {bank:>4}  {board:<22} {fmt_stand(p)}")
    if len(lines) == 2:
        lines.append("(пусто)")
    return "\n".join(lines)


def conflicts() -> list[str]:
    """Пины, на которых больше одного необязательного источника."""
    issues = []
    for p in data().pins.values():
        act = [s for s in p["stand"] if not s.get("optional")]
        drivers = [s for s in act if not s["signal"].startswith(("cam_d", "tft_db"))]
        if len(act) > 1:
            issues.append(
                f"PIN_{p['pin']}: " + ", ".join(f"{s['device']}.{s['signal']}" for s in act)
                + ("  ← несколько активных сигналов" if len(drivers) > 1 else "  ← шина/два устройства")
            )
    return issues


# ---------------------------------------------------------------------------
# инструменты
# ---------------------------------------------------------------------------
def tool_pin_get(args: dict) -> str:
    try:
        n = int(args.get("pin"))
    except (TypeError, ValueError):
        raise ValueError("нужен параметр pin (число, например 42)")
    p = data().pins.get(n)
    if p is None:
        raise ValueError(f"пина {n} нет (диапазон 1..144)")
    lines = [
        f"PIN_{n}",
        f"  тип:    {p['kind']}" + (f"  (I/O банк {p['bank']})" if p['kind'] == 'io' and p['bank'] else ""),
        f"  плата:  {p['board'] or '— (не задействован штатной периферией)'}",
        f"  стенд:  {fmt_stand(p)}",
    ]
    if p["kind"] in ("gnd", "power"):
        lines.append("  ⚠ это не пользовательский вывод: подключать сигналы нельзя")
    if p["kind"] == "config":
        lines.append("  ⚠ конфигурационный/служебный пин (JTAG/AS/nCEO) — использовать как I/O можно только осознанно")
    act = [s for s in p["stand"] if not s.get("optional")]
    opt = [s for s in p["stand"] if s.get("optional")]
    if p["kind"] == "io" and not act:
        if opt:
            lines.append("  ✔ свободен (опц.: "
                         + ", ".join(f"{s['device']}.{s['signal']}" for s in opt) + ")")
        else:
            lines.append("  ✔ свободен")
    return "\n".join(lines)


def tool_pin_list(args: dict) -> str:
    dev = args.get("device")
    kind = args.get("kind")
    free = args.get("free")
    rng = Data.parse_range(args.get("range"))
    rows = []
    for p in data().pins.values():
        if rng is not None and p["pin"] not in rng:
            continue
        if kind and p["kind"] != kind:
            continue
        if dev:
            if not any(dev.lower() in s["device"].lower() for s in p["stand"]):
                continue
        if free:
            if p["kind"] != "io" or p["stand"]:
                continue
        rows.append(p)
    return table(sorted(rows, key=lambda p: p["pin"]))


def tool_pin_free(args: dict) -> str:
    rng = Data.parse_range(args.get("range"))
    count = args.get("count")
    inc = bool(args.get("include_optional"))
    rows = [p for p in data().free(inc) if rng is None or p["pin"] in rng]
    if count:
        rows = rows[: int(count)]
    if not rows:
        return "свободных I/O в заданном диапазоне нет"
    return f"свободных I/O: {len(rows)}\n" + table(rows)


def tool_pin_check(args: dict) -> str:
    raw = args.get("assignments")
    if not raw:
        raise ValueError("нужен assignments: {\"signal\": pin, ...} или [{\"signal\": ..., \"pin\": ...}]")
    items: list[tuple[str, int]] = []
    if isinstance(raw, dict):
        for sig, pin in raw.items():
            items.append((str(sig), int(pin)))
    elif isinstance(raw, list):
        for it in raw:
            items.append((str(it.get("signal", "?")), int(it.get("pin"))))
    else:
        raise ValueError("assignments должен быть объектом или массивом")

    lines = []
    bad = 0
    used: dict[int, str] = {}
    for sig, pin in items:
        p = data().pins.get(pin)
        if p is None:
            lines.append(f"✗ {sig} → PIN_{pin}: пина нет (1..144)")
            bad += 1
            continue
        problems = []
        if p["kind"] in ("gnd", "power"):
            problems.append(f"это {p['kind']} — сигнал подключать нельзя")
        if p["kind"] == "config":
            problems.append("служебный/config-пин")
        act = [s for s in p["stand"] if not s.get("optional")
               and s["signal"] != sig]
        if act:
            problems.append("занят на стенде: " + ", ".join(f"{s['device']}.{s['signal']}" for s in act))
        if pin in used:
            problems.append(f"дубль с {used[pin]}")
        used[pin] = sig
        if problems:
            bad += 1
            lines.append(f"✗ {sig} → PIN_{pin}: " + "; ".join(problems))
        else:
            extra = ""
            opt = [s for s in p["stand"] if s.get("optional")]
            if opt:
                extra = "  (опц.: " + ", ".join(f"{s['device']}.{s['signal']}" for s in opt) + ")"
            lines.append(f"✓ {sig} → PIN_{pin} ({p['board'] or 'свободный I/O'}){extra}")

    head = f"проверено {len(items)} назначений, проблем: {bad}"
    return head + "\n" + "\n".join(lines)


def tool_pin_suggest(args: dict) -> str:
    role = str(args.get("role", "")).strip()
    rng = Data.parse_range(args.get("range"))
    count = int(args.get("count") or 5)
    inc = bool(args.get("include_optional"))
    rows = [p for p in data().free(inc) if rng is None or p["pin"] in rng]
    # приоритет: без штатной функции -> SDRAM-линии -> прочее
    def score(p: dict) -> tuple[int, int]:
        if not p["board"]:
            return (0, p["pin"])
        if p["board"].startswith("SDRAM"):
            return (1, p["pin"])
        return (2, p["pin"])
    rows.sort(key=score)
    rows = rows[:count]
    title = f"кандидаты под «{role}»:" if role else "кандидаты:"
    return title + "\n" + table(rows)


def tool_stand_show(_: dict) -> str:
    by_dev: dict[str, list[tuple[str, int]]] = {}
    for p in data().pins.values():
        for s in p["stand"]:
            by_dev.setdefault(s["device"], []).append(
                (s["signal"] + (" (опц.)" if s.get("optional") else ""), p["pin"]))
    lines = []
    for dev in sorted(by_dev):
        info = data().devices.get(dev) or {}
        title = dev
        if info.get("model"):
            title += f" — {info['model']}"
        if info.get("iface"):
            title += f" ({info['iface']})"
        lines.append(f"## {title}")
        if info.get("notes"):
            lines.append(f"   {info['notes']}")
        if info.get("power"):
            pw = ", ".join(f"{k.upper()} → {v}" for k, v in info["power"].items())
            lines.append(f"   питание: {pw}")
        for sig, pin in sorted(by_dev[dev], key=lambda x: x[1]):
            lines.append(f"  {sig:<26} PIN_{pin}")
        lines.append("")
    cf = conflicts()
    if cf:
        lines.append("## ⚠ конфликты на пинах")
        lines.extend("  " + c for c in cf)
    return "\n".join(lines).rstrip()


TOOLS = {
    "pin_get": {
        "description": "Всё про один пин FPGA: тип (io/power/gnd/config/clock), банк, "
                       "штатная функция на плате, что подключено на стенде.",
        "inputSchema": {
            "type": "object",
            "properties": {"pin": {"type": "integer", "description": "номер пина 1..144"}},
            "required": ["pin"],
        },
        "fn": tool_pin_get,
    },
    "pin_list": {
        "description": "Таблица пинов с фильтрами: device (camera/monitor/telemetry/...), "
                       "kind (io/power/gnd/config/clock), free (только свободные I/O), range (\"1..83\").",
        "inputSchema": {
            "type": "object",
            "properties": {
                "device": {"type": "string"},
                "kind": {"type": "string"},
                "free": {"type": "boolean"},
                "range": {"type": "string", "description": "например \"1..83\" или \"55,60,83\""},
            },
        },
        "fn": tool_pin_list,
    },
    "pin_free": {
        "description": "Список валидных свободных I/O (не занятых ни платой, ни стендом).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "range": {"type": "string"},
                "count": {"type": "integer"},
            },
        },
        "fn": tool_pin_free,
    },
    "pin_check": {
        "description": "Проверить набор назначений {signal: pin} на конфликты: GND/VCC/config, "
                       "занятость на стенде, дубли.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "assignments": {
                    "type": ["object", "array"],
                    "description": "{\"uart_tx\": 42} или [{\"signal\":\"uart_tx\",\"pin\":42}]",
                },
            },
            "required": ["assignments"],
        },
        "fn": tool_pin_check,
    },
    "pin_suggest": {
        "description": "Предложить свободные пины под роль (строб, UART и т.п.) с учётом диапазона.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "role": {"type": "string"},
                "range": {"type": "string"},
                "count": {"type": "integer"},
            },
        },
        "fn": tool_pin_suggest,
    },
    "stand_show": {
        "description": "Текущая обвязка стенда по устройствам (камера, монитор, телеметрия, "
                       "служебные) + конфликты.",
        "inputSchema": {"type": "object", "properties": {}},
        "fn": tool_stand_show,
    },
}


# ---------------------------------------------------------------------------
# MCP (stdio, JSON-RPC 2.0)
# ---------------------------------------------------------------------------
def ok(id_, result) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def err(id_, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def handle(msg: dict):
    method = msg.get("method", "")
    id_ = msg.get("id")
    params = msg.get("params") or {}

    if method == "initialize":
        ver = params.get("protocolVersion") or "2024-11-05"
        return ok(id_, {
            "protocolVersion": ver,
            "capabilities": {"tools": {}, "resources": {}},
            "serverInfo": {"name": "pinmap", "version": VERSION},
        })
    if method in ("notifications/initialized", "initialized"):
        return None
    if method == "ping":
        return ok(id_, {})
    if method == "tools/list":
        return ok(id_, {"tools": [
            {"name": name, "description": spec["description"], "inputSchema": spec["inputSchema"]}
            for name, spec in TOOLS.items()
        ]})
    if method == "tools/call":
        name = params.get("name")
        spec = TOOLS.get(name)
        if not spec:
            return err(id_, -32602, f"неизвестный инструмент: {name}")
        try:
            text = spec["fn"](params.get("arguments") or {})
            return ok(id_, {"content": [{"type": "text", "text": text}], "isError": False})
        except Exception as exc:  # noqa: BLE001 — вернуть ошибку клиенту, не падать
            return ok(id_, {"content": [{"type": "text", "text": f"ошибка: {exc}"}], "isError": True})
    if method == "resources/list":
        return ok(id_, {"resources": [
            {"uri": "pinmap://current", "name": "pinmap.json",
             "description": "Полные данные пинов (JSON)", "mimeType": "application/json"},
            {"uri": "pinmap://table", "name": "pinmap table",
             "description": "Таблица пинов (Markdown)", "mimeType": "text/markdown"},
        ]})
    if method == "resources/read":
        uri = params.get("uri")
        if uri == "pinmap://current":
            return ok(id_, {"contents": [{"uri": uri, "mimeType": "application/json",
                                          "text": json.dumps(data().raw, ensure_ascii=False)}]})
        if uri == "pinmap://table":
            md = "| PIN | тип | банк | плата | стенд |\n|---|---|---|---|---|\n"
            for p in sorted(data().pins.values(), key=lambda p: p["pin"]):
                md += f"| {p['pin']} | {p['kind']} | {p['bank'] or ''} | {p['board']} | {fmt_stand(p)} |\n"
            return ok(id_, {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": md}]})
        return err(id_, -32602, f"неизвестный ресурс: {uri}")
    if id_ is None:
        return None
    return err(id_, -32601, f"метод не поддерживается: {method}")


def main() -> int:
    if not DATA_FILE.exists():
        print(f"нет {DATA_FILE}: запустите build_pinmap.py", file=sys.stderr)
        return 2
    log(f"pinmap: {DATA_FILE}")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as exc:
            print(json.dumps(err(None, -32700, f"parse error: {exc}")), flush=True)
            continue
        try:
            resp = handle(msg)
        except Exception as exc:  # noqa: BLE001
            log("unhandled:", exc)
            resp = err(msg.get("id"), -32603, f"internal error: {exc}")
        if resp is not None:
            print(json.dumps(resp, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
