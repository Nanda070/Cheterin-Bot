import { useState } from 'react'
import { useT } from '../context/LanguageContext'
import { ModuleConfigPanel } from '../components/ModuleConfigPanel'
import { ReactionRolesPage } from './ReactionRoles'
import { EmbedBuilderPage } from './EmbedBuilder'

type Tab = 'reaction-roles' | 'embeds' | 'settings'

export function MessageBuilderPage() {
  const t = useT()
  const [tab, setTab] = useState<Tab>('reaction-roles')

  return (
    <div>
      <div className="mb-4 flex gap-2 border-b border-border">
        <button
          type="button"
          onClick={() => setTab('reaction-roles')}
          className={`cursor-pointer px-3 py-2 text-sm font-medium ${
            tab === 'reaction-roles' ? 'border-b-2 border-primary text-foreground' : 'text-muted hover:text-foreground'
          }`}
        >
          {t('messageBuilder.tab.reactionRoles')}
        </button>
        <button
          type="button"
          onClick={() => setTab('embeds')}
          className={`cursor-pointer px-3 py-2 text-sm font-medium ${
            tab === 'embeds' ? 'border-b-2 border-primary text-foreground' : 'text-muted hover:text-foreground'
          }`}
        >
          {t('messageBuilder.tab.embeds')}
        </button>
        <button
          type="button"
          onClick={() => setTab('settings')}
          className={`cursor-pointer px-3 py-2 text-sm font-medium ${
            tab === 'settings' ? 'border-b-2 border-primary text-foreground' : 'text-muted hover:text-foreground'
          }`}
        >
          {t('messageBuilder.tab.settings')}
        </button>
      </div>
      {tab === 'reaction-roles' && <ReactionRolesPage />}
      {tab === 'embeds' && <EmbedBuilderPage />}
      {tab === 'settings' && (
        <ModuleConfigPanel variant="buttons" title={t('config.section.buttons')} intro={t('messageBuilder.settingsIntro')} />
      )}
    </div>
  )
}
