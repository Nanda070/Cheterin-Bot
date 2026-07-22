/** Mirrors bunker_localize.py — used for language-agnostic card logic in the editor. */

export const BUNKER_RELATIONSHIP_CATEGORY_RU = 'Активные (Отношения)'
export const BUNKER_RELATIONSHIP_CATEGORY_EN = 'Active (Relationships)'

export const BUNKER_RELATIONSHIP_MARKER_RU = 'Игрок №X'
export const BUNKER_RELATIONSHIP_MARKER_RU_GENITIVE = 'игрока №X'
export const BUNKER_RELATIONSHIP_MARKER_EN = 'Player #X'

export const BUNKER_HEALTHY_RU = 'Здоров'
export const BUNKER_HEALTHY_EN = 'Healthy'

export function isBunkerHealthySeverity(severity: string | null | undefined): boolean {
  return severity === BUNKER_HEALTHY_RU || severity === BUNKER_HEALTHY_EN
}

export function isBunkerHealthy(
  health: { severity?: string | null; disease_name?: string | null } | null | undefined,
): boolean {
  if (!health) return false
  if (health.disease_name == null) return true
  return isBunkerHealthySeverity(health.severity)
}

export function isBunkerRelationshipCategory(category: string | null | undefined): boolean {
  return category === BUNKER_RELATIONSHIP_CATEGORY_RU || category === BUNKER_RELATIONSHIP_CATEGORY_EN
}

export function substituteBunkerRelationshipPlayer(template: string, playerName: string): string {
  return template
    .replaceAll(BUNKER_RELATIONSHIP_MARKER_RU, playerName)
    .replaceAll(BUNKER_RELATIONSHIP_MARKER_RU_GENITIVE, playerName)
    .replaceAll(BUNKER_RELATIONSHIP_MARKER_EN, playerName)
}
