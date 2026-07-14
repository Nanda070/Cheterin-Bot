import { X } from '@phosphor-icons/react'
import { Select } from './ui/Select'

interface Option {
  id: string
  name: string
  category?: string
}

interface ChipPickerProps {
  label: string
  hint?: string
  options: Option[]
  selected: string[]
  onChange: (ids: string[]) => void
}

/** Выбор нескольких каналов/ролей: выпадающий список добавляет, чипы удаляются крестиком. */
export function ChipPicker({ label, hint, options, selected, onChange }: ChipPickerProps) {
  const byId = new Map(options.map((o) => [o.id, o]))
  const available = options.filter((o) => !selected.includes(o.id))

  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-sm text-muted">{label}</span>
      <div className="flex flex-wrap items-center gap-1.5 rounded-control border border-border bg-background p-2">
        {selected.map((id) => (
          <span
            key={id}
            className="flex items-center gap-1 rounded-full bg-primary-muted px-2.5 py-1 text-xs text-foreground"
          >
            {byId.get(id)?.name ?? id}
            <button
              type="button"
              onClick={() => onChange(selected.filter((v) => v !== id))}
              className="text-muted hover:text-danger"
              aria-label={`Убрать ${byId.get(id)?.name ?? id}`}
            >
              <X size={12} />
            </button>
          </span>
        ))}
        <Select
          value=""
          onChange={(id) => onChange([...selected, id])}
          options={available.map((o) => ({ ...o, name: o.category ? `${o.category} / ${o.name}` : o.name }))}
          placeholder="+ Добавить…"
          variant="bare"
          className="min-w-36 flex-1"
        />
      </div>
      {hint && <span className="text-xs text-muted">{hint}</span>}
    </div>
  )
}
