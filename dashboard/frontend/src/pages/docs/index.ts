import type { Lang } from '../../i18n/types'
import type { DocSection } from './docPrimitives'
import { DOC_SECTIONS_EN } from './sectionsEn'
import { DOC_SECTIONS_RU } from './sectionsRu'

export type { DocSection } from './docPrimitives'

const GROUPS_RU = ['Общее', 'Модули', 'Справка'] as const
const GROUPS_EN = ['General', 'Modules', 'Reference'] as const

export function getDocSections(lang: Lang): DocSection[] {
  return lang === 'en' ? DOC_SECTIONS_EN : DOC_SECTIONS_RU
}

export function getDocGroups(lang: Lang): readonly string[] {
  return lang === 'en' ? GROUPS_EN : GROUPS_RU
}
