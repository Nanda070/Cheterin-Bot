# Деплой (VPS)

Кратко для сервера Linux: `venv`, `tmux`, сессия **`chetmain`**.

## Обновление на сервере

Одна команда из корня репозитория (после `git pull` скрипт сам подтянет зависимости и соберёт фронт):

```bash
chmod +x update.sh scripts/update.sh   # один раз, если git не сохранил +x
./update.sh
```

Или полный путь:

```bash
~/Cheterin_Bot_Dashboard/update.sh
```

Скрипт: `git pull` → `venv` + `pip install -r requirements.txt` → `npm ci` / `npm install` и `npm run build` в `dashboard/frontend` → `tmux attach -t chetmain`.

Если сессии нет:

```bash
tmux new -s chetmain
tmux ls
```
