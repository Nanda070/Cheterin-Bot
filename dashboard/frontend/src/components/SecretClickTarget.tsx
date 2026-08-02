import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSecretClicks } from '../hooks/useSecretClicks'

type Props = {
  clicks: number
  to: string
  children: ReactNode
  className?: string
  title?: string
  as?: 'button' | 'div'
}

/**
 * Mash hotspot: after N rapid clicks, navigate to `to`.
 * Must be a <div> (not <span>) so headings/block children stay inside the click target.
 */
export function SecretClickTarget({
  clicks,
  to,
  children,
  className,
  title,
  as = 'div',
}: Props) {
  const navigate = useNavigate()
  const onActivate = useSecretClicks(clicks, () => navigate(to))

  if (as === 'button') {
    return (
      <button type="button" className={className} title={title} onClick={onActivate}>
        {children}
      </button>
    )
  }

  return (
    <div
      className={className}
      title={title}
      onClick={onActivate}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onActivate()
        }
      }}
    >
      {children}
    </div>
  )
}
