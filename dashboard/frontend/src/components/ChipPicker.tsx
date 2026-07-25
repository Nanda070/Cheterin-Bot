import { X } from '@phosphor-icons/react'
import { isChannelDead } from '../api/client'
import { useT } from '../context/LanguageContext'
import { Select, type SelectOption } from './ui/Select'

interface ChipPickerProps {
  label: string
  hint?: string
  options: SelectOption[]
  selected: string[]
  onChange: (ids: string[]) => void
}

/** Выбор нескольких каналов/ролей: выпадающий список добавляет, чипы удаляются крестиком. */
export function ChipPicker({ label, hint, options, selected, onChange }: ChipPickerProps) {
  const t = useT()
  const byId = new Map(options.map((o) => [o.id, o]))
  const available = options.filter((o) => !selected.includes(o.id))

  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-sm text-muted">{label}</span>
      <div className="flex flex-wrap items-center gap-1.5 rounded-control border border-border bg-background p-2">
        {selected.map((id) => {
          const opt = byId.get(id)
          const dead = opt ? isChannelDead(opt) : false
          return (
            <span
              key={id}
              className={`flex items-center gap-1 rounded-full px-2.5 py-1 text-xs text-foreground ${
                dead ? 'bg-danger/15 ring-1 ring-danger/40' : 'bg-primary-muted'
              }`}
              title={dead ? t('common.channelDeadHint') : undefined}
            >
              {opt?.name ?? id}
              {dead && (
                <span className="text-[10px] font-medium uppercase tracking-wide text-danger">
                  {t('common.channelDead')}
                </span>
              )}
              <button
                type="button"
                onClick={() => onChange(selected.filter((v) => v !== id))}
                className="text-muted hover:text-danger"
                aria-label={`Убрать ${opt?.name ?? id}`}
              >
                <X size={12} />
              </button>
            </span>
          )
        })}
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
