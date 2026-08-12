# Деплой (VPS)

Кратко для сервера Linux: `venv`, `tmux`, сессия **`chetmain`**.

## Обновление на сервере

Одна команда (из любой директории; `cd` не нужен):

```bash
bash ~/Cheterin_Bot_Dashboard/update.sh
```

**Не используйте `sudo`.** В отличие от Cheterin-Media (`sudo bash ~/Cheterin-Media/deploy/oracle/build-web.sh`), здесь `git` / `pip` / `npm` / `tmux` должны идти от пользователя деплоя. `sudo` сломает активацию `venv` и `tmux attach`.

`chmod +x` не нужен — скрипт запускается через `bash`.

Скрипт сам находит корень репозитория → `git pull` → `venv` + `pip install -r requirements.txt` → `npm ci` / `npm install` и `npm run build` в `dashboard/frontend` → `tmux attach -t chetmain`.

Если сессии нет:

```bash
tmux new -s chetmain
tmux ls
```
