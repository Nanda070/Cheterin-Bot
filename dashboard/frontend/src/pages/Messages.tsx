import { CalendarBlank, PushPin } from '@phosphor-icons/react'
import { useSearchParams } from 'react-router-dom'
import { useT } from '../context/LanguageContext'
import { ScheduledMessagesPage } from './ScheduledMessages'
import { StickyMessagesPage } from './StickyMessages'

type MessagesTab = 'scheduled' | 'sticky'

function parseMessagesTab(raw: string | null): MessagesTab {
  return raw === 'sticky' ? 'sticky' : 'scheduled'
}

function TabBar({
  tab,
  setTab,
  t,
}: {
  tab: MessagesTab
  setTab: (t: MessagesTab) => void
  t: (key: string) => string
}) {
  const tabs: { key: MessagesTab; labelKey: string; icon: typeof CalendarBlank }[] = [
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
  const tab = parseMessagesTab(searchParams.get('tab'))
  const setTab = (next: MessagesTab) => {
    if (next === 'scheduled') setSearchParams({}, { replace: true })
    else setSearchParams({ tab: next }, { replace: true })
  }

  return (
    <div className="flex flex-col gap-4">
      <TabBar tab={tab} setTab={setTab} t={t} />
      {tab === 'sticky' ? <StickyMessagesPage embedded /> : <ScheduledMessagesPage embedded />}
    </div>
  )
}
