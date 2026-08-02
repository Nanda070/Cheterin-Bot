import { Cake, Plus, Trash } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  deleteBirthday,
  fetchBirthdays,
  fetchChannels,
  fetchRoles,
  setBirthday,
  testBirthdayAnnounce,
  updateBirthdaySettings,
  type BirthdaysPayload,
  type ChannelInfo,
  type RoleInfo,
} from '../api/client'
import { formatApiError } from '../api/errors'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

export function BirthdaysCalendarPage() {
  const t = useT()
  const [data, setData] = useState<BirthdaysPayload | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [enabled, setEnabled] = useState(false)
  const [channelId, setChannelId] = useState('')
  const [pingRoleId, setPingRoleId] = useState('')
  const [adding, setAdding] = useState(false)
  const [draft, setDraft] = useState({ user_id: '', mm_dd: '' })
  const [testMessage, setTestMessage] = useState('')

  const reload = () =>
    fetchBirthdays()
      .then((res) => {
        setData(res)
        setEnabled(res.enabled)
        setChannelId(res.channel_id)
        setPingRoleId(res.ping_role_id)
        setError('')
      })
      .catch((err) => setError(formatApiError(err, t, 'birthdays.errorLoad')))

  useEffect(() => {
    reload()
    fetchChannels()
      .then(setChannels)
      .catch((err) => setError(formatApiError(err, t, 'common.errorLoadChannels')))
    fetchRoles()
      .then(setRoles)
      .catch(() => setRoles([]))
  }, [t])

  const act = async (fn: () => Promise<unknown>) => {
    setBusy(true)
    setError('')
    setTestMessage('')
    try {
      await fn()
      await reload()
    } catch (err) {
      setError(formatApiError(err, t, 'common.operationFailed'))
    } finally {
      setBusy(false)
    }
  }

  const sendTest = async () => {
    setBusy(true)
    setError('')
    setTestMessage('')
    try {
      await testBirthdayAnnounce()
      setTestMessage(t('birthdays.testSent'))
    } catch (err) {
      setError(formatApiError(err, t, 'birthdays.testFailed'))
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
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Cake size={22} className="text-primary" />
          {t('birthdays.title')}
        </h1>
        <p className="mt-1 text-sm text-muted">{t('birthdays.intro')}</p>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}
      {testMessage && <p className="text-sm text-success">{testMessage}</p>}

      <Card className="flex flex-col gap-4">
        <Toggle checked={enabled} onChange={setEnabled} label={t('birthdays.enable')} disabled={busy} />
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted">{t('birthdays.channel')}</label>
          <Select
            value={channelId}
            onChange={setChannelId}
            options={channels}
            placeholder={t('common.selectChannel')}
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted">{t('birthdays.pingRole')}</label>
          <Select
            value={pingRoleId}
            onChange={setPingRoleId}
            options={roles}
            kind="role"
            placeholder={t('birthdays.noPing')}
          />
        </div>
        <div className="flex flex-wrap justify-end gap-2 border-t border-border pt-3">
          <Button variant="secondary" disabled={busy || !channelId} onClick={sendTest}>
            {t('birthdays.testSend')}
          </Button>
          <Button
            variant="primary"
            disabled={busy}
            onClick={() =>
              act(() =>
                updateBirthdaySettings({
                  enabled,
                  channel_id: channelId,
                  ping_role_id: pingRoleId,
                }),
              )
            }
          >
            {busy ? t('common.saving') : t('common.save')}
          </Button>
        </div>
      </Card>

      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted">
          {t('birthdays.list', { count: data.birthdays.length })}
        </h2>
        <Button variant="primary" onClick={() => setAdding(true)}>
          <Plus size={16} />
          {t('birthdays.add')}
        </Button>
      </div>

      {data.birthdays.length === 0 ? (
        <Card>
          <p className="text-sm text-muted">{t('birthdays.empty')}</p>
        </Card>
      ) : (
        data.birthdays.map((row) => (
          <Card key={row.user_id} className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-foreground">{row.display_name}</p>
              <p className="text-xs text-muted">{row.mm_dd}</p>
            </div>
            <button
              type="button"
              disabled={busy}
              onClick={() => act(() => deleteBirthday(row.user_id))}
              className="text-muted hover:text-danger"
              aria-label={t('common.delete')}
            >
              <Trash size={17} />
            </button>
          </Card>
        ))
      )}

      <Modal open={adding} onClose={() => setAdding(false)} title={t('birthdays.modal.title')}>
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted">{t('birthdays.userId')}</label>
            <input
              value={draft.user_id}
              onChange={(e) => setDraft((d) => ({ ...d, user_id: e.target.value }))}
              className={inputClass}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted">{t('birthdays.field.mmDd')}</label>
            <input
              placeholder="MM-DD"
              value={draft.mm_dd}
              onChange={(e) => setDraft((d) => ({ ...d, mm_dd: e.target.value }))}
              className={inputClass}
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setAdding(false)}>
              {t('common.cancel')}
            </Button>
            <Button
              variant="primary"
              disabled={busy || !draft.user_id.trim() || !draft.mm_dd.trim()}
              onClick={() =>
                act(async () => {
                  await setBirthday(draft.user_id.trim(), draft.mm_dd.trim())
                  setAdding(false)
                  setDraft({ user_id: '', mm_dd: '' })
                })
              }
            >
              {t('common.save')}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
