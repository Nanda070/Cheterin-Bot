import { UserPlus } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  fetchChannels,
  fetchInvites,
  updateInvitesSettings,
  type ChannelInfo,
  type InvitesSettings,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

export function InvitesTrackerPage({ embedded = false }: { embedded?: boolean }) {
  const t = useT()
  const [data, setData] = useState<InvitesSettings | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [enabled, setEnabled] = useState(false)
  const [welcomeMention, setWelcomeMention] = useState(false)
  const [logChannelId, setLogChannelId] = useState('')

  const reload = () =>
    fetchInvites()
      .then((res) => {
        setData(res)
        setEnabled(res.enabled)
        setWelcomeMention(res.welcome_mention)
        setLogChannelId(res.log_channel_id)
        setError('')
      })
      .catch((err) => setError(formatApiError(err, t, 'invites.errorLoad')))

  useEffect(() => {
    reload()
    fetchChannels()
      .then(setChannels)
      .catch((err) => setError(formatApiError(err, t, 'common.errorLoadChannels')))
  }, [t])

  const save = async () => {
    setBusy(true)
    setError('')
    try {
      await updateInvitesSettings({
        enabled,
        welcome_mention: welcomeMention,
        log_channel_id: logChannelId,
      })
      await reload()
    } catch (err) {
      setError(formatApiError(err, t, 'common.operationFailed'))
    } finally {
      setBusy(false)
    }
  }

  if (!data) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5">
      <div>
        {embedded ? (
          <h2 className="flex items-center gap-2 font-semibold text-foreground">
            <UserPlus size={20} className="text-primary" />
            {t('invites.title')}
          </h2>
        ) : (
          <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <UserPlus size={22} className="text-primary" />
            {t('invites.title')}
          </h1>
        )}
        <p className="mt-1 text-sm text-muted">{t('invites.intro')}</p>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      <Card className="flex flex-col gap-4">
          <Toggle checked={enabled} onChange={setEnabled} label={t('invites.enable')} disabled={busy} />
        <Toggle
          checked={welcomeMention}
          onChange={setWelcomeMention}
          label={t('invites.welcomeMention')}
          disabled={busy}
        />
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted">{t('invites.logChannel')}</label>
          <Select
            value={logChannelId}
            onChange={setLogChannelId}
            options={channels}
            placeholder={t('common.selectChannel')}
          />
        </div>
        <div className="flex justify-end border-t border-border pt-3">
          <Button variant="primary" onClick={save} disabled={busy}>
            {busy ? t('common.saving') : t('common.save')}
          </Button>
        </div>
      </Card>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted">{t('invites.stats')}</h2>
        {data.stats.length === 0 ? (
          <Card>
            <p className="text-sm text-muted">{t('invites.noStats')}</p>
          </Card>
        ) : (
          data.stats.map((row) => (
            <Card key={row.inviter_id} className="flex items-center justify-between gap-3">
              <div>
                <span className="text-sm font-medium text-foreground">
                  {row.inviter_display || row.inviter_id}
                </span>
                {row.inviter_display && row.inviter_display !== row.inviter_id && (
                  <p className="font-mono text-xs text-muted">{row.inviter_id}</p>
                )}
              </div>
              <span className="text-sm text-muted">{t('invites.joins', { count: row.joins })}</span>
            </Card>
          ))
        )}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted">{t('invites.recent')}</h2>
        {data.recent_joins.length === 0 ? (
          <Card>
            <p className="text-sm text-muted">{t('invites.recentEmpty')}</p>
          </Card>
        ) : (
          data.recent_joins.map((row, i) => (
            <Card key={`${row.invitee_id}-${row.joined_at}-${i}`} className="flex flex-col gap-1 text-sm">
              <p className="text-foreground">
                {t('invites.joinLine', {
                  invitee: row.invitee_display || row.invitee_id,
                  inviter: row.inviter_display || row.inviter_id || '—',
                  code: row.code ?? '—',
                })}
              </p>
              <p className="text-xs text-muted">{row.joined_at}</p>
            </Card>
          ))
        )}
      </section>
    </div>
  )
}
