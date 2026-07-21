import { Gear, ListChecks, MaskHappy } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  fetchChannels,
  fetchMafiaGames,
  fetchMafiaSettings,
  updateMafiaSettings,
  type ChannelInfo,
  type MafiaGameSummary,
  type MafiaSettings,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'

type Tab = 'settings' | 'games'

const TABS: { key: Tab; label: string; icon: typeof Gear }[] = [
  { key: 'settings', label: 'Настройки', icon: Gear },
  { key: 'games', label: 'Активные игры', icon: ListChecks },
]

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

const PHASE_LABEL: Record<string, string> = {
  lobby: 'Лобби',
  night: 'Ночь',
  day_discussion: 'Обсуждение',
  day_vote: 'Голосование',
  ended: 'Завершена',
}

export function MafiaPage() {
  const [tab, setTab] = useState<Tab>('settings')
  const [settings, setSettings] = useState<MafiaSettings | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)

  const [games, setGames] = useState<MafiaGameSummary[] | null>(null)

  useEffect(() => {
    Promise.all([fetchMafiaSettings(), fetchChannels()])
      .then(([s, ch]) => {
        setSettings(s)
        setChannels(ch)
      })
      .catch(() => setError('Не удалось загрузить настройки модуля «Мафия»'))
  }, [])

  useEffect(() => {
    if (tab !== 'games') return
    fetchMafiaGames()
      .then(setGames)
      .catch(() => setError('Не удалось загрузить список игр'))
  }, [tab])

  if (!settings) {
    return <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
  }

  const patch = (updater: (prev: MafiaSettings) => MafiaSettings) => {
    setSettings((prev) => (prev ? updater(prev) : prev))
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateMafiaSettings(settings)
      setSettings(updated)
      setSaved('Сохранено.')
    } catch {
      setError('Не удалось сохранить настройки — проверьте поля')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <MaskHappy size={22} className="text-primary" />
          Мафия
        </h1>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => setSettings({ ...settings, enabled: v })}
          label={settings.enabled ? 'Модуль включён' : 'Модуль выключен'}
        />
      </div>
      <p className="text-sm text-muted">
        Игра «Мафия»: лобби и старт через команду /мафия-игра, а весь матч — роль, список игроков, таймер, ночные
        действия и дневное голосование за казнь — на персональной ссылке каждого игрока на дашборде. Пока модуль
        выключен, команда /мафия-игра отвечает «Модуль отключён».
      </p>

      {error && <p className="text-sm text-danger">{error}</p>}

      <div className="flex gap-1 border-b border-border">
        {TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-sm transition-colors ${
              tab === key ? 'border-primary text-foreground' : 'border-transparent text-muted hover:text-foreground'
            }`}
          >
            <Icon size={15} />
            {label}
          </button>
        ))}
      </div>

      {tab === 'settings' && (
        <div className="flex flex-col gap-4">
          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">Игроки по умолчанию</h2>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="mafia-min-players">
                  Минимум игроков (5–99)
                </label>
                <input
                  id="mafia-min-players"
                  type="number"
                  min={5}
                  max={99}
                  value={settings.default_min_players}
                  onChange={(e) => patch((p) => ({ ...p, default_min_players: Number(e.target.value) }))}
                  className={inputClass}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="mafia-max-players">
                  Максимум игроков (5–99)
                </label>
                <input
                  id="mafia-max-players"
                  type="number"
                  min={5}
                  max={99}
                  value={settings.default_max_players}
                  onChange={(e) => patch((p) => ({ ...p, default_max_players: Number(e.target.value) }))}
                  className={inputClass}
                />
              </div>
            </div>
          </Card>

          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">Таймеры по умолчанию (сек)</h2>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="mafia-night-timer">
                  Ночь (10–3600)
                </label>
                <input
                  id="mafia-night-timer"
                  type="number"
                  min={10}
                  max={3600}
                  value={settings.default_night_timer_sec}
                  onChange={(e) => patch((p) => ({ ...p, default_night_timer_sec: Number(e.target.value) }))}
                  className={inputClass}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="mafia-discussion-timer">
                  Обсуждение (10–3600)
                </label>
                <input
                  id="mafia-discussion-timer"
                  type="number"
                  min={10}
                  max={3600}
                  value={settings.default_day_discussion_timer_sec}
                  onChange={(e) => patch((p) => ({ ...p, default_day_discussion_timer_sec: Number(e.target.value) }))}
                  className={inputClass}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-sm text-muted" htmlFor="mafia-vote-timer">
                  Голосование (10–3600)
                </label>
                <input
                  id="mafia-vote-timer"
                  type="number"
                  min={10}
                  max={3600}
                  value={settings.default_day_vote_timer_sec}
                  onChange={(e) => patch((p) => ({ ...p, default_day_vote_timer_sec: Number(e.target.value) }))}
                  className={inputClass}
                />
              </div>
            </div>
          </Card>

          <Card className="flex flex-col gap-3">
            <h2 className="font-semibold text-foreground">Логи</h2>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-muted" htmlFor="mafia-log-channel">
                Канал логов результатов игр
              </label>
              <Select
                id="mafia-log-channel"
                value={settings.log_channel_id}
                onChange={(id) => patch((p) => ({ ...p, log_channel_id: id }))}
                options={channels}
                placeholder="Не задано"
              />
            </div>
          </Card>

          {saved && <p className="text-sm text-primary">{saved}</p>}
          <div>
            <Button variant="primary" onClick={save} disabled={busy}>
              {busy ? 'Сохраняем…' : 'Сохранить'}
            </Button>
          </div>
        </div>
      )}

      {tab === 'games' && (
        <div className="flex flex-col gap-3">
          {!games && <p className="text-sm text-muted">Загрузка…</p>}
          {games && games.length === 0 && <p className="text-sm text-muted">Активных игр нет.</p>}
          {games?.map((game) => (
            <Card key={game.id} className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-foreground">
                  Игра #{game.id} · {game.channel_name}
                </p>
                <p className="text-xs text-muted">
                  {PHASE_LABEL[game.phase] ?? game.phase} · раунд {game.round_number} · {game.alive_count}/
                  {game.player_count} живы
                </p>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
