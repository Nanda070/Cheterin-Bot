import { CaretDown } from '@phosphor-icons/react'
import { useEffect, useRef, useState } from 'react'
import { isChannelDead } from '../../api/client'
import { useT } from '../../context/LanguageContext'

export interface SelectOption {
  id: string
  name: string
  category?: string
  bot_can_view?: boolean
  bot_can_send?: boolean
}

interface SelectProps {
  value: string
  onChange: (id: string) => void
  options: SelectOption[]
  placeholder?: string
  className?: string
  id?: string
  disabled?: boolean
  ariaLabel?: string
  /** 'bare' — без рамки/фона на триггере, для встраивания внутрь уже стилизованного контейнера (см. ChipPicker). */
  variant?: 'default' | 'bare'
}

/**
 * Полностью кастомный themed listbox — замена нативному `<select>`, чей
 * выпадающий попап рисует браузер/ОС и не поддаётся тёмной теме. Паттерн
 * взаимодействия (click-outside, Escape) как у Dropdown.tsx.
 *
 * For channel options with bot_can_view / bot_can_send: dead channels show a
 * badge and cannot be newly selected; a currently saved dead value stays
 * visible and selectable so admins can see/change it.
 */
export function Select({
  value,
  onChange,
  options,
  placeholder = 'Выберите…',
  className = '',
  id,
  disabled,
  ariaLabel,
  variant = 'default',
}: SelectProps) {
  const t = useT()
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!isOpen) return

    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setIsOpen(false)
    }

    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen])

  const selected = options.find((o) => o.id === value)
  const selectedDead = selected ? isChannelDead(selected) : false

  const groups: { category: string; items: SelectOption[] }[] = []
  for (const option of options) {
    const category = option.category ?? ''
    const last = groups[groups.length - 1]
    if (last && last.category === category) {
      last.items.push(option)
    } else {
      groups.push({ category, items: [option] })
    }
  }

  const deadBadge = (
    <span
      className="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-danger bg-danger/15"
      title={t('common.channelDeadHint')}
    >
      {t('common.channelDead')}
    </span>
  )

  return (
    <div className={`relative ${className}`} ref={containerRef}>
      <button
        type="button"
        id={id}
        disabled={disabled}
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        onClick={() => setIsOpen((prev) => !prev)}
        className={`flex w-full cursor-pointer items-center justify-between gap-2 rounded-control text-left text-sm outline-none transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
          variant === 'bare'
            ? 'bg-transparent px-1 py-1'
            : 'border border-border bg-background px-3 py-2 focus:border-primary'
        }`}
      >
        <span className={`flex min-w-0 items-center gap-2 ${selected ? 'text-foreground' : 'text-muted'}`}>
          <span className="truncate">{selected ? selected.name : placeholder}</span>
          {selectedDead && deadBadge}
        </span>
        <CaretDown size={14} className={`shrink-0 text-muted transition-transform duration-150 ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      {isOpen && (
        <div
          role="listbox"
          className="animate-dropdown-in absolute left-0 top-full z-20 mt-1.5 max-h-64 w-full min-w-48 overflow-y-auto rounded-card border border-border bg-surface p-1.5 shadow-[0_12px_28px_-8px_rgba(0,0,0,0.6)]"
        >
          {options.length === 0 && <p className="px-3 py-2 text-sm text-muted">Нет доступных вариантов</p>}
          {groups.map((group, index) => (
            <div key={`${group.category}-${index}`}>
              {group.category && (
                <p className="px-3 pb-1 pt-2 text-[11px] font-medium uppercase tracking-wide text-muted first:pt-1">
                  {group.category}
                </p>
              )}
              {group.items.map((option) => {
                const dead = isChannelDead(option)
                const isCurrent = option.id === value
                // Disable dead channels for new picks; keep current saved value clickable.
                const optionDisabled = dead && !isCurrent
                return (
                  <button
                    key={option.id}
                    type="button"
                    role="option"
                    aria-selected={isCurrent}
                    aria-disabled={optionDisabled || undefined}
                    disabled={optionDisabled}
                    title={dead ? t('common.channelDeadHint') : undefined}
                    onClick={() => {
                      if (optionDisabled) return
                      onChange(option.id)
                      setIsOpen(false)
                    }}
                    className={`flex w-full items-center justify-between gap-2 rounded-[8px] px-3 py-2 text-left text-sm transition-colors duration-150 ease-out ${
                      optionDisabled
                        ? 'cursor-not-allowed opacity-55 text-muted'
                        : isCurrent
                          ? 'cursor-pointer bg-primary-muted text-foreground'
                          : 'cursor-pointer text-foreground hover:bg-surface-hover'
                    }`}
                  >
                    <span className="truncate">{option.name}</span>
                    {dead && deadBadge}
                  </button>
                )
              })}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
