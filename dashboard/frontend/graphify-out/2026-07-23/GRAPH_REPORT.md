# Graph Report - frontend  (2026-07-22)

## Corpus Check
- 175 files · ~110,848 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 887 nodes · 2839 edges · 42 communities (40 shown, 2 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `82841d22`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- react
- apiFetch
- client.ts
- renderWithLanguage.tsx
- ServerEntry.tsx
- devDependencies
- Lockdown.tsx
- types.ts
- Docs.tsx
- BracketDetail.tsx
- Bunker.tsx
- AutoMod.tsx
- compilerOptions
- ModuleConfigPanel.tsx
- Family.tsx
- compilerOptions
- FeedbackCategories.tsx
- useT
- useLanguage
- AuthContext.tsx
- LanguageContext.tsx
- Fun.tsx
- Members.tsx
- ServerSelect.tsx
- Casino.tsx
- Economy.tsx
- plugins
- VoiceStats.tsx
- DashboardShell.tsx
- Login.tsx
- Welcome.tsx
- tsconfig.json
- Toggle.tsx
- FeedbackCaseDetailPanel.tsx
- Home.tsx
- Card.tsx
- Mafia.tsx
- AntiRaid.tsx
- PublicMafiaAction.tsx

## God Nodes (most connected - your core abstractions)
1. `apiFetch()` - 134 edges
2. `useT()` - 117 edges
3. `jsonInit()` - 81 edges
4. `react` - 72 edges
5. `formatApiError()` - 65 edges
6. `Button()` - 43 edges
7. `Card()` - 43 edges
8. `fetchChannels()` - 40 edges
9. `Select()` - 28 edges
10. `fetchRoles()` - 27 edges

## Surprising Connections (you probably didn't know these)
- `FilterExtraFields()` --calls--> `useT()`  [EXTRACTED]
  src/pages/AutoMod.tsx → src/context/LanguageContext.tsx
- `MassAssignModal()` --calls--> `fetchMembers()`  [EXTRACTED]
  src/components/MassAssignModal.tsx → src/api/client.ts
- `HomePage()` --calls--> `fetchMembers()`  [EXTRACTED]
  src/pages/Home.tsx → src/api/client.ts
- `MembersPage()` --calls--> `fetchMembers()`  [EXTRACTED]
  src/pages/Members.tsx → src/api/client.ts
- `MassAssignModal()` --calls--> `fetchRoles()`  [EXTRACTED]
  src/components/MassAssignModal.tsx → src/api/client.ts

## Import Cycles
- None detected.

## Communities (42 total, 2 thin omitted)

### Community 0 - "react"
Cohesion: 0.05
Nodes (56): ChannelInfo, closeEvent(), createEvent(), CreateEventSpec, createGiveaway(), createReactionRole(), createStreamSubscription(), CtdConfig (+48 more)

### Community 1 - "apiFetch"
Cohesion: 0.06
Nodes (68): announceBunkerAbility(), apiFetch(), banMember(), BUNKER_FIELD_KEYS, BunkerFieldKey, BunkerPublicState, cancelSupply(), closeSupply() (+60 more)

### Community 2 - "client.ts"
Cohesion: 0.04
Nodes (49): AuditEntry, AutoRolesSettings, BracketStandingsRow, BunkerAbilityAnnouncement, BunkerAdditionalInfo, BunkerAgeInfo, BunkerBodyType, BunkerGamePhase (+41 more)

### Community 3 - "renderWithLanguage.tsx"
Cohesion: 0.06
Nodes (31): createEmbedMessage(), deleteEmbedTemplate(), EmbedMessagePayload, EmbedTemplate, fetchEmbedMessage(), fetchEmbedTemplates(), saveEmbedTemplate(), updateEmbedMessage() (+23 more)

### Community 4 - "ServerEntry.tsx"
Cohesion: 0.08
Nodes (38): BotConfig, deleteVoiceRoom(), EmbedFieldSpec, EmbedSpec, fetchAutoRoles(), fetchConfig(), fetchVoiceRooms(), fetchWelcomeSettings() (+30 more)

### Community 5 - "devDependencies"
Cohesion: 0.04
Nodes (46): jsdom, oxlint, dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, tailwindcss (+38 more)

### Community 6 - "Lockdown.tsx"
Cohesion: 0.21
Nodes (11): activateLockdown(), deactivateLockdown(), fetchLockdownStatus(), fetchModerationLog(), fetchVerificationSettings(), updateVerificationSettings(), VerificationSettings, LockdownPage() (+3 more)

### Community 7 - "types.ts"
Cohesion: 0.10
Nodes (24): LanguageContextValue, activity, admin, auth, common, community, docsShell, en (+16 more)

### Community 8 - "Docs.tsx"
Cohesion: 0.16
Nodes (14): DocsBanner(), DocNavItem, DocsSearch(), DocsSearchProps, DocsSidebar(), DocsSidebarProps, GROUP_ICONS, DocsToc() (+6 more)

### Community 9 - "BracketDetail.tsx"
Cohesion: 0.09
Nodes (23): BracketDetail, BracketFormat, BracketMatch, BracketSummary, createBracket(), deleteBracket(), disableBracketShare(), enableBracketShare() (+15 more)

### Community 10 - "Bunker.tsx"
Cohesion: 0.14
Nodes (24): applyBunkerAbility(), BunkerCardPools, BunkerCharacter, BunkerGameDetail, BunkerGameSummary, BunkerPlayerRef, BunkerSettings, fetchBunkerCardPools() (+16 more)

### Community 11 - "AutoMod.tsx"
Cohesion: 0.07
Nodes (32): AutomodFilter, AutomodPunishment, AutomodSettings, createEscalationRule(), deleteEscalationRule(), EscalationAction, EscalationRule, fetchAutomod() (+24 more)

### Community 12 - "compilerOptions"
Cohesion: 0.08
Nodes (23): DOM, src, vite/client, compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx (+15 more)

### Community 13 - "ModuleConfigPanel.tsx"
Cohesion: 0.27
Nodes (14): Code(), DocSection, H(), H3(), Note(), OL(), P(), Table() (+6 more)

### Community 14 - "Family.tsx"
Cohesion: 0.22
Nodes (14): deleteCardBg(), fetchXpLeaderboard(), fetchXpOverview(), resetAllXp(), resetMemberXp(), setMemberXp(), updateXpSettings(), uploadCardBg() (+6 more)

### Community 15 - "compilerOptions"
Cohesion: 0.10
Nodes (19): node, vite.config.ts, compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection (+11 more)

### Community 16 - "FeedbackCategories.tsx"
Cohesion: 0.18
Nodes (14): createFeedbackCategory(), deleteFeedbackCategory(), FeedbackCategoryFieldSpec, FeedbackCategorySpec, fetchFeedbackCategories(), publishFeedbackPanel(), updateFeedbackCategory(), sampleSpec (+6 more)

### Community 17 - "useT"
Cohesion: 0.24
Nodes (8): AuditPage, fetchAudit(), Button(), ButtonProps, Variant, VARIANT_CLASSES, AuditPage(), METHOD_COLOR

### Community 18 - "useLanguage"
Cohesion: 0.15
Nodes (12): react, fetchPublicLeaderboard(), PublicLeaderboardEntry, LanguageToggle(), PublicLayout(), useLanguage(), HeadingAnchor(), LeaderboardPage() (+4 more)

### Community 19 - "AuthContext.tsx"
Cohesion: 0.15
Nodes (15): DashboardUser, fetchCurrentUser(), fetchInviteUrl(), fetchManageableGuilds(), logout(), ManageableGuild, selectGuild(), ProtectedRoute() (+7 more)

### Community 20 - "LanguageContext.tsx"
Cohesion: 0.24
Nodes (7): MembersPage, fallbackValue, LanguageContext, LanguageProvider(), readStoredLang(), MembersPage(), NotFoundPage()

### Community 21 - "Fun.tsx"
Cohesion: 0.39
Nodes (7): fetchFunSettings(), fetchWordleSettings(), FunSettings, updateFunSettings(), updateWordleSettings(), WordleSettings, FunPage()

### Community 22 - "Members.tsx"
Cohesion: 0.20
Nodes (9): fetchMassAssignStatus(), MassAssignStatus, MassAssignTarget, MemberSummary, startMassAssign(), MassAssignModal(), Props, Checkbox() (+1 more)

### Community 23 - "ServerSelect.tsx"
Cohesion: 0.23
Nodes (8): ApiError, fetchServerLog(), ServerLogEventConfig, updateServerLog(), API_ERROR_KEYS, formatApiError(), Translate, ServerLogPage()

### Community 24 - "Casino.tsx"
Cohesion: 0.29
Nodes (8): CasinoLeaderboardEntry, CasinoSettings, fetchCasinoLeaderboard(), fetchCasinoSettings(), updateCasinoSettings(), CasinoPage(), emptyLeaderboard, emptySettings

### Community 25 - "Economy.tsx"
Cohesion: 0.39
Nodes (7): EconomySettings, EconomyTopEntry, fetchEconomySettings(), fetchEconomyTop(), setEconomyBalance(), updateEconomySettings(), EconomyPage()

### Community 26 - "plugins"
Cohesion: 0.22
Nodes (8): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema, oxc, typescript, warn

### Community 27 - "VoiceStats.tsx"
Cohesion: 0.18
Nodes (9): fetchVoiceStats(), loginUrl(), VoiceStats, App(), FEATURE_KEYS, LoginPage(), PERIODS, VoiceStatsPage() (+1 more)

### Community 28 - "DashboardShell.tsx"
Cohesion: 0.32
Nodes (6): Dropdown(), DropdownItem(), DropdownProps, NAV_GROUPS, NavGroup, Section

### Community 29 - "Login.tsx"
Cohesion: 0.28
Nodes (10): FeedbackPanelSettings, fetchFeedbackPanelSettings(), updateFeedbackPanelSettings(), EmbedEditor(), useT(), FeedbackPage(), Tab, FeedbackCasesPage() (+2 more)

### Community 35 - "Toggle.tsx"
Cohesion: 0.23
Nodes (10): fetchNewsSettings(), fetchTempbanSettings(), NewsSettings, TempbanSettings, updateNewsSettings(), updateTempbanSettings(), Toggle(), ToggleProps (+2 more)

### Community 36 - "FeedbackCaseDetailPanel.tsx"
Cohesion: 0.25
Nodes (7): decideFeedbackCase(), FeedbackCaseDetail, FeedbackCaseSummary, fetchFeedbackCaseDetail(), FeedbackCaseDetailPanel(), Props, sampleDetail

### Community 37 - "Home.tsx"
Cohesion: 0.25
Nodes (7): fetchEvents(), fetchFeedbackCases(), LockdownStatus, ModerationLogEntry, HomePage(), modlogLabel(), TYPE_ICON

### Community 38 - "Card.tsx"
Cohesion: 0.29
Nodes (7): fetchSpamSettings(), SpamSettings, updateSpamSettings(), Card(), CardProps, AccessDeniedPage(), AntiSpamPage()

### Community 39 - "Mafia.tsx"
Cohesion: 0.36
Nodes (7): fetchMafiaGames(), fetchMafiaSettings(), MafiaGameSummary, MafiaSettings, updateMafiaSettings(), MafiaPage(), Tab

### Community 40 - "AntiRaid.tsx"
Cohesion: 0.43
Nodes (5): AntiRaidSettings, fetchAntiRaidSettings(), updateAntiRaidSettings(), AntiRaidPage(), emptySettings

### Community 41 - "PublicMafiaAction.tsx"
Cohesion: 0.48
Nodes (6): fetchPublicMafia(), MafiaPublicState, submitMafiaAction(), submitMafiaVote(), PublicMafiaActionPage(), useCountdown()

## Knowledge Gaps
- **204 isolated node(s):** `$schema`, `typescript`, `oxc`, `react/rules-of-hooks`, `warn` (+199 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `react` connect `useLanguage` to `react`, `apiFetch`, `renderWithLanguage.tsx`, `ServerEntry.tsx`, `Lockdown.tsx`, `Docs.tsx`, `BracketDetail.tsx`, `Bunker.tsx`, `AutoMod.tsx`, `ModuleConfigPanel.tsx`, `Family.tsx`, `FeedbackCategories.tsx`, `useT`, `AuthContext.tsx`, `LanguageContext.tsx`, `Fun.tsx`, `Members.tsx`, `ServerSelect.tsx`, `Casino.tsx`, `Economy.tsx`, `plugins`, `VoiceStats.tsx`, `DashboardShell.tsx`, `Login.tsx`, `Toggle.tsx`, `FeedbackCaseDetailPanel.tsx`, `Home.tsx`, `Card.tsx`, `Mafia.tsx`, `AntiRaid.tsx`, `PublicMafiaAction.tsx`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `useT()` connect `Login.tsx` to `react`, `apiFetch`, `renderWithLanguage.tsx`, `ServerEntry.tsx`, `Lockdown.tsx`, `BracketDetail.tsx`, `Bunker.tsx`, `AutoMod.tsx`, `Family.tsx`, `FeedbackCategories.tsx`, `useT`, `useLanguage`, `AuthContext.tsx`, `LanguageContext.tsx`, `Fun.tsx`, `ServerSelect.tsx`, `Casino.tsx`, `Economy.tsx`, `VoiceStats.tsx`, `DashboardShell.tsx`, `Toggle.tsx`, `FeedbackCaseDetailPanel.tsx`, `Home.tsx`, `Card.tsx`, `Mafia.tsx`, `AntiRaid.tsx`, `PublicMafiaAction.tsx`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `plugins` connect `plugins` to `useLanguage`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **What connects `$schema`, `typescript`, `oxc` to the rest of the system?**
  _204 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `react` be split into smaller, more focused modules?**
  _Cohesion score 0.05477477477477478 - nodes in this community are weakly interconnected._
- **Should `apiFetch` be split into smaller, more focused modules?**
  _Cohesion score 0.05809979494190021 - nodes in this community are weakly interconnected._
- **Should `client.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.04081632653061224 - nodes in this community are weakly interconnected._