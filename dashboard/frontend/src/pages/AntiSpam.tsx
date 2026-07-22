import { Warning } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { fetchSpamSettings, updateSpamSettings, type SpamSettings } from '../api/client'
import { ModuleConfigPanel } from '../components/ModuleConfigPanel'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { useT } from '../context/LanguageContext'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

export function AntiSpamPage() {
  const t = useT()
  const [spam, setSpam] = useState<SpamSettings | null>(null)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    fetchSpamSettings()
      .then(setSpam)
      .catch(() => setError(t('antispam.errorLoad')))
  }, [t])

  const save = async () => {
    if (!spam) return
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateSpamSettings(spam)
      setSpam(updated)
      setSaved(t('common.saved'))
    } catch {
      setError(t('antispam.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  if (!spam) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      <div>
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Warning size={22} className="text-primary" />
          {t('antispam.title')}
        </h1>
        <p className="mt-1 text-sm text-muted">{t('antispam.intro')}</p>
      </div>

      <ModuleConfigPanel
        variant="antispam"
        title={t('antispam.channelsTitle')}
        intro={t('antispam.channelsIntro')}
      />

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
        {error && <p className="text-sm text-danger">{error}</p>}
        {saved && <p className="text-sm text-primary">{saved}</p>}
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? t('common.saving') : t('common.save')}
        </Button>
      </section>
    </div>
  )
}
