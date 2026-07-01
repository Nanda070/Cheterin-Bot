import type { HTMLAttributes, ReactNode } from 'react'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  interactive?: boolean
}

export function Card({ children, interactive = false, className = '', ...rest }: CardProps) {
  return (
    <div
      className={[
        'rounded-card border border-border bg-surface p-5',
        'shadow-[0_1px_0_0_rgba(255,255,255,0.04)_inset]',
        interactive &&
          'cursor-pointer transition-colors duration-200 ease-out hover:bg-surface-hover',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      {...rest}
    >
      {children}
    </div>
  )
}
