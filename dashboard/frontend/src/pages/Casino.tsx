import { DiceThree, Plus, Trash } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  fetchCasinoSettings,
  updateCasinoSettings,
  fetchCasinoLeaderboard,
  type CasinoSettings,
  type CasinoLeaderboardEntry,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Toggle } from '../components/ui/Toggle'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

export function CasinoPage() {
  const [settings, setSettings] = useState<CasinoSettings | null>(null)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)

  // Leaderboard state
  const [lbMode, setLbMode] = useState<'slots' | 'bj' | 'total'>('total')
  const [lbType, setLbType] = useState<'wins' | 'losses'>('losses')
  const [lbPage, setLbPage] = useState(1)
  const [lbEntries, setLbEntries] = useState<CasinoLeaderboardEntry[]>([])
  const [lbTotal, setLbTotal] = useState(0)

  const reloadLeaderboard = () => {
    fetchCasinoLeaderboard(lbMode, lbType, lbPage)
      .then((res) => {
        setLbEntries(res.entries)
        setLbTotal(res.total)
      })
      .catch(() => {
        setLbEntries([])
        setLbTotal(0)
      })
  }

  useEffect(() => {
    fetchCasinoSettings()
      .then((res) => {
        if (!res.loss_roles) res.loss_roles = []
        setSettings(res)
      })
      .catch(() => setError('Не удалось загрузить настройки казино'))
  }, [])

  useEffect(() => {
    reloadLeaderboard()
  }, [lbMode, lbType, lbPage])

  if (!settings) {
    return <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateCasinoSettings(settings)
      if (!updated.loss_roles) updated.loss_roles = []
      setSettings(updated)
      setSaved('Сохранено.')
    } catch {
      setError('Не удалось сохранить настройки — проверьте поля')
    } finally {
      setBusy(false)
    }
  }

  const updateRole = (index: number, patch: Partial<CasinoSettings['loss_roles'][number]>) => {
    const roles = settings.loss_roles.map((r, i) => (i === index ? { ...r, ...patch } : r))
    setSettings({ ...settings, loss_roles: roles })
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <DiceThree size={22} className="text-primary" />
          Казино
        </h1>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => setSettings({ ...settings, enabled: v })}
          label={settings.enabled ? 'Включено' : 'Выключено'}
        />
      </div>
      <p className="text-sm text-muted">
        Слоты (3 барабана), монетка (орёл/решка) и блэкджек. Обе команды делят один кулдаун на игрока.
        Для работы казино необходим включённый модуль «Экономика».
      </p>

      {error && <p className="text-sm text-danger">{error}</p>}

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">Настройки игры</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="casino-edge">
              Преимущество казино, % (0–50; срезает выигрыш на этот процент)
            </label>
            <input
              id="casino-edge"
              type="number"
              min={0}
              max={50}
              value={settings.house_edge_percent}
              onChange={(e) => setSettings({ ...settings, house_edge_percent: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="casino-cooldown">
              Кулдаун на игрока, сек (0–300, общий)
            </label>
            <input
              id="casino-cooldown"
              type="number"
              min={0}
              max={300}
              value={settings.cooldown_sec}
              onChange={(e) => setSettings({ ...settings, cooldown_sec: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="casino-min-bet">
              Минимальная ставка
            </label>
            <input
              id="casino-min-bet"
              type="number"
              min={1}
              value={settings.min_bet}
              onChange={(e) => setSettings({ ...settings, min_bet: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="casino-max-bet">
              Максимальная ставка (0 — без лимита)
            </label>
            <input
              id="casino-max-bet"
              type="number"
              min={0}
              value={settings.max_bet}
              onChange={(e) => setSettings({ ...settings, max_bet: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
        </div>
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">🏅 Выдача ролей за проигрыши</h2>
        <p className="text-sm text-muted">
          Бот будет автоматически выдавать указанную роль, если участник достиг порога проигрышей.
          Роль выдаётся один раз.
        </p>
        {settings.loss_roles.map((item, index) => (
          <div key={index} className="flex flex-col gap-2 rounded-control border border-border p-3 sm:flex-row sm:items-center">
            <select
              value={item.game}
              onChange={(e) => updateRole(index, { game: e.target.value as any })}
              className={inputClass}
            >
              <option value="slots">Слоты/Монетка</option>
              <option value="bj">Блэкджек</option>
              <option value="total">Суммарно (Слоты+БЖ)</option>
            </select>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted">Порог:</span>
              <input
                type="number"
                min={1}
                value={item.threshold || ''}
                onChange={(e) => updateRole(index, { threshold: Number(e.target.value) })}
                className={`${inputClass} w-24`}
              />
            </div>
            <input
              type="text"
              placeholder="ID роли"
              value={item.role_id}
              onChange={(e) => updateRole(index, { role_id: e.target.value.replace(/\D/g, '') })}
              className={`${inputClass} flex-1`}
            />
            <Button
              variant="ghost"
              onClick={() => setSettings({ ...settings, loss_roles: settings.loss_roles.filter((_, i) => i !== index) })}
            >
              <Trash size={16} />
            </Button>
          </div>
        ))}
        <div>
          <Button
            variant="secondary"
            onClick={() =>
              setSettings({
                ...settings,
                loss_roles: [...settings.loss_roles, { game: 'total', threshold: 10, role_id: '' }],
              })
            }
          >
            <Plus size={16} /> Добавить роль
          </Button>
        </div>
      </Card>

      {saved && <p className="text-sm text-primary">{saved}</p>}
      <div>
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? 'Сохраняем…' : 'Сохранить'}
        </Button>
      </div>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">🏆 Лидерборд (всего записей: {lbTotal})</h2>
        <div className="flex flex-wrap gap-2">
          <Button variant={lbType === 'losses' ? 'primary' : 'secondary'} onClick={() => setLbType('losses')}>
            ❌ Проигрыши
          </Button>
          <Button variant={lbType === 'wins' ? 'primary' : 'secondary'} onClick={() => setLbType('wins')}>
            🏆 Победы
          </Button>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant={lbMode === 'total' ? 'primary' : 'secondary'} onClick={() => setLbMode('total')}>
            📊 Общий
          </Button>
          <Button variant={lbMode === 'slots' ? 'primary' : 'secondary'} onClick={() => setLbMode('slots')}>
            🎰 Слоты/Монетка
          </Button>
          <Button variant={lbMode === 'bj' ? 'primary' : 'secondary'} onClick={() => setLbMode('bj')}>
            🎴 Блэкджек
          </Button>
        </div>

        {lbEntries.length === 0 ? (
          <p className="text-sm text-muted">Таблица пуста.</p>
        ) : (
          <div className="flex flex-col gap-2 mt-2">
            {lbEntries.map((entry, i) => {
              const rank = (lbPage - 1) * 50 + i + 1
              let statsStr = ''
              if (lbMode === 'total') {
                if (lbType === 'wins') {
                  statsStr = `Всего: ${entry.slots_wins + entry.bj_wins} 🏆 (🎰 ${entry.slots_wins} | 🎴 ${entry.bj_wins})`
                } else {
                  statsStr = `Всего: ${entry.slots_losses + entry.bj_losses} ❌ (🎰 ${entry.slots_losses} | 🎴 ${entry.bj_losses})`
                }
              } else if (lbMode === 'slots') {
                statsStr = `🎰 ${lbType === 'wins' ? entry.slots_wins + ' 🏆' : entry.slots_losses + ' ❌'}`
              } else {
                statsStr = `🎴 ${lbType === 'wins' ? entry.bj_wins + ' 🏆' : entry.bj_losses + ' ❌'}`
              }

              return (
                <div key={entry.user_id} className="flex items-center gap-3 rounded border border-border p-2">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center font-bold text-muted">#{rank}</div>
                  {entry.avatar ? (
                    <img src={entry.avatar} alt="" className="h-8 w-8 shrink-0 rounded-full" />
                  ) : (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-surface-hover">
                      <span className="text-xs font-bold text-muted">{entry.username.slice(0, 2).toUpperCase()}</span>
                    </div>
                  )}
                  <div className="flex flex-1 flex-col truncate">
                    <span className="truncate text-sm font-medium text-foreground">{entry.username}</span>
                    <span className="text-xs text-muted">{statsStr}</span>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        <div className="flex items-center gap-2 mt-2">
          <Button
            variant="secondary"
            disabled={lbPage === 1}
            onClick={() => setLbPage(Math.max(1, lbPage - 1))}
          >
            Назад
          </Button>
          <span className="text-sm text-muted">
            Страница {lbPage}
          </span>
          <Button
            variant="secondary"
            disabled={lbEntries.length < 50}
            onClick={() => setLbPage(lbPage + 1)}
          >
            Вперёд
          </Button>
        </div>
      </Card>
    </div>
  )
}
