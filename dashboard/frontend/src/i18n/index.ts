import en from './en'
import ru from './ru'
import type { Lang, TranslationDict } from './types'

export const dictionaries: Record<Lang, TranslationDict> = { ru, en }

export function translate(lang: Lang, key: string, params?: Record<string, string | number>): string {
  const dict = dictionaries[lang] ?? dictionaries.ru
  let text = dict[key] ?? dictionaries.ru[key] ?? key
  if (params) {
    for (const [name, value] of Object.entries(params)) {
      text = text.replaceAll(`{${name}}`, String(value))
    }
  }
  return text
}

export type { Lang, TranslationDict }
export { DEFAULT_LANG, SUPPORTED_LANGS, STORAGE_KEY } from './types'
