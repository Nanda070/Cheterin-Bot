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

  it('includes whatsNew keys', () => {
    expect(translate('ru', 'whatsNew.title')).toBe('Что нового')
    expect(translate('en', 'whatsNew.title')).toBe("What's new")
  })

  it('includes credits keys', () => {
    expect(translate('ru', 'credits.title')).toBe('Авторы')
    expect(translate('en', 'credits.title')).toBe('Credits')
    expect(translate('ru', 'nav.credits')).toBe('Авторы')
    expect(translate('en', 'nav.credits')).toBe('Credits')
    expect(translate('ru', 'credits.eyebrow')).toBe('Cheterin Group')
    expect(translate('en', 'credits.eyebrow')).toBe('Cheterin Group')
  })

  it('includes channel dead badge keys', () => {
    expect(translate('ru', 'common.channelDead')).toBe('мёртв')
    expect(translate('en', 'common.channelDead')).toBe('dead')
  })
})
