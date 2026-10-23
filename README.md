# ov7670-tof — ToF / rolling shutter на OV7670 (Cyclone IV OMDAZZ)

Исследование: **можно ли измерить глубину/дальность дешёвой камерой OV7670
и импульсным светом**, и что реально физически измеримо.

Проект выделен из `Altera_FPGA_OMDAZZ/experiments/004_rolling_shutter`.
Здесь — изолированная работа по ToF/стробу; общие модули (камера, UART,
пинмап) остаются в родительском репозитории как reference.

## Итог предыдущего этапа (кратко)

* **Direct ToF** (по положению световой полосы) — недостижим: дискретность
  `δd ≈ c·T_row/2 ≈ 9.8 км` (по расчёту).
* **AMCW / iToF** (по фазе модуляции) — недостижим: экспозиция OV7670 ≥
  времени строки, контраст модуляции падает как `sinc(π·f_mod·T_exp)` и
  обращается в ноль уже при `f_mod ≈ 1/T_row`.
* **Что измеримо**: время строки `T_row` по положению полосы от строба,
  тайминг камеры, контраст; **структурированный свет** (TFT-проектор) и
  **лазерная триангуляция** — реалистичные способы получить глубину.

Подробнее — `docs/theory.md`.

## Статус

**Скелет проекта.** Реализация RTL, прошивка и измерения — задача агентов.
Промпт с ТЗ — `docs/PROMPT.md`.

## Быстрый старт (после реализации)

```bash
# симуляция (если установлены)
export SIMULATOR=iverilog
make sim

# сборка (Quartus)
export QUARTUS_ROOTDIR=$HOME/intelFPGA_lite/25.1/quartus/bin
make build

# прошивка
make program

# снять дамп с платы (UART)
python3 scripts/capture_uart.py -p /dev/ttyACM1 -o dump.txt
```

## Структура

```
AGENTS.md            гайд для агентов (правила, факты, структура)
docs/PROMPT.md       ТЗ: что нужно сделать
docs/theory.md       физика rolling shutter / ToF
docs/hardware.md     плата, камера, дисплей, строб, пины
docs/measurements.md измеренные числа
docs/plan.md         дорожная карта (L-уровни)
.opencode/           субагенты и скилы
opencode.json        MCP-серверы (без секретов)
board/               выдержка пинмапа OMDAZZ
tools/mcp/pinmap/    MCP «что на каком пине»
rtl/ tb/ scripts/    реализация (пока пусто)
```

## Требования

* Quartus Prime Lite (Cyclone IV) — сборка/прошивка.
* Icarus Verilog / Verilator — симуляция/линт.
* Python 3 + pyserial — приём UART.
* Плата OMDAZZ (EP4CE6E22C8N), OV7670, TFT 240×320, внешняя LED-лента + MOSFET.

## Лицензия

MIT (см. `LICENSE`).
