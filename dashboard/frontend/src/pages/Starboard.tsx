import { Star } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  fetchChannels,
  fetchStarboard,
  updateStarboard,
  type ChannelInfo,
  type StarboardSettings,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

export function StarboardPage() {
  const t = useT()
  const [settings, setSettings] = useState<StarboardSettings | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    Promise.all([fetchStarboard(), fetchChannels()])
      .then(([data, ch]) => {
        setSettings(data)
        setChannels(ch)
      })
      .catch((err) => setError(formatApiError(err, t, 'starboard.errorLoad')))
  }, [t])

  if (!settings) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateStarboard(settings)
      setSettings(updated)
      setSaved(t('common.saved'))
    } catch (err) {
      setError(formatApiError(err, t, 'starboard.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Star size={22} className="text-primary" weight="fill" />
          {t('starboard.title')}
        </h1>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => setSettings({ ...settings, enabled: v })}
          label={settings.enabled ? t('starboard.moduleOn') : t('starboard.moduleOff')}
        />
      </div>
      <p className="text-sm text-muted">{t('starboard.intro')}</p>

      {error && <p className="text-sm text-danger">{error}</p>}
      {saved && <p className="text-sm text-primary">{saved}</p>}

      <Card className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-sm text-muted">{t('starboard.channel')}</label>
          <Select
            value={settings.channel_id}
            onChange={(id) => setSettings({ ...settings, channel_id: id })}
            options={channels}
            placeholder={t('starboard.channelPlaceholder')}
          />
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="sb-emoji">
              {t('starboard.emoji')}
            </label>
            <input
              id="sb-emoji"
              value={settings.emoji}
              onChange={(e) => setSettings({ ...settings, emoji: e.target.value })}
              className={inputClass}
              maxLength={64}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="sb-threshold">
              {t('starboard.threshold')}
            </label>
            <input
              id="sb-threshold"
              type="number"
              min={1}
              max={100}
              value={settings.threshold}
              onChange={(e) =>
                setSettings({ ...settings, threshold: Number(e.target.value) })
              }
              className={inputClass}
            />
          </div>
        </div>
        <Toggle
          checked={settings.self_star}
          onChange={(v) => setSettings({ ...settings, self_star: v })}
          label={t('starboard.selfStar')}
        />
        <Toggle
          checked={settings.ignore_nsfw}
          onChange={(v) => setSettings({ ...settings, ignore_nsfw: v })}
          label={t('starboard.ignoreNsfw')}
        />
      </Card>

      <div>
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? t('common.saving') : t('common.save')}
        </Button>
      </div>
    </div>
  )
}
