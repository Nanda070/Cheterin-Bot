# Graph Report - frontend  (2026-08-03)

## Corpus Check
- 210 files · ~224,178 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1165 nodes · 3895 edges · 66 communities (64 shown, 2 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `41c97e80`
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
- FeedbackCaseDetailPanel.tsx
- Mafia.tsx
- useT
- AntiRaid.tsx
- PublicMafiaAction.tsx
- Supply.tsx
- Toggle.tsx
- ServerSettings.tsx
- EventDetailPanel.tsx
- Streams.tsx
- ServerSelect.tsx
- ScheduledMessages.tsx
- StickyMessages.tsx
- Toggle.tsx
- Credits.tsx
- Giveaways.tsx
- Fun.tsx
- Button.tsx
- AutoReactions.tsx
- ValChecker.tsx
- fetchProfileCardPreview
- Bunker.test.tsx
- MessageBuilder.tsx
- Fun.test.tsx
- Verification.tsx
- Messages.tsx
- AntiRaid.tsx
- ReactionRoles.tsx
- BotProfile.tsx

## God Nodes (most connected - your core abstractions)
1. `apiFetch()` - 194 edges
2. `useT()` - 169 edges
3. `jsonInit()` - 113 edges
4. `formatApiError()` - 103 edges
5. `react` - 91 edges
6. `fetchChannels()` - 60 edges
7. `Button()` - 58 edges
8. `Card()` - 55 edges
9. `Select()` - 41 edges
10. `Toggle()` - 34 edges

## Surprising Connections (you probably didn't know these)
- `WhatsNewBullets()` --calls--> `useT()`  [EXTRACTED]
  src/components/WhatsNew.tsx → src/context/LanguageContext.tsx
- `HeadingAnchor()` --calls--> `useLanguage()`  [EXTRACTED]
  src/pages/docs/docPrimitives.tsx → src/context/LanguageContext.tsx
- `FilterExtraFields()` --calls--> `useT()`  [EXTRACTED]
  src/pages/AutoMod.tsx → src/context/LanguageContext.tsx
- `FeatureSection()` --calls--> `useT()`  [EXTRACTED]
  src/pages/Landing.tsx → src/context/LanguageContext.tsx
- `DashboardShell()` --calls--> `logout()`  [EXTRACTED]
  src/pages/DashboardShell.tsx → src/api/client.ts

## Import Cycles
- None detected.

## Communities (66 total, 2 thin omitted)

### Community 0 - "react"
Cohesion: 0.20
Nodes (11): fetchMassAssignStatus(), fetchMembers(), MassAssignStatus, MassAssignTarget, MembersPage, startMassAssign(), MassAssignModal(), Props (+3 more)

### Community 1 - "apiFetch"
Cohesion: 0.13
Nodes (19): decideFamilyTicket(), deleteFamilyBirthday(), FamilyBirthday, FamilyRosterGroup, FamilySettings, FamilyTicket, FamilyTicketsPage, FamilyTicketStatus (+11 more)

### Community 2 - "client.ts"
Cohesion: 0.03
Nodes (60): AutoRolesSettings, BirthdayEntry, BotProfileSettings, BracketStandingsRow, BunkerAbilityAnnouncement, BunkerAdditionalInfo, BunkerAgeInfo, BunkerBodyType (+52 more)

### Community 3 - "renderWithLanguage.tsx"
Cohesion: 0.20
Nodes (13): fetchRelations(), fetchRelationsMarriages(), fetchRelationsTop(), RelationsAction, RelationsMarriageRow, RelationsPairRow, RelationsSettings, updateRelations() (+5 more)

### Community 4 - "ServerEntry.tsx"
Cohesion: 0.08
Nodes (39): createEmbedMessage(), deleteEmbedTemplate(), EmbedFieldSpec, EmbedMessagePayload, EmbedSpec, EmbedTemplate, FeedbackPanelSettings, fetchEmbedMessage() (+31 more)

### Community 5 - "devDependencies"
Cohesion: 0.04
Nodes (46): jsdom, oxlint, dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, tailwindcss (+38 more)

### Community 6 - "Lockdown.tsx"
Cohesion: 0.06
Nodes (35): createFeedbackCategory(), decideFeedbackCase(), deleteFeedbackCategory(), FeedbackCaseDetail, FeedbackCaseSummary, FeedbackCategoryFieldSpec, FeedbackCategorySpec, fetchFeedbackCaseDetail() (+27 more)

### Community 7 - "types.ts"
Cohesion: 0.09
Nodes (27): activity, admin, auth, common, community, credits, docsShell, en (+19 more)

### Community 8 - "Docs.tsx"
Cohesion: 0.11
Nodes (29): DocsBanner(), DocNavItem, DocsSearch(), DocsSearchProps, DocsSidebar(), DocsSidebarProps, GROUP_ICONS, DocsToc() (+21 more)

### Community 9 - "BracketDetail.tsx"
Cohesion: 0.09
Nodes (23): BracketDetail, BracketFormat, BracketMatch, BracketSummary, createBracket(), deleteBracket(), disableBracketShare(), enableBracketShare() (+15 more)

### Community 10 - "Bunker.tsx"
Cohesion: 0.10
Nodes (30): announceBunkerAbility(), BUNKER_FIELD_KEYS, BunkerFieldKey, BunkerPublicState, fetchPublicBunker(), fetchPublicMafia(), MafiaPublicState, MafiaRole (+22 more)

### Community 11 - "AutoMod.tsx"
Cohesion: 0.09
Nodes (27): AutomodFilter, AutomodPunishment, AutomodSettings, createEscalationRule(), deleteEscalationRule(), EscalationAction, EscalationRule, fetchAutomod() (+19 more)

### Community 12 - "compilerOptions"
Cohesion: 0.08
Nodes (23): DOM, src, vite/client, compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx (+15 more)

### Community 13 - "ModuleConfigPanel.tsx"
Cohesion: 0.19
Nodes (20): apiFetch(), banMember(), CaseTimeline, CaseTimelineItem, createMemberWarn(), deleteWarn(), fetchMemberDetail(), fetchMemberWarns() (+12 more)

### Community 14 - "Family.tsx"
Cohesion: 0.21
Nodes (12): createCustomCommand(), CustomCommandsSettings, deleteCustomCommand(), fetchCustomCommands(), previewTemplate(), setCustomCommandsEnabled(), updateCustomCommand(), CommandPreviewPage() (+4 more)

### Community 15 - "compilerOptions"
Cohesion: 0.10
Nodes (19): node, vite.config.ts, compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection (+11 more)

### Community 16 - "FeedbackCategories.tsx"
Cohesion: 0.18
Nodes (13): createReactionRole(), CustomEmoji, fetchEmojis(), ReactionRoleEntry, ReactionRolePair, updateReactionRole(), EmojiPickerTabs(), Props (+5 more)

### Community 17 - "useT"
Cohesion: 0.20
Nodes (14): AuditEntry, AuditModerator, AuditPage, fetchAudit(), AuditPage(), csvEscape(), downloadAuditCsv(), EntryRow() (+6 more)

### Community 18 - "useLanguage"
Cohesion: 0.16
Nodes (13): fetchPublicLeaderboard(), loginUrl(), PublicLeaderboardEntry, LanguageToggle(), PublicLayout(), useLanguage(), useT(), AccessDeniedPage() (+5 more)

### Community 19 - "AuthContext.tsx"
Cohesion: 0.16
Nodes (16): DashboardUser, fetchCurrentUser(), fetchSuperAdminGuilds(), selectGuild(), SuperAdminGuild, ProtectedRoute(), PublicLandingOrDashboard(), AuthContext (+8 more)

### Community 20 - "LanguageContext.tsx"
Cohesion: 0.25
Nodes (6): fallbackValue, LanguageContext, LanguageContextValue, LanguageProvider(), readStoredLang(), Lang

### Community 21 - "Fun.tsx"
Cohesion: 0.23
Nodes (8): ApiError, deleteTimedRole(), fetchTimedRoles(), TimedRoleEntry, API_ERROR_KEYS, formatApiError(), Translate, TimedRolesPage()

### Community 22 - "Members.tsx"
Cohesion: 0.17
Nodes (13): react, fetchModules(), CommandPalette(), CommandPaletteItem, CommandPaletteProps, Dropdown(), DropdownItem(), DropdownProps (+5 more)

### Community 23 - "ServerSelect.tsx"
Cohesion: 0.11
Nodes (25): deleteCardBg(), fetchVoiceStats(), fetchXpLeaderboard(), fetchXpOverview(), resetAllXp(), resetMemberXp(), setMemberXp(), updateXpSettings() (+17 more)

### Community 24 - "Casino.tsx"
Cohesion: 0.19
Nodes (12): CasinoLeaderboardEntry, CasinoSettings, fetchCasinoLeaderboard(), fetchCasinoSettings(), fetchEconomySettings(), updateCasinoSettings(), updateEconomySettings(), CasinoPage() (+4 more)

### Community 25 - "Economy.tsx"
Cohesion: 0.43
Nodes (7): BirthdaysPayload, deleteBirthday(), fetchBirthdays(), setBirthday(), testBirthdayAnnounce(), updateBirthdaySettings(), BirthdaysCalendarPage()

### Community 26 - "plugins"
Cohesion: 0.23
Nodes (10): fetchAutoRoles(), fetchRoles(), fetchStickyRoles(), StickyRolesSettings, updateAutoRoles(), updateStickyRoles(), Checkbox(), CheckboxProps (+2 more)

### Community 27 - "VoiceStats.tsx"
Cohesion: 0.32
Nodes (9): BunkerCardPools, BunkerCharacter, BunkerPlayerRef, isBunkerHealthy(), isBunkerHealthySeverity(), isBunkerRelationshipCategory(), substituteBunkerRelationshipPlayer(), BunkerCharacterEditor() (+1 more)

### Community 28 - "DashboardShell.tsx"
Cohesion: 0.24
Nodes (6): AccountLink(), FeatureDef, FEATURES, FeatureSection(), GhostButton(), isSpaPath()

### Community 29 - "Login.tsx"
Cohesion: 0.22
Nodes (8): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema, oxc, typescript, warn

### Community 35 - "Toggle.tsx"
Cohesion: 0.22
Nodes (15): advanceBunkerGamePhase(), applyBunkerAbility(), BunkerGameDetail, BunkerGameSummary, endBunkerGame(), fetchBunkerCardPools(), fetchBunkerGameDetail(), fetchBunkerGames() (+7 more)

### Community 36 - "FeedbackCaseDetailPanel.tsx"
Cohesion: 0.27
Nodes (8): WhatsNewBullets(), WhatsNewCard(), WhatsNewModal(), dismissWhatsNew(), isWhatsNewDismissed(), WHATS_NEW, whatsNewDismissKey(), WhatsNewEntry

### Community 37 - "FeedbackCaseDetailPanel.tsx"
Cohesion: 0.24
Nodes (9): deleteVoiceRoom(), fetchVoiceRooms(), publishVoicePanel(), VoiceRoom, Modal(), ModalProps, SIZE_CLASS, Tab (+1 more)

### Community 38 - "Mafia.tsx"
Cohesion: 0.26
Nodes (11): advanceMafiaGamePhase(), endMafiaGame(), fetchMafiaGameDetail(), fetchMafiaGames(), fetchMafiaSettings(), MafiaGameDetail, MafiaGameSummary, MafiaSettings (+3 more)

### Community 39 - "useT"
Cohesion: 0.27
Nodes (7): fetchSpamSettings(), SpamSettings, updateSpamSettings(), Card(), CardProps, AntiSpamPage(), NotFoundPage()

### Community 40 - "AntiRaid.tsx"
Cohesion: 0.10
Nodes (23): closeEvent(), createEvent(), CreateEventSpec, deleteEvent(), endPoll(), EventParticipantTeamCode, fetchEventDetail(), fetchPolls() (+15 more)

### Community 41 - "PublicMafiaAction.tsx"
Cohesion: 0.30
Nodes (11): createDailyTopic(), DailyTopicSettings, deleteDailyTopic(), fetchDailyTopic(), jsonInit(), postDailyTopicNow(), untimeoutMember(), updateDailyTopic() (+3 more)

### Community 42 - "Supply.tsx"
Cohesion: 0.11
Nodes (26): BotConfig, cancelSupply(), closeSupply(), createSupply(), fetchConfig(), fetchSupplyOverview(), isChannelDead(), Supply (+18 more)

### Community 43 - "Toggle.tsx"
Cohesion: 0.29
Nodes (9): fetchChannels(), fetchInvites(), fetchServerLog(), InvitesSettings, ServerLogEventConfig, updateInvitesSettings(), updateServerLog(), InvitesTrackerPage() (+1 more)

### Community 44 - "ServerSettings.tsx"
Cohesion: 0.18
Nodes (15): fetchLanguage(), fetchOwnerAlerts(), fetchTimezone(), OwnerAlertsSettings, ServerLanguage, testOwnerAlerts(), updateLanguage(), updateOwnerAlerts() (+7 more)

### Community 45 - "EventDetailPanel.tsx"
Cohesion: 0.29
Nodes (7): fetchStarboard(), StarboardSettings, TemplatePreviewResult, updateStarboard(), Toggle(), ToggleProps, StarboardPage()

### Community 46 - "Streams.tsx"
Cohesion: 0.36
Nodes (7): createStreamSubscription(), deleteStreamSubscription(), fetchStreams(), StreamSubscription, testStreamSubscription(), updateStreamSubscription(), StreamsPage()

### Community 47 - "ServerSelect.tsx"
Cohesion: 0.29
Nodes (7): fetchInviteUrl(), fetchManageableGuilds(), logout(), ManageableGuild, isForbiddenError(), guildIconUrl(), ServerSelectPage()

### Community 48 - "ScheduledMessages.tsx"
Cohesion: 0.43
Nodes (7): createScheduledMessage(), deleteScheduledMessage(), fetchScheduledMessages(), ScheduledMessagesSettings, setScheduledMessagesEnabled(), updateScheduledMessage(), ScheduledMessagesPage()

### Community 49 - "StickyMessages.tsx"
Cohesion: 0.22
Nodes (10): EconomySettings, EconomyTopEntry, EconomyWeeklyReportRow, fetchEconomyTop(), fetchEconomyWeeklyReport(), resetAllEconomyBalances(), setEconomyBalance(), EconomyPage() (+2 more)

### Community 50 - "Toggle.tsx"
Cohesion: 0.09
Nodes (27): activateLockdown(), createGiveaway(), deactivateLockdown(), endGiveaway(), fetchEvents(), fetchGiveawayOverview(), fetchLockdownStatus(), fetchModerationLog() (+19 more)

### Community 51 - "Credits.tsx"
Cohesion: 0.17
Nodes (7): ASTRA_PROJECTS, CreditsPage(), OTHER_PROJECTS, Project, SERVER_OVERLAY, TEAM, TeamMember

### Community 52 - "Giveaways.tsx"
Cohesion: 0.32
Nodes (7): ChannelInfo, CtdConfig, fetchCtdConfig(), updateCtdConfig(), Button(), CtdPage(), EMPTY

### Community 53 - "Fun.tsx"
Cohesion: 0.13
Nodes (15): fetchFunSettings(), fetchQuoteSettings(), fetchWordleSettings(), FunSettings, QuoteSettings, updateFunSettings(), updateQuoteSettings(), updateWordleSettings() (+7 more)

### Community 54 - "Button.tsx"
Cohesion: 0.28
Nodes (7): fetchNewsSettings(), NewsSettings, updateNewsSettings(), ButtonProps, Variant, VARIANT_CLASSES, NewsPage()

### Community 55 - "AutoReactions.tsx"
Cohesion: 0.43
Nodes (6): AutoReactionRule, AutoReactionsSettings, fetchAutoReactions(), updateAutoReactions(), AutoReactionsPage(), newRule()

### Community 56 - "ValChecker.tsx"
Cohesion: 0.53
Nodes (5): fetchValCheckerSettings(), saveValCheckerSettings(), ValCheckerSettings, clampPoll(), ValCheckerPage()

### Community 57 - "fetchProfileCardPreview"
Cohesion: 0.40
Nodes (5): fetchPreviewBlobUrl(), fetchProfileCardPreview(), fetchProfileCardPreviewGif(), profileCardPreviewGifUrl(), profileCardPreviewUrl()

### Community 58 - "Bunker.test.tsx"
Cohesion: 0.43
Nodes (7): deleteSticky(), fetchSticky(), setStickyEnabled(), StickySettings, testSticky(), upsertSticky(), StickyMessagesPage()

### Community 59 - "MessageBuilder.tsx"
Cohesion: 0.60
Nodes (3): MessageBuilderPage(), parseTab(), Tab

### Community 60 - "Fun.test.tsx"
Cohesion: 0.36
Nodes (7): fetchTempbanSettings(), publishTempbanWarning(), TempbanAction, TempbanSettings, updateTempbanSettings(), ACTIONS, TempbanPage()

### Community 61 - "Verification.tsx"
Cohesion: 0.39
Nodes (6): fetchVerificationSettings(), publishVerificationPanel(), updateVerificationSettings(), VerificationSettings, emptySettings, VerificationPage()

### Community 62 - "Messages.tsx"
Cohesion: 0.32
Nodes (5): MessagesPage(), MessagesSubTab, parseMessagesSubTab(), parseTopTab(), TopTab

### Community 63 - "AntiRaid.tsx"
Cohesion: 0.43
Nodes (5): AntiRaidSettings, fetchAntiRaidSettings(), updateAntiRaidSettings(), AntiRaidPage(), emptySettings

### Community 64 - "ReactionRoles.tsx"
Cohesion: 0.43
Nodes (5): deleteReactionRole(), fetchReactionRoles(), RoleChip, RoleInfo, ReactionRolesPage()

### Community 65 - "BotProfile.tsx"
Cohesion: 0.53
Nodes (5): BotProfileResponse, fetchBotProfile(), updateBotProfile(), BotProfilePage(), fileToDataUri()

## Knowledge Gaps
- **251 isolated node(s):** `$schema`, `typescript`, `oxc`, `react/rules-of-hooks`, `warn` (+246 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `useT()` connect `useLanguage` to `react`, `apiFetch`, `renderWithLanguage.tsx`, `ServerEntry.tsx`, `Lockdown.tsx`, `BracketDetail.tsx`, `AutoMod.tsx`, `ModuleConfigPanel.tsx`, `Family.tsx`, `FeedbackCategories.tsx`, `useT`, `AuthContext.tsx`, `LanguageContext.tsx`, `Fun.tsx`, `Members.tsx`, `ServerSelect.tsx`, `Casino.tsx`, `Economy.tsx`, `plugins`, `VoiceStats.tsx`, `DashboardShell.tsx`, `Toggle.tsx`, `FeedbackCaseDetailPanel.tsx`, `FeedbackCaseDetailPanel.tsx`, `Mafia.tsx`, `useT`, `AntiRaid.tsx`, `PublicMafiaAction.tsx`, `Supply.tsx`, `Toggle.tsx`, `ServerSettings.tsx`, `EventDetailPanel.tsx`, `Streams.tsx`, `ServerSelect.tsx`, `ScheduledMessages.tsx`, `StickyMessages.tsx`, `Toggle.tsx`, `Giveaways.tsx`, `Fun.tsx`, `Button.tsx`, `AutoReactions.tsx`, `ValChecker.tsx`, `Bunker.test.tsx`, `MessageBuilder.tsx`, `Fun.test.tsx`, `Verification.tsx`, `Messages.tsx`, `AntiRaid.tsx`, `ReactionRoles.tsx`, `BotProfile.tsx`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `react` connect `Members.tsx` to `react`, `apiFetch`, `renderWithLanguage.tsx`, `ServerEntry.tsx`, `Lockdown.tsx`, `Docs.tsx`, `BracketDetail.tsx`, `Bunker.tsx`, `AutoMod.tsx`, `ModuleConfigPanel.tsx`, `Family.tsx`, `FeedbackCategories.tsx`, `useT`, `useLanguage`, `AuthContext.tsx`, `LanguageContext.tsx`, `Fun.tsx`, `ServerSelect.tsx`, `Casino.tsx`, `Economy.tsx`, `plugins`, `VoiceStats.tsx`, `DashboardShell.tsx`, `Login.tsx`, `Toggle.tsx`, `FeedbackCaseDetailPanel.tsx`, `FeedbackCaseDetailPanel.tsx`, `Mafia.tsx`, `useT`, `AntiRaid.tsx`, `PublicMafiaAction.tsx`, `Supply.tsx`, `Toggle.tsx`, `ServerSettings.tsx`, `EventDetailPanel.tsx`, `Streams.tsx`, `ServerSelect.tsx`, `ScheduledMessages.tsx`, `StickyMessages.tsx`, `Toggle.tsx`, `Credits.tsx`, `Giveaways.tsx`, `Fun.tsx`, `Button.tsx`, `AutoReactions.tsx`, `ValChecker.tsx`, `Bunker.test.tsx`, `Fun.test.tsx`, `Verification.tsx`, `AntiRaid.tsx`, `ReactionRoles.tsx`, `BotProfile.tsx`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Why does `apiFetch()` connect `ModuleConfigPanel.tsx` to `react`, `apiFetch`, `client.ts`, `renderWithLanguage.tsx`, `ServerEntry.tsx`, `Lockdown.tsx`, `BracketDetail.tsx`, `Bunker.tsx`, `AutoMod.tsx`, `Family.tsx`, `FeedbackCategories.tsx`, `useT`, `useLanguage`, `AuthContext.tsx`, `Fun.tsx`, `ServerSelect.tsx`, `Casino.tsx`, `Economy.tsx`, `plugins`, `Toggle.tsx`, `FeedbackCaseDetailPanel.tsx`, `Mafia.tsx`, `useT`, `AntiRaid.tsx`, `PublicMafiaAction.tsx`, `Supply.tsx`, `Toggle.tsx`, `ServerSettings.tsx`, `EventDetailPanel.tsx`, `Streams.tsx`, `ScheduledMessages.tsx`, `StickyMessages.tsx`, `Toggle.tsx`, `Giveaways.tsx`, `Fun.tsx`, `Button.tsx`, `AutoReactions.tsx`, `ValChecker.tsx`, `Bunker.test.tsx`, `Fun.test.tsx`, `Verification.tsx`, `AntiRaid.tsx`, `ReactionRoles.tsx`, `BotProfile.tsx`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **What connects `$schema`, `typescript`, `oxc` to the rest of the system?**
  _251 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `apiFetch` be split into smaller, more focused modules?**
  _Cohesion score 0.1341991341991342 - nodes in this community are weakly interconnected._
- **Should `client.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.033879781420765025 - nodes in this community are weakly interconnected._
- **Should `ServerEntry.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.08244680851063829 - nodes in this community are weakly interconnected._