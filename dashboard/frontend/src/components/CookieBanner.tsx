import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useT } from '../context/LanguageContext'

export const COOKIE_CONSENT_KEY = 'chetbot_cookie_consent'

function readConsent(): boolean {
  try {
    return localStorage.getItem(COOKIE_CONSENT_KEY) === '1'
  } catch {
    return false
  }
}

function writeConsent(): void {
  try {
    localStorage.setItem(COOKIE_CONSENT_KEY, '1')
  } catch {
    /* private mode — banner may reappear next visit */
  }
}

/** Bottom plaque: essential cookies notice; persists accept in localStorage. */
export function CookieBanner() {
  const t = useT()
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    setVisible(!readConsent())
  }, [])

  if (!visible) return null

  const accept = () => {
    writeConsent()
    setVisible(false)
  }

  return (
    <div
      role="dialog"
      aria-label={t('cookieBanner.aria')}
      className="fixed inset-x-0 bottom-0 z-50 border-t border-primary/30 bg-[color-mix(in_srgb,var(--color-background-deep)_92%,var(--color-primary-deep)_8%)] px-4 py-3 shadow-[0_-8px_32px_rgba(0,0,0,0.45)] backdrop-blur-md sm:px-6"
    >
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-6">
        <p className="min-w-0 text-sm leading-relaxed text-muted">
          {t('cookieBanner.text')}{' '}
          <Link to="/cookies" className="font-medium text-primary hover:underline">
            {t('cookieBanner.link')}
          </Link>
          .
        </p>
        <div className="flex shrink-0 items-center gap-2">
          <Link
            to="/cookies"
            className="rounded-control border border-border px-3 py-1.5 text-sm text-muted transition-colors hover:border-primary/40 hover:text-foreground"
          >
            {t('cookieBanner.learnMore')}
          </Link>
          <button
            type="button"
            onClick={accept}
            className="cursor-pointer rounded-control bg-primary px-4 py-1.5 text-sm font-medium text-white transition-colors hover:bg-primary-hover"
          >
            {t('cookieBanner.accept')}
          </button>
        </div>
      </div>
    </div>
  )
}
