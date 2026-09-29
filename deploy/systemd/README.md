# systemd units for Cheterin (Oracle / Ubuntu)

Units in this folder replace the former tmux sessions **`chetmain`** (bot+dashboard) and **`chetlookup`** (Lookup API).

| Unit | Process | Old tmux |
|:---|:---|:---|
| `cheterin-bot.service` | `python main.py` (bot + dashboard aiohttp) | `chetmain` |
| `cheterin-lookup.service` | `lookup-api` `python app.py` (`127.0.0.1:8090`) | `chetlookup` |

Lookup SPA remains **nginx static** (`lookup/dist`); only the API is a systemd service.

## One-time install (operator on the VPS)

Do this manually when you are ready — agents do **not** SSH/install units for you.

```bash
cd ~/Cheterin_Bot_Dashboard

# Bot venv (if missing)
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# Lookup API venv (recommended; matches unit ExecStart)
python3 -m venv lookup-api/.venv
./lookup-api/.venv/bin/pip install -r lookup-api/requirements.txt

sudo cp deploy/systemd/cheterin-bot.service /etc/systemd/system/
sudo cp deploy/systemd/cheterin-lookup.service /etc/systemd/system/
sudo systemctl daemon-reload

# Stop legacy tmux sessions if still running
tmux kill-session -t chetmain 2>/dev/null || true
tmux kill-session -t chetlookup 2>/dev/null || true

sudo systemctl enable --now cheterin-bot.service
sudo systemctl enable --now cheterin-lookup.service
sudo systemctl status cheterin-bot.service cheterin-lookup.service --no-pager
```

Edit `User=`, `WorkingDirectory=`, and `ExecStart=` in the unit files if your home path is not `/home/ubuntu/Cheterin_Bot_Dashboard`.

Optional: allow passwordless restart for deploys:

```text
# /etc/sudoers.d/cheterin-deploy  (visudo)
ubuntu ALL=(root) NOPASSWD: /bin/systemctl restart cheterin-bot.service, /bin/systemctl restart cheterin-lookup.service, /bin/systemctl reload-or-restart cheterin-bot.service, /bin/systemctl reload-or-restart cheterin-lookup.service, /bin/systemctl is-active cheterin-bot.service, /bin/systemctl is-active cheterin-lookup.service, /bin/systemctl status cheterin-bot.service, /bin/systemctl status cheterin-lookup.service
```

## Day-to-day update

```bash
bash ~/Cheterin_Bot_Dashboard/update.sh
```

That script pulls git, installs Python deps (bot + lookup-api), builds **both** frontends, then `systemctl restart`s both units. See `scripts/update.sh`.

## Logs

```bash
journalctl -u cheterin-bot.service -f
journalctl -u cheterin-lookup.service -f
```
