/** In-memory easter-egg state — survives SPA navigations, clears on full reload (F5). */

export const SECRET_ROOMS = {
  snowdin: '/sans',
  waterfall: '/waterfall',
  core: '/core',
  judgment: '/judgment',
} as const

export type SecretRoomId = keyof typeof SECRET_ROOMS

const STREAK_GAP_MS = 1400

/** Module memory (not sessionStorage) so F5 resets the logo egg. */
let logoEggUnlocked = false
let logoEggTagline = false
let logoStreak = 0
let logoStreakAt = 0

// Drop legacy session keys from earlier builds.
try {
  sessionStorage.removeItem('cheterin.egg.logoTagline')
  sessionStorage.removeItem('cheterin.egg.logoUnlocked')
} catch {
  /* private browsing */
}

export function isLogoEggUnlocked(): boolean {
  return logoEggUnlocked
}

export function logoShowsEggTagline(): boolean {
  return logoEggTagline
}

export function unlockLogoEgg(): void {
  logoEggUnlocked = true
  logoEggTagline = true
}

export type LogoEggResult = 'none' | 'unlock' | 'snowdin'

/**
 * Count a logo click toward the easter egg (module-level streak survives route changes).
 * Does not block normal navigation — caller should only preventDefault on unlock/snowdin.
 */
export function registerLogoEggClick(): LogoEggResult {
  const now = Date.now()
  if (now - logoStreakAt > STREAK_GAP_MS) logoStreak = 0
  logoStreakAt = now
  logoStreak += 1

  const need = logoEggUnlocked ? 5 : 7
  if (logoStreak < need) return 'none'

  logoStreak = 0
  if (!logoEggUnlocked) {
    unlockLogoEgg()
    return 'unlock'
  }
  return 'snowdin'
}

/** Brief crimson glitch on the document root. */
export function flashLogoGlitch(ms = 700): void {
  const root = document.documentElement
  root.classList.add('cheterin-logo-glitch')
  window.setTimeout(() => root.classList.remove('cheterin-logo-glitch'), ms)
}
