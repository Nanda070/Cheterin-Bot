import { CalendarBlank, Chats, PushPin, Star } from '@phosphor-icons/react'
import { useSearchParams } from 'react-router-dom'
import { useT } from '../context/LanguageContext'
import { ScheduledMessagesPage } from './ScheduledMessages'
import { StarboardPage } from './Starboard'
import { StickyMessagesPage } from './StickyMessages'

type TopTab = 'messages' | 'starboard'
type MessagesSubTab = 'scheduled' | 'sticky'

function parseTopTab(raw: string | null): TopTab {
  return raw === 'starboard' ? 'starboard' : 'messages'
}

function parseMessagesSubTab(raw: string | null): MessagesSubTab {
  return raw === 'sticky' ? 'sticky' : 'scheduled'
}

function TopTabBar({
  tab,
  setTab,
  t,
}: {
  tab: TopTab
  setTab: (t: TopTab) => void
  t: (key: string) => string
}) {
  const tabs: { key: TopTab; labelKey: string; icon: typeof Chats }[] = [
    { key: 'messages', labelKey: 'messages.tab.messages', icon: Chats },
    { key: 'starboard', labelKey: 'messages.tab.starboard', icon: Star },
  ]
  return (
    <div className="flex flex-wrap gap-1 border-b border-border">
      {tabs.map(({ key, labelKey, icon: Icon }) => (
        <button
          key={key}
          type="button"
          onClick={() => setTab(key)}
          className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-sm transition-colors ${
            tab === key ? 'border-primary text-foreground' : 'border-transparent text-muted hover:text-foreground'
          }`}
        >
          <Icon size={15} weight={key === 'starboard' ? 'fill' : 'regular'} />
          {t(labelKey)}
        </button>
      ))}
    </div>
  )
}

function MessagesSubTabBar({
  tab,
  setTab,
  t,
}: {
  tab: MessagesSubTab
  setTab: (t: MessagesSubTab) => void
  t: (key: string) => string
}) {
  const tabs: { key: MessagesSubTab; labelKey: string; icon: typeof CalendarBlank }[] = [
    { key: 'scheduled', labelKey: 'messages.tab.scheduled', icon: CalendarBlank },
    { key: 'sticky', labelKey: 'messages.tab.sticky', icon: PushPin },
  ]
  return (
    <div className="flex gap-1 border-b border-border">
      {tabs.map(({ key, labelKey, icon: Icon }) => (
        <button
          key={key}
          type="button"
          onClick={() => setTab(key)}
          className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-sm transition-colors ${
            tab === key ? 'border-primary text-foreground' : 'border-transparent text-muted hover:text-foreground'
          }`}
        >
          <Icon size={15} />
          {t(labelKey)}
        </button>
      ))}
    </div>
  )
}

export function MessagesPage() {
  const t = useT()
  const [searchParams, setSearchParams] = useSearchParams()
  const rawTab = searchParams.get('tab')
  const topTab = parseTopTab(rawTab)
  const subTab = parseMessagesSubTab(rawTab)

  const setTopTab = (next: TopTab) => {
    if (next === 'starboard') setSearchParams({ tab: 'starboard' }, { replace: true })
    else setSearchParams({}, { replace: true })
  }

  const setSubTab = (next: MessagesSubTab) => {
    if (next === 'scheduled') setSearchParams({}, { replace: true })
    else setSearchParams({ tab: next }, { replace: true })
  }

  return (
    <div className="flex flex-col gap-4">
      <TopTabBar tab={topTab} setTab={setTopTab} t={t} />
      {topTab === 'starboard' ? (
        <StarboardPage embedded />
      ) : (
        <>
          <MessagesSubTabBar tab={subTab} setTab={setSubTab} t={t} />
          {subTab === 'sticky' ? <StickyMessagesPage embedded /> : <ScheduledMessagesPage embedded />}
        </>
      )}
    </div>
  )
}
