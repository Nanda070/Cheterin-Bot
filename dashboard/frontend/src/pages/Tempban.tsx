import { Clock } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  fetchTempbanSettings,
  publishTempbanWarning,
  updateTempbanSettings,
  type TempbanAction,
  type TempbanSettings,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { ModuleConfigPanel } from '../components/ModuleConfigPanel'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

const ACTIONS: TempbanAction[] = ['softban', 'ban', 'disabled']

export function TempbanPage() {
  const t = useT()
  const [tempban, setTempban] = useState<TempbanSettings | null>(null)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)
  const [publishBusy, setPublishBusy] = useState(false)

  useEffect(() => {
    fetchTempbanSettings()
      .then(setTempban)
      .catch(() => setError(t('tempban.errorLoad')))
  }, [t])

  const save = async () => {
    if (!tempban) return
    setBusy(true)
    setError('')
    setSaved('')
    try {
      const updated = await updateTempbanSettings(tempban)
      setTempban(updated)
      setSaved(t('common.saved'))
    } catch (err) {
      setError(formatApiError(err, t, 'tempban.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  const publish = async () => {
    setPublishBusy(true)
    setError('')
    setSaved('')
    try {
      const result = await publishTempbanWarning()
      setTempban((prev) =>
        prev
          ? {
              ...prev,
              warning_message_id: result.warning_message_id || result.message_id,
              ban_count: result.ban_count,
            }
          : prev,
      )
      setSaved(t('tempban.publishOk'))
    } catch (err) {
      setError(formatApiError(err, t, 'tempban.errorPublish'))
    } finally {
      setPublishBusy(false)
    }
  }

  if (!tempban) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5 pb-4">
      <div>
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Clock size={22} className="text-primary" />
          {t('tempban.title')}
        </h1>
        <p className="mt-1 text-sm text-muted">{t('tempban.intro')}</p>
      </div>

      <ModuleConfigPanel
        variant="tempban"
        title={t('tempban.channelsTitle')}
        intro={t('tempban.channelsIntro')}
      />

      <section className="flex flex-col gap-4 border-t border-border pt-6">
        <h2 className="font-semibold text-foreground">{t('tempban.actionTitle')}</h2>
        <p className="text-sm text-muted">{t('tempban.actionIntro')}</p>
        <Card className="flex flex-col gap-3">
          <div className="flex flex-col gap-2" role="radiogroup" aria-label={t('tempban.actionTitle')}>
            {ACTIONS.map((action) => (
              <label key={action} className="flex cursor-pointer items-start gap-2 text-sm text-foreground">
                <input
                  type="radio"
                  name="tempban-action"
                  className="mt-1"
                  checked={tempban.action === action}
                  onChange={() => setTempban({ ...tempban, action })}
                />
                <span>
                  <span className="font-medium">{t(`tempban.action.${action}`)}</span>
                  <span className="mt-0.5 block text-xs text-muted">{t(`tempban.actionHint.${action}`)}</span>
                </span>
              </label>
            ))}
          </div>
          <p className="text-sm text-muted">
            {t('tempban.banCount')}: <span className="font-semibold text-foreground">{tempban.ban_count}</span>
          </p>
        </Card>
      </section>

      <section className="flex flex-col gap-4 border-t border-border pt-6">
        <h2 className="font-semibold text-foreground">{t('messageCustomizer.tempbanTitle')}</h2>
        <p className="text-sm text-muted">{t('messageCustomizer.tempbanIntro')}</p>
        <Card className="flex flex-col gap-3">
          <label className="text-sm text-muted">{t('tempban.warningMessage')}</label>
          <textarea
            value={tempban.warning_message}
            onChange={(e) => setTempban({ ...tempban, warning_message: e.target.value })}
            className={inputClass}
            rows={5}
          />
          <p className="text-xs text-muted">{t('tempban.warningHint')}</p>
          <label className="text-sm text-muted">{t('tempban.warningThumb')}</label>
          <input
            value={tempban.warning_thumbnail_url}
            onChange={(e) => setTempban({ ...tempban, warning_thumbnail_url: e.target.value })}
            className={inputClass}
            placeholder="https://"
          />
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={publish} disabled={publishBusy}>
              {publishBusy ? t('common.saving') : t('tempban.publishWarning')}
            </Button>
          </div>

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
          <p className="text-xs text-muted">{t('tempban.dmVarsHint')}</p>

          <Toggle
            checked={tempban.log_enabled}
            onChange={(v) => setTempban({ ...tempban, log_enabled: v })}
            label={t('messageCustomizer.tempbanLogEnabled')}
          />
          <label className="text-sm text-muted">{t('tempban.logMessage')}</label>
          <textarea
            value={tempban.log_message}
            onChange={(e) => setTempban({ ...tempban, log_message: e.target.value })}
            className={inputClass}
            rows={3}
            placeholder={t('tempban.logMessagePlaceholder')}
          />
          <p className="text-xs text-muted">{t('tempban.logMessageHint')}</p>

          <label className="text-sm text-muted">{t('messageCustomizer.tempbanUnbanReason')}</label>
          <input
            value={tempban.unban_reason}
            onChange={(e) => setTempban({ ...tempban, unban_reason: e.target.value })}
            className={inputClass}
          />
        </Card>
        {error && <p className="text-sm text-danger">{error}</p>}
        {saved && <p className="text-sm text-primary">{saved}</p>}
        <Button variant="primary" onClick={save} disabled={busy}>
          {busy ? t('common.saving') : t('common.save')}
        </Button>
      </section>
    </div>
  )
}
