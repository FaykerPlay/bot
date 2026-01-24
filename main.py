import os
import re
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

# =====================
# НАЛАШТУВАННЯ ТА ДАНІ
# =====================
TOKEN = "8570254252:AAE9lXRAQlAU2mv2SsdkpRN_Cn5FoNpYgJY"
PASSWORD = "2402"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Константи кнопок
BACK = "⬅️ Назад"
DONE = "Готово ✅"
MANUAL = "⌨️ Ввести вручну"
CANCEL = "❌ Скасувати"
TODAY = "📅 Сьогодні"
ADD_FLIGHT = "➕ Додати виліт у цей звіт"
NEXT_REPORT = "📄 Почати новий звіт"
OTHER_TARGET = "🎯 Інша ціль"

# --- ПОВНІ СПИСКИ ---
UNITS = [
    'Відділ прикордонної служби (тип С) РУБпАК «Стінгер»',
    'Відділ прикордонної служби (тип С) РУБпАК «Примари»',
    'Відділ прикордонної служби (тип С) РУБпАК «Дінамікс»',
    'Відділ прикордонної служби (тип С) РУБпАК «Рекс»',
]

GROUP_TYPES = ['ударною групою FPV дронів']

PILOTS_BY_UNIT = {
    'Відділ прикордонної служби (тип С) РУБпАК «Стінгер»': [
        'ст. с-нта Грігорова Кирила', 'ст. с-нта Зюзіна Владислава', 
        'мол. с-нта Бернацького Владислава', 'мол. с-нта Тараненка Івана',
        'ст. с-нт ЯРОВОЙ Євген'
    ],
    'Відділ прикордонної служби (тип С) РУБпАК «Примари»': [
        'гол. с-нт. Торохов Євген', 'ст. с-нт. Пшеничний Микита', 'с-нт. Рубан Дмитро', 
        'гол. с-нт. Гурбіч Олександр', 'мол. с-нт. Міненко Ігор'
    ],
    'Відділ прикордонної служби (тип С) РУБпАК «Дінамікс»': [
        'гол. с-нт. Харченко Юрій', 'с-нт. Бугай Іван', 
        'ст. с-нта Аврамов Ігор', 'мол. с-нт. Скітяшин Ігор'
    ],
    'Відділ прикордонної служби (тип С) РУБпАК «Рекс»': [
        "с-нт. Кір'янов Анатолій", 'гол. с-нт. Євстафій Дмитро', 
        'с-нт. Приймак Костянтин', 'ст. солд. Лейкін Ігор', 'с-нт. Кравецький Арсен'
    ],
}

LOCATIONS = [
    "н.п. Камʼянка-Дніпровська", "н.п. Водяне", "н.п. Енергодар", "н.п. Іванівка", 
    "н.п. Заповітне", "н.п. Дніпровка", "н.п. Велика-Знам'янка", "н.п. Михайлівка", 
    "н.п. Бережанка", "н.п. Ушкалка", "н.п. Бабине", "н.п. Новознам'янка", 
    "н.п. Примірне", "н.п. Нововодяне"
]

TARGET_TYPES = [
    'СП рОВ', 'СП КХВД', 'Сартова позиція БпЛА рОВ', 'ДРГ рОВ', 'Група піхоти рОВ', 
    'ВП ствольної артилерії рОВ', 'Т/З рОВ', 'ВАТ рОВ', 'ЛАТ рОВ', 'Антенне обладнання', 
    'РЛС', 'САУ', 'Вогнева позиція', 'Радіозасічка', 'РЕБ/РЕР рОВ', 'Місце проживання о/с рОВ'
]

DRONES = [
    "Diatone KN114", "Shrike 7 (денна)", "Shrike 10 (денна)", "H10F-MD PICA", "Kosar (ніч)", 
    "Kosar (день)", "U10.1T з ТК", "U10.1T", "U13.1T з ТК", "VIRIYJOHNNY PRO 10", 
    "JOHNNY PRO 10 з ТК", "TBS Crossfire 8", "F7 Д", "TTSKFC02", "VIY 7", "VIY 10", 
    "Грім 7 1.3А", "Колібрі 7", "Колібрі 7 ТК", "U7.1T з ТК", "U13.1T Д", "U7.1T", 
    "Shrike 10T", "VIRIY PRO 10", "Генерал Черешня 7 T", "Генерал Черешня 10 ТК", 
    "Генерал Черешня 10 ДК", "Генерал Черешня 10 мод. 1", "Дикі Шершні", "Skypulse 10", 
    "Vyriy 13 з системою скиду", "Johnny 13 з ТК", "Johnny 13T з скидом", "Vyriy 13 (день)", 
    "SPOOK 8 TK", "SPOOK 8 TK 2100МГц/5.8-6.08 ГГц", "BLINK 8 ДК", "BLINK 8 ДК 2100МГц/5.8ГГц", 
    "SPOOK 8 TK 2100МГц/5.8ГГц", "SPOOK 8 TK 2100МГц/5.8ГГц ТК", "BLINK 8 ДК 380МГц/3.3ГГц", 
    "Dart Bee", "Мольфар", "Мольфар ТК", "Колібрі 8 Pro ТК", "Колібрі 8T", "Колібрі 8 PRO АК", 
    "Колібрі 10", "Колібрі 10 ТК", "DFS 10 ДК", "DFS 10 ТК", "Foxeer", "Skyriper", 
    "Skyriper ТК", "Верба 7 ДК", "F10 5.8 TK", "ПЕГАС 7", "ПЕГАС 10 ТК", "FPV цифра", 
    "PHOENIX", "ГЕНЕРАЛ ЧЕРЕШНЯ 10", "Alis-10 Digital", "PICA оптоволоконний", 
    "Avenge Angel Reaper 10", "U13.1T з оптоволоконною системою зв’язку 15 км"
]

MUNITIONS = [
    "СВП", "ОФ", "КЗ", "Інше", 'РБ 15-01', 'РБ40-Ф-01', 'HFB0600F', 'HFB1200 "БУРЯЧОК"', 
    'УАБК-2,0-А', 'БНПП-40М 40мм', 'HFM0050', 'БПБПЛА-ОФ-1100', 'МБ-50КУЗ "Малюк"', 
    'УАБ-0,5', 'HFB0500 (Морква)', 'HFB 1055F', 'УАБ-2,0-А', 'УАБ-2,5-А', 'ФАБ-8,5-А', 
    'ЗАБ-2,5 С', 'ЗАБ-2,5М1 (ОЗП-1)', 'ЗАБ-2,5М2', 'МОА-400', 'МОА-900-03', 'РГТ-27С2', 
    'УАБ-1,5-А', 'ПТМ-У-01', 'ЗБ-2500'
]

SPOTTERS = [
    'ППР 1 прикзас', 'ППР 2 прикзас', 'ППР 3 прикзас', 'ППР 4 прикзас', 
    'ППР "Місяць" від впс (тип С) (РУБпАК)', 'ППР "Сокіл" від впс (тип С) (РУБпАК)', 
    'ППР "Яструб" від впс (тип С) (РУБпАК)', 'ППР "Хмара" від впс (тип С) (РУБпАК)', 
    'ГПР "Хижак" від впс (тип С) (РУБпАК)', 'ГПР "Белфорд" від впс (тип С) (РУБпАК)', 
    'ГПР 1 прикзас', 'ГПР 2 прикзас', 'ГПР 3 прикзас', 'ГПР 4 прикзас', 
    'ГПР "ГОРВ-1"', 'ГПР "ГОРВ-2"', 'ГПР "ГОРВ-3"', 'ГПР "ГОРВ-4"'
]

FREQ_CONTROL = ["380 МГц", "433 МГц", "868 МГц", "900 МГц", "915 МГц", "1.3 ГГц", "2.4 ГГц", "2.6 ГГц"]
FREQ_VIDEO = ["1.2 ГГц", "1.3 ГГц", "2.1 ГГц", "2.4 ГГц", "3.3 ГГц", "4.9 ГГц", "5.8 ГГц", "6.08 ГГц"]

LOSS_REASONS = [
    "Ціль уражено", 
    "Ціль знищено", 
    "Ціль пошкоджено",
    "Втрачено через дію засобів РЕБ", 
    "втрачено через технічні причини, а саме брак відеопередавача",
    "втрачено через технічні причини, а саме брак плати керування",
    "втрачено через технічні причини, а саме нестача АКБ",
    "Втрачено через технічні причини", 
    "Збито зі стрілецької зброї",
    "Без втрат", 
    "Інше"
]

# =====================
# ДОПОМІЖНІ ФУНКЦІЇ
# =====================

def get_kb(items, cols=2, extra=None, show_back=True):
    buttons = [items[i:i + cols] for i in range(0, len(items), cols)]
    if extra: buttons.append(extra)
    nav = []
    if show_back: nav.append(BACK)
    nav.append(CANCEL)
    buttons.append(nav)
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def validate_mgrs(text: str) -> bool:
    return bool(re.match(r'^\d{2}[A-Z]\s?[A-Z]{2}\s?\d{5}\s?\d{5}$', text.strip().upper()))

def is_lost(reason: str) -> bool:
    r = (reason or "").lower()
    return any(x in r for x in ["втрачено", "реб", "техніч", "техн", "збито"])

# =====================
# СТАНИ
# =====================
(AUTH, UNIT, DATE, GROUP, PILOTS, SPOTTER_Q, SPOTTER_NAME, 
 LOCATION, F_START, F_TIME, F_TARGET, F_DIST_L, F_DIST_S, 
 F_DRONE, F_FC, F_FV, F_MUN, F_LOSS, F_MGRS, POST_REPORT) = range(20)

# =====================
# ОБРОБНИКИ
# =====================

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🔐 Введіть пароль для доступу:", reply_markup=ReplyKeyboardRemove())
    return AUTH

async def handle_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == PASSWORD:
        await update.message.reply_text("✅ Доступ дозволено.")
        return await ask_unit(update, context)
    await update.message.reply_text("❌ Пароль невірний.")
    return AUTH

async def ask_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['flights'] = []
    context.user_data['selected_pilots'] = []
    await update.message.reply_text("Оберіть підрозділ:", reply_markup=get_kb(UNITS, 1, [MANUAL], False))
    return UNIT

async def handle_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == CANCEL: return await cancel_h(update, context)
    context.user_data['unit'] = update.message.text
    await update.message.reply_text("Дата:", reply_markup=get_kb([TODAY], 1, [MANUAL]))
    return DATE

async def handle_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text
    if val == BACK: return await ask_unit(update, context)
    context.user_data['date'] = datetime.now().strftime("%d.%m.%Y") if val == TODAY else val
    await update.message.reply_text("Тип групи:", reply_markup=get_kb(GROUP_TYPES, 1, [MANUAL]))
    return GROUP

async def handle_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text
    if val == BACK: return await handle_unit(update, context)
    context.user_data['group'] = val
    return await ask_pilots_menu(update, context)

async def ask_pilots_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    unit = context.user_data.get('unit')
    available = PILOTS_BY_UNIT.get(unit, [])
    selected = context.user_data.setdefault('selected_pilots', [])
    buttons = [f"✅ {p}" if p in selected else p for p in available]
    await update.message.reply_text(f"Склад: {', '.join(selected) if selected else 'не обрано'}\nОберіть пілотів:", 
                                   reply_markup=get_kb(buttons, 2, [MANUAL, DONE]))
    return PILOTS

async def handle_pilots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text
    if val == BACK: return await handle_date(update, context)
    if val == DONE:
        if not context.user_data['selected_pilots']: return PILOTS
        await update.message.reply_text("Був підсвіт?", reply_markup=get_kb(["Так", "Ні"]))
        return SPOTTER_Q
    name = val.replace("✅ ", "")
    selected = context.user_data['selected_pilots']
    if name in selected: selected.remove(name)
    else: selected.append(name)
    return await ask_pilots_menu(update, context)

async def handle_spotter_q(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text
    if val == BACK: return await ask_pilots_menu(update, context)
    if val == "Так":
        await update.message.reply_text("Хто підсвічував?", reply_markup=get_kb(SPOTTERS, 1, [MANUAL]))
        return SPOTTER_NAME
    context.user_data['spotter'] = ""
    return await start_flight_decision(update, context)

async def handle_spotter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text
    if val == BACK: return await handle_spotter_q(update, context)
    context.user_data['spotter'] = val
    return await start_flight_decision(update, context)

async def ask_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Оберіть н.п. для цієї цілі:", reply_markup=get_kb(LOCATIONS, 2, [MANUAL]))
    return LOCATION

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text
    if val == BACK: return await start_flight_decision(update, context)
    context.user_data['current_temp_loc'] = val 
    return await start_flight_manual(update, context)

async def start_flight_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flights = context.user_data.get('flights', [])
    if not flights:
        return await ask_location(update, context)
    mgrs_list = list(dict.fromkeys(f['mgrs'] for f in flights))
    await update.message.reply_text(f"Виліт №{len(flights)+1}: Оберіть координати або нову ціль:", 
                                   reply_markup=get_kb(mgrs_list, 1, [OTHER_TARGET]))
    return F_START

async def handle_f_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text
    if val == OTHER_TARGET: return await ask_location(update, context)
    if validate_mgrs(val):
        prev = next((f for f in context.user_data['flights'] if f['mgrs'] == val), None)
        if prev:
            context.user_data['cur_f'] = {
                'target': prev['target'], 'dist_l': prev['dist_l'], 'dist_s': prev['dist_s'], 
                'mgrs': val, 'loc': prev['loc'], 'is_template': True
            }
            await update.message.reply_text(f"Ціль {prev['target']} вибрана. Вкажіть час:")
            return F_TIME
    return await ask_location(update, context)

async def start_flight_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['cur_f'] = {'is_template': False, 'loc': context.user_data.get('current_temp_loc')}
    await update.message.reply_text("Точний час вильоту:", reply_markup=get_kb([], 1))
    return F_TIME

async def h_f_time(u,c):
    c.user_data['cur_f']['time'] = u.message.text
    if c.user_data['cur_f'].get('is_template'):
        await u.message.reply_text("Дрон:", reply_markup=get_kb(DRONES, 2, [MANUAL]))
        return F_DRONE
    await u.message.reply_text("Тип цілі:", reply_markup=get_kb(TARGET_TYPES, 2, [MANUAL]))
    return F_TARGET

async def h_f_target(u,c):
    c.user_data['cur_f']['target'] = u.message.text
    await u.message.reply_text("Відстань від зльоту (км):", reply_markup=ReplyKeyboardRemove())
    return F_DIST_L
async def h_f_dist_l(u,c):
    c.user_data['cur_f']['dist_l'] = u.message.text
    await u.message.reply_text("Відстань від берега (м):")
    return F_DIST_S
async def h_f_dist_s(u,c):
    c.user_data['cur_f']['dist_s'] = u.message.text
    await u.message.reply_text("Дрон:", reply_markup=get_kb(DRONES, 2, [MANUAL]))
    return F_DRONE
async def h_f_drone(u,c):
    c.user_data['cur_f']['drone'] = u.message.text
    await u.message.reply_text("Частота керування:", reply_markup=get_kb(FREQ_CONTROL, 2, [MANUAL]))
    return F_FC
async def h_f_fc(u,c):
    c.user_data['cur_f']['fc'] = u.message.text
    await u.message.reply_text("Частота відео:", reply_markup=get_kb(FREQ_VIDEO, 2, [MANUAL]))
    return F_FV
async def h_f_fv(u,c):
    c.user_data['cur_f']['fv'] = u.message.text
    await u.message.reply_text("Боєприпас:", reply_markup=get_kb(MUNITIONS, 2, [MANUAL]))
    return F_MUN
async def h_f_mun(u,c):
    c.user_data['cur_f']['mun'] = u.message.text
    await u.message.reply_text("Результат:", reply_markup=get_kb(LOSS_REASONS, 1, [MANUAL]))
    return F_LOSS
async def h_f_loss(u,c):
    c.user_data['cur_f']['loss'] = u.message.text
    if c.user_data['cur_f'].get('is_template'): return await finalize_flight(u, c)
    await u.message.reply_text("Координати MGRS:")
    return F_MGRS

async def h_f_mgrs(u,c):
    val = u.message.text.upper()
    if not validate_mgrs(val): return F_MGRS
    c.user_data['cur_f']['mgrs'] = val
    return await finalize_flight(u, c)

async def finalize_flight(update, context):
    context.user_data['flights'].append(context.user_data.pop('cur_f'))
    report = build_report(context.user_data)
    await update.message.reply_text(f"📊 **Поточний звіт:**\n\n{report}", parse_mode='Markdown')
    kb = [[ADD_FLIGHT], [NEXT_REPORT], [CANCEL]]
    await update.message.reply_text("Що далі?", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return POST_REPORT

async def handle_post_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text
    if val == ADD_FLIGHT: return await start_flight_decision(update, context)
    if val == NEXT_REPORT: return await ask_unit(update, context)
    return await cancel_h(update, context)

# =====================
# ГЕНЕРАЦІЯ ТЕКСТУ
# =====================

def build_report(d: dict) -> str:
    unit, date, group = d['unit'], d['date'], d['group']
    pilots = ", ".join(d['selected_pilots'])
    spotter = d.get('spotter', '')
    flights = d['flights']
    all_times = ", ".join([f['time'] for f in flights])
    
    all_locs = list(dict.fromkeys(f['loc'] for f in flights))
    loc_str = " та ".join(all_locs)

    lost_flights = [f for f in flights if is_lost(f['loss'])]
    
    hits = list(dict.fromkeys([f['target'] for f in flights if "уражено" in f['loss'].lower()]))
    damaged = list(dict.fromkeys([f['target'] for f in flights if "пошкоджено" in f['loss'].lower()]))
    destroyed = list(dict.fromkeys([f['target'] for f in flights if "знищено" in f['loss'].lower()]))
    
    loss_details = ""
    if lost_flights:
        reasons_counts = Counter()
        for f in lost_flights:
            l = f['loss'].lower()
            if "реб" in l: reasons_counts["через дію засобів РЕБ"] += 1
            elif "відеопередавача" in l: reasons_counts["через технічні причини, а саме брак відеопередавача"] += 1
            elif "плати керування" in l: reasons_counts["через технічні причини, а саме брак плати керування"] += 1
            elif "нестача акб" in l: reasons_counts["через технічні причини, а саме нестача АКБ"] += 1
            elif "технічні" in l or "техн" in l: reasons_counts["через технічні причини"] += 1
            elif "стрілецької" in l: reasons_counts["збито зі стрілецької зброї"] += 1
            else: reasons_counts["з інших причин"] += 1
        loss_details = f" ({', '.join([f'{v} од. {k}' for k, v in reasons_counts.items()])})"

    any_result = hits or damaged or destroyed
    action_word = "виконано" if any_result else "виконувалось"
    loss_text = "без втрат" if not lost_flights else f"{len(lost_flights)} од. - втрачено{loss_details}"
    
    results_header = ""
    if any_result:
        results_header = "\nЗа результатами вильотів:"
        parts = []
        if hits: parts.append(f" уражено: {', '.join(hits)}")
        if damaged: parts.append(f" пошкоджено: {', '.join(damaged)}")
        if destroyed: parts.append(f" знищено: {', '.join(destroyed)}")
        results_header += ",".join(parts)

    header = (f"*{unit}: {date} ({all_times})* {group} у складі: {pilots} "
              f"{('спільно з ' + spotter + ' ') if spotter else ''}"
              f"{action_word} завдання з ВУ противника із застосуванням FPV-дронів "
              f"*({len(flights)} од., {loss_text})* в межах {loc_str}.{results_header}")

    grouped = defaultdict(list)
    for f in flights: grouped[f['mgrs']].append(f)

    ok_pts, lost_pts = [], []
    for mgrs, fls in grouped.items():
        ok = [f for f in fls if not is_lost(f['loss'])]
        lost = [f for f in fls if is_lost(f['loss'])]

        def agg(block):
            t_str = ", ".join([x['time'] for x in block])
            dr_str = ", ".join([f"{k}-{v}од." for k,v in Counter([x['drone'] for x in block]).items()])
            mun_str = ", ".join([f"{k}-{v}од." for k,v in Counter([x['mun'] for x in block]).items()])
            f = block[0]
            return (f"{f['target']} ({len(block)} вильоти, {t_str}) відстань від зльоту - {f['dist_l']} км., "
                    f"від берега - {f['dist_s']} м., "
                    f"FPV-дрон: {dr_str}; Частоти: керування-{f['fc']}, відео-{f['fv']}, б/п-{mun_str}, {f['loc']}")

        if ok: ok_pts.append(f"{agg(ok)}.-{ok[0]['loss'].lower()} ({mgrs}).")
        if lost: lost_pts.append(f"{agg(lost)} {', '.join([f['loss'] for f in lost])} ({mgrs}).")

    res = [header, ""]
    for i, p in enumerate(ok_pts, 1): res.append(f"{i}) {p}\n")
    if lost_pts:
        res.append("*Втрачені:*")
        for i, p in enumerate(lost_pts, 1): res.append(f"{i}) {p}\n")
    return "\n".join(res)

async def cancel_h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Завершено. /start", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()
    states = {
        AUTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_auth)],
        UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unit)],
        DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_date)],
        GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group)],
        PILOTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pilots)],
        SPOTTER_Q: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_spotter_q)],
        SPOTTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_spotter_name)],
        LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location)],
        F_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_f_start)],
        F_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, h_f_time)],
        F_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, h_f_target)],
        F_DIST_L: [MessageHandler(filters.TEXT & ~filters.COMMAND, h_f_dist_l)],
        F_DIST_S: [MessageHandler(filters.TEXT & ~filters.COMMAND, h_f_dist_s)],
        F_DRONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, h_f_drone)],
        F_FC: [MessageHandler(filters.TEXT & ~filters.COMMAND, h_f_fc)],
        F_FV: [MessageHandler(filters.TEXT & ~filters.COMMAND, h_f_fv)],
        F_MUN: [MessageHandler(filters.TEXT & ~filters.COMMAND, h_f_mun)],
        F_LOSS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h_f_loss)],
        F_MGRS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h_f_mgrs)],
        POST_REPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_post_report)],
    }
    app.add_handler(ConversationHandler(entry_points=[CommandHandler("start", start_cmd), CommandHandler("dopovid", start_cmd)], states=states, fallbacks=[CommandHandler("cancel", cancel_h)], allow_reentry=True))
    app.run_polling()

if __name__ == "__main__": main()
