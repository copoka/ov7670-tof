#!/usr/bin/env python3
"""build_pinmap.py — собрать pinmap.json для MCP-сервера pinmap.

Источники:
  * .pin-отчёт Quartus (тип пина: io/power/gnd/config/clock + банк);
  * BOARD — штатные функции периферии OMDAZZ (pinout/pinmap.md);
  * STAND — текущая обвязка стенда (003 монитор + 004 камера + UART).

Запуск:
    python3 tools/mcp/pinmap/build_pinmap.py [--pin-report PATH] [-o pinmap.json]

Без --pin-report берётся первый найденный
experiments/*/build/output_files/*.pin (он генерируется `make build`).
"""

from __future__ import annotations

import argparse
import glob
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]

# ---- штатные функции платы (pinout/pinmap.md, официальная таблица) ---------
BOARD: dict[int, str] = {
    1: "LCD D1",
    2: "LCD D4",
    3: "LCD D3",
    7: "LCD D6",
    10: "LCD D5",
    11: "LCD D7",
    23: "FPGA_CLK 50 MHz",
    25: "RESET button",
    84: "LED4",
    85: "LED3",
    86: "LED2",
    87: "LED1",
    88: "KEY1 / DIP ckey1",
    89: "KEY2 / DIP ckey2",
    90: "KEY3 / DIP ckey3",
    91: "KEY4 / DIP ckey4",
    98: "I2C_SDA (AT24C08)",
    99: "I2C_SCL (AT24C08)",
    100: "IR receiver",
    101: "VGA_HSYNC (nCEO!)",
    103: "VGA_VSYNC",
    104: "VGA_B",
    105: "VGA_G",
    106: "VGA_R",
    110: "Buzzer",
    112: "I2C SCL",
    113: "I2C SDA",
    114: "UART TXD",
    115: "UART RXD",
    119: "PS2 CLOCK",
    120: "PS2 DATA",
    121: "7-seg SEG1",
    124: "7-seg SEG6",
    125: "7-seg SEG2",
    126: "7-seg SEG5",
    127: "7-seg SEG7",
    128: "7-seg SEG0",
    129: "7-seg SEG3",
    132: "7-seg SEG4",
    133: "7-seg DIG1",
    135: "7-seg DIG2",
    136: "7-seg DIG3",
    137: "7-seg DIG4",
    138: "LCD RW",
    141: "LCD RS",
    142: "LCD D0",
    143: "LCD E",
    144: "LCD D2",
}

# SDRAM (fpga-pinout.jpg / официальная таблица)
SDRAM = {
    28: "SDRAM DQ0", 30: "SDRAM DQ1", 31: "SDRAM DQ2", 32: "SDRAM DQ3",
    33: "SDRAM DQ4", 34: "SDRAM DQ5", 38: "SDRAM DQ6", 39: "SDRAM DQ7",
    54: "SDRAM DQ8", 53: "SDRAM DQ9", 52: "SDRAM DQ10", 51: "SDRAM DQ11",
    50: "SDRAM DQ12", 49: "SDRAM DQ13", 46: "SDRAM DQ14", 44: "SDRAM DQ15",
    76: "SDRAM A0", 77: "SDRAM A1", 80: "SDRAM A2", 83: "SDRAM A3",
    68: "SDRAM A4", 67: "SDRAM A5", 66: "SDRAM A6", 65: "SDRAM A7",
    64: "SDRAM A8", 60: "SDRAM A9", 75: "SDRAM A10", 59: "SDRAM A11",
    73: "SDRAM BS0", 74: "SDRAM BS1", 42: "SDRAM LDQM", 55: "SDRAM UDQM",
    58: "SDRAM CKE", 43: "SDRAM CLK", 72: "SDRAM CS#", 71: "SDRAM RAS#",
    70: "SDRAM CAS#", 69: "SDRAM WE#",
}
BOARD.update(SDRAM)

# ---- устройства стенда (модели/интерфейсы) ----------------------------------
DEVICES: dict[str, dict] = {
    "camera": {
        "model": "OV7670 (QQVGA 160x120)",
        "iface": "DVP 8-бит + SCCB (I2C-совместимый)",
        "config": {
            "table": "ov7670_regs (REGS_TABLE=0) — полная RGB565, AGC/AEC ON, гамма, AWB (проверено 001/002)",
            "format": "RGB565 (2 байта/пиксель), QQVGA 160x120",
            "luma": "для серого вывода: (R + 2G + B)/4",
            "warning": "урезанная ov7670_regs_yuv (AGC/AEC OFF) даёт тёмный кадр (max ~73) — для «вида камеры» не годится",
        },
        "notes": "ПОДТВЕРЖДЕНО 2026-10-22: кадр снимается полностью (19200/19200 байт), QR с листа бумаги виден на TFT (прошивка top_cam_tft).",
    },
    "monitor": {
        "model": "TFT 240x320, 2.4\", 40-pin",
        "controller": "ILI9341-совместимый (работает на железе 2026-10-22; ID не читается — панель write-only)",
        "iface": "Intel-80, 16-бит DB[15:0] + CS/RS/WR/RD, только запись",
        "power": {
            "vcc": "5V платы",
            "gnd": "GND платы",
        },
        "config": {
            "COLMOD": "0x55 (16 bpp, RGB565)",
            "MADCTL": "0x08 (BGR + портрет) — панель нативно BGR; без 0x08 красный/синий меняются местами",
            "cmd_lane": "DB[7:0] (команды на младшем байте)",
            "window": "CASET 0x00..0xEF (0..239), PASET 0x0000..0x013F (0..319), задавать явно",
            "pixel_write": "1 пиксель = 1 16-битная запись; RAMWR (0x2C) перед заливкой",
        },
        "notes": "ПОДТВЕРЖДЕНО на железе 2026-10-22: (1) заливка/кольца/тест углов — цвета и ориентация верные; (2) кадр с OV7670 выводится на TFT (прошивка top_cam_tft, QR с листа виден). Write-only: RDDID/RDID1..3 читаются как 0x00 (RD# не возвращает данные). Питание VCC→5V, GND→GND (2026-10-21). Подсветка горит при high-Z, ПЛИС не управляется. Рабочие прошивки: top_tft_colors / top_tft_rings / top_cam_tft (эксперимент 004).",
    },
    "monitor_touch": {
        "model": "TSC2046",
        "iface": "SPI (clk/cs/din/do + PENIRQ)",
        "notes": "прочитан с шелкографии модуля (003, 2026-09-15); SPI-команды совместимы с XPT2046/HR2046",
    },
    "monitor_sd": {
        "model": "SD-карта на 40-pin модуле",
        "iface": "SPI",
        "notes": "на стенде может не использоваться; линии 103..105 делятся с данными камеры",
    },
    "telemetry": {
        "model": "CH342 (WCH, USB dual serial)",
        "iface": "UART 115200 8N1, /dev/ttyACM1 (канал 0)",
        "notes": "кадр 8-бит отдаётся строками G<addr> <16 hex>",
    },
}

# ---- текущая обвязка стенда -------------------------------------------------
# (device, signal, pin, optional) — optional=True: линия есть в документации
# устройства, но на стенде может не использоваться (SD/тач монитора).
STAND: list[tuple[str, str, int, bool]] = []


def _camera() -> None:
    STAND.extend([
        ("camera", "cam_xclk", 87, False),
        ("camera", "cam_vsync", 88, False),
        ("camera", "cam_href", 89, False),
        ("camera", "cam_pclk", 90, False),
        ("camera", "cam_d7", 98, False),
        ("camera", "cam_d6", 99, False),
        ("camera", "cam_d5", 100, False),
        ("camera", "cam_d4", 101, False),
        ("camera", "cam_d3", 103, False),
        ("camera", "cam_d2", 104, False),
        ("camera", "cam_d1", 105, False),
        ("camera", "cam_d0", 106, False),
        ("camera", "cam_scl", 84, False),
        ("camera", "cam_sda", 85, False),
    ])


def _monitor() -> None:
    # Фактическая разводка DB0..DB15 (прозвонка пользователя, 2026-10-21)
    db = [11, 7, 10, 2, 144, 142, 138, 136, 141, 137, 135, 132, 128, 125, 121, 119]
    for i, p in enumerate(db):
        STAND.append(("monitor", f"tft_db{i}", p, False))
    STAND.extend([
        ("monitor", "tft_rs", 3, False),
        ("monitor", "tft_wr_n", 1, False),
        ("monitor", "tft_rd_n", 143, False),
        ("monitor", "tft_cs_n", 114, False),
        ("monitor", "tft_res_n", 113, False),
    ])
    # тач и SD — из 003, на стенде могут быть не подключены
    STAND.extend([
        ("monitor_touch", "tp_clk", 3, True),
        ("monitor_touch", "tp_cs_n", 2, True),
        ("monitor_touch", "tp_din", 7, True),
        ("monitor_touch", "tp_do", 10, True),
        ("monitor_touch", "tp_irq", 119, True),
        ("monitor_sd", "sd_clk", 103, True),
        ("monitor_sd", "sd_cs_n", 104, True),
        ("monitor_sd", "sd_din", 105, True),
        ("monitor_sd", "sd_do", 120, True),
    ])


def _service() -> None:
    STAND.extend([
        ("board", "clk", 23, False),
        ("board", "rst_n", 25, False),
        ("board", "key4_n", 91, False),
        ("board", "led3_n", 86, False),
        ("telemetry", "uart_tx", 42, False),
        # в 004 строб по умолчанию на 144 — конфликт с подсветкой монитора
        ("strobe", "light_out", 144, False),
    ])


_camera()
_monitor()
_service()

CONFIG_NAMES = {"TDI", "TCK", "TMS", "TDO", "nCE", "nCEO", "nCONFIG",
                "nSTATUS", "CONF_DONE", "MSEL0", "MSEL1", "MSEL2"}
CLOCK_PINS = {23, 24, 25}   # CLK0..CLK3 (выделенные входы тактирования)


def parse_pin_report(path: pathlib.Path) -> dict[int, dict]:
    """Разобрать .pin-отчёт Quartus → {pin: {kind, bank}}."""
    out: dict[int, dict] = {}
    for line in path.read_text(errors="replace").splitlines():
        if ":" not in line:
            continue
        parts = [p.strip() for p in line.split(":")]
        if len(parts) < 4:
            continue
        name, loc = parts[0], parts[1]
        if not re.fullmatch(r"\d{1,3}", loc):
            continue
        pin = int(loc)
        bank = None
        if len(parts) >= 6 and re.fullmatch(r"\d+", parts[5] or ""):
            bank = int(parts[5])

        upper = name.upper()
        if name == "GND" or upper.startswith(("GND", "VSS")):
            kind = "gnd"
        elif upper.startswith(("VCC", "VCCA", "VCCD", "VCCIO", "VCCN")):
            kind = "power"
        elif name in CONFIG_NAMES or "~ALTERA_" in name:
            kind = "config"
        elif pin in CLOCK_PINS:
            kind = "clock"
        else:
            kind = "io"
        out[pin] = {"kind": kind, "bank": bank}
    return out


def build(pin_report: pathlib.Path) -> dict:
    types = parse_pin_report(pin_report)
    pins = []
    for pin in range(1, 145):
        info = types.get(pin)
        kind = info["kind"] if info else "unknown"
        if kind != "unknown" and pin in SDRAM and kind == "io":
            pass
        entry = {
            "pin": pin,
            "kind": kind,
            "bank": (info or {}).get("bank"),
            "board": BOARD.get(pin, ""),
            "stand": [
                {"device": dev, "signal": sig, "optional": opt}
                for dev, sig, p, opt in STAND if p == pin
            ],
        }
        pins.append(entry)

    return {
        "board": "OMDAZZ Cyclone IV",
        "devices": DEVICES,
        "fpga": "EP4CE6E22C8",
        "package": "EQFP-144",
        "generated_from": str(pin_report.relative_to(REPO)),
        "notes": [
            "kind: io | power | gnd | config | clock | unknown",
            "stand[].optional = линия описана для устройства, но может не использоваться",
            "devices = модели/интерфейсы подключённых модулей",
            "board = штатная функция вывода на плате (pinout/pinmap.md)",
        ],
        "pins": pins,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pin-report", default="")
    ap.add_argument("-o", "--out", default=str(HERE / "pinmap.json"))
    args = ap.parse_args()

    if args.pin_report:
        report = pathlib.Path(args.pin_report)
    else:
        cands = sorted(glob.glob(str(REPO / "experiments" / "*" / "build" /
                                  "output_files" / "*.pin")))
        if not cands:
            print("нет .pin-отчёта: сначала соберите любой эксперимент "
                  "(make build) или укажите --pin-report", file=sys.stderr)
            return 2
        report = pathlib.Path(cands[0])

    data = build(report)
    out = pathlib.Path(args.out)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    print(f"OK: {out} ({len(data['pins'])} пинов, источник {report.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
