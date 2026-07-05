# 8. Для разработчиков

Хотите запустить ChetBot на своем оборудовании? Следуйте этим шагам.

#### Требования

* **Python 3.10+** (Рекомендуется 3.11)
* **Node.js LTS** (Для фронтенда)

#### Шаг 1. Клонирование и зависимости

```bash
git clone https://github.com/Nanda070/Cheterin_Bot_Dashboard.git
cd Cheterin_Bot_Dashboard
python -m venv venv
source venv/bin/activate  # на Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Шаг 2. Конфигурация (.env)

Создайте файл `.env` в корне проекта:

```env
BOT_TOKEN=Твой_Токен_Из_Discord_Developer_Portal
GUILD_ID=ID_Сервера
DISCORD_OAUTH_REDIRECT_URI=http://localhost:8080/api/auth/discord/callback
```

> **Внимание!** Обязательно добавьте `http://localhost:8080/api/auth/discord/callback` в список **Redirect URIs** в настройках вашего бота на портале Discord! Без этого вход в дашборд не будет работать.

#### Шаг 3. Сборка дашборда

```bash
cd dashboard/frontend
npm install
npm run build
cd ../..
```

#### Шаг 4. Запуск

```bash
python main.py
```

Откройте браузер и перейдите по адресу `http://localhost:8080`.

_(Подробные инструкции по деплою на Linux Ubuntu (VPS) с использованием Nginx и Certbot находятся в файле `DEPLOY.md` в корне репозитория)._



_Документация ChetBot. Создано для идеального администрирования._
