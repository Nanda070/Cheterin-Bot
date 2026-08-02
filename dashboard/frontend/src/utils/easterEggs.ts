/** Session-scoped easter-egg state (logo glitch / secret rooms). */

export const LOGO_TAGLINE_KEY = 'cheterin.egg.logoTagline'
export const LOGO_UNLOCKED_KEY = 'cheterin.egg.logoUnlocked'

export const SECRET_ROOMS = {
  snowdin: '/sans',
  waterfall: '/waterfall',
  core: '/core',
  judgment: '/judgment',
} as const

export type SecretRoomId = keyof typeof SECRET_ROOMS

export function isLogoEggUnlocked(): boolean {
  try {
    return sessionStorage.getItem(LOGO_UNLOCKED_KEY) === '1'
  } catch {
    return false
  }
}

export function unlockLogoEgg(): void {
  try {
    sessionStorage.setItem(LOGO_UNLOCKED_KEY, '1')
    sessionStorage.setItem(LOGO_TAGLINE_KEY, '1')
  } catch {
    /* private browsing */
  }
}

export function logoShowsEggTagline(): boolean {
  try {
    return sessionStorage.getItem(LOGO_TAGLINE_KEY) === '1'
  } catch {
    return false
  }
}

/** Brief crimson glitch on the document root. */
export function flashLogoGlitch(ms = 700): void {
  const root = document.documentElement
  root.classList.add('cheterin-logo-glitch')
  window.setTimeout(() => root.classList.remove('cheterin-logo-glitch'), ms)
}
