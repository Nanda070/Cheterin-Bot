import { PushPin, Plus, Trash } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import {
  deleteSticky,
  fetchChannels,
  fetchSticky,
  setStickyEnabled,
  testSticky,
  upsertSticky,
  type ChannelInfo,
  type StickySettings,
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

export function StickyMessagesPage() {
  const t = useT()
  const [settings, setSettings] = useState<StickySettings | null>(null)
  const [channels, setChannels] = useState<ChannelInfo[]>([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [adding, setAdding] = useState(false)
  const [draft, setDraft] = useState({ channel_id: '', content: '' })

  const reload = () =>
    fetchSticky()
      .then((data) => {
        setSettings(data)
        setError('')
      })
      .catch((err) => setError(formatApiError(err, t, 'sticky.errorLoad')))

  useEffect(() => {
    reload()
    fetchChannels()
      .then(setChannels)
      .catch((err) => setError(formatApiError(err, t, 'common.errorLoadChannels')))
  }, [t])

  const act = async (fn: () => Promise<unknown>) => {
    setBusy(true)
    setError('')
    try {
      await fn()
      await reload()
    } catch (err) {
      setError(formatApiError(err, t, 'common.operationFailed'))
    } finally {
      setBusy(false)
    }
  }

  const channelName = (id: string) => channels.find((c) => c.id === id)?.name ?? id

  if (!settings) {
    return <p className="text-sm text-muted">{error || t('common.loading')}</p>
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5">
      <div>
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <PushPin size={22} className="text-primary" />
          {t('sticky.title')}
        </h1>
        <p className="mt-1 text-sm text-muted">{t('sticky.intro')}</p>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      <Card>
        <Toggle
          checked={settings.enabled}
          onChange={(v) => act(() => setStickyEnabled(v))}
          label={t('sticky.enable')}
          disabled={busy}
        />
      </Card>

      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted">
          {t('sticky.list', { count: settings.stickies.length })}
        </h2>
        <Button variant="primary" onClick={() => setAdding(true)}>
          <Plus size={16} />
          {t('sticky.add')}
        </Button>
      </div>

      {settings.stickies.length === 0 ? (
        <Card>
          <p className="text-sm text-muted">{t('sticky.empty')}</p>
        </Card>
      ) : (
        settings.stickies.map((row) => (
          <Card key={row.id} className="flex flex-col gap-2">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-foreground">#{channelName(row.channel_id)}</p>
                <p className="mt-1 whitespace-pre-wrap text-sm text-foreground">{row.content}</p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  disabled={busy || !row.enabled}
                  onClick={() => act(() => testSticky(row.id))}
                >
                  {t('sticky.testSend')}
                </Button>
                <Toggle
                  checked={row.enabled}
                  onChange={(v) =>
                    act(() =>
                      upsertSticky({
                        id: row.id,
                        channel_id: row.channel_id,
                        content: row.content,
                        enabled: v,
                      }),
                    )
                  }
                  disabled={busy}
                />
                <button
                  type="button"
                  onClick={() => act(() => deleteSticky(row.id))}
                  className="text-muted hover:text-danger"
                  aria-label={t('common.delete')}
                >
                  <Trash size={17} />
                </button>
              </div>
            </div>
          </Card>
        ))
      )}

      <Modal open={adding} onClose={() => setAdding(false)} title={t('sticky.modal.title')}>
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted">{t('common.selectChannel')}</label>
            <Select
              value={draft.channel_id}
              onChange={(id) => setDraft((d) => ({ ...d, channel_id: id }))}
              options={channels}
              placeholder={t('common.selectChannel')}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted">{t('sticky.content')}</label>
            <textarea
              rows={3}
              value={draft.content}
              onChange={(e) => setDraft((d) => ({ ...d, content: e.target.value }))}
              className={inputClass}
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setAdding(false)}>
              {t('common.cancel')}
            </Button>
            <Button
              variant="primary"
              disabled={busy || !draft.channel_id || !draft.content.trim()}
              onClick={() =>
                act(async () => {
                  await upsertSticky(draft)
                  setAdding(false)
                  setDraft({ channel_id: '', content: '' })
                })
              }
            >
              {t('common.create')}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
