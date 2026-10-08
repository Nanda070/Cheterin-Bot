import { describe, expect, it } from 'vitest'
import { normalizeEmbedSpec } from './embedUtils'
import { applyPlaceholders, findPlaceholders } from './placeholders'

describe('findPlaceholders', () => {
  it('finds placeholders across fields in first-seen order', () => {
    const embed = normalizeEmbedSpec({
      description: '[{DateNow}](https://time100.ru/) [подключиться]({Channel})',
      fields: [
        { name: 'Ведущий', value: '{Eventer}' },
        { name: 'x', value: '{DateNow}' },
      ],
    })
    expect(findPlaceholders('<@&742> <:1Primogem:772> {Channel}', [embed])).toEqual(['Channel', 'DateNow', 'Eventer'])
  })

  it('looks at every text field of every embed', () => {
    const first = normalizeEmbedSpec({
      title: '{a}',
      url: 'https://x/{b}',
      author: { name: '{c}', url: '{d}', icon_url: '{e}' },
      footer: { text: '{f}', icon_url: '{g}' },
      image: { url: '{h}' },
      thumbnail: { url: '{i}' },
      fields: [{ name: '{j}', value: '{k}' }],
    })
    const second = normalizeEmbedSpec({ description: '{l}' })
    expect(findPlaceholders('', [first, second])).toEqual(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l'])
  })

  it('ignores braces that are not identifiers', () => {
    expect(findPlaceholders('{} {1a} { x } {a-b} {ok_1} {"json": 1}', [])).toEqual(['ok_1'])
  })
})

describe('applyPlaceholders', () => {
  it('applies values in one pass, keeps unfilled names and does not mutate input', () => {
    const embed = normalizeEmbedSpec({ title: '{A} {B} {C}', fields: [{ name: '{A}', value: '{B}' }] })
    const out = applyPlaceholders('{A}', [embed], { A: '{B}', B: 'b', C: '' })
    expect(out.content).toBe('{B}')
    expect(out.embeds[0].title).toBe('{B} b {C}')
    expect(out.embeds[0].fields[0]).toEqual({ name: '{B}', value: 'b', inline: false })
    expect(embed.title).toBe('{A} {B} {C}')
    expect(embed.fields[0].name).toBe('{A}')
  })

  it('substitutes inside urls and leaves unknown names alone', () => {
    const embed = normalizeEmbedSpec({ description: '[go]({Channel}) {Unknown}', image: { url: '{Img}' } })
    const out = applyPlaceholders('', [embed], { Channel: 'https://discord.gg/x', Img: 'https://i/1.png' })
    expect(out.embeds[0].description).toBe('[go](https://discord.gg/x) {Unknown}')
    expect(out.embeds[0].image.url).toBe('https://i/1.png')
  })

  it('treats replacement text literally', () => {
    expect(applyPlaceholders('{A}', [], { A: '$& $1 $$' }).content).toBe('$& $1 $$')
  })

  it('keeps the timestamp and colour untouched', () => {
    const embed = normalizeEmbedSpec({ title: 'T', color: '#2f3136', timestamp: '2026-01-02T03:04:05.000Z' })
    const [out] = applyPlaceholders('', [embed], { T: 'x' }).embeds
    expect(out.color).toBe('#2f3136')
    expect(out.timestamp).toBe('2026-01-02T03:04:05.000Z')
  })
})
