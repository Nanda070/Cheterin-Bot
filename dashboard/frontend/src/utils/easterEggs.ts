/** In-memory easter-egg state — survives SPA navigations, clears on full reload (F5). */

export const SECRET_ROOMS = {
  snowdin: '/sans',
  waterfall: '/waterfall',
  core: '/core',
  judgment: '/judgment',
} as const

export type SecretRoomId = keyof typeof SECRET_ROOMS

/** Module memory (not sessionStorage) so F5 resets the logo egg. */
let logoEggUnlocked = false
let logoEggTagline = false

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

/** Brief crimson glitch on the document root. */
export function flashLogoGlitch(ms = 700): void {
  const root = document.documentElement
  root.classList.add('cheterin-logo-glitch')
  window.setTimeout(() => root.classList.remove('cheterin-logo-glitch'), ms)
}
