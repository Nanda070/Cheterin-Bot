# Graph Report - frontend  (2026-07-22)

## Corpus Check
- 170 files · ~108,190 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 873 nodes · 2680 edges · 35 communities (33 shown, 2 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cfd516c9`
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

## God Nodes (most connected - your core abstractions)
1. `apiFetch()` - 134 edges
2. `useT()` - 113 edges
3. `jsonInit()` - 81 edges
4. `react` - 70 edges
5. `Button()` - 41 edges
6. `Card()` - 41 edges
7. `fetchChannels()` - 40 edges
8. `Select()` - 28 edges
9. `fetchRoles()` - 27 edges
10. `Modal()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `LanguageContextValue` --references--> `Lang`  [EXTRACTED]
  src/context/LanguageContext.tsx → src/i18n/types.ts
- `FilterExtraFields()` --calls--> `useT()`  [EXTRACTED]
  src/pages/AutoMod.tsx → src/context/LanguageContext.tsx
- `DashboardShell()` --calls--> `logout()`  [EXTRACTED]
  src/pages/DashboardShell.tsx → src/api/client.ts
- `FamilyPage()` --calls--> `fetchMembers()`  [EXTRACTED]
  src/pages/Family.tsx → src/api/client.ts
- `HomePage()` --calls--> `fetchMembers()`  [EXTRACTED]
  src/pages/Home.tsx → src/api/client.ts

## Import Cycles
- None detected.

## Communities (35 total, 2 thin omitted)

### Community 0 - "react"
Cohesion: 0.07
Nodes (57): react, ChannelInfo, createEvent(), createReactionRole(), deleteReactionRole(), EventSummary, fetchChannels(), fetchCtdConfig() (+49 more)

### Community 1 - "apiFetch"
Cohesion: 0.06
Nodes (75): announceBunkerAbility(), AntiRaidSettings, apiFetch(), banMember(), BUNKER_FIELD_KEYS, BunkerFieldKey, BunkerPublicState, cancelSupply() (+67 more)

### Community 2 - "client.ts"
Cohesion: 0.03
Nodes (63): AuditEntry, AutoRolesSettings, BracketStandingsRow, BracketSummary, BunkerAbilityAnnouncement, BunkerAdditionalInfo, BunkerAgeInfo, BunkerBodyType (+55 more)

### Community 3 - "renderWithLanguage.tsx"
Cohesion: 0.05
Nodes (37): closeEvent(), decideFeedbackCase(), deleteEvent(), EventDetail, EventParticipantTeamCode, FeedbackCaseDetail, FeedbackCaseSummary, fetchEventDetail() (+29 more)

### Community 4 - "ServerEntry.tsx"
Cohesion: 0.07
Nodes (40): createEmbedMessage(), deleteEmbedTemplate(), EmbedFieldSpec, EmbedMessagePayload, EmbedSpec, EmbedTemplate, FeedbackPanelSettings, fetchAutoRoles() (+32 more)

### Community 5 - "devDependencies"
Cohesion: 0.04
Nodes (46): jsdom, oxlint, dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, tailwindcss (+38 more)

### Community 6 - "Lockdown.tsx"
Cohesion: 0.07
Nodes (27): activateLockdown(), ApiError, deactivateLockdown(), fetchEvents(), fetchLockdownStatus(), fetchModerationLog(), fetchSuperAdminGuilds(), fetchVerificationSettings() (+19 more)

### Community 7 - "types.ts"
Cohesion: 0.11
Nodes (22): activity, admin, auth, common, community, docsShell, en, legal (+14 more)

### Community 8 - "Docs.tsx"
Cohesion: 0.11
Nodes (28): DocsBanner(), DocNavItem, DocsSearch(), DocsSearchProps, DocsSidebar(), DocsSidebarProps, GROUP_ICONS, DocsToc() (+20 more)

### Community 9 - "BracketDetail.tsx"
Cohesion: 0.09
Nodes (20): BracketDetail, BracketFormat, BracketMatch, createBracket(), deleteBracket(), disableBracketShare(), enableBracketShare(), fetchBracketDetail() (+12 more)

### Community 10 - "Bunker.tsx"
Cohesion: 0.11
Nodes (27): applyBunkerAbility(), BunkerCardPools, BunkerCharacter, BunkerGameDetail, BunkerGameSummary, BunkerPlayerRef, BunkerSettings, fetchBunkerCardPools() (+19 more)

### Community 11 - "AutoMod.tsx"
Cohesion: 0.11
Nodes (26): AutomodFilter, AutomodPunishment, AutomodSettings, createEscalationRule(), deleteEscalationRule(), EscalationAction, EscalationRule, fetchAutomod() (+18 more)

### Community 12 - "compilerOptions"
Cohesion: 0.08
Nodes (23): DOM, src, vite/client, compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx (+15 more)

### Community 13 - "ModuleConfigPanel.tsx"
Cohesion: 0.14
Nodes (17): BotConfig, deleteVoiceRoom(), fetchConfig(), fetchVoiceRooms(), publishVoicePanel(), updateConfig(), VoiceRoom, sampleConfig (+9 more)

### Community 14 - "Family.tsx"
Cohesion: 0.13
Nodes (20): CustomEmoji, decideFamilyTicket(), deleteFamilyBirthday(), FamilyBirthday, FamilyRosterGroup, FamilySettings, FamilyTicket, FamilyTicketsPage (+12 more)

### Community 15 - "compilerOptions"
Cohesion: 0.10
Nodes (19): node, vite.config.ts, compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection (+11 more)

### Community 16 - "FeedbackCategories.tsx"
Cohesion: 0.18
Nodes (14): createFeedbackCategory(), deleteFeedbackCategory(), FeedbackCategoryFieldSpec, FeedbackCategorySpec, fetchFeedbackCategories(), publishFeedbackPanel(), updateFeedbackCategory(), sampleSpec (+6 more)

### Community 17 - "useT"
Cohesion: 0.21
Nodes (12): AuditPage, fetchAudit(), fetchPublicLeaderboard(), PublicLeaderboardEntry, App(), PublicLayout(), useT(), AccessDeniedPage() (+4 more)

### Community 18 - "useLanguage"
Cohesion: 0.19
Nodes (6): LanguageToggle(), useLanguage(), HeadingAnchor(), PrivacyPage(), TABLE_ROW_KEYS, TermsPage()

### Community 19 - "AuthContext.tsx"
Cohesion: 0.27
Nodes (8): DashboardUser, fetchCurrentUser(), ProtectedRoute(), AuthContext, AuthContextValue, AuthProvider(), useAuth(), DashboardShell()

### Community 20 - "LanguageContext.tsx"
Cohesion: 0.23
Nodes (7): fallbackValue, LanguageContext, LanguageContextValue, LanguageProvider(), readStoredLang(), translate(), NotFoundPage()

### Community 21 - "Fun.tsx"
Cohesion: 0.24
Nodes (9): fetchFunSettings(), fetchWordleSettings(), FunSettings, updateFunSettings(), updateWordleSettings(), WordleSettings, FunPage(), emptySettings (+1 more)

### Community 22 - "Members.tsx"
Cohesion: 0.23
Nodes (6): fetchMassAssignStatus(), fetchMembers(), MembersPage, startMassAssign(), MassAssignModal(), MembersPage()

### Community 23 - "ServerSelect.tsx"
Cohesion: 0.29
Nodes (7): fetchInviteUrl(), fetchManageableGuilds(), logout(), ManageableGuild, selectGuild(), guildIconUrl(), ServerSelectPage()

### Community 24 - "Casino.tsx"
Cohesion: 0.29
Nodes (8): CasinoLeaderboardEntry, CasinoSettings, fetchCasinoLeaderboard(), fetchCasinoSettings(), updateCasinoSettings(), CasinoPage(), emptyLeaderboard, emptySettings

### Community 25 - "Economy.tsx"
Cohesion: 0.31
Nodes (8): EconomySettings, EconomyTopEntry, fetchEconomySettings(), fetchEconomyTop(), setEconomyBalance(), updateEconomySettings(), EconomyPage(), emptySettings

### Community 26 - "plugins"
Cohesion: 0.22
Nodes (8): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema, oxc, typescript, warn

### Community 27 - "VoiceStats.tsx"
Cohesion: 0.29
Nodes (5): fetchVoiceStats(), VoiceStats, PERIODS, VoiceStatsPage(), WEEKDAY_KEYS

### Community 28 - "DashboardShell.tsx"
Cohesion: 0.32
Nodes (6): Dropdown(), DropdownItem(), DropdownProps, NAV_GROUPS, NavGroup, Section

### Community 29 - "Login.tsx"
Cohesion: 0.50
Nodes (3): loginUrl(), FEATURE_KEYS, LoginPage()

## Knowledge Gaps
- **201 isolated node(s):** `$schema`, `typescript`, `oxc`, `react/rules-of-hooks`, `warn` (+196 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `react` connect `react` to `apiFetch`, `renderWithLanguage.tsx`, `ServerEntry.tsx`, `Lockdown.tsx`, `Docs.tsx`, `BracketDetail.tsx`, `Bunker.tsx`, `AutoMod.tsx`, `ModuleConfigPanel.tsx`, `Family.tsx`, `FeedbackCategories.tsx`, `useT`, `useLanguage`, `AuthContext.tsx`, `LanguageContext.tsx`, `Fun.tsx`, `Members.tsx`, `ServerSelect.tsx`, `Casino.tsx`, `Economy.tsx`, `plugins`, `VoiceStats.tsx`, `DashboardShell.tsx`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Why does `useT()` connect `useT` to `react`, `apiFetch`, `renderWithLanguage.tsx`, `ServerEntry.tsx`, `Lockdown.tsx`, `BracketDetail.tsx`, `Bunker.tsx`, `AutoMod.tsx`, `ModuleConfigPanel.tsx`, `Family.tsx`, `FeedbackCategories.tsx`, `useLanguage`, `AuthContext.tsx`, `LanguageContext.tsx`, `Fun.tsx`, `Members.tsx`, `ServerSelect.tsx`, `Casino.tsx`, `Economy.tsx`, `VoiceStats.tsx`, `DashboardShell.tsx`, `Login.tsx`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `plugins` connect `plugins` to `react`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **What connects `$schema`, `typescript`, `oxc` to the rest of the system?**
  _201 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `react` be split into smaller, more focused modules?**
  _Cohesion score 0.0708548479632817 - nodes in this community are weakly interconnected._
- **Should `apiFetch` be split into smaller, more focused modules?**
  _Cohesion score 0.0560126582278481 - nodes in this community are weakly interconnected._
- **Should `client.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.031746031746031744 - nodes in this community are weakly interconnected._