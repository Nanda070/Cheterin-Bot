import { BookOpen, CaretRight, PuzzlePiece, Question, type Icon } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import type { DocNavItem } from './docsNav'

const GROUP_ICONS: Record<string, Icon> = {
  Общее: BookOpen,
  Модули: PuzzlePiece,
  Справка: Question,
}

interface DocsSidebarProps {
  items: DocNavItem[]
  groups: string[]
  activeId: string
}

export function DocsSidebar({ items, groups, activeId }: DocsSidebarProps) {
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({})

  useEffect(() => {
    const activeGroup = items.find((item) => item.id === activeId)?.group
    if (!activeGroup) return
    setCollapsed((prev) => (prev[activeGroup] ? { ...prev, [activeGroup]: false } : prev))
  }, [activeId, items])

  return (
    <nav aria-label="Разделы документации" className="flex flex-col gap-4">
      {groups.map((group) => {
        const GroupIcon = GROUP_ICONS[group] ?? BookOpen
        const open = !collapsed[group]
        return (
          <div key={group}>
            <button
              type="button"
              aria-expanded={open}
              onClick={() => setCollapsed((prev) => ({ ...prev, [group]: !prev[group] }))}
              className="mb-1 flex w-full cursor-pointer items-center gap-1.5 rounded-control px-1 py-1 text-left text-xs font-medium uppercase tracking-wide text-muted transition-colors hover:text-foreground"
            >
              <GroupIcon size={13} className="shrink-0" />
              <span className="flex-1">{group}</span>
              <CaretRight size={12} className={`shrink-0 transition-transform duration-150 ${open ? 'rotate-90' : ''}`} />
            </button>
            {open && (
              <div className="flex flex-col gap-0.5">
                {items
                  .filter((item) => item.group === group)
                  .map((item) => (
                    <NavLink
                      key={item.id}
                      to={`/docs/${item.id}`}
                      className={`rounded-r-[8px] border-l-2 py-1.5 pl-3 pr-2 text-sm transition-colors ${
                        item.id === activeId
                          ? 'border-primary bg-primary-muted text-foreground'
                          : 'border-transparent text-muted hover:bg-surface-hover hover:text-foreground'
                      }`}
                    >
                      {item.title}
                    </NavLink>
                  ))}
              </div>
            )}
          </div>
        )
      })}
    </nav>
  )
}
