import { ShieldStar } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  fetchAntiRaidSettings,
  fetchSpamSettings,
  fetchTempbanSettings,
  updateAntiRaidSettings,
  updateSpamSettings,
  updateTempbanSettings,
  type AntiRaidSettings,
  type SpamSettings,
  type TempbanSettings,
} from '../api/client'
import { EMPTY_EMBED_SPEC, EmbedEditor } from '../components/EmbedEditor'
import { ModuleConfigPanel } from '../components/ModuleConfigPanel'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

export function AntiRaidPage() {
  const t = useT()
  const [settings, setSettings] = useState<AntiRaidSettings | null>(null)
  const [spam, setSpam] = useState<SpamSettings | null>(null)
  const [tempban, setTempban] = useState<TempbanSettings | null>(null)
  const [error, setError] = useState('')
  const [spamError, setSpamError] = useState('')
  const [tempbanError, setTempbanError] = useState('')
  const [saved, setSaved] = useState('')
  const [spamSaved, setSpamSaved] = useState('')
  const [tempbanSaved, setTempbanSaved] = useState('')
  const [busy, setBusy] = useState(false)
  const [spamBusy, setSpamBusy] = useState(false)
  const [tempbanBusy, setTempbanBusy] = useState(false)

  useEffect(() => {
    Promise.all([fetchAntiRaidSettings(), fetchSpamSettings(), fetchTempbanSettings()])
      .then(([antiRaid, spamSettings, tb]) => {
        setSettings(antiRaid)
        setSpam(spamSettings)
        setTempban({ ...tb, log_embed: { ...EMPTY_EMBED_SPEC, ...tb.log_embed } })
      })
      .catch(() => setError(t('antiraid.errorLoad')))
  }, [t])

  const saveSpam = async () => {
    if (!spam) return
    setSpamBusy(true)
    setSpamError('')
    setSpamSaved('')
    try {
      const updated = await updateSpamSettings(spam)
      setSpam(updated)
      setSpamSaved(t('common.saved'))
    } catch {
      setSpamError(t('antiraid.errorSave'))
    } finally {
      setSpamBusy(false)
    }
  }

  const saveTempban = async () => {
    if (!tempban) return
    setTempbanBusy(true)
    setTempbanError('')
    setTempbanSaved('')
    try {
      const updated = await updateTempbanSettings(tempban)
      setTempban({ ...updated, log_embed: { ...EMPTY_EMBED_SPEC, ...updated.log_embed } })
      setTempbanSaved(t('common.saved'))
    } catch {
      setTempbanError(t('antiraid.errorSave'))
    } finally {
      setTempbanBusy(false)
    }
  }

  if (!settings || !spam || !tempban) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateAntiRaidSettings(settings)
      setSettings(updated)
      setSaved(t('common.saved'))
    } catch {
      setError(t('antiraid.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <ShieldStar size={22} className="text-primary" />
          {t('antiraid.title')}
        </h1>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => setSettings({ ...settings, enabled: v })}
          label={settings.enabled ? t('antiraid.moduleOn') : t('antiraid.moduleOff')}
        />
      </div>
      <p className="text-sm text-muted">
        {t('antiraid.intro.beforeBold')}
        <strong>{t('antiraid.intro.bold')}</strong>
        {t('antiraid.intro.afterBold')}
      </p>

      {error && <p className="text-sm text-danger">{error}</p>}

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">{t('antiraid.spikeTitle')}</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="ar-window">
              {t('antiraid.windowSec')}
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
              {t('antiraid.threshold')}
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
              {t('antiraid.minAccountAge')}
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
        <p className="text-xs text-muted">{t('antiraid.spikeHint')}</p>
      </Card>

      <Card className="flex flex-col gap-3">
        <h2 className="font-semibold text-foreground">{t('antiraid.reactionTitle')}</h2>
        <div className="flex items-center justify-between">
          <span className="text-sm text-foreground">{t('antiraid.actionLockdown')}</span>
          <Toggle
            checked={settings.action_lockdown}
            onChange={(v) => setSettings({ ...settings, action_lockdown: v })}
            label={settings.action_lockdown ? t('common.yes') : t('common.no')}
          />
        </div>
        <div className="flex flex-col gap-1 sm:max-w-xs">
          <label className="text-sm text-muted" htmlFor="ar-slowmode">
            {t('antiraid.slowmode')}
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
            {t('antiraid.cooldown')}
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
          {busy ? t('common.saving') : t('common.save')}
        </Button>
      </div>

      <div className="border-t border-border pt-6">
        <ModuleConfigPanel
          variant="antispam"
          title={t('antiraid.antispamTitle')}
          intro={t('antiraid.antispamIntro')}
        />
      </div>

      <section className="flex flex-col gap-4 border-t border-border pt-6">
        <h2 className="font-semibold text-foreground">{t('antiraid.spamDetectTitle')}</h2>
        <p className="text-sm text-muted">{t('antiraid.spamDetectIntro')}</p>
        <Card className="grid gap-3 sm:grid-cols-3">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="spam-limit-att">
              {t('antiraid.spamLimitAttachments')}
            </label>
            <input
              id="spam-limit-att"
              type="number"
              min={1}
              max={50}
              value={spam.limit_with_attachments}
              onChange={(e) => setSpam({ ...spam, limit_with_attachments: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="spam-limit-text">
              {t('antiraid.spamLimitText')}
            </label>
            <input
              id="spam-limit-text"
              type="number"
              min={1}
              max={50}
              value={spam.limit_without_attachments}
              onChange={(e) => setSpam({ ...spam, limit_without_attachments: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-muted" htmlFor="spam-window">
              {t('antiraid.spamTimeWindow')}
            </label>
            <input
              id="spam-window"
              type="number"
              min={10}
              max={600}
              value={spam.time_window_sec}
              onChange={(e) => setSpam({ ...spam, time_window_sec: Number(e.target.value) })}
              className={inputClass}
            />
          </div>
        </Card>
        <p className="text-xs text-muted">{t('antiraid.spamDetectHint')}</p>
        {spamError && <p className="text-sm text-danger">{spamError}</p>}
        {spamSaved && <p className="text-sm text-primary">{spamSaved}</p>}
        <Button variant="primary" onClick={saveSpam} disabled={spamBusy}>
          {spamBusy ? t('common.saving') : t('common.save')}
        </Button>
      </section>

      <section className="flex flex-col gap-4 border-t border-border pt-6">
        <h2 className="font-semibold text-foreground">{t('messageCustomizer.tempbanTitle')}</h2>
        <p className="text-sm text-muted">{t('messageCustomizer.tempbanIntro')}</p>
        <Card className="flex flex-col gap-3">
          <Toggle
            checked={tempban.dm_enabled}
            onChange={(v) => setTempban({ ...tempban, dm_enabled: v })}
            label={t('messageCustomizer.tempbanDmEnabled')}
          />
          <label className="text-sm text-muted">{t('messageCustomizer.tempbanDmMessage')}</label>
          <textarea
            value={tempban.dm_message}
            onChange={(e) => setTempban({ ...tempban, dm_message: e.target.value })}
            className={inputClass}
            rows={4}
          />
          <Toggle
            checked={tempban.log_enabled}
            onChange={(v) => setTempban({ ...tempban, log_enabled: v })}
            label={t('messageCustomizer.tempbanLogEnabled')}
          />
          <label className="text-sm text-muted">{t('messageCustomizer.tempbanUnbanReason')}</label>
          <input
            value={tempban.unban_reason}
            onChange={(e) => setTempban({ ...tempban, unban_reason: e.target.value })}
            className={inputClass}
          />
        </Card>
        <EmbedEditor
          embed={tempban.log_embed}
          onEmbedChange={(log_embed) => setTempban({ ...tempban, log_embed })}
          showContent={false}
        />
        {tempbanError && <p className="text-sm text-danger">{tempbanError}</p>}
        {tempbanSaved && <p className="text-sm text-primary">{tempbanSaved}</p>}
        <Button variant="primary" onClick={saveTempban} disabled={tempbanBusy}>
          {tempbanBusy ? t('common.saving') : t('common.save')}
        </Button>
      </section>
    </div>
  )
}
