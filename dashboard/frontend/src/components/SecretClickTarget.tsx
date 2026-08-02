import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSecretClicks } from '../hooks/useSecretClicks'

type Props = {
  clicks: number
  to: string
  children: ReactNode
  className?: string
  title?: string
  as?: 'button' | 'span'
}

/** Invisible “mash me” hotspot that navigates after N rapid clicks. */
export function SecretClickTarget({
  clicks,
  to,
  children,
  className,
  title,
  as = 'span',
}: Props) {
  const navigate = useNavigate()
  const onClick = useSecretClicks(clicks, () => navigate(to))

  if (as === 'button') {
    return (
      <button type="button" className={className} title={title} onClick={onClick}>
        {children}
      </button>
    )
  }

  return (
    <span
      className={className}
      title={title}
      onClick={onClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onClick()
        }
      }}
      role="presentation"
    >
      {children}
    </span>
  )
}
