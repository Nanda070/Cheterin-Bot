import { Crosshair } from '@phosphor-icons/react'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useT } from '../context/LanguageContext'
import { CustomsPage } from './Customs'
import { ValCheckerPage } from './ValChecker'

type Tab = 'customs' | 'valchecker'

function resolveTab(raw: string | null): Tab {
  if (raw === 'valchecker') return 'valchecker'
  // customs, panels, premier, commands, or anything else → customs
  return 'customs'
}

export function ValorantPage() {
  const t = useT()
  const [searchParams, setSearchParams] = useSearchParams()
  const requestedTab = searchParams.get('tab')
  const initialTab = resolveTab(requestedTab)
  const [tab, setTab] = useState<Tab>(initialTab)

  useEffect(() => setTab(initialTab), [initialTab])

  // Drop obsolete ?tab=panels|premier|commands onto customs; normalize bare /valorant
  useEffect(() => {
    if (!requestedTab || (requestedTab !== 'customs' && requestedTab !== 'valchecker')) {
      setSearchParams({ tab: 'customs' }, { replace: true })
    }
  }, [requestedTab, setSearchParams])

  const tabs: Tab[] = ['customs', 'valchecker']
  const selectTab = (next: Tab) => {
    setTab(next)
    setSearchParams({ tab: next }, { replace: true })
  }

  return (
    <div className="flex max-w-5xl flex-col gap-5">
      <h1 className="flex items-center gap-2 text-lg font-semibold text-foreground">
        <Crosshair size={22} className="text-primary" />
        {t('valorant.title')}
      </h1>
      <div className="flex flex-wrap gap-2 border-b border-border">
        {tabs.map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => selectTab(item)}
            className={`px-3 py-2 text-sm ${
              tab === item ? 'border-b-2 border-primary text-foreground' : 'text-muted'
            }`}
          >
            {t(`valorant.tab.${item}`)}
          </button>
        ))}
      </div>
      {tab === 'customs' && <CustomsPage />}
      {tab === 'valchecker' && <ValCheckerPage />}
    </div>
  )
}
