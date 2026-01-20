import os
import logging
from datetime import datetime
from collections import defaultdict, Counter

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)

# =====================
# НАЛАШТУВАННЯ
# =====================
MANUAL = "Ввести вручну"
DONE_BTN = "Готово"

UNITS = [
    'Відділ прикордонної служби (тип С) РУБпАК «Стінгер»',
    'Відділ прикордонної служби (тип С) РУБпАК «Примари»',
    'Відділ прикордонної служби (тип С) РУБпАК «Дінамікс»',
    'Відділ прикордонної служби (тип С) РУБпАК «Рекс»',
]

GROUP_TYPES = [
    'ударною групою FPV дронів',
]

PILOTS_BY_UNIT = {
    'Відділ прикордонної служби (тип С) РУБпАК «Стінгер»': [
        'ст. с-нта Грігорова Кирила',
        'ст. с-нта Зюзіна Владислава',
        'мол. с-нта Бернацького Владислава',
        'мол. с-нта Тараненка Івана',
    ],
    'Відділ прикордонної служби (тип С) РУБпАК «Примари»': [
        'гол. с-нт. Торохов Євген',
        'ст. с-нт. Пшеничний Микита',
        'с-нт. Рубан Дмитро',
        'гол. с-нт. Гурбіч Олександр',
        'мол. с-нт. Міненко Ігор',
    ],
    'Відділ прикордонної служби (тип С) РУБпАК «Дінамікс»': [
        'гол. с-нт. Харченко Юрій',
        'с-нт. Бугай Іван',
        'ст. с-нт. Аврамов Ігор',
        'мол. с-нт. Скітяшин Ігор',
    ],
    'Відділ прикордонної служби (тип С) РУБпАК «Рекс»': [
        "с-нт. Кір'янов Анатолій",
        'гол. с-нт. Євстафій Дмитро',
        'с-нт. Приймак Костянтин',
        'ст. солд. Лейкін Ігор',
        'с-нт. Кравецький Арсен',
    ],
}

LOCATIONS = [
    "н.п. Камʼянка-Дніпровська",
    "н.п. Водяне",
    "н.п. Енергодар",
    "н.п. Іванівка",
    "н.п. Заповітне",
    "н.п. Дніпровка",
    "н.п. Велика-Знам'янка",
    "н.п. Михайлівка",
    "н.п. Бережанка",
    "н.п. Ушкалка",
    "н.п. Бабине",
    "н.п. Новознам'янка",
    "н.п. Примірне",
    "н.п. Нововодяне",
]

TARGET_TYPES = [
    'СП рОВ',
    'СП КХВД',
    'Сартова позиція БпЛА рОВ',
    'ДРГ рОВ',
    'Група піхоти рОВ',
    'ВП  ствольної артилерії рОВ',
    'Т/З рОВ',
    'ВАТ рОВ',
    'ЛАТ рОВ',
    'Антенне обладнання',
    'РЛС',
    'САУ',
    'Вогнева позиція',
    'Радіозасічка',
    'РЕБ/РЕР рОВ',
    'Місце проживання о/с рОВ',
]

DRONES = [
    "Diatone KN114",
    "Shrike 7 (денна)",
    "Shrike 10 (денна)",
    "H10F-MD PICA",
    "Kosar (ніч)",
    "Kosar (день)",
    "U10.1T з тепловізійною камерою",
    "U10.1T",
    "U13.1T з тепловізійною камерою",
    "VIRIYJOHNNY PRO 10",
    "JOHNNY PRO 10 з тепловізійною камерою",
    "TBS Crossfire 8",
    "F7 Д",
    "TTSKFC02",
    "VIY 7",
    "VIY 10",
    "Грім 7 1.3А",
    "Колібрі 7",
    "Колібрі 7 ТК",
    "U7.1T з тепловізійною камерою",
    "U13.1T Д",
    "U7.1T",
    "Shrike 10T",
    "VIRIY PRO 10",
    "Генерал Черешня 7 T",
    "Генерал Черешня 10 ТК",
    "Генерал Черешня 10 ДК",
    "Генерал Черешня 10 мод. 1",
    "Дикі Шершні",
    "Skypulse 10",
    "Vyriy 13 з системою скиду",
    "Johnny 13 з тепловізійною камерою",
    "Johnny 13T з системою скиду",
    "Vyriy 13 (день)",
    "SPOOK 8 TK",
    "SPOOK 8 TK 2100МГц/5.8-6.08 ГГц",
    "BLINK 8 ДК",
    "BLINK 8 ДК 2100МГц/5.8ГГц",
    "SPOOK 8 TK 2100МГц/5.8ГГц",
    "SPOOK 8 TK 2100МГц/5.8ГГц ТК",
    "BLINK 8 ДК 380МГц/3.3ГГц",
    "Dart Bee",
    "Мольфар",
    "Мольфар ТК",
    "Колібрі 8 Pro ТК",
    "Колібрі 8T",
    "Колібрі 8 PRO АК",
    "Колібрі 10",
    "Колібрі 10 ТК",
    "DFS 10 ДК",
    "DFS 10 ТК",
    "Foxeer",
    "Skyriper",
    "Skyriper ТК",
    "Верба 7 ДК",
    "F10 5.8 TK",
    "ПЕГАС 7",
    "ПЕГАС 10 ТК",
    "FPV цифра",
    "PHOENIX",
    "ГЕНЕРАЛ ЧЕРЕШНЯ 10",
    "Alis-10 Digital",
    "PICA оптоволоконний",
    "Avenge Angel Reaper 10",
    "U13.1T з оптоволоконною системою зв’язку 15 км",
]

FREQ_CONTROL = [
    "380 МГц",
    "433 МГц",
    "868 МГц",
    "900 МГц",
    "915 МГц",
    "1.3 ГГц",
    "2.4 ГГц",
    "2.6 ГГц",
]

FREQ_VIDEO = [
    "1.2 ГГц",
    "1.3 ГГц",
    "2.1 ГГц",
    "2.4 ГГц",
    "3.3 ГГц",
    "4.9 ГГц",
    "5.8 ГГц",
    "6.08 ГГц",
]

MUNITIONS = [
"СВП",
    "ОФ",
    "КЗ",
    "Інше",
    'РБ 15-01',
    'РБ40-Ф-01',
    'HFB0600F',
    'HFB1200 "БУРЯЧОК"',
    'УАБК-2,0-А',
    'БНПП-40М 40мм',
    'HFM0050',
    'БПБПЛА-ОФ-1100',
    'МБ-50КУЗ "Малюк"',
    'УАБ-0,5',
    'HFB0500 (Морква)',
    'HFB 1055F',
    'УАБ-2,0-А',
    'УАБ-2,5-А',
    'ФАБ-8,5-А',
    'ЗАБ-2,5 С',
    'ЗАБ-2,5М1 (ОЗП-1)',
    'ЗАБ-2,5М2',
    'МОА-400',
    'МОА-900-03',
    'РГТ-27С2',
    'УАБ-1,5-А',
    'ПТМ-У-01',
    'ЗБ-2500',
]
LOSS_REASONS = [
    "Ціль уражено",
    "Втрачено через дію засобів РЕБ",
    "Втрачено через технічні причини",
    "Без втрат",
    "Інше",
]


SPOTTERS = [
    'ППР 1 прикзас',
    'ППР 2 прикзас',
    'ППР 3 прикзас',
    'ППР 4 прикзас',
    'ППР "Місяць" від впс (тип С) (РУБпАК)',
    'ППР "Сокіл" від впс (тип С) (РУБпАК)',
    'ППР "Яструб" від впс (тип С) (РУБпАК)',
    'ППР "Хмара" від впс (тип С) (РУБпАК)',
    'ГПР "Хижак" від впс (тип С) (РУБпАК)',
    'ГПР "Белфорд" від впс (тип С) (РУБпАК)',
    'ГПР 1 прикзас',
    'ГПР 2 прикзас',
    'ГПР 3 прикзас',
    'ГПР 4 прикзас',
    'ГПР "ГОРВ-1"',
    'ГПР "ГОРВ-2"',
    'ГПР "ГОРВ-3"',
    'ГПР "ГОРВ-4"',
]


# =====================
# Допоміжні
# =====================
def kb(items, cols=2, extra=None):
    buttons = list(items)
    if extra:
        buttons += list(extra)
    if MANUAL not in buttons:
        buttons.append(MANUAL)
    rows = [buttons[i:i + cols] for i in range(0, len(buttons), cols)]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)

def clean(t: str) -> str:
    return (t or "").strip()

def today_str() -> str:
    return datetime.now().strftime("%d.%m.%Y")

def parse_intervals(time_ranges: str):
    return [p.strip() for p in (time_ranges or "").split(",") if p.strip()]

def loss_bucket(loss: str) -> str:
    l = (loss or "").lower()
    if "реб" in l:
        return "reb"
    if "техніч" in l or "техн" in l:
        return "tech"
    if "втрачено" in l:
        return "other"
    return "ok"

def set_awaiting(context: ContextTypes.DEFAULT_TYPE, field: str):
    context.user_data["awaiting_field"] = field

def take_awaiting(context: ContextTypes.DEFAULT_TYPE, field: str) -> bool:
    if context.user_data.get("awaiting_field") == field:
        context.user_data["awaiting_field"] = None
        return True
    return False

# =====================
# СТАНИ
# =====================
(
    UNIT, DATE, TIME_RANGES, GROUP, PILOT_PICK,
    SPOTTER_Q, SPOTTER_PICK,
    FLIGHTS_COUNT, LOCATION_PICK,
    FLIGHT_TIME, FLIGHT_TARGET, FLIGHT_DIST1, FLIGHT_DIST2,
    FLIGHT_DRONE, FLIGHT_FC, FLIGHT_FV, FLIGHT_MUN, FLIGHT_LOSS, FLIGHT_MGRS,
    ASK_NEW,
) = range(20)

# =====================
# Команди
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Працюю ✅\n\nКоманди:\n/dopovid — сформувати довідку\n/cancel — скасувати",
        reply_markup=ReplyKeyboardRemove(),
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Скасовано.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# =====================
# /dopovid
# =====================
async def dopovid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["pilots"] = []
    context.user_data["flights"] = []
    context.user_data["intervals"] = []
    context.user_data["awaiting_field"] = None
    await update.message.reply_text("Обери підрозділ:", reply_markup=kb(UNITS, cols=1))
    return UNIT

async def set_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = clean(update.message.text)

    if take_awaiting(context, "unit"):
        context.user_data["unit"] = txt
    elif txt == MANUAL:
        set_awaiting(context, "unit")
        await update.message.reply_text("Впиши підрозділ (текстом):", reply_markup=ReplyKeyboardRemove())
        return UNIT
    else:
        context.user_data["unit"] = txt

    await update.message.reply_text(
        f"Дата довідки? (за замовчуванням {today_str()})\nНатисни 'Сьогодні' або введи (дд.мм.рррр):",
        reply_markup=kb(["Сьогодні"], cols=1),
    )
    return DATE

async def set_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = clean(update.message.text)

    if take_awaiting(context, "date"):
        context.user_data["date"] = txt
    elif txt == MANUAL:
        set_awaiting(context, "date")
        await update.message.reply_text("Впиши дату (дд.мм.рррр):", reply_markup=ReplyKeyboardRemove())
        return DATE
    else:
        context.user_data["date"] = today_str() if txt == "Сьогодні" else txt

    await update.message.reply_text(
        "Час/інтервали (через кому), напр.: 22:46-22:56, 23:02-23:07",
        reply_markup=ReplyKeyboardRemove(),
    )
    return TIME_RANGES

async def set_time_ranges(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = clean(update.message.text)
    context.user_data["time_ranges"] = txt
    context.user_data["intervals"] = parse_intervals(txt)
    await update.message.reply_text("Тип групи:", reply_markup=kb(GROUP_TYPES, cols=1))
    return GROUP

async def set_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = clean(update.message.text)

    if take_awaiting(context, "group"):
        context.user_data["group"] = txt
    elif txt == MANUAL:
        set_awaiting(context, "group")
        await update.message.reply_text("Впиши тип групи (текстом):", reply_markup=ReplyKeyboardRemove())
        return GROUP
    else:
        context.user_data["group"] = txt

    unit = context.user_data.get("unit", "")
    pilots = PILOTS_BY_UNIT.get(unit, [])
    context.user_data["available_pilots"] = pilots

    await update.message.reply_text(
        "Додай пілотів (по одному). Можна натискати кнопки або 'Ввести вручну'.\nКоли завершиш — натисни 'Готово'.",
        reply_markup=kb(pilots, cols=2, extra=[DONE_BTN]),
    )
    return PILOT_PICK


async def proceed_after_pilots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Переходимо до наступного кроку після вибору пілотів (з урахуванням автопідрахунку вильотів з інтервалів).
    """
    intervals = context.user_data.get("intervals", [])
    if len(intervals) >= 2:
        context.user_data["flights_total"] = len(intervals)
        context.user_data["flight_idx"] = 0
        await update.message.reply_text(f"Вказано {len(intervals)} інтервали → кількість вильотів: {len(intervals)} ✅")
        await update.message.reply_text("Локація:", reply_markup=kb(LOCATIONS, cols=2))
        return LOCATION_PICK

    await update.message.reply_text("Скільки вильотів описуємо?", reply_markup=kb(["1", "2", "3", "4"], cols=4))
    return FLIGHTS_COUNT

async def pick_pilots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = clean(update.message.text)
    pilots = context.user_data.get("available_pilots", [])

    if take_awaiting(context, "pilot"):
        if txt and txt not in context.user_data["pilots"]:
            context.user_data["pilots"].append(txt)
        current = "; ".join(context.user_data["pilots"])
        await update.message.reply_text(
            f"Додано ✅ Поточний склад: {current}\nДодавай ще або натисни 'Готово'.",
            reply_markup=kb(pilots, cols=2, extra=[DONE_BTN]),
        )
        return PILOT_PICK

    if txt == DONE_BTN:
        if not context.user_data["pilots"]:
            await update.message.reply_text("Додай хоча б одного пілота.", reply_markup=kb(pilots, cols=2, extra=[DONE_BTN]))
            return PILOT_PICK

        # Питання про підсвіт
        await update.message.reply_text("Хтось робив підсвіт?", reply_markup=kb(["Так", "Ні"], cols=2))
        return SPOTTER_Q

    if txt == MANUAL:
        set_awaiting(context, "pilot")
        await update.message.reply_text("Впиши ПІБ/звання пілота (текстом):", reply_markup=ReplyKeyboardRemove())
        return PILOT_PICK

    if txt and txt not in context.user_data["pilots"]:
        context.user_data["pilots"].append(txt)

    current = "; ".join(context.user_data["pilots"])
    await update.message.reply_text(
        f"Ок ✅ Поточний склад: {current}\nДодавай ще абоым натисни 'Готово'.",
        reply_markup=kb(pilots, cols=2, extra=[DONE_BTN]),
    )
    return PILOT_PICK


async def spotter_q(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = clean(update.message.text)
    if txt == "Ні":
        context.user_data["spotter"] = ""
        return await proceed_after_pilots(update, context)
    if txt == "Так":
        await update.message.reply_text("Обери хто підсвічував (або 'Ввести вручну'):", reply_markup=kb(SPOTTERS, cols=2))
        return SPOTTER_PICK

    await update.message.reply_text("Обери 'Так' або 'Ні'.", reply_markup=kb(["Так", "Ні"], cols=2))
    return SPOTTER_Q

async def spotter_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = clean(update.message.text)
    if take_awaiting(context, "spotter"):
        context.user_data["spotter"] = txt
        return await proceed_after_pilots(update, context)

    if txt == MANUAL:
        set_awaiting(context, "spotter")
        await update.message.reply_text("Впиши хто підсвічував (текстом):", reply_markup=ReplyKeyboardRemove())
        return SPOTTER_PICK

    context.user_data["spotter"] = txt
    return await proceed_after_pilots(update, context)

async def set_flights_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = clean(update.message.text)

    if take_awaiting(context, "flights_total"):
        val = txt
    elif txt == MANUAL:
        set_awaiting(context, "flights_total")
        await update.message.reply_text("Впиши кількість вильотів (число):", reply_markup=ReplyKeyboardRemove())
        return FLIGHTS_COUNT
    else:
        val = txt

    try:
        n = int(val)
        if n < 1 or n > 50:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Введи число (1–50) або обери кнопкою.", reply_markup=kb(["1","2","3","4"], cols=4))
        return FLIGHTS_COUNT

    context.user_data["flights_total"] = n
    context.user_data["flight_idx"] = 0
    await update.message.reply_text("Локація:", reply_markup=kb(LOCATIONS, cols=2))
    return LOCATION_PICK

async def set_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = clean(update.message.text)

    if take_awaiting(context, "location"):
        context.user_data["location"] = txt
    elif txt == MANUAL:
        set_awaiting(context, "location")
        await update.message.reply_text("Впиши локацію (текстом):", reply_markup=ReplyKeyboardRemove())
        return LOCATION_PICK
    else:
        context.user_data["location"] = txt

    return await start_flight(update, context)

async def start_flight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data.get("flight_idx", 0)
    total = context.user_data.get("flights_total", 1)

    intervals = context.user_data.get("intervals", [])
    default_interval = intervals[idx] if idx < len(intervals) else ""

    if default_interval:
        await update.message.reply_text(
            f"Виліт {idx+1}/{total}: час (за замовчуванням {default_interval})",
            reply_markup=kb([default_interval, "Ввести інше"], cols=2),
        )
    else:
        await update.message.reply_text(
            f"Виліт {idx+1}/{total}: інтервал часу (напр. 22:46-22:56):",
            reply_markup=ReplyKeyboardRemove(),
        )
    return FLIGHT_TIME

async def flight_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = clean(update.message.text)
    if txt == "Ввести інше":
        await update.message.reply_text("Впиши інтервал часу (напр. 22:46-22:56):", reply_markup=ReplyKeyboardRemove())
        return FLIGHT_TIME

    context.user_data["current_flight"] = {"time": txt}
    await update.message.reply_text("Тип цілі:", reply_markup=kb(TARGET_TYPES, cols=2))
    return FLIGHT_TARGET

async def flight_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = clean(update.message.text)

    if take_awaiting(context, "target"):
        context.user_data["current_flight"]["target"] = txt
    elif txt == MANUAL:
        set_awaiting(context, "target")
        await update.message.reply_text("Впиши тип цілі (текстом):", reply_markup=ReplyKeyboardRemove())
        return FLIGHT_TARGET
    else:
        context.user_data["current_flight"]["target"] = txt

    await update.message.reply_text("Відстань від місця зльоту до цілі (км):", reply_markup=ReplyKeyboardRemove())
    return FLIGHT_DIST1

async def flight_dist1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["current_flight"]["dist_launch"] = clean(update.message.text)
    await update.message.reply_text("Відстань від берега противника до цілі (м):")
    return FLIGHT_DIST2

async def flight_dist2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["current_flight"]["dist_shore"] = clean(update.message.text)
    await update.message.reply_text("Дрон:", reply_markup=kb(DRONES, cols=2))
    return FLIGHT_DRONE

async def flight_drone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = clean(update.message.text)

    if take_awaiting(context, "drone"):
        context.user_data["current_flight"]["drone"] = txt
    elif txt == MANUAL:
        set_awaiting(context, "drone")
        await update.message.reply_text("Впиши назву дрона (текстом):", reply_markup=ReplyKeyboardRemove())
        return FLIGHT_DRONE
    else:
        context.user_data["current_flight"]["drone"] = txt

    await update.message.reply_text("Частота керування:", reply_markup=kb(FREQ_CONTROL, cols=2))
    return FLIGHT_FC

async def flight_fc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = clean(update.message.text)

    if take_awaiting(context, "freq_control"):
        context.user_data["current_flight"]["freq_control"] = txt
    elif txt == MANUAL:
        set_awaiting(context, "freq_control")
        await update.message.reply_text("Впиши частоту керування (текстом):", reply_markup=ReplyKeyboardRemove())
        return FLIGHT_FC
    else:
        context.user_data["current_flight"]["freq_control"] = txt

    await update.message.reply_text("Частота відео:", reply_markup=kb(FREQ_VIDEO, cols=2))
    return FLIGHT_FV

async def flight_fv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = clean(update.message.text)

    if take_awaiting(context, "freq_video"):
        context.user_data["current_flight"]["freq_video"] = txt
    elif txt == MANUAL:
        set_awaiting(context, "freq_video")
        await update.message.reply_text("Впиши частоту відео (текстом):", reply_markup=ReplyKeyboardRemove())
        return FLIGHT_FV
    else:
        context.user_data["current_flight"]["freq_video"] = txt

    await update.message.reply_text("Боєприпас:", reply_markup=kb(MUNITIONS, cols=2))
    return FLIGHT_MUN

async def flight_mun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = clean(update.message.text)

    if take_awaiting(context, "munition"):
        context.user_data["current_flight"]["munition"] = txt
    elif txt == MANUAL:
        set_awaiting(context, "munition")
        await update.message.reply_text("Впиши боєприпас (текстом):", reply_markup=ReplyKeyboardRemove())
        return FLIGHT_MUN
    else:
        context.user_data["current_flight"]["munition"] = txt

    await update.message.reply_text("Результат/втрата:", reply_markup=kb(LOSS_REASONS, cols=2))
    return FLIGHT_LOSS

async def flight_loss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = clean(update.message.text)

    if take_awaiting(context, "loss"):
        context.user_data["current_flight"]["loss"] = txt
    elif txt == MANUAL:
        set_awaiting(context, "loss")
        await update.message.reply_text("Впиши результат/причину (текстом):", reply_markup=ReplyKeyboardRemove())
        return FLIGHT_LOSS
    else:
        context.user_data["current_flight"]["loss"] = txt

    await update.message.reply_text("Координати (MGRS), напр. 36T XT 10899 51239:", reply_markup=ReplyKeyboardRemove())
    return FLIGHT_MGRS

async def flight_mgrs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["current_flight"]["mgrs"] = clean(update.message.text)

    context.user_data["flights"].append(context.user_data.pop("current_flight"))
    context.user_data["flight_idx"] = context.user_data.get("flight_idx", 0) + 1

    if context.user_data["flight_idx"] < context.user_data["flights_total"]:
        return await start_flight(update, context)

    report = build_report(context.user_data)
    await update.message.reply_text("Готово ✅ Ось сформована довідка:\n\n" + report, reply_markup=ReplyKeyboardRemove())
    return await ask_new_report(update, context)

async def ask_new_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Створити ще одну довідку?", reply_markup=kb(["Так", "Ні"], cols=2))
    return ASK_NEW

async def handle_new_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ans = clean(update.message.text)
    if ans == "Так":
        return await dopovid(update, context)
    await update.message.reply_text("Ок 👍", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# =====================
# Формування довідки: групування по MGRS
# =====================


def is_lost(value: str) -> bool:
    # True якщо втрата (РЕБ/технічна/будь-яка "втрачено")
    s = (value or "").lower()
    return ("втрачено" in s) or ("реб" in s) or ("тех" in s)

def is_lost(value: str) -> bool:
    s = (value or "").lower()
    return ("втрачено" in s) or ("реб" in s) or ("тех" in s)




from collections import defaultdict, Counter

def build_report(d: dict) -> str:
    unit = d.get("unit", "")
    date = d.get("date", "")
    time_ranges = d.get("time_ranges", "")
    group = d.get("group", "")
    pilots = ", ".join(d.get("pilots", []))
    spotter = d.get("spotter", "")
    loc = d.get("location", "")
    flights = d.get("flights", [])

    total = len(flights)
    lost_total = sum(1 for f in flights if is_lost(f.get("loss", f.get("result", ""))))
    loss_text = "без втрат" if lost_total == 0 else f"{lost_total} од. - втрачено"

    header = (
        f"{unit}: {date} *({time_ranges})* {group} у складі: {pilots} "
        f"{('спільно з ' + spotter + ' ') if spotter else ''}"
        f"виконувалось завдання з ВУ противника із застосуванням FPV-дронів "
        f"*({total} од., {loss_text})* в межах {loc}."
    )

    by_mgrs = defaultdict(list)
    for f in flights:
        mgrs = f.get("mgrs") or f.get("coord") or "N/A"
        by_mgrs[mgrs].append(f)

    ok_points = []
    lost_points = []

    for mgrs, fls in by_mgrs.items():
        ok = [f for f in fls if not is_lost(f.get("loss", f.get("result", "")))]
        bad = [f for f in fls if is_lost(f.get("loss", f.get("result", "")))]

        def agg(block):
            times = ", ".join([x.get("time", "") for x in block if x.get("time")])
            target = block[0].get("target", "")
            dist = block[0].get("dist_launch", "")
            shore = block[0].get("dist_shore", "")
            fc = block[0].get("freq_control", "")
            fv = block[0].get("freq_video", "")
            drones = Counter([x.get("drone", "") for x in block if x.get("drone")])
            muns = Counter([x.get("munition", "") for x in block if x.get("munition")])
            drones_str = ", ".join([f"{k} - {v} од." for k, v in drones.items()])
            muns_str = ", ".join([f"{k} - {v} од." for k, v in muns.items()])
            return times, target, dist, shore, fc, fv, drones_str, muns_str

        if ok:
            times, target, dist, shore, fc, fv, drones_str, muns_str = agg(ok)
            ok_points.append(
                f"{target} ({len(ok)} вильоти, {times}) відстань від місця зльоту до цілі - {dist} км., "
                f"відстань від берега противника до цілі - {shore} м., "
                f"FPV-дрон: {drones_str}; Частоти : керування - {fc} , відео- {fv}, "
                f"б/п- {muns_str}.-ціль уражено, {loc} ({mgrs})."
            )

        if bad:
            times, target, dist, shore, fc, fv, drones_str, muns_str = agg(bad)
            reasons = Counter([x.get("loss", x.get("result", "")) for x in bad])
            reasons_str = ", ".join([f"{k} - {v} од." for k, v in reasons.items() if k])
            lost_points.append(
                f"{target} : ({len(bad)} вильоти, {times}) відстань від місця зльоту до цілі - {dist} км., "
                f"від берега противника до цілі - {shore} м., "
                f"FPV-дрон {drones_str}. Частоти : керування - {fc} , відео- {fv}, "
                f"б/п: {muns_str} {reasons_str} {loc} ({mgrs})."
            )

    lines = [header, ""]
    for i, p in enumerate(ok_points, 1):
        lines.append(f"{i}) {p}")
        lines.append("")

    if lost_points:
        lines.append("Втрачені:")
        lines.append("")
        for i, p in enumerate(lost_points, 1):
            lines.append(f"{i}) {p}")
            lines.append("")

    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Нема BOT_TOKEN. Задай змінну середовища BOT_TOKEN і запусти ще раз.")

    app = Application.builder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("dopovid", dopovid)],
        states={
            UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_unit)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_date)],
            TIME_RANGES: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_time_ranges)],
            GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_group)],
            PILOT_PICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, pick_pilots)],
            SPOTTER_Q: [MessageHandler(filters.TEXT & ~filters.COMMAND, spotter_q)],
            SPOTTER_PICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, spotter_pick)],
            FLIGHTS_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_flights_count)],
            LOCATION_PICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_location)],
            FLIGHT_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, flight_time)],
            FLIGHT_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, flight_target)],
            FLIGHT_DIST1: [MessageHandler(filters.TEXT & ~filters.COMMAND, flight_dist1)],
            FLIGHT_DIST2: [MessageHandler(filters.TEXT & ~filters.COMMAND, flight_dist2)],
            FLIGHT_DRONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, flight_drone)],
            FLIGHT_FC: [MessageHandler(filters.TEXT & ~filters.COMMAND, flight_fc)],
            FLIGHT_FV: [MessageHandler(filters.TEXT & ~filters.COMMAND, flight_fv)],
            FLIGHT_MUN: [MessageHandler(filters.TEXT & ~filters.COMMAND, flight_mun)],
            FLIGHT_LOSS: [MessageHandler(filters.TEXT & ~filters.COMMAND, flight_loss)],
            FLIGHT_MGRS: [MessageHandler(filters.TEXT & ~filters.COMMAND, flight_mgrs)],
            ASK_NEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_report)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(conv)

    app.run_polling()

if __name__ == "__main__":
    main()
