# Cheterin

Многофункциональный Discord-бот с веб-панелью управления.  
Модерация, уровни, экономика, игры, ValChecker, события — почти всё настраивается в браузере, без перезапуска.

**Панель:** [cheterin.online](https://cheterin.online) · **Документация:** `/docs` на сайте

---

## Возможности

| Раздел | Что внутри |
|--------|------------|
| **Модерация** | Логи, антиспам, автомод, верификация, антирейд, варны, tempban |
| **Сообщество** | Уровни и XP, приветствия, инвайты, sticky-роли, дни рождения |
| **Экономика** | Валюта сервера, магазин ролей, daily, казино |
| **Игры** | Семья и поставки (GTA5RP), **ValChecker** (Valorant) |
| **Развлечения** | Wordle, русская рулетка, Мафия, Бункер |
| **Контент** | Embed Builder, события, розыгрыши, опросы, сетки, стримы |
| **Служебное** | Приватные войсы, отложенные/закреплённые сообщения, тикеты |

Участникам доступна команда **`/help`** — короткая справка по страницам.  
Статус бота: `Playing /help • Cheterin`.

---

## Быстрый старт

### Требования

- Python **3.11+**
- Node.js **20+** (фронтенд панели)
- Discord Application + Bot Token
- Для ValChecker — ключ [HenrikDev](https://docs.henrikdev.xyz/)

### 1. Клонирование и зависимости

```bash
git clone https://github.com/<your-org>/Cheterin_Bot_Dashboard.git
cd Cheterin_Bot_Dashboard

python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Заполните `.env` (токен бота, OAuth для панели, секреты сессии и т.д.).

### 2. Панель (frontend)

```bash
cd dashboard/frontend
npm install
npm run build
# разработка: npm run dev
```

### 3. Запуск

```bash
# из корня репозитория, с активированным venv
python main.py
```

Бот поднимает Discord-клиент и HTTP API панели.  
Пригласите бота на сервер → войдите в панель → выберите гильдию → включите нужные модули.

---

## ValChecker

Модуль статистики Valorant (раздел **Игры → ValChecker**).

| Команда | Назначение |
|---------|------------|
| `/val setup` | Привязка Riot ID, трекинг матчей, отвязка |
| `/val profile` | Профиль: обзор, статы, агенты, карты |
| `/val match` | Последний матч или история |
| `/val compare` | Сравнение двух игроков |
| `/val lb` | Топ сервера среди привязанных |
| `/val status` | Инциденты и очереди |

В панели: тумблер модуля, канал матчей, канал статус-алертов, интервал опроса (30–3600 с).  
В `.env` обязательно:

```env
HENRIK_API_KEY=your_key_here
# опционально:
# VALCHECKER_DB_PATH=valchecker.db
```

---

## Структура

```
├── main.py                 # точка входа бота
├── *_cog.py / *.py         # модули Discord
├── locales/                # RU / EN строки бота
├── dashboard/
│   ├── backend/            # aiohttp API
│   └── frontend/           # React-панель
├── requirements.txt
└── .env.example
```

---

## Разработка

```bash
# тесты бэкенда / логики бота
python -m pytest dashboard/backend/tests -q

# фронтенд
cd dashboard/frontend && npm test
```

Язык UI панели и ответы бота — **RU / EN** (настраивается в панели).

---

## Документы

- [Политика конфиденциальности](https://cheterin.online/privacy)
- [Условия использования](https://cheterin.online/terms)
- Встроенная документация модулей: [cheterin.online/docs](https://cheterin.online/docs)

---

## Лицензия

Проприетарный проект. Использование — по согласованию с владельцем.
