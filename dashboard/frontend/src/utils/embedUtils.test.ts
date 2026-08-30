import { describe, expect, it } from 'vitest'
import { EMPTY_EMBED_SPEC, normalizeEmbedSpec, validateEmbedSpec } from './embedUtils'

describe('normalizeEmbedSpec', () => {
  it('fills nested author, footer, image and fields when the payload is empty', () => {
    const spec = normalizeEmbedSpec({})
    expect(spec.author).toEqual({ name: '', url: '', icon_url: '' })
    expect(spec.footer).toEqual({ text: '', icon_url: '' })
    expect(spec.image).toEqual({ url: '' })
    expect(spec.thumbnail).toEqual({ url: '' })
    expect(spec.fields).toEqual([])
    expect(spec.color).toBe(EMPTY_EMBED_SPEC.color)
  })

  it('keeps an explicit empty color from the API', () => {
    expect(normalizeEmbedSpec({ title: 'T', color: '' }).color).toBe('')
  })

  it('treats null author/fields as empty instead of throwing', () => {
    const spec = normalizeEmbedSpec({ title: 'T', author: null, footer: null, fields: null })
    expect(spec.title).toBe('T')
    expect(spec.author.name).toBe('')
    expect(spec.footer.text).toBe('')
    expect(spec.fields).toEqual([])
  })
})

describe('validateEmbedSpec', () => {
  it('does not throw on a missing spec', () => {
    expect(validateEmbedSpec(undefined, '')).toBe('embedBuilder.error.validation.empty')
    expect(validateEmbedSpec(undefined, 'hello')).toBeNull()
  })
})
