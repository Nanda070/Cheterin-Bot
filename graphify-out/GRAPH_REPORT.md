# Graph Report - Cheterin_Bot_Dashboard  (2026-07-22)

## Corpus Check
- 501 files · ~292,780 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5082 nodes · 13220 edges · 201 communities (181 shown, 20 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 188 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6cf0943d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Game Settings & Bunker DB
- Supply Module
- Dashboard App Bootstrap
- Test Fake Channels
- API Client Types
- Test Fake Bot
- Automod Route Tests
- Tournament Brackets
- Feedback Cases
- Giveaways Routes
- Automod Cog
- Server Event Logging
- Automod Filter Core
- Test Fake Members
- Daily Topic Module
- API Client Functions
- Bunker Game Core
- Moderation Routes
- Bunker Discord Cog
- Mass Role Assignment
- Embed Builder Routes
- Bot Entrypoint & Auth Middleware
- Frontend Package Deps
- Lockdown API Client
- Mafia DB Tests
- Mafia Core Tests
- Stream Notifications
- Feedback Panel Tests
- Reaction Roles Tests
- Streams API Client
- Voice Rooms Routes
- XP API Client
- Mafia Discord Cog
- Feedback API Client
- Family DB Tests
- Events & Embeds Client
- Lockdown Routes
- Events Route Tests
- Mafia Public Route Tests
- Family Tickets
- Button Forms
- Audit Log & Stats DB
- Giveaway Cog
- Brackets Client Tests
- Bunker API Client
- Automod API Client
- Event Builder UI
- Family Core Tests
- XP Core Tests
- Event Publish Tests
- TypeScript Config
- Bot Config Store
- Family Birthdays
- Anti-Spam Cog
- news.py
- events.py
- test_feedback_routes.py
- FeedbackCategories.tsx
- Docs.tsx
- voice_rooms.py
- XPCog
- auth.py
- resolve_guild_member()
- xp.py
- test_feedback_category_routes.py
- Supply.tsx
- MassAssignModal.tsx
- compilerOptions
- .__init__()
- VoiceTracker
- Interaction
- ensure_owner()
- family.py
- test_family_routes.py
- test_access.py
- test_config_routes.py
- RosterCog
- reaction_roles.py
- PublicBunkerAction.tsx
- Leaderboard.tsx
- VoiceManager
- mafia.py
- events.py
- ChetBot
- ChannelInfo
- MafiaLobbyView
- voice_logs.py
- test_auto_roles_routes.py
- Giveaways.tsx
- PublicMafiaAction.tsx
- Welcome
- test_mafia_routes.py
- test_warns_routes.py
- test_xp_routes.py
- config.py
- setup_static_routes()
- FakeAsset
- plugins
- DocsSearch.tsx
- xp_card.py
- auto_roles.py
- icons.svg
- format_voice_time()
- DocsToc.tsx
- FakeVoiceChannel
- favicon.svg
- Hero Image Graphic
- tsconfig.json
- React Logo Image
- DocsSearch.tsx
- test_fun_routes.py
- Vite Logo
- DocsSearch.tsx
- test_members_list.py
- test_member_detail.py
- DocsToc.tsx
- init
- Request
- Response
- Button.tsx
- events.py
- wordle_card.py
- events.py
- load_events
- test_supply_routes.py
- PublicMafiaAction.tsx
- wordle.py
- test_warns_routes.py
- Supply.tsx
- .__init__
- test_roles.py
- test_giveaway_routes.py
- format_voice_time
- test_feedback_panel_routes.py
- MafiaLobbyView
- FakeResponse
- FakeResponse
- test_news_routes.py
- test_auto_roles_routes.py
- test_supply_routes.py
- lockdown.py
- test_xp_routes.py
- Levels.tsx
- format_voice_time
- FakeVoiceChannel
- test_economy_routes.py
- FakeResponse
- _FakeMember
- Casino.tsx
- SupplyView
- config.py
- resolve_ticket
- .start_lobby
- economy.py
- load_dashboard_config
- EventDetailPanel.tsx
- test_members_list.py
- test_button_config.py
- FakeResponse
- test_ctd_routes.py
- Giveaways.tsx
- Giveaways.tsx
- test_feedback_panel_routes.py
- test_roles.py
- setup_session
- test_wordle_routes.py
- test_ctd_routes.py
- FakeResponse
- test_members_list.py
- test_antiraid_routes.py
- Welcome.tsx
- __init__.py
- test_fun_routes.py
- VCTheme
- init
- pick_bunker_conditions
- DocsSearch.tsx
- setup_session
- test_casino_routes.py
- FakeResponse
- init
- day_number
- DocsToc.tsx
- Toggle.tsx
- Connection
- Row
- Application
- Path
- ClientSession
- FreeTypeFont
- Image
- ImageFont

## God Nodes (most connected - your core abstractions)
1. `force_login()` - 313 edges
2. `FakeMember` - 233 edges
3. `FakeGuild` - 214 edges
4. `FakeBot` - 191 edges
5. `apiFetch()` - 134 edges
6. `useT()` - 113 edges
7. `FakeChannel` - 111 edges
8. `t()` - 104 edges
9. `FakeRole` - 100 edges
10. `jsonInit()` - 81 edges

## Surprising Connections (you probably didn't know these)
- `Unified settings.db Per-Guild Storage` --references--> `get_settings()`  [INFERRED]
  MULTIGUILD_PLAN.md → bunker_core.py
- `Phase 2.4: Bot Detached from GUILD_ID` --references--> `ChetBot`  [EXTRACTED]
  MULTIGUILD_PLAN.md → main.py
- `Phase 2.3: OAuth Guilds Scope and Server Selection` --references--> `callback()`  [EXTRACTED]
  MULTIGUILD_PLAN.md → dashboard/backend/auth.py
- `FakeInteraction` --uses--> `BlackjackView`  [INFERRED]
  dashboard/backend/tests/test_blackjack_cog.py → blackjack.py
- `FakeMessage` --uses--> `BlackjackView`  [INFERRED]
  dashboard/backend/tests/test_blackjack_cog.py → blackjack.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Phase 2 Multi-Guild Core** — multiguild_plan_settings_db, multiguild_plan_guild_dimension_migration, multiguild_plan_oauth_guilds_flow, multiguild_plan_bot_global_sync [EXTRACTED 1.00]
- **Main Guild Privileged Features** — multiguild_plan_main_guild_id, multiguild_plan_ctd_main_guild_gate, multiguild_plan_news_relay_superadmin, multiguild_plan_superadmin_main_check [EXTRACTED 1.00]
- **RU/EN Localization Program** — multiguild_plan_i18n_infrastructure, multiguild_plan_two_level_language_model, multiguild_plan_slash_command_localization, multiguild_plan_bunker_cards_bilingual [EXTRACTED 1.00]
- **Backend Runtime Dependencies** — requirements_discord_py, requirements_python_dotenv, requirements_aiohttp, requirements_aiohttp_session, requirements_cryptography, requirements_pillow [INFERRED 0.95]
- **Dashboard Application Architecture** — readme_chetbot, readme_dashboard, dashboard_frontend_index_html [INFERRED 0.85]
- **External Platform and Social Icons Set** — dashboard_frontend_public_icons_bluesky_icon, dashboard_frontend_public_icons_discord_icon, dashboard_frontend_public_icons_github_icon, dashboard_frontend_public_icons_x_icon, dashboard_frontend_public_icons_social_icon [INFERRED 0.85]
- **Dashboard UI Icon Asset Set** — dashboard_frontend_public_icons_bluesky_icon, dashboard_frontend_public_icons_discord_icon, dashboard_frontend_public_icons_documentation_icon, dashboard_frontend_public_icons_github_icon, dashboard_frontend_public_icons_social_icon, dashboard_frontend_public_icons_x_icon [EXTRACTED 1.00]
- **Docs Page User Interface** — dashboard_frontend_src_pages_docs, dashboard_frontend_src_components_docs_docsbanner, dashboard_frontend_src_assets_docs_banner [INFERRED 0.90]
- **Hero Page Visual Branding Elements** — dashboard_frontend_src_assets_hero, dashboard_frontend_src_assets_hero_branding, dashboard_frontend_src_assets_hero_layered_stack [INFERRED 0.85]

## Communities (201 total, 20 thin omitted)

### Community 0 - "Game Settings & Bunker DB"
Cohesion: 0.13
Nodes (21): get_tempban_settings(), Request, Response, update_tempban_settings(), get_welcome_settings(), Request, Response, _serialize_messages() (+13 more)

### Community 1 - "Supply Module"
Cohesion: 0.09
Nodes (49): _display_name(), _finalize(), Request, Response, _serialize_supply(), supply_cancel(), supply_close(), supply_create() (+41 more)

### Community 2 - "Dashboard App Bootstrap"
Cohesion: 0.07
Nodes (28): activateLockdown(), ApiError, deactivateLockdown(), fetchFeedbackCases(), fetchLockdownStatus(), fetchMembers(), fetchModerationLog(), fetchSuperAdminGuilds() (+20 more)

### Community 3 - "Test Fake Channels"
Cohesion: 0.09
Nodes (8): DashboardConfig, FakeAsset, FakeAuditLogExtra, _FakeChannelType, FakeColor, FakeGuildInner, FakePermissions, FakeVoiceChannel

### Community 4 - "API Client Types"
Cohesion: 0.03
Nodes (86): AntiRaidSettings, AuditEntry, AutoRolesSettings, BracketStandingsRow, BunkerAbilityAnnouncement, BunkerAdditionalInfo, BunkerAgeInfo, BunkerBodyType (+78 more)

### Community 5 - "Test Fake Bot"
Cohesion: 0.05
Nodes (69): FakeBot, FakeGuild, FakeThread, make_client_app(), test_guild_unavailable_gets_503(), test_member_not_in_guild_gets_403(), test_member_with_access_reaches_handler(), test_member_without_access_role_gets_403() (+61 more)

### Community 6 - "Automod Route Tests"
Cohesion: 0.07
Nodes (39): LanguageContextValue, activity, admin, auth, common, community, docsShell, en (+31 more)

### Community 7 - "Tournament Brackets"
Cohesion: 0.07
Nodes (61): create_bracket(), create_bracket_v2(), _de_get_match(), _de_match(), _de_recompute_match(), _de_resolve(), extract_entries_from_event(), generate_de() (+53 more)

### Community 8 - "Feedback Cases"
Cohesion: 0.15
Nodes (15): add_reviewers(), build_mentions(), close_case(), create_feedback_case(), FeedbackDecisionView, FeedbackMenu, FeedbackModal, FeedbackView (+7 more)

### Community 9 - "Giveaways Routes"
Cohesion: 0.08
Nodes (55): _display_name(), giveaways_create(), giveaways_end(), giveaways_overview(), giveaways_reroll(), Request, Response, _serialize_giveaway() (+47 more)

### Community 10 - "Automod Cog"
Cohesion: 0.14
Nodes (10): AutoMod, _consecutive_run_length(), BaseException, Bot, Guild, Interaction, Member, Message (+2 more)

### Community 11 - "Server Event Logging"
Cohesion: 0.07
Nodes (38): AuditLogAction, AuditLogEntry, Request, Response, serverlog_get(), serverlog_put(), test_format_stay_duration(), test_format_stay_duration_negative_clamped_to_zero() (+30 more)

### Community 12 - "Automod Filter Core"
Cohesion: 0.08
Nodes (40): add_escalation_rule(), _default_filter(), _default_notify_template(), delete_escalation_rule(), detect_bad_words(), detect_caps_lock(), detect_emoji_spam(), detect_invites() (+32 more)

### Community 13 - "Test Fake Members"
Cohesion: 0.20
Nodes (35): eliminate_player(), build(), _character(), _setup_game(), test_ability_already_used(), test_ability_dead_player(), test_ability_game_not_active(), test_ability_happy_path_marks_card_used_and_announces() (+27 more)

### Community 14 - "Daily Topic Module"
Cohesion: 0.19
Nodes (20): already_posted_today(), get_today_post_time(), is_valid_time(), mark_posted_today(), _normalized(), Ядро модуля «Ежедневная рубрика».  Бот раз в день публикует тему/вопрос в заданн, Возвращает выбранное на сегодня время публикации, выбирая его при первом обращен, Пора ли публиковать тему дня: время настало и сегодня ещё не публиковали. (+12 more)

### Community 15 - "API Client Functions"
Cohesion: 0.05
Nodes (42): BlackjackGame, _build_deck(), can_double(), card_rank(), card_suit(), _deal_card(), dealer_play(), format_hand() (+34 more)

### Community 16 - "Bunker Game Core"
Cohesion: 0.08
Nodes (26): default_bunker_capacity(), has_moderator_access(), is_game_over(), Большинство голосов за исключение; ничья среди лидеров — никто не исключён., Половина игроков (округление вниз, минимум 1) — если ведущий не задал своё число, resolve_expulsion_vote(), save_config(), _FakeMember (+18 more)

### Community 17 - "Moderation Routes"
Cohesion: 0.23
Nodes (25): _assignable_roles(), ban_member(), dashboard_reason(), _get_guild_or_none(), get_moderation_log(), _get_target_or_response(), grant_role(), kick_member() (+17 more)

### Community 18 - "Bunker Discord Cog"
Cohesion: 0.12
Nodes (16): build_expulsion_result_embed(), build_lobby_cancelled_embed(), build_result_embed(), build_vote_embed(), BunkerCog, _character_summary(), _display_name(), _frontend_url() (+8 more)

### Community 19 - "Mass Role Assignment"
Cohesion: 0.04
Nodes (57): AuditPage, fetchAudit(), fetchInviteUrl(), fetchLanguage(), fetchManageableGuilds(), fetchPublicLeaderboard(), fetchPublicMafia(), fetchVoiceStats() (+49 more)

### Community 20 - "Embed Builder Routes"
Cohesion: 0.08
Nodes (55): create_embed_message(), create_embed_template(), delete_embed_template(), get_embed_message(), _get_guild_or_none(), _is_role_assignable(), list_embed_templates(), _parse_body() (+47 more)

### Community 21 - "Bot Entrypoint & Auth Middleware"
Cohesion: 0.08
Nodes (30): require_dashboard_access Middleware, CTD, CTDCloseView, CTDView, _is_main_guild(), BaseException, Button, Interaction (+22 more)

### Community 22 - "Frontend Package Deps"
Cohesion: 0.04
Nodes (46): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, tailwindcss, @tailwindcss/vite, devDependencies (+38 more)

### Community 23 - "Lockdown API Client"
Cohesion: 0.22
Nodes (21): test_load_categories_returns_empty_dict_when_file_missing(), test_migrate_from_env_if_needed_creates_config_from_env(), test_migrate_from_env_if_needed_skips_when_env_vars_missing(), test_migrate_from_env_if_needed_skips_when_file_already_exists(), test_save_then_load_round_trip(), test_validate_category_spec_accepts_valid_spec(), test_validate_category_spec_allows_own_case_prefix_on_edit(), test_validate_category_spec_allows_same_key_on_edit() (+13 more)

### Community 24 - "Mafia DB Tests"
Cohesion: 0.14
Nodes (32): build(), _poll_create_spec(), _poll_event(), test_close_event_route_404(), test_close_event_route_requires_auth(), test_close_event_route_success(), test_create_event_404_when_channel_missing(), test_create_event_404_when_role_reward_missing() (+24 more)

### Community 25 - "Mafia Core Tests"
Cohesion: 0.08
Nodes (37): _FakeMember, _FakePermissions, isolated_config(), test_assign_roles_matches_scale_and_covers_all_players(), test_check_win_condition_mafia_wins_at_parity(), test_check_win_condition_no_winner_yet(), test_check_win_condition_town_wins_when_no_mafia(), test_get_settings_defaults() (+29 more)

### Community 26 - "Stream Notifications"
Cohesion: 0.10
Nodes (24): ClientSession, _public_sub(), Request, Response, streams_create(), streams_delete(), streams_list(), streams_update() (+16 more)

### Community 27 - "Feedback Panel Tests"
Cohesion: 0.10
Nodes (34): bet_error(), flip_coin(), get_settings(), payout_amount(), Ядро модуля «Казино»: слоты, монетка и блэкджек на серверную валюту.  Без импорт, Настройки модуля сервера с дефолтами (выключен по умолчанию)., None — ставка допустима, иначе текст ошибки для игрока., Выигрыш с учётом преимущества казино (округление вниз). (+26 more)

### Community 28 - "Reaction Roles Tests"
Cohesion: 0.08
Nodes (47): create_reaction_role(), delete_reaction_role(), _get_guild_or_none(), _is_role_assignable(), list_channels(), list_emojis(), list_reaction_roles(), Request (+39 more)

### Community 29 - "Streams API Client"
Cohesion: 0.07
Nodes (36): Тесты синглтона состояния панели голосовых комнат (voice_rooms, Фаза 2.2б).  Ран, test_panel_state_defaults_empty(), test_panel_state_round_trip(), Modal, apply_owner_permissions(), build_embed(), ChannelControlView, _config_channel_id() (+28 more)

### Community 30 - "Voice Rooms Routes"
Cohesion: 0.11
Nodes (32): Request, Response, voice_panel_publish(), voice_room_delete(), voice_rooms_list(), build(), FakeVoiceChannel, isolated_db() (+24 more)

### Community 31 - "XP API Client"
Cohesion: 0.08
Nodes (49): audit_list(), Request, Response, isolated_db(), _create_legacy_schema(), isolated_db(), Тесты stats_db: per-guild изоляция XP/войс/аудита и миграция старой схемы.  Фаза, Схема до Фазы 2.2а: без guild_id (как в проде на мейн-сервере). (+41 more)

### Community 32 - "Mafia Discord Cog"
Cohesion: 0.11
Nodes (18): build_game_started_embed(), build_lobby_cancelled_embed(), build_lynch_result_embed(), build_morning_embed(), build_result_embed(), build_vote_embed(), _frontend_url(), MafiaCog (+10 more)

### Community 33 - "Feedback API Client"
Cohesion: 0.07
Nodes (42): Request, Response, verification_get(), verification_put(), build(), FakeInteraction, FakeResponse, Тесты кога «Верификация»: выключена по умолчанию, join-роль, кнопка. (+34 more)

### Community 34 - "Family DB Tests"
Cohesion: 0.12
Nodes (42): _create_legacy_schema(), isolated_db(), Тесты family_db: per-guild ростер/заявки/дни рождения + миграция старой схемы., Схема до Фазы 2.2б: синглтоны roster_msg/birthday_msg (id=1), single-PK     pen, test_birthday_message_roundtrip_and_isolation(), test_birthday_roundtrip_and_queries(), test_list_and_count_tickets_scoped_and_filtered(), test_migration_assigns_legacy_rows_to_main_guild() (+34 more)

### Community 35 - "Events & Embeds Client"
Cohesion: 0.15
Nodes (27): _cmd(), _grp(), _key(), Any, Apply slash command localizations for every cog (Phase 3.2(3))., register_automod(), register_blackjack(), register_bunker() (+19 more)

### Community 36 - "Lockdown Routes"
Cohesion: 0.21
Nodes (10): DashboardUser, fetchCurrentUser(), loginUrl(), ProtectedRoute(), AuthContext, AuthContextValue, AuthProvider(), useAuth() (+2 more)

### Community 37 - "Events Route Tests"
Cohesion: 0.09
Nodes (26): BlackjackCog, BlackjackView, build_embed(), Bot, Button, Embed, Interaction, Member (+18 more)

### Community 38 - "Mafia Public Route Tests"
Cohesion: 0.07
Nodes (55): language_get(), language_put(), Request, Response, _display_name(), _is_id(), mafia_games_list(), mafia_get() (+47 more)

### Community 39 - "Family Tickets"
Cohesion: 0.11
Nodes (23): English card pools for the Bunker survival tabletop game., Данные для игры «Бункер»: возраст, телосложение, профессии, хобби, здоровье, стр, additional_info_en_template(), _en_item(), get_card_pools(), localize_character(), merge_additional_info(), merge_age() (+15 more)

### Community 40 - "Button Forms"
Cohesion: 0.11
Nodes (14): ButtonCreate, DynamicQuestionsModal, _get_allowed_role_ids(), _load_buttons_config(), BaseException, Interaction, Member, Role (+6 more)

### Community 41 - "Audit Log & Stats DB"
Cohesion: 0.07
Nodes (37): isolated_config(), Тесты ядра Вордла: целостность словаря, оценка догадок, слово дня, настройки., test_board_lines_pads_empty_rows(), test_evaluate_all_green(), test_evaluate_duplicate_letters_consume_stock(), test_evaluate_green_priority_over_yellow(), test_evaluate_yellow_and_gray(), test_guess_error_cases() (+29 more)

### Community 42 - "Giveaway Cog"
Cohesion: 0.11
Nodes (13): generate_embed(), GiveawayCog, GiveawayView, Bot, Button, Embed, Interaction, Range (+5 more)

### Community 43 - "Brackets Client Tests"
Cohesion: 0.09
Nodes (20): fetchMassAssignStatus(), MassAssignStatus, MassAssignTarget, MemberSummary, startMassAssign(), ChipPickerProps, Option, MassAssignModal() (+12 more)

### Community 44 - "Bunker API Client"
Cohesion: 0.18
Nodes (14): BotConfig, deleteVoiceRoom(), fetchConfig(), fetchVoiceRooms(), publishVoicePanel(), updateConfig(), VoiceRoom, sampleConfig (+6 more)

### Community 45 - "Automod API Client"
Cohesion: 0.22
Nodes (15): get(), load_config(), migrate_from_env_if_needed(), Invite link for tempban DM and other modules (no hardcoded fallback)., resolve_server_invite_link(), test_get_returns_default_when_key_missing(), test_get_returns_stored_value(), test_load_config_returns_empty_dict_when_missing() (+7 more)

### Community 47 - "Event Builder UI"
Cohesion: 0.14
Nodes (16): Messageable, _config_int(), generate_embed(), get_reminder_minutes(), _main_guild_id(), Bot, Button, Color (+8 more)

### Community 48 - "Family Core Tests"
Cohesion: 0.13
Nodes (20): _FakeGuild, _FakeGuildRef, _FakeMember, isolated_config(), test_build_birthday_text_groups_by_month_and_resolves_mentions(), test_can_manage_tickets_requires_configured_role(), test_has_staff_access_admin_bypasses_role_check(), test_has_staff_access_via_role() (+12 more)

### Community 49 - "XP Core Tests"
Cohesion: 0.08
Nodes (34): Request, Response, voice_stats(), test_deserved_roles(), test_format_voice_time(), test_level_formula_monotonic(), test_level_from_xp_roundtrip(), test_level_progress() (+26 more)

### Community 50 - "Event Publish Tests"
Cohesion: 0.20
Nodes (22): _poll_spec(), test_publish_event_poll_creates_matching_event_obj_and_view(), test_publish_event_role_reward_none_stays_none(), test_publish_event_tournament_creates_matching_event_obj_and_view(), test_validate_event_spec_accepts_valid_poll_spec(), test_validate_event_spec_accepts_valid_tournament_spec(), test_validate_event_spec_allows_missing_team_size_check_for_solo_mode(), test_validate_event_spec_rejects_description_too_long() (+14 more)

### Community 51 - "TypeScript Config"
Cohesion: 0.08
Nodes (23): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+15 more)

### Community 52 - "Bot Config Store"
Cohesion: 0.18
Nodes (14): createFeedbackCategory(), deleteFeedbackCategory(), FeedbackCategoryFieldSpec, FeedbackCategorySpec, fetchFeedbackCategories(), publishFeedbackPanel(), updateFeedbackCategory(), sampleSpec (+6 more)

### Community 53 - "Family Birthdays"
Cohesion: 0.15
Nodes (12): BirthdayCog, build_birthday_embed(), BaseException, Bot, Embed, Guild, Interaction, Member (+4 more)

### Community 54 - "Anti-Spam Cog"
Cohesion: 0.15
Nodes (26): test_build_goodbye_uses_custom_text(), test_resolve_dm_footer_uses_custom_text(), test_resolve_dm_thumbnail_returns_empty_without_custom(), test_resolve_dm_thumbnail_uses_custom_fallback(), test_substitute_placeholders(), test_welcome_settings_defaults(), embed_spec_has_content(), Placeholder substitution for customizable bot messages. (+18 more)

### Community 55 - "news.py"
Cohesion: 0.15
Nodes (18): _is_id_like(), news_get(), news_put(), Request, Response, get_channel_map(), get_settings(), _main_guild_id() (+10 more)

### Community 56 - "events.py"
Cohesion: 0.26
Nodes (5): CasinoLeaderboardView, Button, Embed, Guild, Interaction

### Community 57 - "test_feedback_routes.py"
Cohesion: 0.09
Nodes (28): add(), connect(), get_by_user(), get_db_path(), init(), list_all(), _now(), Connection (+20 more)

### Community 58 - "FeedbackCategories.tsx"
Cohesion: 0.27
Nodes (7): _fmt_voice(), LeaderboardView, Button, Guild, Interaction, Формат времени голоса Ч:ММ:СС (как в JuniperBot)., Интерактивный лидерборд: сортировка по Опыту / Голосу + пагинация.

### Community 59 - "Docs.tsx"
Cohesion: 0.14
Nodes (14): ChetBot, command_sync_mode(), get_main_guild_id(), main(), on_guild_join(), on_guild_remove(), on_ready(), Embed (+6 more)

### Community 60 - "voice_rooms.py"
Cohesion: 0.17
Nodes (23): add_round_event(), connect(), count_players(), create_ability_announcement(), get_ability_announcement(), get_active_game_in_channel(), get_db_path(), get_game_by_lobby_message() (+15 more)

### Community 61 - "XPCog"
Cohesion: 0.13
Nodes (14): XP_ADMIN_MAX, XP_ADMIN_MIN, channel_allowed(), member_has_ignored_role(), Bot, Embed, Member, Message (+6 more)

### Community 62 - "auth.py"
Cohesion: 0.21
Nodes (20): DiscordOAuthError, exchange_code_for_token(), fetch_discord_identity(), fetch_user_guilds(), ClientSession, Exception, Список серверов пользователя (`/users/@me/guilds`, требует scope `guilds`)., refresh_access_token() (+12 more)

### Community 63 - "resolve_guild_member()"
Cohesion: 0.18
Nodes (11): MemberLookupResult, resolve_guild_member(), FakeBot, FakeGuild, _StubHTTPException, _StubNotFound, test_falls_back_to_fetch_when_not_cached(), test_not_found_when_fetch_raises_notfound() (+3 more)

### Community 64 - "xp.py"
Cohesion: 0.19
Nodes (22): _int_in(), _is_id_list(), Request, Response, Вкладка «Участники» дашборда: весь ростер гильдии, а не только те,     кто уже, _serialize_row(), xp_card_bg_delete(), xp_card_bg_upload() (+14 more)

### Community 65 - "test_feedback_category_routes.py"
Cohesion: 0.16
Nodes (15): _has_legacy_role_access(), Переходный грант по роли на активном сервере (если задан DASHBOARD_ACCESS_ROLE_I, Гейт доступа к серверу (Фаза 2.3): сессия → активный сервер → Manage Server., Гейт для списка серверов бота — намеренно хардкод-роль, см. access.py., require_dashboard_access(), require_super_admin(), get_ctd(), put_ctd() (+7 more)

### Community 66 - "Supply.tsx"
Cohesion: 0.16
Nodes (21): get_stats(), build(), FakeInteraction, FakeMessage, FakeResponse, make_game(), Тесты кога «Блэкджек»: гейты, ставки, натуральный BJ, кнопки Ещё/Стоп/Удвоить., start_view_game() (+13 more)

### Community 67 - "MassAssignModal.tsx"
Cohesion: 0.22
Nodes (17): build(), FakeChoice, FakeInteraction, FakeResponse, Тесты кога «Казино»: /слоты и /монетка — через .callback(), паттерн test_fun_cog, test_coinflip_disabled_module(), test_coinflip_house_edge_reduces_payout(), test_coinflip_loss() (+9 more)

### Community 68 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+11 more)

### Community 69 - ".__init__()"
Cohesion: 0.21
Nodes (8): test_load_events_reads_fresh_after_external_write(), test_load_events_returns_empty_events_dict_when_file_missing(), test_save_then_load_roundtrips(), create_participation_view(), EventManageSelect, load_events(), View, SelectOption

### Community 70 - "VoiceTracker"
Cohesion: 0.14
Nodes (8): is_active(), BaseException, Bot, VoiceState, Войс-трекер: единый учёт голосовых сессий.  Кормит сразу два модуля: - статис, setup(), VoiceSession, VoiceTracker

### Community 71 - "Interaction"
Cohesion: 0.19
Nodes (20): lockdown_activate(), lockdown_deactivate(), lockdown_status(), _log(), Request, Response, _role(), test_activate_collects_errors_and_continues() (+12 more)

### Community 72 - "ensure_owner()"
Cohesion: 0.08
Nodes (40): Тесты ядра экономики: курс от XP, комиссии, валидация ставок, хук award_for_xp., test_award_for_xp_disabled_gives_nothing(), test_award_for_xp_uses_kind_rate(), test_bet_error_cases(), test_bet_error_unlimited_when_max_zero(), test_claim_daily_bonus_consecutive_day_extends_streak(), test_claim_daily_bonus_first_time(), test_claim_daily_bonus_gap_resets_streak() (+32 more)

### Community 73 - "family.py"
Cohesion: 0.29
Nodes (17): _decide_ticket(), _display_name(), family_birthday_delete(), family_birthday_set(), family_birthdays_list(), family_get(), family_put(), family_roster() (+9 more)

### Community 74 - "test_family_routes.py"
Cohesion: 0.10
Nodes (42): Тесты economy_db: атомарные списания, переводы, топ, журнал., test_add_ignores_non_positive(), test_daily_bonus_default_when_missing(), test_daily_bonus_roundtrip_and_update(), test_equip_roundtrip_and_clear(), test_grant_and_own_cosmetic(), test_grant_cosmetic_is_idempotent(), test_history_recorded() (+34 more)

### Community 75 - "test_access.py"
Cohesion: 0.33
Nodes (10): test_resolve_banner_url_returns_empty_when_unset(), test_resolve_banner_url_uses_custom_setting(), build_panel_payload(), default_panel_embed_spec(), get_settings(), _load_raw(), panel_banner_url(), Feedback panel appearance customization. (+2 more)

### Community 76 - "test_config_routes.py"
Cohesion: 0.20
Nodes (22): add_player(), update_game(), _make_game(), База, созданная до появления voice_channel_id/vote_message_id/unique_cards,, _sample_character(), test_add_player_rejects_duplicate(), test_assign_character_and_get_by_token(), test_create_and_get_game() (+14 more)

### Community 77 - "RosterCog"
Cohesion: 0.20
Nodes (9): generate_roster_text(), Bot, Guild, Interaction, Member, Live-ростер семьи: список участников по настроенным ролям.  Портировано из FamQ, Debounce: аккумулирует изменения и обновляет сообщение через 10 секунд., RosterCog (+1 more)

### Community 78 - "reaction_roles.py"
Cohesion: 0.14
Nodes (13): build_topic_message(), DailyTopicCog, BaseException, Bot, Ког «Ежедневная рубрика»: раз в день публикует тему/вопрос дня в заданный канал,, Публикует тему дня немедленно (используется циклом и ручным триггером         из, setup(), build() (+5 more)

### Community 79 - "PublicBunkerAction.tsx"
Cohesion: 0.10
Nodes (19): test_build_board_embed_finished_loss_reveals_answer(), File, _avatar_bytes(), BoardView, build_board_embed(), _card_file(), GuessModal, PlayNowView (+11 more)

### Community 80 - "Leaderboard.tsx"
Cohesion: 0.05
Nodes (63): fun_get(), fun_put(), Request, Response, _auto_emoji_config(), build(), enable_economy(), FakeInteraction (+55 more)

### Community 81 - "VoiceManager"
Cohesion: 0.07
Nodes (27): get_spam_settings(), Request, Response, update_spam_settings(), test_message_limit_with_attachments(), test_spam_settings_defaults(), test_spam_settings_roundtrip(), build() (+19 more)

### Community 82 - "mafia.py"
Cohesion: 0.08
Nodes (23): BracketDetail, BracketFormat, BracketMatch, BracketSummary, createBracket(), deleteBracket(), disableBracketShare(), enableBracketShare() (+15 more)

### Community 83 - "events.py"
Cohesion: 0.19
Nodes (20): member_warns_create(), member_warns_list(), Request, Response, warn_delete(), test_active_warn_count_excludes_expired_and_removed(), test_add_and_get_warn(), test_add_warn_without_moderator_is_automod() (+12 more)

### Community 84 - "ChetBot"
Cohesion: 0.15
Nodes (14): Web Dashboard Index HTML, React Root Mount Element, React Entry Point Script, ChetBot, ChetBot Web Dashboard, ChetBot Official Documentation, aiohttp Dependency, aiohttp-session Dependency (+6 more)

### Community 85 - "ChannelInfo"
Cohesion: 0.21
Nodes (21): get_settings(), Настройки модуля сервера с дефолтами (выключен по умолчанию)., assign_character(), create_game(), build(), _sample_character(), test_apply_ability_announcement(), test_apply_ability_announcement_not_found() (+13 more)

### Community 86 - "MafiaLobbyView"
Cohesion: 0.25
Nodes (16): build(), test_birthday_set_invalid_date(), test_birthday_set_unknown_member(), test_birthdays_crud(), test_get_defaults(), test_put_then_get(), test_put_validation(), test_requires_auth() (+8 more)

### Community 87 - "voice_logs.py"
Cohesion: 0.11
Nodes (37): isolated_db(), Тесты wordle_db: игры дня, статистика со стриками, мета сервера., test_add_guess_accumulates_and_finishes(), test_group_streak_gap_resets(), test_group_streak_grows_and_resets(), test_last_announced_day_roundtrip(), test_list_day_games_filters_by_day(), test_live_message_roundtrip() (+29 more)

### Community 88 - "test_auto_roles_routes.py"
Cohesion: 0.23
Nodes (17): build(), build_with_guild(), _full_config(), PUT /api/config не должен затирать ключи других разделов (авто-роли, приветствия, test_get_config_requires_auth(), test_get_config_returns_defaults_when_file_missing(), test_get_config_returns_stored_values(), test_put_config_preserves_foreign_keys() (+9 more)

### Community 89 - "Giveaways.tsx"
Cohesion: 0.05
Nodes (78): FakeChannel, FakeComponentRow, FakeCustomEmoji, FakeMessage, FakeRole, test_parse_role_button_ids_extracts_matching_custom_ids(), test_parse_role_button_ids_handles_no_components(), test_parse_role_button_ids_ignores_non_role_buttons() (+70 more)

### Community 90 - "PublicMafiaAction.tsx"
Cohesion: 0.13
Nodes (22): reset_settings_db(), isolated_db(), Тесты settings_migration: перенос плоских JSON в settings_db, идемпотентность., test_migrate_all_is_idempotent_across_two_runs(), test_migrate_all_migrates_existing_files_only(), test_migrate_one_missing_file_is_noop(), test_migrate_one_moves_data_and_renames_file(), test_migrate_one_treats_corrupt_json_as_empty_object() (+14 more)

### Community 91 - "Welcome"
Cohesion: 0.09
Nodes (10): command_reason(), format_duration(), normalize_reason(), parse_duration(), parse_mute_duration(), Ядро команд модерации (/ban /kick /unban /clear): парсинг и форматирование срока, Секунды из строки вида 10m/2h/7d/30s. ValueError с понятным текстом при неверном, Как parse_duration, но с проверкой лимита Discord в 28 дней. (+2 more)

### Community 93 - "test_mafia_routes.py"
Cohesion: 0.18
Nodes (7): ApplicationModalPart1, ContinueApplicationView, OpenTicketView, Button, Interaction, setup(), TicketControlView

### Community 94 - "test_warns_routes.py"
Cohesion: 0.09
Nodes (23): can_manage_guild_permissions(), has_dashboard_access(), has_manage_server(), has_super_admin_access(), manageable_guilds(), Контроль доступа к дашборду (модель MEE6, Фаза 2.3).  Доступ к серверу = право, DEPRECATED (Фаза 1, роль-модель). Оставлено до перевода auth/middleware на, Доступ к настройкам сервера: Manage Server или Administrator на этой гильдии. (+15 more)

### Community 95 - "test_xp_routes.py"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does SelectOption connect Mafia Game Engine to Discord Embed Builder, Supply Cog Tests?, Source Nodes

### Community 96 - "config.py"
Cohesion: 0.11
Nodes (50): isolated_db(), _make_game(), test_add_player_rejects_duplicate(), test_assign_player_role_and_get_by_token(), test_create_and_get_game(), test_get_active_game_in_channel_filters_by_status(), test_get_day_vote_single_row(), test_get_game_by_lobby_and_vote_message() (+42 more)

### Community 97 - "setup_static_routes()"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does force_login() connect Mock Services & Unit Tests to a wide array of system modules and tests?, Source Nodes

### Community 98 - "FakeAsset"
Cohesion: 0.06
Nodes (47): guild_context_middleware(), Request, Per-request guild-контекст (Фаза 2.3).  Раньше гильдия была одна на всё приложен, make_moderation_app(), build(), isolated_config(), test_get_defaults_disabled(), test_put_then_get() (+39 more)

### Community 99 - "plugins"
Cohesion: 0.22
Nodes (8): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema, oxc, typescript, warn

### Community 100 - "DocsSearch.tsx"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Are the inferred relationships involving mock objects (FakeMember, FakeGuild, FakeBot, FakeRole) with DashboardConfig and _StubForbidden correct?, Source Nodes

### Community 101 - "xp_card.py"
Cohesion: 0.21
Nodes (20): build(), build_with_channels(), _case(), test_decide_feedback_case_404_when_unknown(), test_decide_feedback_case_409_when_already_decided(), test_decide_feedback_case_409_when_category_deleted(), test_decide_feedback_case_approves_and_persists(), test_decide_feedback_case_rejects_non_boolean_approved() (+12 more)

### Community 102 - "auto_roles.py"
Cohesion: 0.11
Nodes (26): AutomodFilter, AutomodPunishment, AutomodSettings, createEscalationRule(), deleteEscalationRule(), EscalationAction, EscalationRule, fetchAutomod() (+18 more)

### Community 103 - "icons.svg"
Cohesion: 0.38
Nodes (6): Bluesky Icon, Discord Icon, Documentation Icon, GitHub Icon, Social Icon, X Icon

### Community 104 - "format_voice_time()"
Cohesion: 0.51
Nodes (9): save_config(), build_cog(), make_joining_member(), Тесты кога приветствий: канал/тумблеры/тексты берутся строго из настроек сервера, test_dm_title_uses_event_guild_name(), test_dm_toggle_off_suppresses_dm(), test_per_guild_isolation_of_welcome_channel(), test_welcome_channel_toggle_off_suppresses_public_message() (+1 more)

### Community 105 - "DocsToc.tsx"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: What connects schema, typescript, oxc to the rest of the system?, Source Nodes

### Community 108 - "Hero Image Graphic"
Cohesion: 1.00
Nodes (3): Hero Image Graphic, Cheterin Isometric Branding Concept, Layered Isometric Architecture Illustration

### Community 111 - "DocsSearch.tsx"
Cohesion: 0.20
Nodes (24): get_player_by_token(), list_alive_players(), list_players(), _row_to_player(), bunker_apply_ability(), bunker_card_pools(), bunker_game_detail(), bunker_games_list() (+16 more)

### Community 112 - "test_fun_routes.py"
Cohesion: 0.20
Nodes (14): Тесты рендера карточки ранга: базовый рендер, кастомная рамка и титул., test_hex_to_rgb(), test_render_rank_card_long_title_does_not_crash(), test_render_rank_card_with_custom_frame_and_title(), test_render_rank_card_without_cosmetics_produces_png(), FreeTypeFont, Image, ImageFont (+6 more)

### Community 120 - "DocsSearch.tsx"
Cohesion: 0.26
Nodes (16): _Deck, generate_characters(), _pick_additional_info(), _pick_age(), _pick_backpack_item(), _pick_body_type(), _pick_health(), _pick_hobby() (+8 more)

### Community 121 - "test_members_list.py"
Cohesion: 0.08
Nodes (34): decideFeedbackCase(), EmbedFieldSpec, EmbedSpec, FeedbackCaseDetail, FeedbackCaseSummary, FeedbackPanelSettings, fetchAutoRoles(), fetchFeedbackCaseDetail() (+26 more)

### Community 122 - "test_member_detail.py"
Cohesion: 0.29
Nodes (13): ConfigError, load_dashboard_config(), Exception, test_access_role_ids_empty_string_ok(), test_access_role_ids_optional_empty_when_absent(), test_frontend_dist_defaults_to_empty_string(), test_frontend_dist_picked_up_when_present(), test_frontend_url_defaults_to_empty_string() (+5 more)

### Community 123 - "DocsToc.tsx"
Cohesion: 0.24
Nodes (18): build(), FakeInteraction, Тесты кога Вордла — вызов через .callback()/методы кога, паттерн test_xp_command, test_announce_nobody_played(), test_announce_nobody_won_reveals_word(), test_announce_with_winner_crowns_best_and_streak(), test_commands_disabled_module(), test_daily_guess_edits_existing_live_card() (+10 more)

### Community 124 - "init"
Cohesion: 0.29
Nodes (18): create_feedback_category(), decide_feedback_case(), delete_feedback_category(), get_feedback_case(), get_feedback_panel_settings(), _get_guild_or_none(), list_feedback_cases(), list_feedback_categories() (+10 more)

### Community 125 - "Request"
Cohesion: 0.10
Nodes (24): get_settings(), is_suspicious_account(), JoinTracker, datetime, Ядро модуля «Антирейд»: детект всплеска входов новых участников.  Без импорта di, Настройки модуля сервера с дефолтами. enabled=False по умолчанию — модуль не, Считается ли аккаунт «свежим» (подозрительным) на момент входа., Скользящее окно недавних «подозрительных» входов на один сервер.      Чистая стр (+16 more)

### Community 126 - "Response"
Cohesion: 0.18
Nodes (6): EventBuilderView, LimitsModal, OptionsModal, Interaction, TextChannel, TextModal

### Community 127 - "Button.tsx"
Cohesion: 0.10
Nodes (17): BALANCE_ADMIN_MAX, CosmeticsView, EconomyCog, _item_label(), Bot, Guild, Interaction, Member (+9 more)

### Community 128 - "events.py"
Cohesion: 0.29
Nodes (16): FakeAuditLogEntry, Одна запись аудита для guild.audit_logs() — только то, что нужно     serverlog., build(), enable(), last_embed(), Embed, Тесты кога «Логирование»: стиль эмбедов (description+footer+thumbnail), формати, test_member_join_embed_style() (+8 more)

### Community 129 - "wordle_card.py"
Cohesion: 0.21
Nodes (16): ImageDraw, _avatar_image(), _circle_avatar(), _draw_grid(), _font(), _grid_size(), _placeholder_avatar(), FreeTypeFont (+8 more)

### Community 130 - "events.py"
Cohesion: 0.16
Nodes (14): createEmbedMessage(), deleteEmbedTemplate(), EmbedMessagePayload, EmbedTemplate, fetchEmbedMessage(), fetchEmbedTemplates(), saveEmbedTemplate(), updateEmbedMessage() (+6 more)

### Community 131 - "load_events"
Cohesion: 0.21
Nodes (12): build(), Test that partial failures during deactivate are logged with Ошибки field in emb, Test that activate returns 503 when guild is unavailable., Test that partial failures are logged with Ошибки field in embed., _StubForbidden, test_activate_guild_unavailable_503(), test_activate_then_status_then_deactivate(), test_activate_with_partial_errors_logs_error_field() (+4 more)

### Community 132 - "test_supply_routes.py"
Cohesion: 0.15
Nodes (43): build(), cosmetics_shop_config(), FakeInteraction, FakeResponse, Тесты кога «Экономика»: /баланс /перевести /монеты-топ /магазин — через .callbac, shop_config(), test_balance_disabled_module(), test_balance_shows_amount_and_rank() (+35 more)

### Community 133 - "PublicMafiaAction.tsx"
Cohesion: 0.13
Nodes (24): connect(), _ensure_row(), get_db_path(), init(), leaderboard(), Connection, SQLite-хранилище статистики казино (победы/поражения)., result: 'win', 'lose', 'push (+16 more)

### Community 134 - "wordle.py"
Cohesion: 0.33
Nodes (15): get_game(), get_player(), bunker_patch_player(), Ручное применение эффекта спец. возможности ведущим — частичная замена полей кар, build(), _cleanup_timer(), _make_lobby(), Тесты игрового цикла кога «Бункер»: старт игры (раздача карточек, голосовой кана (+7 more)

### Community 135 - "test_warns_routes.py"
Cohesion: 0.12
Nodes (26): applyBunkerAbility(), BunkerCardPools, BunkerCharacter, BunkerGameDetail, BunkerGameSummary, BunkerPlayerRef, BunkerSettings, fetchBunkerCardPools() (+18 more)

### Community 136 - "Supply.tsx"
Cohesion: 0.29
Nodes (9): Request, Response, wordle_get(), wordle_put(), test_settings_defaults(), test_settings_roundtrip(), get_settings(), Настройки модуля сервера с дефолтами (выключен по умолчанию).      channel_id — (+1 more)

### Community 137 - ".__init__"
Cohesion: 0.16
Nodes (25): add_topic(), delete_topic(), pick_next_topic(), Выбирает следующую тему по кругу без повторов, пока список не закончится.      В, update_topic(), test_add_update_delete_topic(), test_pick_next_topic_avoids_immediate_repeat_when_cycle_restarts(), test_pick_next_topic_cycles_without_repeats() (+17 more)

### Community 138 - "test_roles.py"
Cohesion: 0.25
Nodes (14): isolated_db(), isolated_db(), add_warn(), db_connect(), db_init(), get_active_warn_count(), get_db_path(), get_warn() (+6 more)

### Community 139 - "test_giveaway_routes.py"
Cohesion: 0.20
Nodes (9): build_lobby_embed(), BunkerLobbyView, Bot, ButtonStyle, Interaction, PLAYERS_CEIL, PLAYERS_FLOOR, Range (+1 more)

### Community 140 - "format_voice_time"
Cohesion: 0.10
Nodes (13): CreateTeamCodeModal, DraftEvent, EventNotifyModal, EventPublishSelect, Events, handle_registration(), JoinTeamCodeModal, Embed (+5 more)

### Community 141 - "test_feedback_panel_routes.py"
Cohesion: 0.31
Nodes (13): callback(), _frontend(), invite_url(), list_guilds(), login(), logout(), me(), Request (+5 more)

### Community 142 - "MafiaLobbyView"
Cohesion: 0.25
Nodes (7): build_lobby_embed(), MafiaLobbyView, ButtonStyle, Interaction, PLAYERS_CEIL, PLAYERS_FLOOR, Range

### Community 143 - "FakeResponse"
Cohesion: 0.06
Nodes (53): FakeMember, build(), _StubForbidden, _StubNotFound, test_ban_calls_discord_and_logs(), test_ban_discord_not_found_maps_to_404(), test_ban_forbidden_maps_to_403(), test_ban_invalid_json_body_returns_400() (+45 more)

### Community 144 - "FakeResponse"
Cohesion: 0.41
Nodes (13): utcnow(), build(), fresh_member(), Тесты кога «Антирейд»: выключен по умолчанию, детект всплеска, действия., test_below_threshold_does_not_trigger(), test_cooldown_prevents_immediate_retrigger(), test_disabled_by_default_does_nothing(), test_explicitly_disabled_ignores_burst() (+5 more)

### Community 145 - "test_news_routes.py"
Cohesion: 0.47
Nodes (8): _check_channel(), _check_role(), get_config(), Request, Response, update_config(), _validate_relations(), _validate_structure()

### Community 146 - "test_auto_roles_routes.py"
Cohesion: 0.33
Nodes (6): Application, Path, setup_static_routes(), test_asset_path_serves_asset_file(), test_root_path_serves_index_html(), test_unmatched_path_serves_index_html()

### Community 147 - "test_supply_routes.py"
Cohesion: 0.07
Nodes (66): force_login(), build(), test_get_auto_roles_defaults_to_empty_when_file_missing(), test_get_auto_roles_requires_auth(), test_get_auto_roles_returns_stored_values(), test_update_auto_roles_persists_valid_roles(), test_update_auto_roles_rejects_managed_role(), test_update_auto_roles_rejects_non_list_body() (+58 more)

### Community 148 - "lockdown.py"
Cohesion: 0.24
Nodes (12): build(), FakeDailyTopicCog, test_create_topic_validation(), test_get_defaults(), test_post_now(), test_post_now_no_cog(), test_post_now_requires_channel(), test_post_now_requires_topics() (+4 more)

### Community 149 - "test_xp_routes.py"
Cohesion: 0.12
Nodes (10): FakeFollowup, FakeResponse, build(), FakeFollowup, FakeInteraction, FakeResponse, Тесты /ранг: подтягивание экипированной косметики (рамка/титул) из магазина., test_rank_command_ignores_unequipped_owned_cosmetics() (+2 more)

### Community 150 - "Levels.tsx"
Cohesion: 0.22
Nodes (17): update_escalation_rule(), update_manual_warn_duration(), update_module_enabled(), automod_create_escalation(), automod_delete_escalation(), automod_get(), automod_update_enabled(), automod_update_escalation() (+9 more)

### Community 151 - "format_voice_time"
Cohesion: 0.33
Nodes (5): Lockdown, Choice, Guild, Interaction, setup()

### Community 152 - "FakeVoiceChannel"
Cohesion: 0.23
Nodes (21): После миграции один user_id может существовать на разных серверах., test_xp_add_text_and_get_scoped_per_guild(), test_xp_add_text_increments_messages_and_ts(), test_xp_members_primary_key_is_composite(), test_xp_reset_member_only_targets_one_guild(), build(), FakeInteraction, Тесты команд /xp (add/set/clear) и /leaders в XPCog — вызов через .callback(), (+13 more)

### Community 153 - "test_economy_routes.py"
Cohesion: 0.32
Nodes (13): close_event_route(), create_event(), delete_event_route(), get_event(), list_events(), notify_event_route(), Request, Response (+5 more)

### Community 154 - "FakeResponse"
Cohesion: 0.32
Nodes (12): Client, get_log_channel_id(), log_action(), log_error(), log_security(), log_unhide_action(), Color, Exception (+4 more)

### Community 155 - "_FakeMember"
Cohesion: 0.21
Nodes (5): Interaction, Invite, Member, setup(), Welcome

### Community 156 - "Casino.tsx"
Cohesion: 0.17
Nodes (20): MassAssignJob, run_mass_assign(), build(), test_mass_assign_all_except_bots_completes(), test_mass_assign_concurrent_requests_only_one_job_starts(), test_mass_assign_job_marked_failed_on_unexpected_exception(), test_mass_assign_rejects_role_above_bot(), test_mass_assign_rejects_second_job_while_running() (+12 more)

### Community 158 - "config.py"
Cohesion: 0.33
Nodes (9): test_append_event_defaults_moderator_to_none_for_automatic_events(), test_append_event_stores_all_fields(), test_append_event_trims_to_max_entries(), test_append_then_load_returns_newest_first(), test_load_events_returns_empty_list_on_corrupt_json(), test_load_events_returns_empty_list_when_file_missing(), append_event(), load_events() (+1 more)

### Community 159 - "resolve_ticket"
Cohesion: 0.13
Nodes (27): test_status_color_and_label(), status_color(), status_label(), add_custom_emoji_reaction(), ApplicationModalPart2, build_full_embed(), build_mini_embed(), build_ticket_result_embed() (+19 more)

### Community 160 - ".start_lobby"
Cohesion: 0.07
Nodes (43): ChannelInfo, createEvent(), CreateEventSpec, createReactionRole(), createStreamSubscription(), CtdConfig, deleteReactionRole(), deleteStreamSubscription() (+35 more)

### Community 161 - "economy.py"
Cohesion: 0.07
Nodes (24): EconomySettings, EconomyTopEntry, fetchEconomySettings(), fetchEconomyTop(), fetchMafiaGames(), fetchMafiaSettings(), MafiaGameSummary, MafiaSettings (+16 more)

### Community 162 - "load_dashboard_config"
Cohesion: 0.19
Nodes (20): Application, AppRunner, create_app(), start_dashboard(), FakeBot, A non-ConfigError, non-OSError failure during app construction/startup     must, On a real port-bind conflict (OSError from TCPSite.start), the     http_session, test_bracket_routes_are_registered() (+12 more)

### Community 163 - "EventDetailPanel.tsx"
Cohesion: 0.26
Nodes (9): closeEvent(), deleteEvent(), EventParticipantTeamCode, fetchEventDetail(), notifyEventParticipants(), EventDetailPanel(), Props, pollDetail (+1 more)

### Community 164 - "test_members_list.py"
Cohesion: 0.48
Nodes (6): get_auto_roles(), _get_guild_or_none(), _is_role_assignable(), Request, Response, update_auto_roles()

### Community 166 - "FakeResponse"
Cohesion: 0.24
Nodes (8): createGiveaway(), endGiveaway(), fetchGiveawayOverview(), Giveaway, GiveawayOverview, rerollGiveaway(), GiveawaysPage(), emptyOverview

### Community 167 - "test_ctd_routes.py"
Cohesion: 0.25
Nodes (11): json_error_middleware(), audit_middleware(), describe_action(), Request, Аудит действий дашборда: каждое мутирующее действие модератора пишется в stats.d, build_app(), test_describe_action_known_and_fallback(), test_failed_mutation_not_audited() (+3 more)

### Community 168 - "Giveaways.tsx"
Cohesion: 0.22
Nodes (8): ban_reason_for_api(), Embed, Guild, Message, При старте бота проверяем, нет ли пользователей в бан-листе         с причиной T, setup(), TempBan, tempban_reason()

### Community 169 - "Giveaways.tsx"
Cohesion: 0.24
Nodes (9): fetchFunSettings(), fetchWordleSettings(), FunSettings, updateFunSettings(), updateWordleSettings(), WordleSettings, FunPage(), emptySettings (+1 more)

### Community 170 - "test_feedback_panel_routes.py"
Cohesion: 0.10
Nodes (32): test_guild_t_uses_server_language(), test_module_disabled_named(), test_pick_random_returns_known_key(), test_t_falls_back_to_key_for_unknown(), test_t_falls_back_to_russian_for_unknown_lang(), test_t_formats_placeholders(), test_t_returns_english_when_requested(), test_t_returns_russian_by_default() (+24 more)

### Community 171 - "test_roles.py"
Cohesion: 0.67
Nodes (3): main(), One-off generator for locales/{ru,en}/slash.py — run from repo root., render()

### Community 173 - "test_wordle_routes.py"
Cohesion: 0.08
Nodes (31): isolated_state(), isolated_config(), isolated_settings_db(), isolated_config(), isolated_config(), isolated_state(), isolated_config(), isolated_config() (+23 more)

### Community 174 - "test_ctd_routes.py"
Cohesion: 0.43
Nodes (7): build(), CTD-настройки — привилегия мейна (Фаза 2b): роут доступен только когда активный, test_ctd_forbidden_when_active_guild_not_main(), test_ctd_requires_auth(), test_get_ctd_defaults_on_main_guild(), test_put_and_get_ctd_round_trip(), test_put_ctd_404_when_role_missing()

### Community 175 - "FakeResponse"
Cohesion: 0.27
Nodes (6): AntiRaidCog, Bot, Member, Ког «Антирейд»: автоматический Lockdown при всплеске входов новых участников.  В, setup(), JoinTracker

### Community 176 - "test_members_list.py"
Cohesion: 0.38
Nodes (10): get_settings(), daily_topic_create_topic(), daily_topic_delete_topic(), daily_topic_get(), daily_topic_post_now(), daily_topic_update_settings(), daily_topic_update_topic(), Request (+2 more)

### Community 177 - "test_antiraid_routes.py"
Cohesion: 0.07
Nodes (55): announceBunkerAbility(), apiFetch(), banMember(), BUNKER_FIELD_KEYS, BunkerFieldKey, BunkerPublicState, cancelSupply(), closeSupply() (+47 more)

### Community 180 - "test_fun_routes.py"
Cohesion: 0.39
Nodes (8): build(), isolated_config(), test_get_defaults(), test_put_auto_emoji_roundtrip_and_validation(), test_put_then_get(), test_put_validation(), test_put_zero_disables_punishment_and_cooldown(), test_requires_auth()

### Community 181 - "VCTheme"
Cohesion: 0.31
Nodes (8): build(), FakeAutoModCog, test_create_warn(), test_create_warn_validation(), test_create_warn_without_cog_still_succeeds(), test_delete_warn(), test_list_warns_empty(), test_requires_auth()

### Community 182 - "init"
Cohesion: 0.31
Nodes (9): build(), test_get_welcome_settings_defaults_to_enabled_when_file_missing(), test_get_welcome_settings_requires_auth(), test_get_welcome_settings_returns_stored_values(), test_update_welcome_settings_persists(), test_update_welcome_settings_rejects_non_boolean(), test_update_welcome_settings_rejects_non_dict_body(), test_update_welcome_settings_requires_auth() (+1 more)

### Community 183 - "pick_bunker_conditions"
Cohesion: 0.25
Nodes (9): build_game_started_embed(), pick_bunker_conditions(), pick_catastrophe(), localize_game_scenario(), merge_bunker_conditions(), merge_catastrophe(), Catastrophe + bunker conditions names/descriptions for embeds and public API., test_pick_catastrophe_and_bunker_conditions_return_known_entries() (+1 more)

### Community 184 - "DocsSearch.tsx"
Cohesion: 0.33
Nodes (4): DocNavItem, DocsSearchProps, DocsSidebarProps, GROUP_ICONS

### Community 185 - "setup_session"
Cohesion: 0.43
Nodes (6): derive_fernet_key(), Application, setup_session(), test_derive_fernet_key_differs_per_secret(), test_derive_fernet_key_is_deterministic(), test_derive_fernet_key_is_valid_fernet_key()

### Community 186 - "test_casino_routes.py"
Cohesion: 0.43
Nodes (7): build(), isolated_config(), test_get_defaults(), test_put_allows_unlimited_max_bet(), test_put_then_get(), test_put_validation(), test_requires_login()

### Community 188 - "init"
Cohesion: 0.40
Nodes (5): init(), isolated_state(), isolated_db(), isolated_state(), isolated_state()

### Community 189 - "day_number"
Cohesion: 0.60
Nodes (5): test_day_number_epoch(), date, day_number(), Номер сегодняшнего Вордла (день эпохи = №1)., today_msk()

### Community 190 - "DocsToc.tsx"
Cohesion: 0.50
Nodes (4): DocsToc(), DocsTocProps, slugify(), TocItem

## Knowledge Gaps
- **239 isolated node(s):** `EmbedMessageResult`, `FeedbackCaseField`, `EventParticipantSolo`, `EventParticipantTeamCaptain`, `EventParticipantTeamCodeMember` (+234 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FakeMember` connect `FakeResponse` to `events.py`, `Supply Module`, `Test Fake Channels`, `test_supply_routes.py`, `Test Fake Bot`, `wordle.py`, `load_events`, `Giveaways Routes`, `FakeResponse`, `test_supply_routes.py`, `lockdown.py`, `test_xp_routes.py`, `Mafia DB Tests`, `FakeVoiceChannel`, `Casino.tsx`, `Voice Rooms Routes`, `test_ctd_routes.py`, `test_wordle_routes.py`, `test_ctd_routes.py`, `test_fun_routes.py`, `VCTheme`, `test_casino_routes.py`, `Supply.tsx`, `MassAssignModal.tsx`, `ChannelInfo`, `MafiaLobbyView`, `Giveaways.tsx`, `FakeAsset`, `xp_card.py`, `format_voice_time()`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `force_login()` connect `test_supply_routes.py` to `Supply Module`, `load_events`, `Test Fake Bot`, `Giveaways Routes`, `FakeResponse`, `lockdown.py`, `Mafia DB Tests`, `Casino.tsx`, `Voice Rooms Routes`, `test_ctd_routes.py`, `test_wordle_routes.py`, `test_ctd_routes.py`, `test_fun_routes.py`, `VCTheme`, `test_casino_routes.py`, `ChannelInfo`, `MafiaLobbyView`, `Giveaways.tsx`, `config.py`, `FakeAsset`, `xp_card.py`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Why does `t()` connect `test_feedback_panel_routes.py` to `Game Settings & Bunker DB`, `Test Fake Bot`, `Tournament Brackets`, `Feedback Cases`, `Giveaways Routes`, `test_giveaway_routes.py`, `Automod Filter Core`, `format_voice_time`, `MafiaLobbyView`, `Server Event Logging`, `Moderation Routes`, `Bunker Discord Cog`, `Stream Notifications`, `Feedback Panel Tests`, `Reaction Roles Tests`, `Streams API Client`, `resolve_ticket`, `Mafia Discord Cog`, `Events Route Tests`, `Audit Log & Stats DB`, `Giveaway Cog`, `Event Builder UI`, `Family Core Tests`, `XP Core Tests`, `Event Publish Tests`, `Family Birthdays`, `Anti-Spam Cog`, `pick_bunker_conditions`, `xp.py`, `.__init__()`, `Interaction`, `ensure_owner()`, `test_access.py`, `RosterCog`, `reaction_roles.py`, `PublicBunkerAction.tsx`, `Welcome`, `test_fun_routes.py`, `Button.tsx`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 28 inferred relationships involving `FakeMember` (e.g. with `DashboardConfig` and `_StubForbidden`) actually correct?**
  _`FakeMember` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `FakeGuild` (e.g. with `DashboardConfig` and `_StubForbidden`) actually correct?**
  _`FakeGuild` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `FakeBot` (e.g. with `DashboardConfig` and `_StubForbidden`) actually correct?**
  _`FakeBot` has 27 INFERRED edges - model-reasoned connections that need verification._
- **What connects `EmbedMessageResult`, `FeedbackCaseField`, `EventParticipantSolo` to the rest of the system?**
  _239 weakly-connected nodes found - possible documentation gaps or missing edges._