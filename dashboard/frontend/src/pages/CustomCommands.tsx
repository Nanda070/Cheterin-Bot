import { ChatTeardropText, Eye, Plus, Trash } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  createCustomCommand,
  deleteCustomCommand,
  fetchCustomCommands,
  setCustomCommandsEnabled,
  updateCustomCommand,
  type CustomCommandsSettings,
} from '../api/client'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Modal } from '../components/ui/Modal'
import { Select } from '../components/ui/Select'
import { Toggle } from '../components/ui/Toggle'
import { useT } from '../context/LanguageContext'
import { CommandPreviewPage } from './CommandPreview'

const inputClass =
  'rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary'

type Tab = 'commands' | 'preview'

function parseTab(raw: string | null): Tab {
  return raw === 'preview' ? 'preview' : 'commands'
}

function TabBar({ tab, setTab, t }: { tab: Tab; setTab: (t: Tab) => void; t: (key: string) => string }) {
  const tabs: { key: Tab; labelKey: string; icon: typeof ChatTeardropText }[] = [
    { key: 'commands', labelKey: 'customCommands.tab.commands', icon: ChatTeardropText },
    { key: 'preview', labelKey: 'customCommands.tab.preview', icon: Eye },
  ]
  return (
    <div className="flex gap-1 border-b border-border">
      {tabs.map(({ key, labelKey, icon: Icon }) => (
        <button
          key={key}
          type="button"
          onClick={() => setTab(key)}
          className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-sm transition-colors ${
            tab === key ? 'border-primary text-foreground' : 'border-transparent text-muted hover:text-foreground'
          }`}
        >
          <Icon size={15} />
          {t(labelKey)}
        </button>
      ))}
    </div>
  )
}

export function CustomCommandsPage() {
  const t = useT()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = parseTab(searchParams.get('tab'))
  const setTab = (next: Tab) => {
    if (next === 'commands') setSearchParams({}, { replace: true })
    else setSearchParams({ tab: next }, { replace: true })
  }

  const [settings, setSettings] = useState<CustomCommandsSettings | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [adding, setAdding] = useState(false)
  const [draft, setDraft] = useState({ trigger: '', match: 'exact' as 'exact' | 'contains', reply_text: '' })

  const reload = () =>
    fetchCustomCommands()
      .then(setSettings)
      .catch(() => setError(t('customCommands.errorLoad')))

  useEffect(() => {
    if (tab === 'commands') reload()
  }, [tab])

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

  if (tab === 'preview') {
    return (
      <div className="flex flex-col gap-4">
        <TabBar tab={tab} setTab={setTab} t={t} />
        <CommandPreviewPage embedded />
      </div>
    )
  }

  if (!settings) {
    return (
      <div className="flex flex-col gap-4">
        <TabBar tab={tab} setTab={setTab} t={t} />
        <p className="text-sm text-muted">{error || t('common.loading')}</p>
      </div>
    )
  }

  return (
    <div className="flex max-w-3xl flex-col gap-5">
      <TabBar tab={tab} setTab={setTab} t={t} />

      <div>
        <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <ChatTeardropText size={22} className="text-primary" />
          {t('customCommands.title')}
        </h1>
        <p className="mt-1 text-sm text-muted">{t('customCommands.intro')}</p>
      </div>

      {error && <p className="text-sm text-danger">{error}</p>}

      <Card className="flex flex-col gap-3">
        <Toggle
          checked={settings.enabled}
          onChange={(v) => act(() => setCustomCommandsEnabled(v))}
          label={t('customCommands.enabled')}
          disabled={busy}
        />
      </Card>

      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium uppercase tracking-wide text-muted">
          {t('customCommands.list', { count: settings.commands.length })}
        </h2>
        <Button variant="primary" onClick={() => setAdding(true)}>
          <Plus size={16} />
          {t('customCommands.add')}
        </Button>
      </div>

      {settings.commands.length === 0 && (
        <Card>
          <p className="text-sm text-muted">{t('customCommands.empty')}</p>
        </Card>
      )}

      {settings.commands.map((cmd) => (
        <Card key={cmd.id} className="flex flex-col gap-2">
          <div className="flex items-center justify-between gap-2">
            <div className="min-w-0">
              <p className="truncate font-medium text-foreground">{cmd.trigger}</p>
              <p className="text-xs text-muted">
                {cmd.match === 'exact' ? t('customCommands.match.exact') : t('customCommands.match.contains')}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Toggle
                checked={cmd.enabled}
                onChange={(v) => act(() => updateCustomCommand(cmd.id, { enabled: v }))}
                disabled={busy}
              />
              <button
                type="button"
                onClick={() => act(() => deleteCustomCommand(cmd.id))}
                className="text-muted hover:text-danger"
                aria-label={t('customCommands.deleteAria')}
              >
                <Trash size={17} />
              </button>
            </div>
          </div>
          <p className="whitespace-pre-wrap text-sm text-muted">{cmd.reply_text || '—'}</p>
        </Card>
      ))}

      <Modal open={adding} title={t('customCommands.modal.title')} onClose={() => setAdding(false)}>
        <div className="flex flex-col gap-3">
          <input
            value={draft.trigger}
            onChange={(e) => setDraft((d) => ({ ...d, trigger: e.target.value }))}
            placeholder={t('customCommands.field.trigger')}
            className={inputClass}
          />
          <Select
            value={draft.match}
            onChange={(id) => setDraft((d) => ({ ...d, match: id as 'exact' | 'contains' }))}
            options={[
              { id: 'exact', name: t('customCommands.match.exact') },
              { id: 'contains', name: t('customCommands.match.contains') },
            ]}
          />
          <textarea
            rows={3}
            value={draft.reply_text}
            onChange={(e) => setDraft((d) => ({ ...d, reply_text: e.target.value }))}
            placeholder={t('customCommands.field.reply')}
            className={inputClass}
          />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setAdding(false)}>
              {t('common.cancel')}
            </Button>
            <Button
              variant="primary"
              disabled={busy || !draft.trigger.trim()}
              onClick={() =>
                act(async () => {
                  await createCustomCommand(draft)
                  setAdding(false)
                  setDraft({ trigger: '', match: 'exact', reply_text: '' })
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
