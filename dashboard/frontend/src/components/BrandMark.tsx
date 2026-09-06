import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Sparkle } from '@phosphor-icons/react'
import { useT } from '../context/LanguageContext'
import {
  flashLogoGlitch,
  logoShowsEggTagline,
  registerLogoEggClick,
  SECRET_ROOMS,
} from '../utils/easterEggs'

/** Docs / legal — no easter-egg counters (user request). */
function eggDisabledOnPath(pathname: string): boolean {
  return (
    pathname.startsWith('/docs') ||
    pathname.startsWith('/terms') ||
    pathname.startsWith('/privacy') ||
    pathname.startsWith('/cookies') ||
    pathname.startsWith('/disclaimer')
  )
}

type Props = {
  to?: string
  className?: string
  iconClassName?: string
  iconSize?: number
  labelClassName?: string
}

/**
 * Site brand mark — navigates immediately on click.
 * 7 rapid clicks (streak survives SPA nav) → glitch + tagline; 5 more → /sans.
 */
const BRAND_MARK_BASE = 'inline-flex items-center gap-2 font-semibold tracking-tight'

export function BrandMark({
  to = '/about',
  className = '',
  iconClassName = 'text-primary',
  iconSize = 20,
  labelClassName,
}: Props) {
  const t = useT()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const eggsOff = eggDisabledOnPath(pathname)
  const [taglineOn, setTaglineOn] = useState(() => logoShowsEggTagline())

  const label = !eggsOff && taglineOn ? t('egg.logo.tagline') : 'Cheterin'

  return (
    <Link
      to={to}
      className={`${BRAND_MARK_BASE}${className ? ` ${className}` : ''}`}
      onClick={(e) => {
        if (eggsOff) return

        const result = registerLogoEggClick()
        if (result === 'unlock') {
          e.preventDefault()
          flashLogoGlitch()
          setTaglineOn(true)
          return
        }
        if (result === 'snowdin') {
          e.preventDefault()
          navigate(SECRET_ROOMS.snowdin)
          return
        }
        // Normal click: let <Link> navigate immediately (no delay).
      }}
    >
      <Sparkle size={iconSize} weight="fill" className={iconClassName} aria-hidden />
      <span className={labelClassName}>{label}</span>
    </Link>
  )
}
