import { useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Sparkle } from '@phosphor-icons/react'
import { useT } from '../context/LanguageContext'
import {
  flashLogoGlitch,
  isLogoEggUnlocked,
  logoShowsEggTagline,
  unlockLogoEgg,
  SECRET_ROOMS,
} from '../utils/easterEggs'

const STREAK_GAP_MS = 1400

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
 * Site brand mark.
 * 7 rapid clicks → glitch + tagline (clears on F5).
 * 5 more rapid clicks → /sans.
 * Single slow click → normal navigate to `to`.
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
  const countRef = useRef(0)
  const lastRef = useRef(0)
  const navTimerRef = useRef<number | null>(null)

  const clearNavTimer = () => {
    if (navTimerRef.current != null) {
      window.clearTimeout(navTimerRef.current)
      navTimerRef.current = null
    }
  }

  const label = !eggsOff && taglineOn ? t('egg.logo.tagline') : 'Cheterin'

  return (
    <Link
      to={to}
      className={className}
      onClick={(e) => {
        if (eggsOff) return

        // Keep the mark mounted so the click streak can accumulate.
        e.preventDefault()
        clearNavTimer()

        const now = Date.now()
        if (now - lastRef.current > STREAK_GAP_MS) countRef.current = 0
        lastRef.current = now
        countRef.current += 1

        const need = unlocked ? 5 : 7
        if (countRef.current >= need) {
          countRef.current = 0
          if (!unlocked) {
            unlockLogoEgg()
            flashLogoGlitch()
            setUnlocked(true)
            setTaglineOn(true)
          } else {
            navigate(SECRET_ROOMS.snowdin)
          }
          return
        }

        // Lone click (or start of a streak): go to brand page if no more clicks arrive.
        if (countRef.current === 1) {
          navTimerRef.current = window.setTimeout(() => {
            countRef.current = 0
            navTimerRef.current = null
            navigate(to)
          }, STREAK_GAP_MS)
        }
      }}
    >
      <Sparkle size={iconSize} weight="fill" className={iconClassName} aria-hidden />
      <span className={labelClassName}>{label}</span>
    </Link>
  )
}
