/**
 * Admin-facing dashboard changelog. Bump `version` when shipping user-visible panel updates.
 * Only the latest update is kept here; the full history lives in the Dev Blog (/dev-blog).
 */

export interface WhatsNewEntry {
  /** Opaque id used for dismiss persistence (e.g. `2026.08`). */
  version: string
  /** Display date in `YYYY-MM` form — do not invent precise day stamps. */
  date: string
  /** i18n key suffixes under `whatsNew.item.*`. */
  itemKeys: readonly string[]
}

export const WHATS_NEW: readonly WhatsNewEntry[] = [
  {
    version: '2026.10.1',
    date: '2026-10',
    itemKeys: ['embedJsonImport', 'embedMultiple', 'embedPlaceholders', 'embedBulkTemplates'],
  },
]

export const LATEST_WHATS_NEW = WHATS_NEW[0]

export function whatsNewDismissKey(version: string): string {
  return `cheterin.whatsNew.dismissed.${version}`
}

export function isWhatsNewDismissed(version: string): boolean {
  try {
    return localStorage.getItem(whatsNewDismissKey(version)) === '1'
  } catch {
    return false
  }
}

export function dismissWhatsNew(version: string): void {
  try {
    localStorage.setItem(whatsNewDismissKey(version), '1')
  } catch {
    /* private browsing / blocked storage */
  }
}
