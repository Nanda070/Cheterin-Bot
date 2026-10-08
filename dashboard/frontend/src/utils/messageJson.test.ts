import { describe, expect, it } from 'vitest'
import { normalizeEmbedSpec } from './embedUtils'
import { exportMessageJson, parseMessageJson, type ImportedMessage, type JsonNotice } from './messageJson'

function parsed(input: unknown): { messages: ImportedMessage[]; warnings: JsonNotice[] } {
  const result = parseMessageJson(typeof input === 'string' ? input : JSON.stringify(input))
  if (!result.ok) throw new Error(`expected ok, got ${result.error.key}`)
  return result
}

function errorKey(text: string): string {
  const result = parseMessageJson(text)
  if (result.ok) throw new Error('expected an error')
  return result.error.key
}

const WRAPPER = {
  category: 'oneball',
  score: 1,
  event: 'Brawlhalla',
  embed: {
    plainText: '<@&742676959183765544>',
    author: { name: 'Brawlhalla' },
    description: '> Файтинг\n> Время: **[{DateNow}](https://time100.ru/)**',
    color: 3092790,
    image: { url: 'https://media.discordapp.net/a.png' },
    footer: { text: 'Ивент модерируется на усмотрение ведущего.' },
    fields: [
      { name: 'Ведущий', value: '{Eventer}', inline: true },
      { name: '1 место', value: '200 <:1Primogem:772748673616576522>', inline: true },
    ],
  },
}

describe('parseMessageJson — shapes', () => {
  it('reads a Discohook message with several embeds', () => {
    const { messages, warnings } = parsed({ content: 'hi', embeds: [{ title: 'A', color: 5814783 }, { title: 'B' }] })
    expect(messages).toHaveLength(1)
    expect(messages[0].content).toBe('hi')
    expect(messages[0].embeds.map((e) => e.title)).toEqual(['A', 'B'])
    expect(messages[0].embeds.map((e) => e.color)).toEqual(['#58b9ff', ''])
    expect(warnings).toEqual([])
  })

  it('reads a Discohook backup with several messages', () => {
    const { messages } = parsed({ messages: [{ data: { content: 'a' } }, { data: { embeds: [{ title: 'T' }] } }] })
    expect(messages.map((m) => m.content)).toEqual(['a', ''])
    expect(messages[1].embeds[0].title).toBe('T')
  })

  it('reads a wrapped library entry without warnings', () => {
    const { messages, warnings } = parsed(WRAPPER)
    expect(warnings).toEqual([])
    const [message] = messages
    expect(message.name).toBe('Brawlhalla')
    expect(message.group).toBe('oneball')
    expect(message.content).toBe('<@&742676959183765544>')
    expect(message.embeds).toHaveLength(1)
    const [embed] = message.embeds
    expect(embed.color).toBe('#2f3136')
    expect(embed.author.name).toBe('Brawlhalla')
    expect(embed.image.url).toBe('https://media.discordapp.net/a.png')
    expect(embed.footer.text).toBe('Ивент модерируется на усмотрение ведущего.')
    expect(embed.fields).toEqual([
      { name: 'Ведущий', value: '{Eventer}', inline: true },
      { name: '1 место', value: '200 <:1Primogem:772748673616576522>', inline: true },
    ])
  })

  it('reads an array of wrapped entries as separate messages', () => {
    const second = { ...WRAPPER, event: 'Пазлы', category: 'twoballs' }
    const { messages } = parsed([WRAPPER, second])
    expect(messages.map((m) => [m.name, m.group])).toEqual([
      ['Brawlhalla', 'oneball'],
      ['Пазлы', 'twoballs'],
    ])
  })

  it('treats a short array of bare embeds as one message', () => {
    const { messages } = parsed([{ title: 'A' }, { title: 'B' }, { description: 'C' }])
    expect(messages).toHaveLength(1)
    expect(messages[0].embeds).toHaveLength(3)
  })

  it('treats more than 10 bare embeds as separate messages', () => {
    const { messages } = parsed(Array.from({ length: 11 }, (_, i) => ({ title: `E${i}` })))
    expect(messages).toHaveLength(11)
    expect(messages[10].embeds[0].title).toBe('E10')
    expect(messages[10].name).toBe('E10')
  })

  it('treats bare embeds carrying plainText as separate messages', () => {
    const { messages } = parsed([
      { title: 'A', plainText: 'one' },
      { title: 'B', plainText: 'two' },
    ])
    expect(messages.map((m) => m.content)).toEqual(['one', 'two'])
  })

  it('reads a single bare embed', () => {
    const { messages } = parsed({ description: 'just this', plainText: 'ping' })
    expect(messages[0].content).toBe('ping')
    expect(messages[0].embeds[0].description).toBe('just this')
  })

  it('names messages from event, name, title, embed title, author — in that order', () => {
    expect(parsed({ name: 'N', embed: { title: 'T' } }).messages[0].name).toBe('N')
    expect(parsed({ title: 'W', embed: { description: 'd' } }).messages[0].name).toBe('W')
    expect(parsed({ embeds: [{ title: 'ET', author: { name: 'AU' } }] }).messages[0].name).toBe('ET')
    expect(parsed({ embeds: [{ description: 'd', author: { name: 'AU' } }] }).messages[0].name).toBe('AU')
    expect(parsed({ content: 'only text' }).messages[0].name).toBe('')
  })
})

describe('parseMessageJson — warnings', () => {
  it('drops embeds past the tenth and warns', () => {
    const { messages, warnings } = parsed({ embeds: Array.from({ length: 12 }, (_, i) => ({ title: `E${i}` })) })
    expect(messages[0].embeds).toHaveLength(10)
    expect(warnings.map((w) => w.key)).toEqual(['embedBuilder.json.warn.tooManyEmbeds'])
  })

  it('lists ignored message keys once', () => {
    const { warnings } = parsed({
      messages: [
        { data: { content: 'x', username: 'u', avatar_url: 'a', components: [{}], attachments: [] } },
        { data: { content: 'y', username: 'u2', thread_name: 't' } },
      ],
    })
    expect(warnings).toEqual([
      { key: 'embedBuilder.json.warn.ignoredKeys', params: { keys: 'username, avatar_url, components, thread_name' } },
    ])
  })

  it('skips unrecognised array items and counts them', () => {
    const { messages, warnings } = parsed([WRAPPER, { foo: 1 }, 42, null])
    expect(messages).toHaveLength(1)
    expect(warnings).toEqual([{ key: 'embedBuilder.json.warn.skippedItems', params: { count: 3 } }])
  })
})

describe('parseMessageJson — tolerant input', () => {
  it('strips a markdown code fence and a BOM', () => {
    expect(parsed('```json\n{"content":"hi"}\n```').messages[0].content).toBe('hi')
    expect(parsed('```\n{"content":"hi"}\n```').messages[0].content).toBe('hi')
    expect(parsed('﻿{"content":"hi"}').messages[0].content).toBe('hi')
  })

  it('skips non-object entries in embeds', () => {
    const { messages } = parsed({ embeds: [null, 'x', 7, { title: 'A' }] })
    expect(messages[0].embeds.map((e) => e.title)).toEqual(['A'])
  })

  it('coerces scalar field values and only accepts a boolean inline', () => {
    const { messages } = parsed({ embeds: [{ title: 5, fields: [{ name: 1, value: 100, inline: 'true' }, 'junk'] }] })
    expect(messages[0].embeds[0].title).toBe('5')
    expect(messages[0].embeds[0].fields).toEqual([{ name: '1', value: '100', inline: false }])
  })

  it('normalises colours and drops invalid ones', () => {
    const colors = (values: unknown[]) =>
      parsed({ embeds: values.map((color) => ({ title: 'T', color })) }).messages[0].embeds.map((e) => e.color)
    expect(colors([0, 16777215, '2f3136', '#2F3136'])).toEqual(['#000000', '#ffffff', '#2f3136', '#2f3136'])
    expect(colors([-5, 16777216, 1.5, 'red', null])).toEqual(['', '', '', '', ''])
  })

  it('keeps url, icon urls and timestamp', () => {
    const [embed] = parsed({
      embeds: [
        {
          title: 'T',
          url: 'https://a',
          author: { name: 'n', url: 'https://b', icon_url: 'https://c' },
          footer: { text: 'f', icon_url: 'https://d' },
          thumbnail: { url: 'https://e' },
          timestamp: '2026-01-02T03:04:05.000Z',
        },
      ],
    }).messages[0].embeds
    expect(embed.url).toBe('https://a')
    expect(embed.author).toEqual({ name: 'n', url: 'https://b', icon_url: 'https://c' })
    expect(embed.footer).toEqual({ text: 'f', icon_url: 'https://d' })
    expect(embed.thumbnail.url).toBe('https://e')
    expect(embed.timestamp).toBe('2026-01-02T03:04:05.000Z')
  })
})

describe('parseMessageJson — errors', () => {
  it('reports a syntax error with the parser detail', () => {
    const result = parseMessageJson('{oops')
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.key).toBe('embedBuilder.json.error.syntax')
      expect(String(result.error.params?.detail)).not.toBe('')
    }
  })

  it('rejects scalars and empty input', () => {
    expect(errorKey('42')).toBe('embedBuilder.json.error.shape')
    expect(errorKey('"text"')).toBe('embedBuilder.json.error.shape')
    expect(errorKey('null')).toBe('embedBuilder.json.error.shape')
    expect(errorKey('   ')).toBe('embedBuilder.json.error.syntax')
  })

  it('rejects input with no recognisable message', () => {
    expect(errorKey('[{"foo":1}]')).toBe('embedBuilder.json.error.noMessages')
    expect(errorKey('{"foo":1}')).toBe('embedBuilder.json.error.noMessages')
    expect(errorKey('[]')).toBe('embedBuilder.json.error.noMessages')
    expect(errorKey('{"content":"","embeds":[{}]}')).toBe('embedBuilder.json.error.noMessages')
  })
})

describe('exportMessageJson', () => {
  const spec = normalizeEmbedSpec({
    title: 'T',
    color: '#2f3136',
    footer: { text: 'f' },
    fields: [{ name: 'n', value: 'v', inline: true }],
  })

  it('writes Discohook-shaped JSON without empty keys', () => {
    expect(JSON.parse(exportMessageJson('hi', [spec]))).toEqual({
      content: 'hi',
      embeds: [{ title: 'T', color: 3092790, footer: { text: 'f' }, fields: [{ name: 'n', value: 'v', inline: true }] }],
      attachments: [],
    })
  })

  it('uses null for missing content and embeds', () => {
    expect(JSON.parse(exportMessageJson('', [normalizeEmbedSpec({})]))).toEqual({
      content: null,
      embeds: null,
      attachments: [],
    })
  })

  it('round-trips through the parser', () => {
    const second = normalizeEmbedSpec({ description: 'd', color: '', timestamp: '2026-01-02T03:04:05.000Z' })
    const { messages } = parsed(exportMessageJson('hello', [spec, second]))
    expect(messages[0].content).toBe('hello')
    expect(messages[0].embeds).toEqual([spec, second])
  })
})
