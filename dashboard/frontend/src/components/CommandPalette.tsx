import { MagnifyingGlass } from '@phosphor-icons/react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Modal } from './ui/Modal'

export interface CommandPaletteItem {
  id: string
  title: string
  group: string
}

interface CommandPaletteProps {
  items: CommandPaletteItem[]
  onSelect: (id: string) => void
  title: string
  placeholder: string
  emptyLabel: string
  /** Trigger button label. Omit (with `hideTrigger`) when the palette is opened from elsewhere (e.g. a header icon). */
  triggerLabel?: string
  shortcutLabel?: string
  /** Hide the built-in trigger button; Ctrl/Cmd+K still opens it, and `open`/`onOpenChange` let a caller open it too. */
  hideTrigger?: boolean
  open?: boolean
  onOpenChange?: (open: boolean) => void
  triggerClassName?: string
}

/**
 * Generic Ctrl/Cmd+K search-and-jump palette: filters `items` by title, grouped by `group`,
 * Enter selects the first match. Extracted from the docs search so DashboardShell can reuse it
 * to jump between nav pages.
 */
export function CommandPalette({
  items,
  onSelect,
  title,
  placeholder,
  emptyLabel,
  triggerLabel,
  shortcutLabel = 'Ctrl K',
  hideTrigger = false,
  open: openProp,
  onOpenChange,
  triggerClassName,
}: CommandPaletteProps) {
  const [openState, setOpenState] = useState(false)
  const open = openProp ?? openState
  const setOpen = (v: boolean) => {
    setOpenState(v)
    onOpenChange?.(v)
  }
  const [query, setQuery] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setOpen(true)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (open) {
      setQuery('')
      setTimeout(() => inputRef.current?.focus(), 0)
    }
  }, [open])

  const groupedResults = useMemo(() => {
    const q = query.trim().toLowerCase()
    const filtered = q ? items.filter((item) => item.title.toLowerCase().includes(q)) : items
    const groups: { group: string; items: CommandPaletteItem[] }[] = []
    for (const item of filtered) {
      const last = groups[groups.length - 1]
      if (last && last.group === item.group) {
        last.items.push(item)
      } else {
        groups.push({ group: item.group, items: [item] })
      }
    }
    return groups
  }, [items, query])

  const flatResults = useMemo(() => groupedResults.flatMap((g) => g.items), [groupedResults])

  const select = (id: string) => {
    onSelect(id)
    setOpen(false)
  }

  return (
    <>
      {!hideTrigger && (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className={
            triggerClassName ??
            'mb-4 flex w-full cursor-pointer items-center gap-2 rounded-control border border-border bg-background px-3 py-2 text-sm text-muted transition-colors hover:border-primary hover:text-foreground'
          }
        >
          <MagnifyingGlass size={15} className="shrink-0" />
          <span className="flex-1 text-left">{triggerLabel}</span>
          <span className="rounded-[6px] border border-border bg-surface px-1.5 py-0.5 text-[11px] text-muted">{shortcutLabel}</span>
        </button>
      )}

      <Modal open={open} title={title} onClose={() => setOpen(false)}>
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && flatResults.length > 0) select(flatResults[0].id)
          }}
          placeholder={placeholder}
          className="mb-3 w-full rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />
        <div className="max-h-80 overflow-y-auto">
          {flatResults.length === 0 && <p className="px-1 py-2 text-sm text-muted">{emptyLabel}</p>}
          {groupedResults.map(({ group, items: groupItems }) => (
            <div key={group} className="mb-2">
              <p className="mb-1 px-1 text-[11px] font-medium uppercase tracking-wide text-muted">{group}</p>
              {groupItems.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => select(item.id)}
                  className="flex w-full cursor-pointer items-center rounded-[8px] px-3 py-2 text-left text-sm text-foreground transition-colors hover:bg-surface-hover"
                >
                  {item.title}
                </button>
              ))}
            </div>
          ))}
        </div>
      </Modal>
    </>
  )
}
