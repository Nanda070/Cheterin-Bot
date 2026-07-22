import { describe, expect, it } from 'vitest'
import { translate } from './index'

describe('i18n translate', () => {
  it('returns Russian by default', () => {
    expect(translate('ru', 'nav.docs')).toBe('Документация')
  })

  it('returns English when requested', () => {
    expect(translate('en', 'nav.docs')).toBe('Documentation')
  })

  it('falls back to key when missing', () => {
    expect(translate('en', 'missing.key')).toBe('missing.key')
  })

  it('interpolates params', () => {
    expect(translate('en', 'feedback.categories.fieldsCount', { prefix: 'PR', channel: 'general', count: 3 })).toContain('3')
  })

  it('includes community keys', () => {
    expect(translate('ru', 'events.title')).toBe('События и голосования')
    expect(translate('en', 'events.title')).toBe('Events & polls')
  })

  it('resolves community keys', () => {
    expect(translate('ru', 'mafia.gameMeta', { phase: 'Ночь', round: 2, alive: 6, total: 8 })).toContain('раунд 2')
  })
})
