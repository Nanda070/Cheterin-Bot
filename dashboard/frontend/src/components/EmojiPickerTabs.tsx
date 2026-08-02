import { useEffect, useState } from 'react'
import { fetchEmojis, type CustomEmoji } from '../api/client'
import { useT } from '../context/LanguageContext'

const STANDARD_EMOJIS = [
  '⭐',
  '🌟',
  '✨',
  '💫',
  '❤️',
  '🧡',
  '💛',
  '💚',
  '💙',
  '💜',
  '🤍',
  '🖤',
  '🔥',
  '💯',
  '👍',
  '👎',
  '👏',
  '🙌',
  '🎉',
  '🎊',
  '🏆',
  '🥇',
  '💎',
  '👑',
  '📌',
  '📍',
  '✅',
  '❌',
  '⚡',
  '🌙',
  '☀️',
  '🌈',
]

type Tab = 'standard' | 'custom'

type Props = {
  value: string
  onChange: (emoji: string) => void
  id?: string
}

export function EmojiPickerTabs({ value, onChange, id }: Props) {
  const t = useT()
  const [tab, setTab] = useState<Tab>('standard')
  const [custom, setCustom] = useState<CustomEmoji[]>([])
  const [loadError, setLoadError] = useState(false)

  useEffect(() => {
    fetchEmojis()
      .then(setCustom)
      .catch(() => setLoadError(true))
  }, [])

  const selectedCustom = custom.find((e) => value === `<:${e.name}:${e.id}>` || value === `<a:${e.name}:${e.id}>`)

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className="inline-flex min-h-9 min-w-9 items-center justify-center rounded-control border border-border bg-background px-2 text-xl">
          {selectedCustom ? (
            <img src={selectedCustom.url} alt={selectedCustom.name} className="h-6 w-6" />
          ) : (
            <span aria-hidden>{value || '—'}</span>
          )}
        </span>
        <input
          id={id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="min-w-0 flex-1 rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          maxLength={64}
          placeholder={t('emojiPicker.manualPlaceholder')}
          aria-label={t('emojiPicker.manualAria')}
        />
      </div>

      <div className="flex gap-1 border-b border-border">
        {(
          [
            { key: 'standard' as const, labelKey: 'emojiPicker.tab.standard' },
            { key: 'custom' as const, labelKey: 'emojiPicker.tab.custom' },
          ] as const
        ).map(({ key, labelKey }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`border-b-2 px-3 py-1.5 text-sm transition-colors ${
              tab === key
                ? 'border-primary text-foreground'
                : 'border-transparent text-muted hover:text-foreground'
            }`}
          >
            {t(labelKey)}
          </button>
        ))}
      </div>

      {tab === 'standard' && (
        <div className="grid max-h-40 grid-cols-8 gap-1 overflow-y-auto sm:grid-cols-10">
          {STANDARD_EMOJIS.map((emoji) => (
            <button
              key={emoji}
              type="button"
              onClick={() => onChange(emoji)}
              className={`flex h-9 items-center justify-center rounded-control text-lg transition-colors hover:bg-primary-muted ${
                value === emoji ? 'bg-primary-muted ring-1 ring-primary' : 'bg-background'
              }`}
              aria-label={emoji}
              aria-pressed={value === emoji}
            >
              {emoji}
            </button>
          ))}
        </div>
      )}

      {tab === 'custom' && (
        <div>
          {loadError && <p className="text-xs text-muted">{t('emojiPicker.customError')}</p>}
          {!loadError && custom.length === 0 && (
            <p className="text-xs text-muted">{t('emojiPicker.customEmpty')}</p>
          )}
          {custom.length > 0 && (
            <div className="grid max-h-40 grid-cols-6 gap-1 overflow-y-auto sm:grid-cols-8">
              {custom.map((emoji) => {
                const token = `<:${emoji.name}:${emoji.id}>`
                const selected = value === token || value === `<a:${emoji.name}:${emoji.id}>`
                return (
                  <button
                    key={emoji.id}
                    type="button"
                    onClick={() => onChange(token)}
                    title={emoji.name}
                    className={`flex h-9 items-center justify-center rounded-control transition-colors hover:bg-primary-muted ${
                      selected ? 'bg-primary-muted ring-1 ring-primary' : 'bg-background'
                    }`}
                    aria-label={emoji.name}
                    aria-pressed={selected}
                  >
                    <img src={emoji.url} alt={emoji.name} className="h-6 w-6" />
                  </button>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
