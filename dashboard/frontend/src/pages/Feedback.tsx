import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useT } from '../context/LanguageContext'
import { FeedbackCasesPage } from './FeedbackCases'
import { FeedbackCategoriesPage } from './FeedbackCategories'
import { FeedbackPanelPage } from './FeedbackPanel'
import { IdeasPage } from './Ideas'

type Tab = 'cases' | 'categories' | 'panel' | 'ideas'

const VALID_TABS: Tab[] = ['cases', 'categories', 'panel', 'ideas']

function tabFromSearch(raw: string | null): Tab {
  if (raw && (VALID_TABS as string[]).includes(raw)) return raw as Tab
  return 'cases'
}

export function FeedbackPage() {
  const t = useT()
  const [searchParams, setSearchParams] = useSearchParams()
  const [tab, setTab] = useState<Tab>(() => tabFromSearch(searchParams.get('tab')))

  useEffect(() => {
    setTab(tabFromSearch(searchParams.get('tab')))
  }, [searchParams])

  const selectTab = (next: Tab) => {
    setTab(next)
    setSearchParams(next === 'cases' ? {} : { tab: next }, { replace: true })
  }

  return (
    <div>
      <div className="mb-4 flex gap-2 border-b border-border">
        <button
          type="button"
          onClick={() => selectTab('cases')}
          className={`cursor-pointer px-3 py-2 text-sm font-medium ${
            tab === 'cases' ? 'border-b-2 border-primary text-foreground' : 'text-muted hover:text-foreground'
          }`}
        >
          {t('feedback.tab.cases')}
        </button>
        <button
          type="button"
          onClick={() => selectTab('categories')}
          className={`cursor-pointer px-3 py-2 text-sm font-medium ${
            tab === 'categories' ? 'border-b-2 border-primary text-foreground' : 'text-muted hover:text-foreground'
          }`}
        >
          {t('feedback.tab.categories')}
        </button>
        <button
          type="button"
          onClick={() => selectTab('panel')}
          className={`cursor-pointer px-3 py-2 text-sm font-medium ${
            tab === 'panel' ? 'border-b-2 border-primary text-foreground' : 'text-muted hover:text-foreground'
          }`}
        >
          {t('feedback.tab.panel')}
        </button>
        <button
          type="button"
          onClick={() => selectTab('ideas')}
          className={`cursor-pointer px-3 py-2 text-sm font-medium ${
            tab === 'ideas' ? 'border-b-2 border-primary text-foreground' : 'text-muted hover:text-foreground'
          }`}
        >
          {t('ideas.title')}
        </button>
      </div>
      {tab === 'cases' ? (
        <FeedbackCasesPage />
      ) : tab === 'categories' ? (
        <FeedbackCategoriesPage />
      ) : tab === 'panel' ? (
        <FeedbackPanelPage />
      ) : (
        <IdeasPage />
      )}
    </div>
  )
}
