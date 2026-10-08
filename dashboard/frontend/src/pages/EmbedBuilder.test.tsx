import { fireEvent, screen, waitFor } from '@testing-library/react'
import { renderWithLanguage } from '../test/renderWithLanguage'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import * as client from '../api/client'
import { EmbedBuilderPage } from './EmbedBuilder'

describe('EmbedBuilderPage', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  beforeEach(() => {
    vi.spyOn(client, 'fetchEmbedTemplates').mockResolvedValue({ templates: [], components_version: 'v1' })
  })

  it('creates a new embed message', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([{ id: '7', name: 'VIP', color: '#5865f2', position: 5 }])
    const createSpy = vi
      .spyOn(client, 'createEmbedMessage')
      .mockResolvedValue({ message_id: '999', channel_id: '500' })

    renderWithLanguage(<EmbedBuilderPage />)

    await waitFor(() => screen.getByLabelText('Канал'))
    fireEvent.click(screen.getByLabelText('Канал'))
    fireEvent.click(await screen.findByRole('option', { name: 'general' }))
    fireEvent.change(screen.getByLabelText(/^Заголовок/), { target: { value: 'Hello' } })
    fireEvent.click(screen.getByText('Отправить'))

    await waitFor(() =>
      expect(createSpy).toHaveBeenCalledWith(
        '500',
        expect.objectContaining({
          embeds: [expect.objectContaining({ title: 'Hello' })],
          components_version: 'v1',
        }),
      ),
    )
    expect(await screen.findByText(/999/)).toBeInTheDocument()
  })

  it('rejects an empty embed before calling the API', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    const createSpy = vi.spyOn(client, 'createEmbedMessage')

    renderWithLanguage(<EmbedBuilderPage />)

    await waitFor(() => screen.getByLabelText('Канал'))
    fireEvent.click(screen.getByLabelText('Канал'))
    fireEvent.click(await screen.findByRole('option', { name: 'general' }))
    fireEvent.click(screen.getByText('Отправить'))

    expect(await screen.findByText(/Заполните хотя бы/)).toBeInTheDocument()
    expect(createSpy).not.toHaveBeenCalled()
  })

  it('adds and removes a field', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    renderWithLanguage(<EmbedBuilderPage />)

    fireEvent.click(await screen.findByText(/\+ Добавить поле/))
    expect(screen.getByPlaceholderText('Название поля')).toBeInTheDocument()

    fireEvent.click(screen.getByText('×'))
    expect(screen.queryByPlaceholderText('Название поля')).not.toBeInTheDocument()
  })

  it('loads an existing message (legacy single-embed response) and prefills the form', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    vi.spyOn(client, 'fetchEmbedMessage').mockResolvedValue({
      content: 'existing content',
      embed: {
        title: 'Existing title',
        description: '',
        url: '',
        color: '#D44556',
        author: { name: '', url: '', icon_url: '' },
        footer: { text: '', icon_url: '' },
        image: { url: '' },
        thumbnail: { url: '' },
        timestamp: null,
        fields: [],
      },
      role_ids: [],
    } as unknown as client.EmbedMessagePayload)

    renderWithLanguage(<EmbedBuilderPage />)

    fireEvent.click(await screen.findByText('Редактировать существующее'))
    fireEvent.click(screen.getByLabelText('Канал'))
    fireEvent.click(await screen.findByRole('option', { name: 'general' }))
    fireEvent.change(screen.getByPlaceholderText('ID существующего сообщения'), { target: { value: '999' } })
    fireEvent.click(screen.getByText('Загрузить'))

    await waitFor(() => expect(screen.getByLabelText(/^Заголовок/)).toHaveValue('Existing title'))
    expect(screen.getByLabelText('Текст сообщения')).toHaveValue('existing content')
  })

  it('loads a partial API embed without crashing on missing author/fields', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    vi.spyOn(client, 'fetchEmbedMessage').mockResolvedValue({
      content: 'partial',
      embed: { title: 'Partial title' },
      role_ids: [],
    } as unknown as client.EmbedMessagePayload)

    renderWithLanguage(<EmbedBuilderPage />)

    fireEvent.click(await screen.findByText('Редактировать существующее'))
    fireEvent.click(screen.getByLabelText('Канал'))
    fireEvent.click(await screen.findByRole('option', { name: 'general' }))
    fireEvent.change(screen.getByPlaceholderText('ID существующего сообщения'), { target: { value: '999' } })
    fireEvent.click(screen.getByText('Загрузить'))

    await waitFor(() => expect(screen.getByLabelText(/^Заголовок/)).toHaveValue('Partial title'))
    expect(screen.getByLabelText('Текст сообщения')).toHaveValue('partial')
    expect(screen.getByLabelText(/^Автор/)).toHaveValue('')
    expect(screen.getByPlaceholderText('Имя автора')).toBeInTheDocument()
  })

  it('loads a V2 payload into the form and shows a mapping notice', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    vi.spyOn(client, 'fetchEmbedMessage').mockResolvedValue({
      content: 'v2 text',
      embed: {
        title: 'V2 Title',
        description: 'mapped',
        url: '',
        color: '',
        author: { name: '', url: '', icon_url: '' },
        footer: { text: '', icon_url: '' },
        image: { url: '' },
        thumbnail: { url: '' },
        timestamp: null,
        fields: [],
      },
      role_ids: [],
      components_version: 'v2',
    } as unknown as client.EmbedMessagePayload)

    renderWithLanguage(<EmbedBuilderPage />)

    fireEvent.click(await screen.findByText('Редактировать существующее'))
    fireEvent.click(screen.getByLabelText('Канал'))
    fireEvent.click(await screen.findByRole('option', { name: 'general' }))
    fireEvent.change(screen.getByPlaceholderText('ID существующего сообщения'), { target: { value: '999' } })
    fireEvent.click(screen.getByText('Загрузить'))

    await waitFor(() => expect(screen.getByLabelText(/^Заголовок/)).toHaveValue('V2 Title'))
    expect(screen.getByLabelText('Текст сообщения')).toHaveValue('v2 text')
    expect(screen.getByText(/без классического эмбеда/)).toBeInTheDocument()
  })

  it('renders the live preview with the current title', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])

    renderWithLanguage(<EmbedBuilderPage />)

    fireEvent.change(await screen.findByLabelText(/^Заголовок/), { target: { value: 'Preview Title' } })
    await waitFor(() => expect(screen.getByText('Preview Title')).toBeInTheDocument())
  })

  it('rejects a spec that exceeds the aggregate 6000-character budget', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    const createSpy = vi.spyOn(client, 'createEmbedMessage')

    renderWithLanguage(<EmbedBuilderPage />)

    await waitFor(() => screen.getByLabelText('Канал'))
    fireEvent.click(screen.getByLabelText('Канал'))
    fireEvent.click(await screen.findByRole('option', { name: 'general' }))
    fireEvent.change(screen.getByLabelText(/^Описание/), { target: { value: 'x'.repeat(4096) } })
    fireEvent.change(screen.getByLabelText(/^Подвал/), { target: { value: 'y'.repeat(1905) } })
    fireEvent.click(screen.getByText('Отправить'))

    expect(await screen.findByText(/Суммарная длина/)).toBeInTheDocument()
    expect(createSpy).not.toHaveBeenCalled()
  })

  it('allows saving content-only messages without any embed field', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    const createSpy = vi
      .spyOn(client, 'createEmbedMessage')
      .mockResolvedValue({ message_id: '999', channel_id: '500' })

    renderWithLanguage(<EmbedBuilderPage />)

    await waitFor(() => screen.getByLabelText('Канал'))
    fireEvent.click(screen.getByLabelText('Канал'))
    fireEvent.click(await screen.findByRole('option', { name: 'general' }))
    fireEvent.change(screen.getByLabelText('Текст сообщения'), { target: { value: 'Just text' } })
    fireEvent.click(screen.getByText('Отправить'))

    await waitFor(() =>
      expect(createSpy).toHaveBeenCalledWith('500', expect.objectContaining({ content: 'Just text' })),
    )
  })

  it('rejects blank content and a blank embed together', async () => {
    vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
    vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    const createSpy = vi.spyOn(client, 'createEmbedMessage')

    renderWithLanguage(<EmbedBuilderPage />)

    await waitFor(() => screen.getByLabelText('Канал'))
    fireEvent.click(screen.getByLabelText('Канал'))
    fireEvent.click(await screen.findByRole('option', { name: 'general' }))
    fireEvent.change(screen.getByLabelText('Текст сообщения'), { target: { value: '   ' } })
    fireEvent.click(screen.getByText('Отправить'))

    expect(await screen.findByText(/Заполните хотя бы/)).toBeInTheDocument()
    expect(createSpy).not.toHaveBeenCalled()
  })

  describe('JSON import', () => {
    const LIBRARY = [
      {
        category: 'oneball',
        score: 1,
        event: 'Brawlhalla',
        embed: {
          plainText: '<@&742676959183765544>',
          author: { name: 'Brawlhalla' },
          description: '> Файтинг\n> Время: **[{DateNow}](https://time100.ru/)**\n> Канал: **[подключиться]({Channel})**',
          color: 3092790,
          fields: [{ name: 'Ведущий', value: '{Eventer}', inline: true }],
        },
      },
      {
        category: 'twoballs',
        score: 2,
        event: 'Шляпа',
        embed: { plainText: '<@&742676959183765544>', description: '> Alias', author: { name: 'Шляпа' } },
      },
    ]

    const pasteJson = async (value: unknown) => {
      fireEvent.change(await screen.findByLabelText('JSON'), {
        target: { value: typeof value === 'string' ? value : JSON.stringify(value) },
      })
      fireEvent.click(screen.getByText('Применить JSON'))
    }

    const pickChannel = async () => {
      fireEvent.click(screen.getByLabelText('Канал'))
      fireEvent.click(await screen.findByRole('option', { name: 'general' }))
    }

    beforeEach(() => {
      vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
      vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    })

    it('fills the form from a Discohook message with two embeds and sends both', async () => {
      const createSpy = vi
        .spyOn(client, 'createEmbedMessage')
        .mockResolvedValue({ message_id: '999', channel_id: '500' })
      renderWithLanguage(<EmbedBuilderPage />)

      await pasteJson({ content: 'hello', embeds: [{ title: 'First', color: 5814783 }, { title: 'Second' }] })

      expect(screen.getByLabelText('Текст сообщения')).toHaveValue('hello')
      expect(screen.getByLabelText(/^Заголовок/)).toHaveValue('First')
      expect(screen.getByRole('button', { name: 'Эмбед 2' })).toBeInTheDocument()
      // Both embeds are in the preview at once.
      expect(screen.getByText('First')).toBeInTheDocument()
      expect(screen.getByText('Second')).toBeInTheDocument()

      fireEvent.click(screen.getByRole('button', { name: 'Эмбед 2' }))
      expect(screen.getByLabelText(/^Заголовок/)).toHaveValue('Second')

      await pickChannel()
      fireEvent.click(screen.getByText('Отправить'))
      await waitFor(() =>
        expect(createSpy).toHaveBeenCalledWith(
          '500',
          expect.objectContaining({
            content: 'hello',
            embeds: [
              expect.objectContaining({ title: 'First', color: '#58b9ff' }),
              expect.objectContaining({ title: 'Second' }),
            ],
          }),
        ),
      )
    })

    it('lists a message library, loads the picked entry and substitutes placeholders on send', async () => {
      const createSpy = vi
        .spyOn(client, 'createEmbedMessage')
        .mockResolvedValue({ message_id: '999', channel_id: '500' })
      renderWithLanguage(<EmbedBuilderPage />)

      await pasteJson(LIBRARY)
      expect(screen.getByText('Сообщений в JSON: 2')).toBeInTheDocument()
      // Nothing is loaded until an entry is picked.
      expect(screen.getByLabelText('Текст сообщения')).toHaveValue('')

      fireEvent.change(screen.getByPlaceholderText('Поиск по названию'), { target: { value: 'brawl' } })
      expect(screen.queryByRole('button', { name: /Шляпа/ })).not.toBeInTheDocument()
      fireEvent.click(screen.getByRole('button', { name: /Brawlhalla/ }))

      expect(screen.getByLabelText('Текст сообщения')).toHaveValue('<@&742676959183765544>')
      expect(screen.getByLabelText(/^Автор/)).toHaveValue('Brawlhalla')
      expect(screen.getByText('Не заполнено: {DateNow}, {Channel}, {Eventer}')).toBeInTheDocument()

      fireEvent.change(screen.getByLabelText('{Eventer}'), { target: { value: '<@1>' } })
      fireEvent.change(screen.getByLabelText('{Channel}'), { target: { value: 'https://discord.gg/x' } })
      expect(screen.getByText('Не заполнено: {DateNow}')).toBeInTheDocument()
      // The preview shows the substituted value; the form keeps the raw placeholder.
      expect(screen.getByText('<@1>')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Значение поля')).toHaveValue('{Eventer}')

      await pickChannel()
      fireEvent.click(screen.getByText('Отправить'))
      await waitFor(() => expect(createSpy).toHaveBeenCalled())
      const payload = createSpy.mock.calls[0][1]
      expect(payload.embeds).toHaveLength(1)
      expect(payload.embeds[0].fields).toEqual([{ name: 'Ведущий', value: '<@1>', inline: true }])
      expect(payload.embeds[0].description).toContain('[подключиться](https://discord.gg/x)')
      expect(payload.embeds[0].description).toContain('{DateNow}')
      expect(payload.embeds[0].color).toBe('#2f3136')
    })

    it('saves the whole library as templates with raw placeholders', async () => {
      const bulkSpy = vi.spyOn(client, 'saveEmbedTemplatesBulk').mockResolvedValue({
        created: [{ id: '1', name: 'Brawlhalla', content: '', embeds: [], role_ids: [] }],
        skipped: [{ name: 'Шляпа', reason: 'duplicate_name' }],
      })
      renderWithLanguage(<EmbedBuilderPage />)

      await pasteJson(LIBRARY)
      fireEvent.click(screen.getByText('Сохранить все как шаблоны (2)'))

      expect(await screen.findByText('Шаблоны: создано 1, пропущено 1')).toBeInTheDocument()
      const [templates] = bulkSpy.mock.calls[0]
      expect(templates.map((template) => template.name)).toEqual(['Brawlhalla', 'Шляпа'])
      expect(templates[0].content).toBe('<@&742676959183765544>')
      expect(templates[0].embeds[0].fields[0].value).toBe('{Eventer}')
    })

    it('returns to the first embed when a shorter message replaces the current one', async () => {
      renderWithLanguage(<EmbedBuilderPage />)

      await pasteJson({ embeds: [{ title: 'One' }, { title: 'Two' }, { title: 'Three' }] })
      fireEvent.click(screen.getByRole('button', { name: 'Эмбед 3' }))
      expect(screen.getByLabelText(/^Заголовок/)).toHaveValue('Three')

      await pasteJson({ embeds: [{ title: 'Solo' }] })
      expect(screen.getByLabelText(/^Заголовок/)).toHaveValue('Solo')
      expect(screen.queryByRole('button', { name: 'Эмбед 2' })).not.toBeInTheDocument()
    })

    it('reports invalid JSON and leaves the form untouched', async () => {
      renderWithLanguage(<EmbedBuilderPage />)

      fireEvent.change(await screen.findByLabelText(/^Заголовок/), { target: { value: 'Keep me' } })
      await pasteJson('{oops')

      expect(screen.getByText(/^Некорректный JSON:/)).toBeInTheDocument()
      expect(screen.getByLabelText(/^Заголовок/)).toHaveValue('Keep me')
    })

    it('warns about webhook-only keys it cannot use', async () => {
      renderWithLanguage(<EmbedBuilderPage />)

      await pasteJson({ content: 'x', username: 'Hook', avatar_url: 'https://a/b.png' })
      expect(screen.getByText('Не поддерживается и пропущено: username, avatar_url')).toBeInTheDocument()
    })

    it('exports the current message as Discohook JSON', async () => {
      renderWithLanguage(<EmbedBuilderPage />)

      fireEvent.change(await screen.findByLabelText('Текст сообщения'), { target: { value: 'hi' } })
      fireEvent.change(screen.getByLabelText(/^Заголовок/), { target: { value: 'T' } })
      fireEvent.change(screen.getByPlaceholderText('#D44556'), { target: { value: '#2f3136' } })
      fireEvent.click(screen.getByText('Скопировать JSON'))

      const exported = JSON.parse((screen.getByLabelText('JSON') as HTMLTextAreaElement).value)
      expect(exported).toEqual({ content: 'hi', embeds: [{ title: 'T', color: 3092790 }], attachments: [] })
    })
  })

  describe('multiple embeds', () => {
    beforeEach(() => {
      vi.spyOn(client, 'fetchChannels').mockResolvedValue([{ id: '500', name: 'general' }])
      vi.spyOn(client, 'fetchRoles').mockResolvedValue([])
    })

    it('adds a second embed, skips blank slots on send and removes embeds', async () => {
      const createSpy = vi
        .spyOn(client, 'createEmbedMessage')
        .mockResolvedValue({ message_id: '999', channel_id: '500' })
      renderWithLanguage(<EmbedBuilderPage />)

      fireEvent.change(await screen.findByLabelText(/^Заголовок/), { target: { value: 'A' } })
      expect(screen.getByText('Удалить эмбед')).toBeDisabled()
      fireEvent.click(screen.getByText('+ Добавить эмбед'))
      // The new blank embed becomes active.
      expect(screen.getByLabelText(/^Заголовок/)).toHaveValue('')
      fireEvent.click(screen.getByText('+ Добавить эмбед'))
      fireEvent.change(screen.getByLabelText(/^Заголовок/), { target: { value: 'C' } })

      fireEvent.click(screen.getByLabelText('Канал'))
      fireEvent.click(await screen.findByRole('option', { name: 'general' }))
      fireEvent.click(screen.getByText('Отправить'))
      await waitFor(() => expect(createSpy).toHaveBeenCalled())
      expect(createSpy.mock.calls[0][1].embeds.map((embed) => embed.title)).toEqual(['A', 'C'])

      fireEvent.click(screen.getByText('Удалить эмбед'))
      expect(screen.queryByRole('button', { name: 'Эмбед 3' })).not.toBeInTheDocument()
      expect(screen.getByLabelText(/^Заголовок/)).toHaveValue('')
    })

    it('loads every embed of an existing message', async () => {
      vi.spyOn(client, 'fetchEmbedMessage').mockResolvedValue({
        content: 'c',
        embeds: [{ title: 'E1' }, { title: 'E2' }],
        role_ids: [],
      } as unknown as client.EmbedMessagePayload)
      renderWithLanguage(<EmbedBuilderPage />)

      fireEvent.click(await screen.findByText('Редактировать существующее'))
      fireEvent.click(screen.getByLabelText('Канал'))
      fireEvent.click(await screen.findByRole('option', { name: 'general' }))
      fireEvent.change(screen.getByPlaceholderText('ID существующего сообщения'), { target: { value: '999' } })
      fireEvent.click(screen.getByText('Загрузить'))

      await waitFor(() => expect(screen.getByLabelText(/^Заголовок/)).toHaveValue('E1'))
      fireEvent.click(screen.getByRole('button', { name: 'Эмбед 2' }))
      expect(screen.getByLabelText(/^Заголовок/)).toHaveValue('E2')
    })
  })
})
