# pinmap MCP — «что и на каком пине висит»

Локальный MCP-сервер (stdio, JSON-RPC 2.0, **без внешних зависимостей**),
который отдаёт агенту проверенную карту пинов OMDAZZ / EP4CE6E22C8:
тип вывода, штатную функцию платы и текущую обвязку стенда (камера, монитор,
телеметрия).

## Зачем

* не выдумывать пины и не путать `PIN_4 = GND` с пользовательским I/O;
* сразу видеть конфликт («строб на 144, а 144 — подсветка монитора»);
* получать список свободных валидных I/O в нужном диапазоне.

## Состав

```text
server.py           # MCP-сервер (stdio)
build_pinmap.py     # генератор pinmap.json
pinmap.json         # данные (генерируются)
```

`pinmap.json` собирается из:

| Источник | Что даёт |
|---|---|
| `.pin`-отчёт Quartus (`make build` → `build/output_files/*.pin`) | `kind`: io / power / gnd / config / clock + банк |
| `board/omdazz_cyclone_iv/pinout/pinmap.md` | штатная функция вывода (`board`) |
| `experiments/003_tft_parallel_bus/README.md` | монитор: DB[0..15], RS/WR/RD/CS, res, backlight, тач, SD |
| `experiments/004_rolling_shutter/README.md` | камера: XCLK/VSYNC/HREF/PCLK/D[7:0], SCCB |
| текущая прошивка | `uart_tx` (PIN_42), `light_out` (PIN_144), KEY4, LED3 |

Пересобрать после изменения распиновки:

```bash
python3 tools/mcp/pinmap/build_pinmap.py
# или с явным отчётом:
python3 tools/mcp/pinmap/build_pinmap.py --pin-report \
        experiments/004_rolling_shutter/build/output_files/004_rolling_shutter.pin
```

## Инструменты

| Tool | Аргументы | Что возвращает |
|---|---|---|
| `pin_get` | `pin` | тип, банк, функция на плате, обвязка стенда, пометки (GND/config/свободен) |
| `pin_list` | `device`, `kind`, `free`, `range` | таблица пинов |
| `pin_free` | `range`, `count` | свободные валидные I/O |
| `pin_check` | `assignments` | `{signal: pin}` → конфликты, GND/VCC/config, дубли |
| `pin_suggest` | `role`, `range`, `count` | кандидаты под роль (сначала без штатной функции, потом SDRAM-линии) |
| `stand_show` | — | сводка по устройствам + конфликты |

Ресурсы: `pinmap://current` (JSON), `pinmap://table` (Markdown).

## Регистрация в OpenCode

```json
"pinmap": {
  "type": "local",
  "command": ["/usr/bin/python3",
              "/home/l/projects/Altera_FPGA_OMDAZZ/tools/mcp/pinmap/server.py"]
}
```

в `opencode.json` → `mcp.servers`. После правки конфига нужен перезапуск
сессии.

## Как править данные

1. Поменяли проводку — правьте `STAND` в `build_pinmap.py`, пересоберите
   `pinmap.json`.
2. Для «опциональных» линий (тач/SD монитора) ставьте `optional=True` —
   `pin_free`/`pin_suggest` по умолчанию такие пины не предлагают, но
   `pin_list` показывает с пометкой `(опц.)`.
3. Источник истины по типам пинов — `.pin`-отчёт Quartus, не догадки.

## Проверка

```bash
printf '%s\n' \
 '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
 '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"pin_get","arguments":{"pin":42}}}' \
 | python3 tools/mcp/pinmap/server.py
```

Ожидаемый ответ на `pin_get(42)`: `io`, банк 3, `SDRAM LDQM`,
`telemetry.uart_tx`.
