# Закупка комплектующих (Ozon)

Список собран с реальной выдачи Ozon **2026-10-23**. Цены и наличие меняются —
перед заказом сверяй по ссылке. Все ссылки ведут на карточку товара.

## Что именно нужно и почему

| Узел | Зачем | Критичные параметры |
|---|---|---|
| MOSFET N-канал | ключ low-side для ленты | **logic-level**: `Vgs(th) ≤ 2.5 В`, `Rds(on)` нормирован при 4 В (иначе от 3.3 В ПЛИС не откроется) |
| LED-лента 12 В | источник строба | **неадресная**, постоянного напряжения, один цвет; холодный белый 6000–6500 K — максимум яркости |
| БП 12 В | питание ленты | 5 А с запасом (лента потребляет 0.4–1.5 А на метр) |
| Резисторы | затвор 100 Ω + подтяжка 10 кΩ | набор 0.25 Вт, 1 % |
| Макетка + провода | сборка | 830 точек; Dupont |
| ИК-светодиод 850 нм | ИК-вариант | **только после снятия IR-cut с OV7670** |
| Лазер 650 нм | триангуляция / структурный свет | линия, 5 мВт, 3–5 В |

## 1. MOSFET (ключ)

**Брать (logic-level):**

| Позиция | Цена | Рейтинг | Ссылка |
|---|---|---|---|
| 2 шт IRLZ44N, N-канал 55 В 47 А, TO-220AB (YANXINLIANG) | **225 ₽** | 4.9 / 42 | https://www.ozon.ru/product/2-shtuki-tranzistor-irlz44n-n-kanal-55v-47a-logic-to-220ab-yanxinliang-644920392/ |
| 2 шт IRLZ44N | 240 ₽ | 5.0 / 3 | https://www.ozon.ru/product/2sht-irlz44n-tranzistor-5575462279/ |
| IRLZ44N TO-220, 55 В 41 А | 245 ₽ | 5.0 / 6 | https://www.ozon.ru/product/tranzistor-irlz44n-to-220-mosfet-tranzistor-n-ch-55v-41a-3579490435/ |
| IRL540N TO-220, 100 В 36 А | 245 ₽ | 5.0 / 4 | https://www.ozon.ru/product/tranzistor-irl540n-to-220-mosfet-tranzistor-n-ch-100v-36a-3579489439/ |
| **10 шт IRL540N** (запас, самый выгодный) | 285 ₽ | 5.0 / 5 | https://www.ozon.ru/product/10sht-upak-irl540n-2793060072/ |
| FQP30N06L TO-220, 60 В 32 А (logic-level) | 377 ₽ | 5.0 / 3 | https://www.ozon.ru/product/tranzistor-fqp30n06l-to-220-mosfet-n-ch-60v-32a-1634336916/ |

Обвязка: затвор ← GPIO через **100 Ω**, затвор → GND через **10 кΩ** (чтобы
ключ закрывался, когда пин в Z). Исток → GND платы, сток → минус ленты,
плюс ленты → +12 В БП. **Общий GND** БП и платы обязателен.

> Про 3.3 В: IRLZ44N/IRL540N нормируются при `Vgs = 4…5 В`. При 3.3 В они
> открываются, но `Rds(on)` растёт примерно вдвое (≈0.05 Ω) — для 1–2 А
> нормально. Если нужен запас — поставить мелкий драйвер затвора или
> поднять затвор до 5 В через повторитель.

## 2. Светодиодная лента 12 В (неадресная)

| Позиция | Цена | Рейтинг | Ссылка |
|---|---|---|---|
| Feron LS603, 4.8 Вт/м, **6500 K** холодный белый, 5 м | **393 ₽** | 4.9 / 8 325 | https://www.ozon.ru/product/svetodiodnaya-lenta-12v-5-metrov-4-8-vt-m-6500k-holodnyy-belyy-svet-feron-ls603-27603-553677171/ |
| Feron LS612, 9.6 Вт/м, 4000 K, 5 м | **690 ₽** | 4.9 / 8 325 | https://www.ozon.ru/product/svetodiodnaya-lenta-12v-5-metrov-9-6-vt-m-4000k-neytralnyy-belyy-svet-feron-ls612-41448-553677123/ |
| Feron LS616, 17 Вт/м, 4000 K, 5 м (максимум) | 808 ₽ | 4.9 / 8 325 | https://www.ozon.ru/product/svetodiodnaya-lenta-12v-5-metrov-17-vt-m-4000k-neytralnyy-belyy-svet-feron-ls616-41530-553677141/ |
| 2835, 60 led/m, 12 В, 24 Вт / 5 м (бюджет) | 301 ₽ | 4.8 | https://www.ozon.ru/product/svetodiodnaya-lenta-teplyy-belyy-svet-3300k-dlina-5m-ip22-smd-2835-60led-m-12v-dc-24w-ot-dled-2168520269/ |

Практика: режем **0.5–1.5 м** и гоняем короткими импульсами. Ток ≈ `P_уд × L / 12`:
1 м ленты 9.6 Вт/м → 0.8 А, 1 м 17 Вт/м → 1.4 А. Для строба это и есть
нужная яркость; всю катушку не включаем.

## 3. Блок питания 12 В

| Позиция | Цена | Рейтинг | Ссылка |
|---|---|---|---|
| DLED Lite 60 Вт 12 В **5 А**, 5.5×2.1 | **200 ₽** | 4.7 / 3 219 | https://www.ozon.ru/product/lite-blok-pitaniya-dlya-svetodiodnoy-lenty-i-neona-60w-12v-5a-razem-5-5x2-1mm-brend-dled-3543815802/ |
| Универсальный 12 В 5 А, 5.5×2.5 | 492 ₽ | 4.9 / 26 268 | https://www.ozon.ru/product/universalnyy-blok-pitaniya-12v-5a-bez-indikatora-raboty-shteker-5-5h2-5mm-podhodit-dlya-tv-1330651077/ |
| DLED 12 В 60 Вт 5 А | 528 ₽ | 4.8 / 663 | https://www.ozon.ru/product/blok-pitaniya-dlya-lent-i-neona-ot-dled-12v-60w-5a-2156564360/ |
| 12 В 2 А (если лента ≤ 1 м) | 215 ₽ | 4.9 / 16 653 | https://www.ozon.ru/product/blok-pitaniya-12v-2a-dlya-trikolor-pristavki-dlya-routera-kamer-videonablyudeniya-858265592/ |

Бери вариант **5 А** — дешевле 2-амперного и с запасом на импульс.

## 4. Резисторы

| Позиция | Цена | Рейтинг | Ссылка |
|---|---|---|---|
| Комплект 0.25 Вт 1 %, 30 номиналов, 600 шт | **241 ₽** | 5.0 / 74 | https://www.ozon.ru/product/komplekt-rezistorov-0-25vt-1-30-nominalov-20-sht-vsego-600-sht-5686682636/ |
| Набор 0.25 Вт, 10 Ом – 1 МОм, 600 шт | 236 ₽ | 5.0 / 1 366 | https://www.ozon.ru/product/nabor-rezistorov-0-25w-10-om-1-mom-600-shtuk-4702940745/ |
| То же в футляре | 299 ₽ | 5.0 / 1 366 | https://www.ozon.ru/product/nabor-rezistorov-v-futlyare-0-25w-600sht-10-om-1-mom-4703014983/ |

## 5. Макетка и провода

| Позиция | Цена | Рейтинг | Ссылка |
|---|---|---|---|
| Breadboard 830 точек | **258 ₽** | 4.9 / 997 | https://www.ozon.ru/product/bespaechnaya-maketnaya-plata-breadboard-830-tochek-dlya-arduino-stm32-nodemcu-raspberry-1538810601/ |
| Breadboard 400 точек | 177 ₽ | 4.9 / 240 | https://www.ozon.ru/product/bespaechnaya-maketnaya-plata-arduino-breadboard-400-tochek-5236816722/ |
| Провода Dupont 120 шт, 3 вида по 40, 10 см | **247 ₽** | 5.0 / 2 255 | https://www.ozon.ru/product/120-sht-provoda-peremychki-dlya-maketnyh-plat-soedinitelnye-provoda-dlya-moduley-kontrollerov-2078265319/ |
| Dupont папа-папа, 40 см, 40 шт | 198 ₽ | 4.9 / 5 246 | https://www.ozon.ru/product/provod-soedinitelnyy-papa-papa-dupont-40-sm-40-sht-923020921/ |

> ⚠️ Силовой ток ленты (0.8–1.5 А) **не пускай через макетку** — контакты
> подгорят. Силовую часть (БП → сток/исток → лента) паяй или сажай на
> винтовые клеммы; макетка — только для затвора и логики.

## 6. ИК-вариант (опционально)

| Позиция | Цена | Рейтинг | Ссылка |
|---|---|---|---|
| SMD 3535 ИК 3 Вт, 840–850 нм, 5 шт | 349 ₽ | 5.0 | https://www.ozon.ru/product/svetodiod-smd-3535-ik-infrakrasnyy-3-vt-840-850nm-up-5sht-3763833805/ |
| ИК 3 Вт 850 нм, 2 чипа | 251 ₽ | — | https://www.ozon.ru/product/svetodiod-infrakrasnyy-ik-3w-850nm-2-chipa-dlya-kamer-videonablyudeniya-3319593891/ |
| ИК-прожектор 850 нм, 30 м | 572 ₽ | — | https://www.ozon.ru/product/infrakrasnyy-prozhektor-dlya-videonablyudeniya-30-m-850-nm-vodonepronitsaemyy-metallicheskiy-korpus-5965269163/ |
| ИК-прожектор IR-MT-60/18, 850 нм, 35 м | 2 157 ₽ | 4.8 / 362 | https://www.ozon.ru/product/ir-mt-60-18-infrakrasnyy-prozhektor-dlya-skrytogo-videonablyudeniya-dalnost-do-35-metrov-1421624837/ |

**Важно:** у OV7670 стоит IR-cut фильтр — без его снятия 850/940 нм камера
не увидит (будет чёрный кадр). Покупать ИК имеет смысл только если готов
разбирать модуль камеры.

## 7. Лазер (структурный свет / триангуляция)

| Позиция | Цена | Рейтинг | Ссылка |
|---|---|---|---|
| Модуль **линия** 650 нм, 5 мВт, 3–5 В | **244 ₽** | 4.9 / 505 | https://www.ozon.ru/product/lazernyy-modul-s-luchom-liniya-650-nm-5-mvt-3-5v-842426760/ |
| SYD1230 полоска 12 мм, 2 шт, с фокусировкой | 568 ₽ | 4.8 / 90 | https://www.ozon.ru/product/2sht-lazernyy-modul-poloska-12mm-3-5v-5mvt-650nm-s-fokusirovkoy-syd1230-2839462388/ |
| LM6R точка 5 В | 178 ₽ | 4.9 / 20 | https://www.ozon.ru/product/lazernyy-modul-lm6r-dot-5v-rck353000-krasnaya-tochka-650nm-5mvt-5v-4103057686/ |

Класс 3R: в луч не смотреть, не направлять в глаза. Питание 3.3 В с платы
пойдёт (потребление ~30 мА), но лучше отдельный 5 В — стабильнее яркость.

## 8. Готовые модули ключа (если не паять)

| Позиция | Цена | Ссылка |
|---|---|---|
| Модуль MOSFET AOD4184, 5–36 В 15 А | 207 ₽ | https://www.ozon.ru/product/modul-mosfet-klyucha-aod4184-5-36v-15a-400vt-kzy4807m-967551231/ |
| XY-MOS AOD4184 | 203 ₽ | https://www.ozon.ru/product/modul-mosfet-klyucha-xy-mos-aod4184-1851186858/ |
| Модуль на LR7843 | 176 ₽ | https://www.ozon.ru/product/modul-drayvera-upravleniya-nagruzkoy-na-polevom-tranzistore-lr7843-1621501972/ |
| Модуль на IRF520N ⚠️ | 98 ₽ | https://www.ozon.ru/product/modul-mosfet-tranzistora-irf520n-silovoy-klyuch-0-24v-5a-dlya-arduino-2708696125/ |

⚠️ Модули рассчитаны на ШИМ в единицы кГц и содержат свой драйвер/оптопару —
для импульсов в единицы микросекунд это лишняя и плохо предсказуемая задержка.
Для измерения `T_row` надёжнее дискретный IRLZ44N с резистором в затворе.

## 9. Лампочка (только для статической подсветки сцены)

| Позиция | Цена | Рейтинг | Ссылка |
|---|---|---|---|
| 30 Вт E27 6500 K, 2850 лм | 214 ₽ | 4.9 / 32 008 | https://www.ozon.ru/product/lampa-svetodiodnaya-e27-led-hp-30vt-holodnyy-svet-6500k-2850lm-in-home-843475517/ |
| 30 Вт E27 T80 колокол 6500 K | 221 ₽ | 4.9 / 55 565 | https://www.ozon.ru/product/lampochka-svetodiodnaya-moshchnaya-era-led-e27-30-vt-t80-kolokol-6500k-holodnyy-belyy-svet-1-1635791915/ |

Для строба **не годится**: внутри импульсный драйвер → пульсации 100 Гц и
медленный фронт (миллисекунды). Только постоянный свет.

## 10. Чего не брать

| Не брать | Причина |
|---|---|
| WS2812 / WS2812B / адресные ленты | свой протокол + ШИМ ~1 кГц, для мкс-строба бесполезно |
| IRFZ44N, IRF540N, IRF520N | **не** logic-level: при 3.3 В не откроются (нормируются при 10 В) |
| RGB-ленты | для строба нужен максимум белого; RGB даёт меньше света на ватт |
| Ленты 24 В | нужен другой БП, смысла нет |
| Лампы/прожекторы на 220 В | драйвер, 100 Гц, медленный фронт |
| ИК без снятия IR-cut | камера не увидит 850/940 нм |

## Минимальная корзина

| Позиция | Цена |
|---|---|
| 2 шт IRLZ44N | 225 ₽ |
| Лента Feron LS612 9.6 Вт/м 5 м | 690 ₽ |
| БП 12 В 5 А (DLED) | 200 ₽ |
| Набор резисторов 0.25 Вт, 600 шт | 241 ₽ |
| Breadboard 830 | 258 ₽ |
| Провода Dupont, 120 шт | 247 ₽ |
| **Итого** | **≈ 1 861 ₽** |

Опции: ИК 850 нм (+349 ₽, только со снятым IR-cut), лазер-линия (+244 ₽,
для триангуляции), запас IRL540N 10 шт (+285 ₽).

## Проверка при получении

1. MOSFET: мультиметром в режиме диода — сток-исток не звонится в обе стороны,
   есть внутренний диод исток→сток. При 3.3 В на затворе (через 100 Ω)
   канал открывается: сопротивление сток-исток единицы ом.
2. Лента: 12 В → светится ровно, без мерцания. Отрезок 1 м 9.6 Вт/м
   потребляет ≈ 0.8 А.
3. Ключ в сборе: при `GPIO = 0` лента полностью гаснет (проверить, что нет
   подсветки от утечки — иначе нужен подтягивающий резистор 10 кΩ).
