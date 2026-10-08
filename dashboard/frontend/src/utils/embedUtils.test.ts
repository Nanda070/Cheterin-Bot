import { describe, expect, it } from 'vitest'
import { EMPTY_EMBED_SPEC, embedsFromPayload, normalizeEmbedSpec, validateEmbedSpec, validateEmbedSpecs } from './embedUtils'

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

describe('validateEmbedSpecs', () => {
  const one = normalizeEmbedSpec({ title: 'T' })

  it('validates the list as a whole', () => {
    expect(validateEmbedSpecs(Array(10).fill(one), '')).toBeNull()
    expect(validateEmbedSpecs(Array(11).fill(one), '')).toBe('embedBuilder.error.validation.embedsCount')
    const big = normalizeEmbedSpec({ description: 'x'.repeat(3001) })
    expect(validateEmbedSpecs([big], '')).toBeNull()
    expect(validateEmbedSpecs([big, big], '')).toBe('embedBuilder.error.validation.totalLength')
  })

  it('ignores empty slots and still requires something to send', () => {
    expect(validateEmbedSpecs([EMPTY_EMBED_SPEC], '')).toBe('embedBuilder.error.validation.empty')
    expect(validateEmbedSpecs([], '  ')).toBe('embedBuilder.error.validation.empty')
    expect(validateEmbedSpecs([EMPTY_EMBED_SPEC], 'hi')).toBeNull()
    expect(validateEmbedSpecs([...Array(10).fill(one), EMPTY_EMBED_SPEC], '')).toBeNull()
  })

  it('reports per-embed limits from any embed', () => {
    const longTitle = normalizeEmbedSpec({ title: 'x'.repeat(257) })
    expect(validateEmbedSpecs([one, longTitle], '')).toBe('embedBuilder.error.validation.title')
  })
})

describe('embedsFromPayload', () => {
  it('reads embeds or the legacy embed and never returns an empty list', () => {
    expect(embedsFromPayload({ embeds: [{ title: 'A' }, { title: 'B' }] }).map((e) => e.title)).toEqual(['A', 'B'])
    expect(embedsFromPayload({ embed: { title: 'L' } })[0].title).toBe('L')
    expect(embedsFromPayload({ embeds: [] })).toHaveLength(1)
    expect(embedsFromPayload({ embeds: [], embed: { title: 'L' } })[0].title).toBe('L')
    expect(embedsFromPayload({})).toHaveLength(1)
    expect(embedsFromPayload({ embeds: 'nope' })).toHaveLength(1)
  })

  it('fills nested keys of every embed', () => {
    const [first] = embedsFromPayload({ embeds: [{ title: 'A' }] })
    expect(first.author).toEqual({ name: '', url: '', icon_url: '' })
    expect(first.fields).toEqual([])
  })
})
