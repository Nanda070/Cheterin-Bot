import { useEffect, useRef, useState, type ReactNode } from 'react'

interface DropdownProps {
  trigger: ReactNode
  children: ReactNode
  align?: 'left' | 'right'
}

export function Dropdown({ trigger, children, align = 'right' }: DropdownProps) {
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

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={isOpen}
        onClick={() => setIsOpen((prev) => !prev)}
        className="cursor-pointer rounded-control transition-colors duration-200 ease-out"
      >
        {trigger}
      </button>
      {isOpen && (
        <div
          role="menu"
          className={[
            'animate-dropdown-in absolute top-full z-20 mt-2 min-w-48 origin-top rounded-card',
            'border border-border bg-surface p-1.5 shadow-[0_12px_28px_-8px_rgba(0,0,0,0.6)]',
            align === 'right' ? 'right-0' : 'left-0',
          ].join(' ')}
          onClick={() => setIsOpen(false)}
        >
          {children}
        </div>
      )}
    </div>
  )
}

export function DropdownItem({
  children,
  onClick,
  danger = false,
}: {
  children: ReactNode
  onClick?: () => void
  danger?: boolean
}) {
  return (
    <button
      type="button"
      role="menuitem"
      onClick={onClick}
      className={[
        'flex w-full cursor-pointer items-center gap-2 rounded-[8px] px-3 py-2 text-left text-sm',
        'transition-colors duration-150 ease-out',
        danger ? 'text-danger hover:bg-danger/10' : 'text-foreground hover:bg-surface-hover',
      ].join(' ')}
    >
      {children}
    </button>
  )
}
