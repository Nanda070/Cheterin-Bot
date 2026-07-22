import { Confetti } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  fetchFunSettings,
  fetchWordleSettings,
  updateFunSettings,
  updateWordleSettings,
  type FunSettings,
  type WordleSettings,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

export function FunPage() {
  const t = useT()
  const [settings, setSettings] = useState<FunSettings | null>(null)
  const [wordle, setWordle] = useState<WordleSettings | null>(null)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    fetchFunSettings()
      .then(setSettings)
      .catch(() => setError(t('fun.errorLoad')))
    fetchWordleSettings()
      .then(setWordle)
      .catch(() => setError(t('fun.errorLoadWordle')))
  }, [t])

  if (!settings || !wordle) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateFunSettings(settings)
      setSettings(updated)
      const updatedWordle = await updateWordleSettings(wordle)
      setWordle(updatedWordle)
      setSaved(t('common.saved'))
    } catch (err) {
      setError(formatApiError(err, t, 'fun.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Confetti size={22} className="text-primary" />
          {t('fun.title')}
        </h1>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => setSettings({ ...settings, enabled: v })}
          label={settings.enabled ? t('common.moduleEnabled') : t('common.moduleDisabled')}
        />
      </div>
      <p className="text-sm text-muted">{t('fun.intro')}</p>

      {error && <p className="text-sm text-danger">{error}</p>}

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">{t('fun.roulette.title')}</h2>
        <p className="text-sm text-muted">{t('fun.roulette.desc')}</p>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="fun-roulette-timeout">
              {t('fun.roulette.timeout')}
            </label>
            <input
              id="fun-roulette-timeout"
              type="number"
              min={0}
              max={1440}
              value={settings.roulette_timeout_minutes}
              onChange={(e) => setSettings({ ...settings, roulette_timeout_minutes: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="fun-roulette-cooldown">
              {t('fun.roulette.cooldown')}
            </label>
            <input
              id="fun-roulette-cooldown"
              type="number"
              min={0}
              max={3600}
              value={settings.roulette_cooldown_sec}
              onChange={(e) => setSettings({ ...settings, roulette_cooldown_sec: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
        </div>
        <p className="text-xs text-muted">{t('fun.roulette.hint')}</p>
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">{t('fun.emojiRoulette.title')}</h2>
        <p className="text-sm text-muted">{t('fun.emojiRoulette.desc')}</p>
      </Card>

      <Card className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-foreground">{t('fun.autoEmoji.title')}</h2>
          <Toggle
            checked={settings.auto_emoji_enabled}
            onChange={(v) => setSettings({ ...settings, auto_emoji_enabled: v })}
            label={settings.auto_emoji_enabled ? t('fun.autoEmoji.on') : t('fun.autoEmoji.off')}
          />
        </div>
        <p className="text-sm text-muted">{t('fun.autoEmoji.desc')}</p>
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="fun-ae-chance">
              {t('fun.autoEmoji.chance')}
            </label>
            <input
              id="fun-ae-chance"
              type="number"
              min={1}
              max={100}
              value={settings.auto_emoji_chance_percent}
              onChange={(e) => setSettings({ ...settings, auto_emoji_chance_percent: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="fun-ae-interval">
              {t('fun.autoEmoji.interval')}
            </label>
            <input
              id="fun-ae-interval"
              type="number"
              min={0}
              max={86400}
              value={settings.auto_emoji_min_interval_sec}
              onChange={(e) => setSettings({ ...settings, auto_emoji_min_interval_sec: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="fun-ae-remove">
              {t('fun.autoEmoji.remove')}
            </label>
            <input
              id="fun-ae-remove"
              type="number"
              min={0}
              max={3600}
              value={settings.auto_emoji_remove_after_sec}
              onChange={(e) => setSettings({ ...settings, auto_emoji_remove_after_sec: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
        </div>
      </Card>

      <Card className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-foreground">{t('fun.wordle.title')}</h2>
          <Toggle
            checked={wordle.enabled}
            onChange={(v) => setWordle({ ...wordle, enabled: v })}
            label={wordle.enabled ? t('fun.wordle.enabled') : t('fun.wordle.disabled')}
          />
        </div>
        <p className="text-sm text-muted">{t('fun.wordle.desc')}</p>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="wordle-channel">
              {t('fun.wordle.channel')}
            </label>
            <input
              id="wordle-channel"
              type="text"
              inputMode="numeric"
              placeholder={t('fun.wordle.channelPlaceholder')}
              value={wordle.channel_id}
              onChange={(e) => setWordle({ ...wordle, channel_id: e.target.value.replace(/\D/g, '') })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="wordle-time">
              {t('fun.wordle.time')}
            </label>
            <input
              id="wordle-time"
              type="text"
              placeholder="09:00"
              value={wordle.announce_time}
              onChange={(e) => setWordle({ ...wordle, announce_time: e.target.value })}
              className={inputClass}
            />
          </div>
        </div>
        <p className="text-xs text-muted">{t('fun.wordle.hint')}</p>
      </Card>

      {saved && <p className="text-sm text-primary">{saved}</p>}
      <div>
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? t('common.saving') : t('common.save')}
        </Button>
      </div>
    </div>
  )
}
