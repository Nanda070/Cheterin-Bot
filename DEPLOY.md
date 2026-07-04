# Деплой на продакшен (Oracle Cloud, Ubuntu)

Этот гайд предполагает: Oracle Cloud compute instance с Ubuntu уже создан, есть SSH-доступ, домен `cheterin.online` уже куплен и панель DNS-провайдера доступна. Код уже перенесён на сервер через `git clone` (репозиторий `https://github.com/Nanda070/Cheterin_Bot_Dashboard.git`).

## 1. DNS

В панели вашего DNS-провайдера (там, где куплен `cheterin.online`) добавьте A-запись:

| Тип | Имя | Значение |
|-----|-----|----------|
| A   | `@` (или `cheterin.online`) | публичный IP сервера |
| A   | `www` | публичный IP сервера |

Подождите распространения DNS (обычно от нескольких минут до часа) перед шагом с certbot — certbot проверяет, что домен резолвится на этот сервер.

## 2. Oracle Cloud Security List

В консоли Oracle Cloud: **Networking → Virtual Cloud Networks → (ваша VCN) → Security Lists → (список по умолчанию) → Ingress Rules → Add Ingress Rules**.

Добавьте два правила (если ещё не добавлены):

- Source CIDR `0.0.0.0/0`, IP Protocol `TCP`, Destination Port Range `80`
- Source CIDR `0.0.0.0/0`, IP Protocol `TCP`, Destination Port Range `443`

Это отдельный уровень firewall от `ufw` на самой машине — оба должны быть открыты одновременно, иначе соединение не пройдёт даже при правильно настроенном `ufw`.

## 3. Firewall на сервере (ufw)

Подключитесь по SSH к серверу и выполните:

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status
```

Убедитесь, что порт 22 (SSH) в списке разрешённых, прежде чем включать `ufw`, если он ещё не включён (`sudo ufw enable`) — иначе можно потерять доступ к серверу.

## 4. Системные зависимости

```bash
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx tmux python3 python3-venv python3-pip
```

Для сборки фронтенда нужен Node.js (LTS, через NodeSource, так как версия в стандартном репозитории Ubuntu обычно старая):

```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
node --version
```

## 5. Обновление кода

Код уже склонирован на сервер. Перед каждым обновлением (включая внедрение раздачи статики):

```bash
cd ~/ChetMain
git pull origin main
```

## 6. Правки `.env` на сервере

Откройте `.env` в корне проекта на сервере и измените/добавьте следующие значения (остальные ключи — токены, ID каналов и ролей — не трогайте, они те же, что и в разработке):

```
DISCORD_OAUTH_REDIRECT_URI=https://cheterin.online/api/auth/discord/callback
DASHBOARD_FRONTEND_URL=
DASHBOARD_FRONTEND_DIST=/home/<ваш-пользователь>/ChetMain/dashboard/frontend/dist
```

Замените `<ваш-пользователь>` на реальное имя пользователя на сервере (проверить командой `whoami`), и используйте **абсолютный путь** — не относительный, так как `python main.py` может быть запущен из tmux-сессии с произвольным текущим рабочим каталогом.

Также добавьте `https://cheterin.online/api/auth/discord/callback` в список Redirect URIs в [Discord Developer Portal](https://discord.com/developers/applications) → ваше приложение → OAuth2 → Redirects. **Не удаляйте** существующий `http://localhost:8080/...` URI — оба могут сосуществовать, это нужно для локальной разработки.

## 7. Установка зависимостей и сборка

```bash
cd ~/ChetMain
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cd dashboard/frontend
npm ci
npm run build
cd ~/ChetMain
```

Сборка фронтенда создаёт `dashboard/frontend/dist/` — именно на эту папку должен указывать `DASHBOARD_FRONTEND_DIST` из шага 6.

## 8. nginx + TLS (certbot)

Создайте конфиг `/etc/nginx/sites-available/cheterin`:

```nginx
server {
    listen 80;
    server_name cheterin.online www.cheterin.online;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Включите сайт и перезапустите nginx:

```bash
sudo ln -s /etc/nginx/sites-available/cheterin /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Получите TLS-сертификат (certbot сам допишет `listen 443 ssl` и настроит редирект с http на https в этом файле):

```bash
sudo certbot --nginx -d cheterin.online -d www.cheterin.online
```

## 9. Запуск бота+дашборда в tmux

tmux используется вместо systemd осознанно — процесс не переживёт перезагрузку сервера, после ребута нужно будет зайти по SSH и перезапустить вручную.

```bash
cd ~/ChetMain
tmux new -s chetmain
source venv/bin/activate
python main.py
```

Отсоединиться от сессии, оставив процесс работать: `Ctrl+B`, затем `D`.

Подключиться обратно после переподключения по SSH:

```bash
tmux attach -t chetmain
```

Посмотреть список запущенных tmux-сессий: `tmux ls`.

## 10. Проверка

1. Откройте `https://cheterin.online` в браузере — должна открыться страница логина.
2. Пройдите логин через Discord OAuth — должно перекинуть на главную страницу дашборда.
3. Откройте любую страницу с client-side маршрутом (например раздел "Сетки" → конкретная сетка) и сделайте обновление страницы (F5) — страница должна открыться заново, а не выдать 404 (это и есть проверка SPA-fallback в проде).
4. Проверьте, что бот онлайн на Discord-сервере как обычно.
