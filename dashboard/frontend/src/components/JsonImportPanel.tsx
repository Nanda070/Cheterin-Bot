import { useState } from 'react'
import { useT } from '../context/LanguageContext'
import { parseMessageJson, type ImportedMessage, type JsonNotice } from '../utils/messageJson'
import { Button } from './ui/Button'

interface Props {
  /** JSON of the message currently in the form (Discohook shape). */
  exportJson: () => string
  /** Put one imported message into the form. */
  onLoad: (message: ImportedMessage) => void
  /** Save every imported message as a template; resolves with the outcome counts. */
  onSaveAll: (messages: ImportedMessage[]) => Promise<{ created: number; skipped: number }>
  busy: boolean
}

/**
 * Paste-JSON block of the Embed Builder: Discohook-style message JSON in, form filled.
 * JSON holding several messages turns into a searchable list to pick from.
 */
export function JsonImportPanel({ exportJson, onLoad, onSaveAll, busy }: Props) {
  const t = useT()
  const [text, setText] = useState('')
  const [messages, setMessages] = useState<ImportedMessage[]>([])
  const [active, setActive] = useState(-1)
  const [query, setQuery] = useState('')
  const [error, setError] = useState<JsonNotice | null>(null)
  const [warnings, setWarnings] = useState<JsonNotice[]>([])
  const [notice, setNotice] = useState('')
  const [saving, setSaving] = useState(false)

  const load = (list: ImportedMessage[], index: number) => {
    setActive(index)
    onLoad(list[index])
    setNotice(t('embedBuilder.json.loaded'))
  }

  const handleApply = () => {
    setNotice('')
    const result = parseMessageJson(text)
    if (!result.ok) {
      setError(result.error)
      setWarnings([])
      return
    }
    // Unnamed entries get a stable label, also used as the template name on "save all".
    const named = result.messages.map((message, index) => ({
      ...message,
      name: message.name || t('embedBuilder.json.unnamed', { n: index + 1 }),
    }))
    setError(null)
    setWarnings(result.warnings)
    setMessages(named)
    setQuery('')
    if (named.length === 1) {
      load(named, 0)
    } else {
      setActive(-1)
    }
  }

  const handleCopy = () => {
    const json = exportJson()
    setText(json)
    setError(null)
    setWarnings([])
    setNotice(t('embedBuilder.json.copied'))
    // Clipboard may be unavailable (permissions, insecure context) — the textarea still has the JSON.
    void navigator.clipboard?.writeText(json).catch(() => {})
  }

  const handleSaveAll = async () => {
    setNotice('')
    setSaving(true)
    try {
      const outcome = await onSaveAll(messages)
      setNotice(t('embedBuilder.json.savedAll', outcome))
    } catch {
      setError({ key: 'embedBuilder.json.error.saveAll' })
    } finally {
      setSaving(false)
    }
  }

  const needle = query.trim().toLowerCase()
  const visible = messages
    .map((message, index) => ({ message, index }))
    .filter(({ message }) => !needle || message.name.toLowerCase().includes(needle))

  return (
    <div className="flex flex-col gap-2 rounded-control border border-border bg-surface p-3">
      <label className="text-sm font-medium text-foreground" htmlFor="eb-json">
        {t('embedBuilder.json.title')}
      </label>
      <textarea
        id="eb-json"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={t('embedBuilder.json.hint')}
        spellCheck={false}
        rows={5}
        className="rounded-control border border-border bg-background px-3 py-2 font-mono text-xs text-foreground outline-none focus:border-primary"
      />
      <div className="flex flex-wrap gap-2">
        <Button variant="secondary" onClick={handleApply} disabled={!text.trim()}>
          {t('embedBuilder.json.apply')}
        </Button>
        <Button variant="ghost" onClick={handleCopy}>
          {t('embedBuilder.json.copy')}
        </Button>
      </div>

      {error && <p className="text-xs text-danger">{t(error.key, error.params)}</p>}
      {warnings.map((warning, index) => (
        <p key={`${warning.key}-${index}`} className="text-xs text-warning">
          {t(warning.key, warning.params)}
        </p>
      ))}
      {notice && <p className="text-xs text-primary">{notice}</p>}

      {messages.length > 1 && (
        <>
          <p className="text-xs text-muted">{t('embedBuilder.json.messages', { count: messages.length })}</p>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t('embedBuilder.json.search')}
            aria-label={t('embedBuilder.json.search')}
            className="rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />
          <ul className="max-h-64 overflow-y-auto rounded-control border border-border/60">
            {visible.map(({ message, index }) => (
              <li key={index}>
                <button
                  type="button"
                  onClick={() => load(messages, index)}
                  aria-current={index === active}
                  className={`flex w-full cursor-pointer items-center justify-between gap-2 px-3 py-1.5 text-left text-sm transition-colors ${
                    index === active ? 'bg-primary-muted text-foreground' : 'text-foreground hover:bg-surface-hover'
                  }`}
                >
                  <span className="truncate">{message.name}</span>
                  {message.group && <span className="shrink-0 text-xs text-muted">{message.group}</span>}
                </button>
              </li>
            ))}
          </ul>
          <Button variant="secondary" onClick={handleSaveAll} disabled={busy || saving}>
            {t('embedBuilder.json.saveAll', { count: messages.length })}
          </Button>
        </>
      )}
    </div>
  )
}
