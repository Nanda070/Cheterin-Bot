import type { EmbedSpec } from '../api/client'
import type { Lang } from '../i18n/types'
import { EMPTY_EMBED_SPEC } from '../components/EmbedEditor'

/** Server 404 default thumbnail used in the classic welcome DM. */
export const DEFAULT_DM_THUMBNAIL_URL = 'https://i.imgur.com/4ydti00.png'

const RU_FOOTER = 'Для помощи — обращайся к Администрации. По вопросам ботов — пиши Nandak070.'
const EN_FOOTER = 'For help — contact the Administration. For bot questions — message Nandak070.'

/** Classic Server 404 welcome DM as an embed constructor default. */
export function buildDefaultDmEmbed(lang: Lang = 'ru'): EmbedSpec {
  if (lang === 'en') {
    return {
      ...EMPTY_EMBED_SPEC,
      title: 'Welcome to {guild_name}',
      description: 'Glad to have you here! Below is a quick guide to key resources:',
      color: '#1a4a8a',
      footer: { text: EN_FOOTER, icon_url: '' },
      thumbnail: { url: DEFAULT_DM_THUMBNAIL_URL },
      timestamp: new Date().toISOString(),
      fields: [
        {
          name: '〘❗〙 Announcements',
          value: '{announcements_channel} — important news and updates',
          inline: false,
        },
        {
          name: '〘📜〙 Rules',
          value: '{rules_channel} — read before chatting',
          inline: false,
        },
        {
          name: '〘❗〙 Roles',
          value: '{roles_channel} — get access to perks',
          inline: false,
        },
        {
          name: '〘🔎〙 Find players',
          value: '{search_channel} — find teammates for your goals',
          inline: false,
        },
        {
          name: '📈 Level system',
          value:
            'Stay active in voice channels to earn XP — your role and name color grow with you.',
          inline: false,
        },
        {
          name: '💡 Getting started',
          value:
            '1. Introduce yourself in chat.\n2. Check the Rules section and react with ✔️.\n3. Pick roles that interest you.\n4. Ask questions — we\'re friendly here :)',
          inline: false,
        },
      ],
    }
  }

  return {
    ...EMPTY_EMBED_SPEC,
    title: 'Добро пожаловать на {guild_name}',
    description: 'Рады видеть тебя в нашем пространстве! Ниже — краткое руководство по ключевым ресурсам:',
    color: '#1a4a8a',
    footer: { text: RU_FOOTER, icon_url: '' },
    thumbnail: { url: DEFAULT_DM_THUMBNAIL_URL },
    timestamp: new Date().toISOString(),
    fields: [
      {
        name: '〘❗〙 Объявления',
        value: '{announcements_channel} — все важные новости и анонсы',
        inline: false,
      },
      {
        name: '〘📜〙 Правила',
        value: '{rules_channel} — ознакомься перед общением',
        inline: false,
      },
      {
        name: '〘❗〙 Роли',
        value: '{roles_channel} — получи доступ к привилегиям',
        inline: false,
      },
      {
        name: '〘🔎〙 Поиск игроков',
        value: '{search_channel} — найдёшь тиммейтов под свои задачи',
        inline: false,
      },
      {
        name: '📈 Система уровней',
        value:
          'Наращивай активность в голосовых чатах и зарабатывай опыт — твоя роль и цвет ника будут расти вместе с тобой.',
        inline: false,
      },
      {
        name: '💡 Советы по вливанию',
        value:
          '1. Представься в чате.\n2. Загляни в раздел «Правила» и ставь реакцию ✔️.\n3. Выбери роли, которые тебе интересны.\n4. Не стесняйся задавать вопросы — мы тут все на «ты» :)',
        inline: false,
      },
    ],
  }
}

export function embedHasContent(embed: EmbedSpec | null | undefined): boolean {
  if (!embed) return false
  if (embed.title || embed.description) return true
  if (embed.image?.url || embed.thumbnail?.url) return true
  return (embed.fields?.length ?? 0) > 0
}
