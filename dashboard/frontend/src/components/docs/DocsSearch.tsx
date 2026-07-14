import { MagnifyingGlass } from '@phosphor-icons/react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Modal } from '../ui/Modal'
import type { DocNavItem } from './docsNav'

interface DocsSearchProps {
  items: DocNavItem[]
}

export function DocsSearch({ items }: DocsSearchProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setOpen(true)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
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
    const groups: { group: string; items: DocNavItem[] }[] = []
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
    navigate(`/docs/${id}`)
    setOpen(false)
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="mb-4 flex w-full cursor-pointer items-center gap-2 rounded-control border border-border bg-background px-3 py-2 text-sm text-muted transition-colors hover:border-primary hover:text-foreground"
      >
        <MagnifyingGlass size={15} className="shrink-0" />
        <span className="flex-1 text-left">Поиск…</span>
        <span className="rounded-[6px] border border-border bg-surface px-1.5 py-0.5 text-[11px] text-muted">Ctrl K</span>
      </button>

      <Modal open={open} title="Поиск по документации" onClose={() => setOpen(false)}>
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && flatResults.length > 0) select(flatResults[0].id)
          }}
          placeholder="Название раздела…"
          className="mb-3 w-full rounded-control border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        />
        <div className="max-h-80 overflow-y-auto">
          {flatResults.length === 0 && <p className="px-1 py-2 text-sm text-muted">Ничего не найдено.</p>}
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
