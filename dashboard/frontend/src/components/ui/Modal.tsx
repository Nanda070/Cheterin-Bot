import { useEffect, type ReactNode } from 'react'

interface ModalProps {
  open: boolean
  title: string
  children: ReactNode
  onClose: () => void
  size?: 'md' | 'xl'
}

const SIZE_CLASS = {
  md: 'max-w-md',
  xl: 'max-w-5xl',
} as const

export function Modal({ open, title, children, onClose, size = 'md' }: ModalProps) {
  useEffect(() => {
    if (!open) return
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [open, onClose])

  if (!open) return null

  return (
    <div
      data-testid="modal-overlay"
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 p-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        className={`animate-dropdown-in flex max-h-[90vh] w-full flex-col rounded-card border border-border bg-surface p-5 shadow-[0_12px_28px_-8px_rgba(0,0,0,0.6)] ${SIZE_CLASS[size]}`}
        onClick={(event) => event.stopPropagation()}
      >
        <h2 className="mb-4 shrink-0 text-lg font-semibold text-foreground">{title}</h2>
        <div className="min-h-0 flex-1 overflow-y-auto pr-1">{children}</div>
      </div>
    </div>
  )
}
