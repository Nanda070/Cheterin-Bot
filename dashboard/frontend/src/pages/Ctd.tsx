import { Ticket } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  fetchChannels,
  fetchCtdConfig,
  fetchRoles,
  updateCtdConfig,
  type ChannelInfo,
  type CtdConfig,
  type RoleInfo,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Select } from '../components/ui/Select'
import { useT } from '../context/LanguageContext'

const EMPTY: CtdConfig = { CTD_ROLE_ID: '', CTD_CHANNEL_ID: '' }

export function CtdPage() {
  const t = useT()
  const [config, setConfig] = useState<CtdConfig>(EMPTY)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [savedMessage, setSavedMessage] = useState('')
  const [dirty, setDirty] = useState(false)

  useEffect(() => {
    Promise.all([fetchCtdConfig(), fetchChannels(), fetchRoles()])
      .then(([cfg, ch, rl]) => {
        setConfig(cfg)
        setChannels(ch)
        setRoles(rl)
      })
      .catch(() => setError(t('ctd.errorLoad')))
      .finally(() => setLoading(false))
  }, [t])

  const setField = (key: keyof CtdConfig, value: string) => {
    setConfig((prev) => ({ ...prev, [key]: value }))
    setDirty(true)
    setSavedMessage('')
  }

  const save = async () => {
    setBusy(true)
    setError('')
    setSavedMessage('')
    try {
      const updated = await updateCtdConfig(config)
      setConfig(updated)
      setSavedMessage(t('common.saved'))
      setDirty(false)
    } catch (err) {
      setError(formatApiError(err, t, 'ctd.errorSave'))
    } finally {
      setBusy(false)
    }
  }

  if (loading) {
    return <p className="text-sm text-muted">{t('common.loading')}</p>
  }

  return (
    <div className="flex max-w-2xl flex-col gap-5">
      <div>
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Ticket size={22} className="text-primary" />
          {t('ctd.title')}
        </h1>
        <p className="mt-1 text-sm text-muted">{t('ctd.intro')}</p>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      <section className="flex flex-col gap-3 rounded-card border border-border bg-surface p-4">
        <div className="flex flex-col gap-1">
          <label className="text-sm text-muted" htmlFor="CTD_ROLE_ID">
            {t('ctd.field.supportRole')}
          </label>
          <Select
            id="CTD_ROLE_ID"
            value={config.CTD_ROLE_ID}
            onChange={(id) => setField('CTD_ROLE_ID', id)}
            options={roles}
            kind="role"
            placeholder={t('common.notSet')}
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm text-muted" htmlFor="CTD_CHANNEL_ID">
            {t('ctd.field.ticketPanel')}
          </label>
          <Select
            id="CTD_CHANNEL_ID"
            value={config.CTD_CHANNEL_ID}
            onChange={(id) => setField('CTD_CHANNEL_ID', id)}
            options={channels}
            placeholder={t('common.notSet')}
          />
        </div>
      </section>

      <div className="flex items-center justify-between gap-3">
        <span className="text-sm text-muted">
          {savedMessage ? (
            <span className="text-primary">{savedMessage}</span>
          ) : dirty ? (
            t('common.unsavedChanges')
          ) : (
            t('common.allSaved')
          )}
        </span>
        <Button variant="primary" onClick={save} disabled={busy || !dirty}>
          {busy ? t('common.saving') : t('common.save')}
        </Button>
      </div>
    </div>
  )
}
