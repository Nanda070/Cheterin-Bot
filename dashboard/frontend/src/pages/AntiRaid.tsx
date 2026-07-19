import { ShieldStar } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { fetchAntiRaidSettings, updateAntiRaidSettings, type AntiRaidSettings } from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Toggle } from '../components/ui/Toggle'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

export function AntiRaidPage() {
  const [settings, setSettings] = useState<AntiRaidSettings | null>(null)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    fetchAntiRaidSettings()
      .then(setSettings)
      .catch(() => setError('Не удалось загрузить настройки модуля «Антирейд»'))
  }, [])

  if (!settings) {
    return <p className="text-sm text-muted">{error || 'Загрузка…'}</p>
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateAntiRaidSettings(settings)
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
          <ShieldStar size={22} className="text-primary" />
          Антирейд
        </h1>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => setSettings({ ...settings, enabled: v })}
          label={settings.enabled ? 'Модуль включён' : 'Модуль выключен'}
        />
      </div>
      <p className="text-sm text-muted">
        Модуль <strong>выключен по умолчанию</strong> и не имеет никакого эффекта, пока вы явно не включите его здесь
        — не связан с остальными настройками бота. При включении бот следит за всплесками входов новых участников: если
        подряд входит N «свежих» аккаунтов за короткое время, автоматически включается уже знакомый Lockdown-режим
        (снятие прав массовых упоминаний у ролей) и, по желанию, slowmode во всех текстовых каналах.
      </p>

      {error && <p className="text-sm text-danger">{error}</p>}

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">Детект всплеска</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="ar-window">
              Окно, сек (1–3600)
            </label>
            <input
              id="ar-window"
              type="number"
              min={1}
              max={3600}
              value={settings.join_window_sec}
              onChange={(e) => setSettings({ ...settings, join_window_sec: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="ar-threshold">
              Порог входов в окне (1–1000)
            </label>
            <input
              id="ar-threshold"
              type="number"
              min={1}
              max={1000}
              value={settings.join_threshold}
              onChange={(e) => setSettings({ ...settings, join_threshold: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1 sm:col-span-2">
            <label className="text-sm text-muted" htmlFor="ar-age">
              Минимальный возраст аккаунта, ч (0 — считать все входы, без фильтра)
            </label>
            <input
              id="ar-age"
              type="number"
              min={0}
              max={8760}
              value={settings.min_account_age_hours}
              onChange={(e) => setSettings({ ...settings, min_account_age_hours: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
        </div>
        <p className="text-xs text-muted">
          Считаются только входы аккаунтов младше указанного возраста — так обычный наплыв реальных людей (например,
          после рекламы) не спутать с рейдом ботов.
        </p>
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">Реакция на срабатывание</h2>
        <div className="flex items-center justify-between">
          <span className="text-sm text-foreground">Включать Lockdown (антиспам-режим)</span>
          <Toggle
            checked={settings.action_lockdown}
            onChange={(v) => setSettings({ ...settings, action_lockdown: v })}
            label={settings.action_lockdown ? 'Да' : 'Нет'}
          />
        </div>
        <div className="flex flex-col gap-1 sm:max-w-xs">
          <label className="text-sm text-muted" htmlFor="ar-slowmode">
            Slowmode во всех текстовых каналах, сек (0 — не включать, до 21600)
          </label>
          <input
            id="ar-slowmode"
            type="number"
            min={0}
            max={21600}
            value={settings.action_slowmode_sec}
            onChange={(e) => setSettings({ ...settings, action_slowmode_sec: Number(e.target.value) })}
            className={inputClass}
          />
        </div>
        <div className="flex flex-col gap-1 sm:max-w-xs">
          <label className="text-sm text-muted" htmlFor="ar-cooldown">
            Кулдаун повторного срабатывания, мин (0–1440)
          </label>
          <input
            id="ar-cooldown"
            type="number"
            min={0}
            max={1440}
            value={settings.cooldown_minutes}
            onChange={(e) => setSettings({ ...settings, cooldown_minutes: Number(e.target.value) })}
            className={inputClass}
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
  )
}
