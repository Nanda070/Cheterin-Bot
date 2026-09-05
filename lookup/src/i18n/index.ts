export type Lang = 'ru' | 'en'

export const SUPPORTED_LANGS: Lang[] = ['ru', 'en']
export const DEFAULT_LANG: Lang = 'ru'
export const STORAGE_KEY = 'chetbot_ui_lang'

export type TranslationDict = Record<string, string>

import { ru } from './ru'
import { en } from './en'

const dictionaries: Record<Lang, TranslationDict> = { ru, en }

export function translate(lang: Lang, key: string, params?: Record<string, string | number>): string {
  const raw = dictionaries[lang][key] ?? dictionaries.ru[key] ?? key
  if (!params) return raw
  return Object.entries(params).reduce(
    (acc, [name, value]) => acc.replaceAll(`{${name}}`, String(value)),
    raw,
  )
}
