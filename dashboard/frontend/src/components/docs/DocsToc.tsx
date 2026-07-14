import { useEffect, useState, type RefObject } from 'react'

interface TocItem {
  id: string
  text: string
  level: 2 | 3
}

interface DocsTocProps {
  containerRef: RefObject<HTMLElement | null>
  activeId: string
}

function slugify(text: string, seen: Map<string, number>): string {
  const base =
    text
      .toLowerCase()
      .trim()
      .replace(/[^\p{L}\p{N}]+/gu, '-')
      .replace(/^-+|-+$/g, '') || 'section'
  const count = seen.get(base) ?? 0
  seen.set(base, count + 1)
  return count === 0 ? base : `${base}-${count + 1}`
}

export function DocsToc({ containerRef, activeId }: DocsTocProps) {
  const [items, setItems] = useState<TocItem[]>([])
  const [activeHeadingId, setActiveHeadingId] = useState<string | null>(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container) {
      setItems([])
      return
    }

    const headings = Array.from(container.querySelectorAll<HTMLHeadingElement>('h2, h3'))
    const seen = new Map<string, number>()
    const nextItems = headings.map((heading) => {
      // heading.textContent includes the "#" permalink button rendered inside it —
      // strip that from a clone before reading the label, without touching the live DOM.
      const clone = heading.cloneNode(true) as HTMLElement
      clone.querySelector('button')?.remove()
      const text = clone.textContent?.trim() ?? ''
      const id = slugify(text, seen)
      heading.id = id
      return { id, text, level: heading.tagName === 'H3' ? 3 : 2 } as TocItem
    })
    setItems(nextItems)
    setActiveHeadingId(nextItems[0]?.id ?? null)

    if (headings.length === 0 || typeof IntersectionObserver === 'undefined') return

    const visible = new Set<string>()
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          const id = (entry.target as HTMLElement).id
          if (entry.isIntersecting) visible.add(id)
          else visible.delete(id)
        }
        const first = nextItems.find((item) => visible.has(item.id))
        if (first) setActiveHeadingId(first.id)
      },
      { rootMargin: '-96px 0px -70% 0px', threshold: 0 },
    )

    headings.forEach((heading) => observer.observe(heading))
    return () => observer.disconnect()
  }, [containerRef, activeId])

  if (items.length === 0) return null

  return (
    <nav className="sticky top-20 hidden w-56 shrink-0 self-start lg:block">
      <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">На этой странице</p>
      <ul className="flex flex-col gap-1 border-l border-border">
        {items.map((item) => (
          <li key={item.id}>
            <a
              href={`#${item.id}`}
              className={`block border-l-2 py-1 text-sm transition-colors ${
                item.level === 3 ? 'pl-6' : 'pl-3'
              } -ml-px ${
                item.id === activeHeadingId
                  ? 'border-primary text-foreground'
                  : 'border-transparent text-muted hover:text-foreground'
              }`}
            >
              {item.text}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  )
}
