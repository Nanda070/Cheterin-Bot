import { useNavigate } from 'react-router-dom'
import { CommandPalette } from '../CommandPalette'
import type { DocNavItem } from './docsNav'

interface DocsSearchProps {
  items: DocNavItem[]
}

export function DocsSearch({ items }: DocsSearchProps) {
  const navigate = useNavigate()

  return (
    <CommandPalette
      items={items}
      onSelect={(id) => navigate(`/docs/${id}`)}
      triggerLabel="Поиск…"
      title="Поиск по документации"
      placeholder="Название раздела…"
      emptyLabel="Ничего не найдено."
    />
  )
}
