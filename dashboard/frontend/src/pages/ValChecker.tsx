import { Crosshair } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  fetchChannels,
  fetchValCheckerSettings,
  saveValCheckerSettings,
  type ChannelInfo,
  type ValCheckerSettings,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

const POLL_MIN = 30
const POLL_MAX = 3600
const POLL_DEFAULT = 90

function clampPoll(value: number): number {
  if (!Number.isFinite(value)) return POLL_DEFAULT
  return Math.min(POLL_MAX, Math.max(POLL_MIN, Math.trunc(value)))
}

export function ValCheckerPage() {
  const t = useT()
  const [settings, setSettings] = useState<ValCheckerSettings | null>(null)
  const [baseline, setBaseline] = useState<ValCheckerSettings | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)
  const [pollDraft, setPollDraft] = useState('')

  useEffect(() => {
    let cancelled = false
    setError('')
    fetchValCheckerSettings()
      .then((data) => {
        if (cancelled) return
        setSettings(data)
        setBaseline(data)
        setPollDraft(String(data.poll_interval_sec))
      })
      .catch((err) => {
        if (!cancelled) setError(formatApiError(err, t, 'valchecker.errorLoad'))
      })
    fetchChannels()
      .then((ch) => {
        if (!cancelled) setChannels(ch)
      })
      .catch((err) => {
        if (!cancelled) setError(formatApiError(err, t, 'valchecker.errorChannels'))
      })
    return () => {
      cancelled = true
    }
  }, [t])

  if (!settings) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  const pollValid = (() => {
    const n = Number.parseInt(pollDraft, 10)
    return Number.isFinite(n) && n >= POLL_MIN && n <= POLL_MAX
  })()

  const dirty =
    !baseline ||
    settings.enabled !== baseline.enabled ||
    settings.match_channel_id !== baseline.match_channel_id ||
    settings.alert_channel_id !== baseline.alert_channel_id ||
    clampPoll(Number.parseInt(pollDraft, 10)) !== baseline.poll_interval_sec ||
    pollDraft !== String(baseline.poll_interval_sec)

  const enableWithoutMatch = settings.enabled && !settings.match_channel_id

  const save = async () => {
    if (!pollValid) {
      setError(t('apiError.invalid_poll_interval'))
      return
    }
    const payload: ValCheckerSettings = {
      ...settings,
      poll_interval_sec: clampPoll(Number.parseInt(pollDraft, 10)),
    }
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await saveValCheckerSettings(payload)
      setSettings(updated)
      setBaseline(updated)
      setPollDraft(String(updated.poll_interval_sec))
      setSaved(t('common.saved'))
    } catch (err) {
      setError(formatApiError(err, t, 'valchecker.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Crosshair size={22} className="text-primary" weight="bold" />
          {t('valchecker.title')}
        </h1>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => setSettings({ ...settings, enabled: v })}
          label={settings.enabled ? t('valchecker.moduleOn') : t('valchecker.moduleOff')}
        />
      </div>
      <p className="text-sm text-muted">{t('valchecker.intro')}</p>

      {error && <p className="text-sm text-danger">{error}</p>}
      {saved && <p className="text-sm text-primary">{saved}</p>}
      {enableWithoutMatch && (
        <p className="text-sm text-warning">{t('valchecker.warnNoMatchChannel')}</p>
      )}

      <Card className="flex flex-col gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-sm text-muted" htmlFor="vc-match-channel">
            {t('valchecker.matchChannel')}
          </label>
          <Select
            id="vc-match-channel"
            value={settings.match_channel_id}
            onChange={(id) => setSettings({ ...settings, match_channel_id: id })}
            options={channels}
            placeholder={t('valchecker.channelPlaceholder')}
            allowClear
            ariaLabel={t('valchecker.matchChannel')}
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm text-muted" htmlFor="vc-alert-channel">
            {t('valchecker.alertChannel')}
          </label>
          <Select
            id="vc-alert-channel"
            value={settings.alert_channel_id}
            onChange={(id) => setSettings({ ...settings, alert_channel_id: id })}
            options={channels}
            placeholder={t('valchecker.channelPlaceholder')}
            allowClear
            ariaLabel={t('valchecker.alertChannel')}
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm text-muted" htmlFor="vc-poll">
            {t('valchecker.pollInterval')}
          </label>
          <input
            id="vc-poll"
            type="number"
            min={POLL_MIN}
            max={POLL_MAX}
            value={pollDraft}
            onChange={(e) => setPollDraft(e.target.value)}
            onBlur={() => {
              const n = Number.parseInt(pollDraft, 10)
              if (Number.isFinite(n)) {
                const clamped = clampPoll(n)
                setPollDraft(String(clamped))
                setSettings({ ...settings, poll_interval_sec: clamped })
              } else {
                setPollDraft(String(settings.poll_interval_sec || POLL_DEFAULT))
              }
            }}
            className={inputClass}
          />
          <p className="text-xs text-muted">{t('valchecker.pollHint')}</p>
          {!pollValid && pollDraft !== '' && (
            <p className="text-xs text-danger">{t('apiError.invalid_poll_interval')}</p>
          )}
        </div>
      </Card>

      <div>
        <Button onClick={save} disabled={busy || !dirty || !pollValid}>
          {t('common.save')}
        </Button>
      </div>
    </div>
  )
}
