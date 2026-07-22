export type Lang = 'ru' | 'en'

export const SUPPORTED_LANGS: Lang[] = ['ru', 'en']
export const DEFAULT_LANG: Lang = 'ru'
export const STORAGE_KEY = 'chetbot_ui_lang'

export type TranslationDict = Record<string, string>
