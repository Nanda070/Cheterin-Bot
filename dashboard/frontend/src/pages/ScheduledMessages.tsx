import { ClockCountdown, Plus, Trash } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  createScheduledMessage,
  deleteScheduledMessage,
  fetchChannels,
  fetchScheduledMessages,
  setScheduledMessagesEnabled,
  updateScheduledMessage,
  type ChannelInfo,
  type ScheduledMessagesSettings,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

export function ScheduledMessagesPage({ embedded = false }: { embedded?: boolean }) {
  const t = useT()
  const [settings, setSettings] = useState<ScheduledMessagesSettings | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [adding, setAdding] = useState(false)
  const [draft, setDraft] = useState({
    channel_id: '',
    content: '',
    schedule_type: 'daily' as 'once' | 'daily',
    run_at: '',
    daily_time: '12:00',
  })

  const reload = () =>
    fetchScheduledMessages()
      .then(setSettings)
      .catch(() => setError(t('scheduledMessages.errorLoad')))

  useEffect(() => {
    reload()
    fetchChannels().then(setChannels).catch(() => setChannels([]))
  }, [])

  const act = async (fn: () => Promise<unknown>) => {
    setBusy(true)
    setError('')
    try {
      await fn()
      await reload()
    } catch {
      setError(t('common.operationFailed'))
    } finally {
      setBusy(false)
    }
  }

  if (!settings) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5">
      <div>
        {embedded ? (
          <h2 className="flex items-center gap-2 font-semibold text-foreground">
            <ClockCountdown size={20} className="text-primary" />
            {t('scheduledMessages.title')}
          </h2>
        ) : (
          <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <ClockCountdown size={22} className="text-primary" />
            {t('scheduledMessages.title')}
          </h1>
        )}
        <p className="mt-1 text-sm text-muted">{t('scheduledMessages.intro')}</p>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      <Card>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => act(() => setScheduledMessagesEnabled(v))}
          label={t('scheduledMessages.enable')}
          disabled={busy}
        />
      </Card>

      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted">
          {t('scheduledMessages.list', { count: settings.messages.length })}
        </h2>
        <Button variant="primary" onClick={() => setAdding(true)}>
          <Plus size={16} />
          {t('scheduledMessages.add')}
        </Button>
      </div>

      {settings.messages.length === 0 && (
        <Card>
          <p className="text-sm text-muted">{t('scheduledMessages.empty')}</p>
        </Card>
      )}

      {settings.messages.map((msg) => (
        <Card key={msg.id} className="flex flex-col gap-2">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0 flex-1">
              <p className="text-sm text-muted">
                {msg.schedule_type === 'daily'
                  ? t('scheduledMessages.dailyAt', { time: msg.daily_time })
                  : t('scheduledMessages.onceAt', { time: msg.run_at || '—' })}
              </p>
              <p className="mt-1 whitespace-pre-wrap text-sm text-foreground">{msg.content}</p>
            </div>
            <div className="flex items-center gap-2">
              <Toggle
                checked={msg.enabled}
                onChange={(v) => act(() => updateScheduledMessage(msg.id, { enabled: v }))}
                disabled={busy}
              />
              <button
                type="button"
                onClick={() => act(() => deleteScheduledMessage(msg.id))}
                className="text-muted hover:text-danger"
                aria-label={t('scheduledMessages.deleteAria')}
              >
                <Trash size={17} />
              </button>
            </div>
          </div>
        </Card>
      ))}

      <Modal open={adding} title={t('scheduledMessages.modal.title')} onClose={() => setAdding(false)}>
        <div className="flex flex-col gap-3">
          <Select
            value={draft.channel_id}
            onChange={(id) => setDraft((d) => ({ ...d, channel_id: id }))}
            options={channels}
            placeholder={t('common.selectChannel')}
          />
          <Select
            value={draft.schedule_type}
            onChange={(id) => setDraft((d) => ({ ...d, schedule_type: id as 'once' | 'daily' }))}
            options={[
              { id: 'daily', name: t('scheduledMessages.type.daily') },
              { id: 'once', name: t('scheduledMessages.type.once') },
            ]}
          />
          {draft.schedule_type === 'daily' ? (
            <input
              type="time"
              value={draft.daily_time}
              onChange={(e) => setDraft((d) => ({ ...d, daily_time: e.target.value }))}
              className={inputClass}
            />
          ) : (
            <input
              type="datetime-local"
              value={draft.run_at}
              onChange={(e) => setDraft((d) => ({ ...d, run_at: e.target.value ? new Date(e.target.value).toISOString() : '' }))}
              className={inputClass}
            />
          )}
          <textarea
            rows={3}
            value={draft.content}
            onChange={(e) => setDraft((d) => ({ ...d, content: e.target.value }))}
            placeholder={t('scheduledMessages.field.content')}
            className={inputClass}
          />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setAdding(false)}>
              {t('common.cancel')}
            </Button>
            <Button
              variant="primary"
              disabled={busy || !draft.channel_id || !draft.content.trim()}
              onClick={() =>
                act(async () => {
                  await createScheduledMessage(draft)
                  setAdding(false)
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
