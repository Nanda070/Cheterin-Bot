import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  variant?: Variant
}

const VARIANT_CLASSES: Record<Variant, string> = {
  primary:
    'bg-primary text-white shadow-[0_0_0_1px_rgba(88,101,242,0.4),0_8px_20px_-6px_rgba(88,101,242,0.55)] hover:bg-primary-hover',
  secondary: 'bg-surface-hover text-foreground border border-border hover:bg-border',
  ghost: 'bg-transparent text-muted hover:bg-surface-hover hover:text-foreground',
  danger: 'bg-danger text-white hover:bg-danger-hover',
}

export function Button({ children, variant = 'primary', className = '', disabled, ...rest }: ButtonProps) {
  return (
    <button
      disabled={disabled}
      className={[
        'inline-flex cursor-pointer items-center justify-center gap-2 rounded-control px-4 py-2.5',
        'text-sm font-medium transition-all duration-200 ease-out',
        'disabled:cursor-not-allowed disabled:opacity-50',
        VARIANT_CLASSES[variant],
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      {...rest}
    >
      {children}
    </button>
  )
}
