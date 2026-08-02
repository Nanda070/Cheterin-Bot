import { useCallback, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Sparkle } from '@phosphor-icons/react'
import { useT } from '../context/LanguageContext'
import { useSecretClicks } from '../hooks/useSecretClicks'
import {
  flashLogoGlitch,
  isLogoEggUnlocked,
  logoShowsEggTagline,
  unlockLogoEgg,
  SECRET_ROOMS,
} from '../utils/easterEggs'

/** Docs / legal — no easter-egg counters (user request). */
function eggDisabledOnPath(pathname: string): boolean {
  return (
    pathname.startsWith('/docs') ||
    pathname.startsWith('/terms') ||
    pathname.startsWith('/privacy')
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
 * Site brand mark. 7 rapid clicks → glitch + session tagline (idea 2).
 * 5 more rapid clicks after unlock → /sans (Snowdin).
 */
export function BrandMark({
  to = '/about',
  className = 'flex items-center gap-2 font-semibold tracking-tight',
  iconClassName = 'text-primary',
  iconSize = 20,
  labelClassName,
}: Props) {
  const t = useT()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const eggsOff = eggDisabledOnPath(pathname)
  const [taglineOn, setTaglineOn] = useState(() => logoShowsEggTagline())
  const [unlocked, setUnlocked] = useState(() => isLogoEggUnlocked())

  const goSnowdin = useCallback(() => {
    navigate(SECRET_ROOMS.snowdin)
  }, [navigate])

  const unlock = useCallback(() => {
    unlockLogoEgg()
    flashLogoGlitch()
    setUnlocked(true)
    setTaglineOn(true)
  }, [])

  const onSecretClick = useSecretClicks(unlocked ? 5 : 7, unlocked ? goSnowdin : unlock)

  const label = !eggsOff && taglineOn ? t('egg.logo.tagline') : 'Cheterin'

  return (
    <Link
      to={to}
      className={className}
      onClick={() => {
        if (!eggsOff) onSecretClick()
      }}
    >
      <Sparkle size={iconSize} weight="fill" className={iconClassName} aria-hidden />
      <span className={labelClassName}>{label}</span>
    </Link>
  )
}
