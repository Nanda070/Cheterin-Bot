import { useT } from '../context/LanguageContext'

interface Props {
  /** Placeholder names found in the message, e.g. `Eventer` for `{Eventer}`. */
  names: string[]
  values: Record<string, string>
  onChange: (name: string, value: string) => void
}

/** One input per `{Name}` placeholder found in the message; renders nothing when there are none. */
export function PlaceholderInputs({ names, values, onChange }: Props) {
  const t = useT()
  if (names.length === 0) return null

  return (
    <div className="flex flex-col gap-2 rounded-control border border-border bg-surface p-3">
      <p className="text-sm font-medium text-foreground">{t('embedBuilder.placeholders.title')}</p>
      <p className="text-xs text-muted">{t('embedBuilder.placeholders.hint')}</p>
      {names.map((name) => (
        <label key={name} className="flex items-center gap-2">
          <code className="w-32 shrink-0 truncate text-xs text-muted" title={`{${name}}`}>{`{${name}}`}</code>
          <input
            value={values[name] ?? ''}
            onChange={(e) => onChange(name, e.target.value)}
            className="min-w-0 flex-1 rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
          />
        </label>
      ))}
    </div>
  )
}
