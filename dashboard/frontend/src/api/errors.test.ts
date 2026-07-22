import { describe, expect, it } from 'vitest'
import { ApiError } from './client'
import { formatApiError } from './errors'

const t = (key: string) => {
  const map: Record<string, string> = {
    'welcome.errorSave': 'Не удалось сохранить настройки',
    'apiError.field_value_too_long': 'Значение поля эмбеда слишком длинное (макс. 1024 символа)',
    'apiError.empty_embed': 'Эмбед пустой — заполните заголовок, описание или поля',
  }
  return map[key] ?? key
}

describe('formatApiError', () => {
  it('maps known API codes to human text', () => {
    expect(formatApiError(new ApiError(400, 'field_value_too_long'), t, 'welcome.errorSave')).toBe(
      'Значение поля эмбеда слишком длинное (макс. 1024 символа)',
    )
  })

  it('appends unknown codes to the fallback', () => {
    expect(formatApiError(new ApiError(400, 'weird_code'), t, 'welcome.errorSave')).toBe(
      'Не удалось сохранить настройки (weird_code)',
    )
  })

  it('uses fallback for non-ApiError', () => {
    expect(formatApiError(new Error('boom'), t, 'welcome.errorSave')).toBe('Не удалось сохранить настройки')
  })
})
