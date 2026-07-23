# Graph Report - Cheterin_Bot_Dashboard  (2026-07-23)

## Corpus Check
- 553 files · ~318,608 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5567 nodes · 15048 edges · 226 communities (203 shown, 23 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 211 edges (avg confidence: 0.57)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ff5f910b`
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
- Reaction Roles Client
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
- renderWithI18n.tsx
- Welcome
- test_mafia_routes.py
- test_warns_routes.py
- test_xp_routes.py
- CTD
- setup_static_routes()
- FakeAsset
- plugins
- DocsSearch.tsx
- access_middleware.py
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
- EmbedBuilder.tsx
- Button.tsx
- events.py
- wordle_card.py
- events.py
- load_events
- test_supply_routes.py
- ru.ts
- wordle.py
- test_warns_routes.py
- Supply.tsx
- .__init__
- Docs.tsx
- EventDetailPanel.tsx
- format_voice_time
- test_feedback_panel_routes.py
- setup_session
- FakeResponse
- FakeResponse
- test_news_routes.py
- test_auto_roles_routes.py
- test_supply_routes.py
- lockdown.py
- test_xp_routes.py
- mafia.py
- format_voice_time
- FakeVoiceChannel
- Fun.tsx
- FakeResponse
- _FakeMember
- Casino.tsx
- lang_for
- AntiRaidCog
- resolve_ticket
- welcome.py
- test_auto_roles_routes.py
- load_dashboard_config
- EventDetailPanel.tsx
- test_members_list.py
- test_button_config.py
- test_welcome_routes.py
- test_ctd_routes.py
- Giveaways.tsx
- birthdays_db.py
- test_feedback_panel_routes.py
- test_roles.py
- test_access.py
- test_wordle_routes.py
- casino_db.py
- Mafia.tsx
- test_ctd_routes.py
- EmbedBuilder.tsx
- Welcome.tsx
- __init__.py
- test_auto_roles_routes.py
- test_supply_routes.py
- Docs.tsx
- auto_roles.py
- ctd.py
- resolve_ticket
- CustomCommandsCog
- test_antiraid_cog.py
- test_feedback_panel_routes.py
- TimedRolesCog
- BracketView.tsx
- wordle_core.py
- pick_bunker_conditions
- format_voice_time
- resolve_ticket
- ScheduledMessagesCog
- test_feedback_panel_routes.py
- FakeResponse
- useLanguage
- setup_session
- test_supply_routes.py
- save_config
- SupplyView
- get_settings
- AntiRaidCog
- test_fun_routes.py
- lang_for
- board_lines
- _recent_audit_entry
- day_number
- DocsToc.tsx
- guild_context.py
- Dropdown.tsx
- result_score_text
- Row
- Choice
- Path
- Invite
- datetime
- Any
- TextChannel
- ClientSession
- View
- VoiceChannel
- VoiceState

## God Nodes (most connected - your core abstractions)
1. `force_login()` - 354 edges
2. `FakeMember` - 326 edges
3. `FakeGuild` - 259 edges
4. `FakeBot` - 236 edges
5. `apiFetch()` - 162 edges
6. `FakeChannel` - 131 edges
7. `FakeRole` - 114 edges
8. `get()` - 104 edges
9. `jsonInit()` - 95 edges
10. `make_moderation_app()` - 93 edges

## Surprising Connections (you probably didn't know these)
- `Unified settings.db Per-Guild Storage` --references--> `get_settings()`  [INFERRED]
  MULTIGUILD_PLAN.md → bunker_core.py
- `Phase 2.3: OAuth Guilds Scope and Server Selection` --references--> `callback()`  [EXTRACTED]
  MULTIGUILD_PLAN.md → dashboard/backend/auth.py
- `Phase 2.4: Bot Detached from GUILD_ID` --references--> `ChetBot`  [EXTRACTED]
  MULTIGUILD_PLAN.md → main.py
- `CTD Main-Guild Gate` --references--> `CTD`  [EXTRACTED]
  MULTIGUILD_PLAN.md → memobb.py
- `BlackjackView` --uses--> `CasinoCog`  [INFERRED]
  blackjack.py → casino.py

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

## Communities (226 total, 23 thin omitted)

### Community 0 - "Game Settings & Bunker DB"
Cohesion: 0.05
Nodes (29): FakeAsset, _FakeChannelType, FakeColor, FakeComponentRow, FakeCustomEmoji, FakeGuildInner, FakeMessage, FakePermissions (+21 more)

### Community 1 - "Supply Module"
Cohesion: 0.13
Nodes (41): _display_name(), _finalize(), Request, Response, _serialize_supply(), supply_cancel(), supply_close(), supply_create() (+33 more)

### Community 2 - "Dashboard App Bootstrap"
Cohesion: 0.14
Nodes (22): AutomodFilter, AutomodPunishment, AutomodSettings, createEscalationRule(), deleteEscalationRule(), EscalationAction, EscalationRule, fetchAutomod() (+14 more)

### Community 3 - "Test Fake Channels"
Cohesion: 0.08
Nodes (37): CustomEmoji, decideFamilyTicket(), deleteCardBg(), deleteFamilyBirthday(), FamilyBirthday, FamilyRosterGroup, FamilySettings, FamilyTicket (+29 more)

### Community 4 - "API Client Types"
Cohesion: 0.02
Nodes (111): announceBunkerAbility(), AntiRaidSettings, AutoRolesSettings, BirthdayEntry, BracketStandingsRow, BUNKER_FIELD_KEYS, BunkerAbilityAnnouncement, BunkerAdditionalInfo (+103 more)

### Community 5 - "Test Fake Bot"
Cohesion: 0.05
Nodes (70): FakeBot, FakeGuild, FakeThread, make_client_app(), test_guild_unavailable_gets_503(), test_member_not_in_guild_gets_403(), test_member_with_access_reaches_handler(), test_member_without_access_role_gets_403() (+62 more)

### Community 6 - "Automod Route Tests"
Cohesion: 0.13
Nodes (15): LanguageContextValue, dictionaries, translate(), activity, admin, auth, common, community (+7 more)

### Community 7 - "Tournament Brackets"
Cohesion: 0.06
Nodes (64): create_bracket(), create_bracket_v2(), _de_get_match(), _de_match(), _de_recompute_match(), _de_resolve(), extract_entries_from_event(), find_by_share_token() (+56 more)

### Community 8 - "Feedback Cases"
Cohesion: 0.15
Nodes (15): add_reviewers(), build_mentions(), close_case(), create_feedback_case(), FeedbackDecisionView, FeedbackMenu, FeedbackModal, FeedbackView (+7 more)

### Community 9 - "Giveaways Routes"
Cohesion: 0.08
Nodes (55): _display_name(), giveaways_create(), giveaways_end(), giveaways_overview(), giveaways_reroll(), Request, Response, _serialize_giveaway() (+47 more)

### Community 10 - "Automod Cog"
Cohesion: 0.06
Nodes (43): AutoMod, _consecutive_run_length(), BaseException, Bot, Guild, Interaction, Member, Message (+35 more)

### Community 11 - "Server Event Logging"
Cohesion: 0.15
Nodes (12): _Role, _clip(), Color, Embed, Guild, GuildChannel, Interaction, Invite (+4 more)

### Community 12 - "Automod Filter Core"
Cohesion: 0.08
Nodes (42): _default_filter(), _default_notify_template(), detect_bad_words(), detect_caps_lock(), detect_emoji_spam(), detect_invites(), detect_links(), detect_mentions() (+34 more)

### Community 13 - "Test Fake Members"
Cohesion: 0.20
Nodes (35): eliminate_player(), build(), _character(), _setup_game(), test_ability_already_used(), test_ability_dead_player(), test_ability_game_not_active(), test_ability_happy_path_marks_card_used_and_announces() (+27 more)

### Community 14 - "Daily Topic Module"
Cohesion: 0.11
Nodes (41): add_topic(), already_posted_today(), delete_topic(), get_settings(), get_today_post_time(), is_valid_time(), mark_posted_today(), _normalized() (+33 more)

### Community 15 - "API Client Functions"
Cohesion: 0.05
Nodes (42): BlackjackGame, _build_deck(), can_double(), card_rank(), card_suit(), _deal_card(), dealer_play(), format_hand() (+34 more)

### Community 16 - "Bunker Game Core"
Cohesion: 0.07
Nodes (29): default_bunker_capacity(), get_settings(), has_moderator_access(), is_game_over(), Большинство голосов за исключение; ничья среди лидеров — никто не исключён., Настройки модуля сервера с дефолтами (выключен по умолчанию)., Половина игроков (округление вниз, минимум 1) — если ведущий не задал своё число, resolve_expulsion_vote() (+21 more)

### Community 17 - "Moderation Routes"
Cohesion: 0.23
Nodes (25): _assignable_roles(), ban_member(), dashboard_reason(), _get_guild_or_none(), get_moderation_log(), _get_target_or_response(), grant_role(), kick_member() (+17 more)

### Community 18 - "Bunker Discord Cog"
Cohesion: 0.06
Nodes (72): ApiError, deleteVoiceRoom(), fetchAntiRaidSettings(), fetchAutoRoles(), fetchCasinoLeaderboard(), fetchCasinoSettings(), fetchFeedbackCaseDetail(), fetchFeedbackPanelSettings() (+64 more)

### Community 19 - "Mass Role Assignment"
Cohesion: 0.07
Nodes (37): DashboardUser, fetchCurrentUser(), fetchInviteUrl(), fetchManageableGuilds(), fetchPublicLeaderboard(), fetchSuperAdminGuilds(), loginUrl(), logout() (+29 more)

### Community 20 - "Embed Builder Routes"
Cohesion: 0.11
Nodes (36): test_build_embed_omits_color_when_absent(), test_build_embed_sets_author_footer_image_thumbnail(), test_build_embed_sets_basic_fields(), test_build_embed_sets_fields(), test_build_embed_sets_timestamp(), test_delete_template_missing_returns_false(), test_delete_template_removes_only_target_and_guild(), test_embed_to_spec_returns_empty_color_when_absent() (+28 more)

### Community 21 - "Bot Entrypoint & Auth Middleware"
Cohesion: 0.14
Nodes (26): add_escalation_rule(), delete_escalation_rule(), update_escalation_rule(), get_settings(), mark_announced(), Birthday calendar settings: channel + optional ping role., save_settings(), test_escalation_crud() (+18 more)

### Community 22 - "Frontend Package Deps"
Cohesion: 0.04
Nodes (46): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, tailwindcss, @tailwindcss/vite, devDependencies (+38 more)

### Community 23 - "Lockdown API Client"
Cohesion: 0.20
Nodes (22): isolated_config(), test_load_categories_returns_empty_dict_when_file_missing(), test_migrate_from_env_if_needed_creates_config_from_env(), test_migrate_from_env_if_needed_skips_when_env_vars_missing(), test_migrate_from_env_if_needed_skips_when_file_already_exists(), test_save_then_load_round_trip(), test_validate_category_spec_accepts_valid_spec(), test_validate_category_spec_allows_own_case_prefix_on_edit() (+14 more)

### Community 24 - "Mafia DB Tests"
Cohesion: 0.08
Nodes (20): fetchPublicMafia(), MafiaPublicState, submitMafiaAction(), submitMafiaVote(), baseGameSummary, emptySettings, mockPools, emptyLeaderboard (+12 more)

### Community 25 - "Mafia Core Tests"
Cohesion: 0.08
Nodes (37): _FakeMember, _FakePermissions, isolated_config(), test_assign_roles_matches_scale_and_covers_all_players(), test_check_win_condition_mafia_wins_at_parity(), test_check_win_condition_no_winner_yet(), test_check_win_condition_town_wins_when_no_mafia(), test_get_settings_defaults() (+29 more)

### Community 26 - "Stream Notifications"
Cohesion: 0.10
Nodes (24): ClientSession, _public_sub(), Request, Response, streams_create(), streams_delete(), streams_list(), streams_update() (+16 more)

### Community 27 - "Feedback Panel Tests"
Cohesion: 0.11
Nodes (29): bet_error(), flip_coin(), get_settings(), payout_amount(), Ядро модуля «Казино»: слоты, монетка и блэкджек на серверную валюту.  Без импорт, Настройки модуля сервера с дефолтами (выключен по умолчанию)., None — ставка допустима, иначе текст ошибки для игрока., Выигрыш с учётом преимущества казино (округление вниз). (+21 more)

### Community 28 - "Reaction Roles Tests"
Cohesion: 0.13
Nodes (32): create_reaction_role(), delete_reaction_role(), _get_guild_or_none(), _is_role_assignable(), list_channels(), list_emojis(), list_reaction_roles(), Request (+24 more)

### Community 29 - "Streams API Client"
Cohesion: 0.13
Nodes (27): FakeMember, build(), FakeFollowup, FakeInteraction, Тесты кога слэш-команд модерации: /ban /kick /unban /clear.  Команды вызываютс, test_ban_forbidden_reports_ephemeral_error(), test_ban_invalid_duration_format(), test_ban_permanent_default() (+19 more)

### Community 30 - "Voice Rooms Routes"
Cohesion: 0.25
Nodes (12): build(), FakeVoiceChannel, Роуты проверяют isinstance(channel, discord.VoiceChannel) — подменяем на утиную, test_delete_room(), test_delete_room_not_found(), test_delete_room_rejects_other_guild(), test_panel_publish(), test_requires_auth() (+4 more)

### Community 31 - "XP API Client"
Cohesion: 0.08
Nodes (51): isolated_db(), _create_legacy_schema(), isolated_db(), Тесты stats_db: per-guild изоляция XP/войс/аудита и миграция старой схемы.  Фаза, Схема до Фазы 2.2а: без guild_id (как в проде на мейн-сервере)., После миграции один user_id может существовать на разных серверах., test_audit_add_list_count_scoped_per_guild(), test_audit_list_and_count_filter_by_search() (+43 more)

### Community 32 - "Mafia Discord Cog"
Cohesion: 0.13
Nodes (20): build_game_started_embed(), build_lobby_cancelled_embed(), build_lobby_embed(), build_lynch_result_embed(), build_morning_embed(), build_result_embed(), build_vote_embed(), _frontend_url() (+12 more)

### Community 33 - "Feedback API Client"
Cohesion: 0.08
Nodes (21): decideFeedbackCase(), fetchFeedbackCases(), fetchLockdownStatus(), fetchMassAssignStatus(), fetchMembers(), fetchModerationLog(), LockdownStatus, MassAssignStatus (+13 more)

### Community 34 - "Family DB Tests"
Cohesion: 0.12
Nodes (42): _create_legacy_schema(), isolated_db(), Тесты family_db: per-guild ростер/заявки/дни рождения + миграция старой схемы., Схема до Фазы 2.2б: синглтоны roster_msg/birthday_msg (id=1), single-PK     pen, test_birthday_message_roundtrip_and_isolation(), test_birthday_roundtrip_and_queries(), test_list_and_count_tickets_scoped_and_filtered(), test_migration_assigns_legacy_rows_to_main_guild() (+34 more)

### Community 35 - "Events & Embeds Client"
Cohesion: 0.14
Nodes (30): Any, _cmd(), _grp(), _key(), Apply slash command localizations for every cog (Phase 3.2(3))., register_automod(), register_birthdays(), register_blackjack() (+22 more)

### Community 36 - "Lockdown Routes"
Cohesion: 0.18
Nodes (14): createFeedbackCategory(), deleteFeedbackCategory(), FeedbackCategoryFieldSpec, FeedbackCategorySpec, fetchFeedbackCategories(), publishFeedbackPanel(), updateFeedbackCategory(), sampleSpec (+6 more)

### Community 37 - "Events Route Tests"
Cohesion: 0.15
Nodes (23): has_running_job(), MassAssignJob, run_mass_assign(), build(), test_mass_assign_all_except_bots_completes(), test_mass_assign_allows_job_when_other_guild_running(), test_mass_assign_concurrent_requests_only_one_job_starts(), test_mass_assign_job_marked_failed_on_unexpected_exception() (+15 more)

### Community 38 - "Mafia Public Route Tests"
Cohesion: 0.06
Nodes (98): _display_name(), _is_id(), mafia_games_list(), mafia_get(), mafia_public_action(), mafia_public_state(), mafia_public_vote(), mafia_put() (+90 more)

### Community 39 - "Family Tickets"
Cohesion: 0.08
Nodes (31): pick_bunker_conditions(), pick_catastrophe(), English card pools for the Bunker survival tabletop game., Данные для игры «Бункер»: возраст, телосложение, профессии, хобби, здоровье, стр, additional_info_en_template(), _en_item(), get_card_pools(), localize_character() (+23 more)

### Community 40 - "Button Forms"
Cohesion: 0.12
Nodes (12): ButtonCreate, DynamicQuestionsModal, _get_allowed_role_ids(), _load_buttons_config(), BaseException, Interaction, Удаляет устаревшие записи кулдаунов., Возвращает оставшиеся секунды если кулдаун активен, иначе None. (+4 more)

### Community 41 - "Audit Log & Stats DB"
Cohesion: 0.16
Nodes (13): isolated_config(), Тесты ядра Вордла: целостность словаря, оценка догадок, слово дня, настройки., test_evaluate_all_green(), test_evaluate_duplicate_letters_consume_stock(), test_evaluate_green_priority_over_yellow(), test_evaluate_yellow_and_gray(), test_letter_hints(), test_word_for_day_deterministic_and_from_answers() (+5 more)

### Community 42 - "Giveaway Cog"
Cohesion: 0.11
Nodes (13): generate_embed(), GiveawayCog, GiveawayView, Bot, Button, Embed, Interaction, Range (+5 more)

### Community 43 - "Brackets Client Tests"
Cohesion: 0.21
Nodes (22): list_alive_players(), bunker_apply_ability(), bunker_card_pools(), bunker_game_detail(), bunker_games_list(), bunker_get(), bunker_patch_player(), bunker_public_reveal() (+14 more)

### Community 44 - "Bunker API Client"
Cohesion: 0.25
Nodes (16): build(), test_birthday_set_invalid_date(), test_birthday_set_unknown_member(), test_birthdays_crud(), test_get_defaults(), test_put_then_get(), test_put_validation(), test_requires_auth() (+8 more)

### Community 45 - "Automod API Client"
Cohesion: 0.11
Nodes (26): BotConfig, EmbedFieldSpec, EmbedSpec, fetchConfig(), fetchWelcomeSettings(), updateAutoRoles(), updateConfig(), updateWelcomeSettings() (+18 more)

### Community 47 - "Event Builder UI"
Cohesion: 0.21
Nodes (23): assign_character(), create_game(), build(), _sample_character(), test_apply_ability_announcement(), test_apply_ability_announcement_not_found(), test_apply_ability_rejects_other_guild(), test_card_pools_endpoint_requires_auth() (+15 more)

### Community 48 - "Family Core Tests"
Cohesion: 0.13
Nodes (19): _FakeGuild, _FakeGuildRef, _FakeMember, isolated_config(), test_build_birthday_text_groups_by_month_and_resolves_mentions(), test_can_manage_tickets_requires_configured_role(), test_has_staff_access_admin_bypasses_role_check(), test_has_staff_access_via_role() (+11 more)

### Community 49 - "XP Core Tests"
Cohesion: 0.09
Nodes (36): xp_member_set(), isolated_config(), test_deserved_roles(), test_get_settings_voice_new_fields_defaults(), test_level_formula_monotonic(), test_level_from_xp_roundtrip(), test_level_progress(), test_render_announce() (+28 more)

### Community 50 - "Event Publish Tests"
Cohesion: 0.10
Nodes (40): close_event_route(), create_event(), delete_event_route(), get_event(), list_events(), notify_event_route(), Request, Response (+32 more)

### Community 51 - "TypeScript Config"
Cohesion: 0.08
Nodes (23): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+15 more)

### Community 52 - "Bot Config Store"
Cohesion: 0.10
Nodes (52): add_player(), add_round_event(), connect(), count_players(), create_ability_announcement(), get_ability_announcement(), get_active_game_in_channel(), get_db_path() (+44 more)

### Community 53 - "Family Birthdays"
Cohesion: 0.15
Nodes (11): BirthdayCog, build_birthday_embed(), BaseException, Bot, Embed, Guild, Interaction, User (+3 more)

### Community 54 - "Anti-Spam Cog"
Cohesion: 0.09
Nodes (42): test_resolve_banner_url_returns_empty_when_unset(), test_resolve_banner_url_uses_custom_setting(), test_build_goodbye_uses_custom_text(), test_default_dm_embed_uses_channel_placeholders(), test_resolve_dm_footer_uses_custom_text(), test_resolve_dm_thumbnail_returns_default_imgur_without_custom(), test_resolve_dm_thumbnail_uses_custom_fallback(), test_substitute_placeholders() (+34 more)

### Community 55 - "news.py"
Cohesion: 0.15
Nodes (18): _is_id_like(), news_get(), news_put(), Request, Response, get_channel_map(), get_settings(), _main_guild_id() (+10 more)

### Community 56 - "events.py"
Cohesion: 0.14
Nodes (14): Ког «Блэкджек»: интерактивная игра против дилера на серверную валюту.  Требует, casino_top_command(), CasinoCog, CasinoLeaderboardView, check_loss_roles(), _coinflip_label(), Bot, Button (+6 more)

### Community 57 - "test_feedback_routes.py"
Cohesion: 0.08
Nodes (39): BirthdaysPayload, ChannelInfo, createReactionRole(), createStreamSubscription(), CtdConfig, deleteBirthday(), deleteReactionRole(), deleteStreamSubscription() (+31 more)

### Community 58 - "FeedbackCategories.tsx"
Cohesion: 0.27
Nodes (7): _fmt_voice(), LeaderboardView, Button, Guild, Interaction, Формат времени голоса Ч:ММ:СС (как в JuniperBot)., Интерактивный лидерборд: сортировка по Опыту / Голосу + пагинация.

### Community 59 - "Docs.tsx"
Cohesion: 0.11
Nodes (20): can_manage_guild_permissions(), has_dashboard_access(), has_manage_server(), has_super_admin_access(), manageable_guilds(), Контроль доступа к дашборду (модель MEE6, Фаза 2.3).  Доступ к серверу = право, DEPRECATED (Фаза 1, роль-модель). Оставлено до перевода auth/middleware на, Доступ к настройкам сервера: Manage Server или Administrator на этой гильдии. (+12 more)

### Community 60 - "voice_rooms.py"
Cohesion: 0.15
Nodes (14): BlackjackView, build_embed(), Button, Embed, Interaction, Member, User, Кнопки игры: Ещё карту / Стоп / Удвоить. (+6 more)

### Community 61 - "XPCog"
Cohesion: 0.13
Nodes (14): XP_ADMIN_MAX, XP_ADMIN_MIN, channel_allowed(), member_has_ignored_role(), Bot, Embed, Member, Message (+6 more)

### Community 62 - "auth.py"
Cohesion: 0.52
Nodes (6): get_welcome_settings(), Request, Response, _serialize_messages(), update_welcome_settings(), _validate_messages_payload()

### Community 63 - "resolve_guild_member()"
Cohesion: 0.31
Nodes (13): callback(), _frontend(), invite_url(), list_guilds(), login(), logout(), me(), Request (+5 more)

### Community 64 - "xp.py"
Cohesion: 0.15
Nodes (26): Request, Response, voice_stats(), _int_in(), _is_id_list(), _public_leaderboard_payload(), Request, Response (+18 more)

### Community 65 - "test_feedback_category_routes.py"
Cohesion: 0.12
Nodes (25): reset_settings_db(), isolated_db(), Тесты settings_migration: перенос плоских JSON в settings_db, идемпотентность., test_migrate_all_is_idempotent_across_two_runs(), test_migrate_all_migrates_existing_files_only(), test_migrate_one_missing_file_is_noop(), test_migrate_one_moves_data_and_renames_file(), test_migrate_one_skips_when_already_migrated() (+17 more)

### Community 66 - "Supply.tsx"
Cohesion: 0.14
Nodes (32): build(), _poll_create_spec(), _poll_event(), test_close_event_route_404(), test_close_event_route_requires_auth(), test_close_event_route_success(), test_create_event_404_when_channel_missing(), test_create_event_404_when_role_reward_missing() (+24 more)

### Community 67 - "MassAssignModal.tsx"
Cohesion: 0.11
Nodes (20): _has_legacy_role_access(), Переходный грант по роли на активном сервере (если задан DASHBOARD_ACCESS_ROLE_I, Гейт доступа к серверу (Фаза 2.3): сессия → активный сервер → Manage Server., Гейт для списка серверов бота — намеренно хардкод-роль, см. access.py., require_dashboard_access(), require_super_admin(), json_error_middleware(), casino_get() (+12 more)

### Community 68 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+11 more)

### Community 69 - ".__init__()"
Cohesion: 0.13
Nodes (22): require_dashboard_access Middleware, Phase 2.4: Bot Detached from GUILD_ID, Bilingual Bunker Game Cards, CTD Main-Guild Gate, Phase 2.2: Guild Dimension for Module Data, Phase 3: RU/EN i18n Infrastructure, MAIN_GUILD_ID Constant, Manage Server Access Model (+14 more)

### Community 70 - "VoiceTracker"
Cohesion: 0.14
Nodes (8): is_active(), BaseException, Bot, VoiceState, Войс-трекер: единый учёт голосовых сессий.  Кормит сразу два модуля: - статис, setup(), VoiceSession, VoiceTracker

### Community 71 - "Interaction"
Cohesion: 0.13
Nodes (18): build_expulsion_result_embed(), build_game_started_embed(), build_lobby_cancelled_embed(), build_lobby_embed(), build_result_embed(), BunkerLobbyView, _character_summary(), _frontend_url() (+10 more)

### Community 72 - "ensure_owner()"
Cohesion: 0.07
Nodes (44): Тесты ядра экономики: курс от XP, комиссии, валидация ставок, хук award_for_xp., test_award_for_xp_disabled_gives_nothing(), test_bet_error_cases(), test_bet_error_unlimited_when_max_zero(), test_claim_daily_bonus_consecutive_day_extends_streak(), test_claim_daily_bonus_first_time(), test_claim_daily_bonus_gap_resets_streak(), test_claim_daily_bonus_same_day_rejected() (+36 more)

### Community 73 - "family.py"
Cohesion: 0.29
Nodes (17): _decide_ticket(), _display_name(), family_birthday_delete(), family_birthday_set(), family_birthdays_list(), family_get(), family_put(), family_roster() (+9 more)

### Community 74 - "test_family_routes.py"
Cohesion: 0.09
Nodes (47): _create_legacy_schema(), Тесты economy_db: атомарные списания, переводы, топ, журнал, per-guild изоляция., test_add_ignores_non_positive(), test_cosmetics_isolated_per_guild(), test_daily_bonus_default_when_missing(), test_daily_bonus_roundtrip_and_update(), test_equip_roundtrip_and_clear(), test_grant_and_own_cosmetic() (+39 more)

### Community 75 - "test_access.py"
Cohesion: 0.11
Nodes (20): Request, Response, serverlog_get(), serverlog_put(), test_format_stay_duration(), test_format_stay_duration_negative_clamped_to_zero(), event_channel_id(), format_stay_duration() (+12 more)

### Community 76 - "test_config_routes.py"
Cohesion: 0.21
Nodes (20): build(), build_with_channels(), _case(), test_decide_feedback_case_404_when_unknown(), test_decide_feedback_case_409_when_already_decided(), test_decide_feedback_case_409_when_category_deleted(), test_decide_feedback_case_approves_and_persists(), test_decide_feedback_case_rejects_non_boolean_approved() (+12 more)

### Community 77 - "RosterCog"
Cohesion: 0.21
Nodes (8): generate_roster_text(), Bot, Guild, Interaction, Live-ростер семьи: список участников по настроенным ролям.  Портировано из FamQ, Debounce: аккумулирует изменения и обновляет сообщение через 10 секунд., RosterCog, setup()

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
Cohesion: 0.19
Nodes (15): FakePayload, _setup_config(), test_cleanup_missing_messages_keeps_entries_for_existing_messages(), test_handle_reaction_change_add_grants_role_using_payload_member(), test_handle_reaction_change_ignores_bots_own_reaction(), test_handle_reaction_change_ignores_unconfigured_message(), test_handle_reaction_change_ignores_unmatched_emoji(), test_handle_reaction_change_remove_falls_back_to_fetch_member_when_not_cached() (+7 more)

### Community 82 - "mafia.py"
Cohesion: 0.06
Nodes (63): activateLockdown(), apiFetch(), banMember(), cancelSupply(), closeSupply(), createCustomCommand(), createDailyTopic(), createMemberWarn() (+55 more)

### Community 83 - "events.py"
Cohesion: 0.18
Nodes (8): CTD, CTDCloseView, CTDView, _is_main_guild(), BaseException, Button, Interaction, setup()

### Community 84 - "ChetBot"
Cohesion: 0.15
Nodes (14): Web Dashboard Index HTML, React Root Mount Element, React Entry Point Script, ChetBot, ChetBot Web Dashboard, ChetBot Official Documentation, aiohttp Dependency, aiohttp-session Dependency (+6 more)

### Community 85 - "ChannelInfo"
Cohesion: 0.22
Nodes (17): FakeAuditLogEntry, FakeAuditLogExtra, Одна запись аудита для guild.audit_logs() — только то, что нужно     serverlog., build(), enable(), last_embed(), Embed, Тесты кога «Логирование»: стиль эмбедов (description+footer+thumbnail), формати (+9 more)

### Community 86 - "MafiaLobbyView"
Cohesion: 0.16
Nodes (9): CLEAR_MAX, CLEAR_MIN, ModerationCommandsCog, Bot, Interaction, Range, User, Ког слэш-команд модерации: /ban /kick /mute /unmute /unban /clear.  Каждое дейст (+1 more)

### Community 87 - "voice_logs.py"
Cohesion: 0.10
Nodes (41): isolated_state(), test_announce_nobody_won_reveals_word(), isolated_db(), Тесты wordle_db: игры дня, статистика со стриками, мета сервера (per-guild)., test_add_guess_accumulates_and_finishes(), test_daily_games_isolated_per_guild(), test_group_streak_gap_resets(), test_group_streak_grows_and_resets() (+33 more)

### Community 88 - "test_auto_roles_routes.py"
Cohesion: 0.23
Nodes (17): build(), build_with_guild(), _full_config(), PUT /api/config не должен затирать ключи других разделов (авто-роли, приветствия, test_get_config_requires_auth(), test_get_config_returns_defaults_when_file_missing(), test_get_config_returns_stored_values(), test_put_config_preserves_foreign_keys() (+9 more)

### Community 89 - "Giveaways.tsx"
Cohesion: 0.08
Nodes (64): FakeChannel, FakeRole, build(), test_create_embed_message_allows_content_only(), test_create_embed_message_channel_not_found(), test_create_embed_message_checks_channel_before_role_assignability(), test_create_embed_message_discord_error_logged(), test_create_embed_message_rejects_blank_content_and_empty_embed() (+56 more)

### Community 90 - "renderWithI18n.tsx"
Cohesion: 0.21
Nodes (20): add_command(), delete_command(), get_settings(), match_message(), _normalized(), Per-guild custom commands / auto-replies (exact or contains match)., Return first matching enabled command for message content, or None., update_command() (+12 more)

### Community 91 - "Welcome"
Cohesion: 0.09
Nodes (10): command_reason(), format_duration(), normalize_reason(), parse_duration(), parse_mute_duration(), Ядро команд модерации (/ban /kick /unban /clear): парсинг и форматирование срока, Секунды из строки вида 10m/2h/7d/30s. ValueError с понятным текстом при неверном, Как parse_duration, но с проверкой лимита Discord в 28 дней. (+2 more)

### Community 93 - "test_mafia_routes.py"
Cohesion: 0.33
Nodes (9): language_get(), language_put(), Request, Response, test_language_core_set_and_get(), get_language(), get_settings(), Язык бота для сервера (Фаза 3.1 MULTIGUILD_PLAN.md).  Хранится в settings.db ( (+1 more)

### Community 94 - "test_warns_routes.py"
Cohesion: 0.21
Nodes (20): DiscordOAuthError, exchange_code_for_token(), fetch_discord_identity(), fetch_user_guilds(), ClientSession, Exception, Список серверов пользователя (`/users/@me/guilds`, требует scope `guilds`)., refresh_access_token() (+12 more)

### Community 95 - "test_xp_routes.py"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does SelectOption connect Mafia Game Engine to Discord Embed Builder, Supply Cog Tests?, Source Nodes

### Community 96 - "CTD"
Cohesion: 0.13
Nodes (11): ModuleConfigPanelProps, EMPTY_BOT_CONFIG, ModuleConfigVariant, emptySettings, baseSettings(), FILTER_KEYS, FILTER_LABELS_RU, makeFilter() (+3 more)

### Community 97 - "setup_static_routes()"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does force_login() connect Mock Services & Unit Tests to a wide array of system modules and tests?, Source Nodes

### Community 98 - "FakeAsset"
Cohesion: 0.06
Nodes (46): init(), build(), isolated_config(), test_get_defaults_disabled(), test_put_then_get(), test_put_validation(), test_requires_login(), isolated_config() (+38 more)

### Community 99 - "plugins"
Cohesion: 0.22
Nodes (8): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema, oxc, typescript, warn

### Community 100 - "DocsSearch.tsx"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Are the inferred relationships involving mock objects (FakeMember, FakeGuild, FakeBot, FakeRole) with DashboardConfig and _StubForbidden correct?, Source Nodes

### Community 101 - "access_middleware.py"
Cohesion: 0.23
Nodes (18): Request, Response, sticky_delete(), sticky_get(), sticky_settings(), sticky_upsert(), test_disabled_module_hides_sticky(), test_get_settings_defaults() (+10 more)

### Community 102 - "auto_roles.py"
Cohesion: 0.18
Nodes (5): MafiaCog, Guild, Вызывается дашбордом после каждой отправки ночного действия., Вызывается дашбордом после каждой отправки дневного голоса., _resolve_alive_members()

### Community 103 - "icons.svg"
Cohesion: 0.38
Nodes (6): Bluesky Icon, Discord Icon, Documentation Icon, GitHub Icon, Social Icon, X Icon

### Community 104 - "format_voice_time()"
Cohesion: 0.13
Nodes (25): BlackjackCog, Bot, setup(), get_stats(), build(), FakeInteraction, FakeMessage, FakeResponse (+17 more)

### Community 105 - "DocsToc.tsx"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: What connects schema, typescript, oxc to the rest of the system?, Source Nodes

### Community 108 - "Hero Image Graphic"
Cohesion: 1.00
Nodes (3): Hero Image Graphic, Cheterin Isometric Branding Concept, Layered Isometric Architecture Illustration

### Community 111 - "DocsSearch.tsx"
Cohesion: 0.18
Nodes (12): Messageable, _config_int(), generate_embed(), get_reminder_minutes(), _main_guild_id(), Bot, Color, Embed (+4 more)

### Community 112 - "test_fun_routes.py"
Cohesion: 0.20
Nodes (14): Тесты рендера карточки ранга: базовый рендер, кастомная рамка и титул., test_hex_to_rgb(), test_render_rank_card_long_title_does_not_crash(), test_render_rank_card_with_custom_frame_and_title(), test_render_rank_card_without_cosmetics_produces_png(), _background(), _circle_avatar(), _font() (+6 more)

### Community 120 - "DocsSearch.tsx"
Cohesion: 0.22
Nodes (17): build(), FakeChoice, FakeInteraction, FakeResponse, Тесты кога «Казино»: /слоты и /монетка — через .callback(), паттерн test_fun_cog, test_coinflip_disabled_module(), test_coinflip_house_edge_reduces_payout(), test_coinflip_loss() (+9 more)

### Community 121 - "test_members_list.py"
Cohesion: 0.18
Nodes (13): get_tempban_settings(), Request, Response, update_tempban_settings(), build_log_embed(), default_dm_message(), get_settings(), _load_raw() (+5 more)

### Community 122 - "test_member_detail.py"
Cohesion: 0.44
Nodes (12): get_game(), build(), _cleanup_timer(), _make_lobby(), Тесты игрового цикла кога «Бункер»: старт игры (раздача карточек, голосовой кана, Полный цикл: старт (4 игрока, вместимость 2) -> два раунда голосований -> игра з, test_end_game_deletes_voice_channel(), test_full_round_vote_ends_game_at_capacity() (+4 more)

### Community 123 - "DocsToc.tsx"
Cohesion: 0.28
Nodes (20): build(), FakeInteraction, Тесты кога Вордла — вызов через .callback()/методы кога, паттерн test_xp_command, test_announce_nobody_played(), test_announce_with_winner_crowns_best_and_streak(), test_commands_disabled_module(), test_daily_guess_edits_existing_live_card(), test_daily_guess_progresses_and_posts_live_card() (+12 more)

### Community 124 - "init"
Cohesion: 0.26
Nodes (16): _Deck, generate_characters(), _pick_additional_info(), _pick_age(), _pick_backpack_item(), _pick_body_type(), _pick_health(), _pick_hobby() (+8 more)

### Community 125 - "Request"
Cohesion: 0.14
Nodes (15): is_suspicious_account(), JoinTracker, datetime, Ядро модуля «Антирейд»: детект всплеска входов новых участников.  Без импорта di, Считается ли аккаунт «свежим» (подозрительным) на момент входа., Скользящее окно недавних «подозрительных» входов на один сервер.      Чистая стр, Добавить вход и вернуть текущее число подозрительных входов в окне., isolated_config() (+7 more)

### Community 126 - "EmbedBuilder.tsx"
Cohesion: 0.15
Nodes (8): build_vote_embed(), BunkerCog, _display_name(), Guild, Вызывается дашбордом после каждой отправки голоса за исключение., Обновляет информационное табло голосования в канале (редактирует одно сообщение,, Публикует в канал игры заявку игрока на спец. возможность — ведущий/админ примен, _resolve_alive_members()

### Community 127 - "Button.tsx"
Cohesion: 0.09
Nodes (18): BALANCE_ADMIN_MAX, CosmeticsView, EconomyCog, _item_label(), Bot, Embed, Guild, Interaction (+10 more)

### Community 128 - "events.py"
Cohesion: 0.20
Nodes (14): AuditEntry, AuditModerator, AuditPage, fetchAudit(), AuditPage(), csvEscape(), downloadAuditCsv(), EntryRow() (+6 more)

### Community 129 - "wordle_card.py"
Cohesion: 0.21
Nodes (16): ImageDraw, _avatar_image(), _circle_avatar(), _draw_grid(), _font(), _grid_size(), _placeholder_avatar(), FreeTypeFont (+8 more)

### Community 130 - "events.py"
Cohesion: 0.12
Nodes (24): build(), FakeInteraction, FakeResponse, Тесты кога «Верификация»: выключена по умолчанию, join-роль, кнопка., test_disabled_by_default_no_join_role(), test_explicitly_disabled_no_join_role(), test_join_assigns_unverified_role(), test_join_without_unverified_role_configured_does_nothing() (+16 more)

### Community 131 - "load_events"
Cohesion: 0.18
Nodes (17): ConfigError, DashboardConfig, load_dashboard_config(), Exception, _FakeBot, test_auto_roles_route_is_registered_in_the_real_app(), test_access_role_ids_empty_string_ok(), test_access_role_ids_optional_empty_when_absent() (+9 more)

### Community 132 - "test_supply_routes.py"
Cohesion: 0.13
Nodes (48): build(), cosmetics_shop_config(), FakeInteraction, FakeResponse, Тесты кога «Экономика»: /баланс /перевести /монеты-топ /магазин — через .callbac, shop_config(), test_balance_disabled_module(), test_balance_shows_amount_and_rank() (+40 more)

### Community 133 - "ru.ts"
Cohesion: 0.22
Nodes (8): ban_reason_for_api(), Embed, Guild, Message, При старте бота проверяем, нет ли пользователей в бан-листе         с причиной T, setup(), TempBan, tempban_reason()

### Community 134 - "wordle.py"
Cohesion: 0.14
Nodes (21): test_localize_command_sets_english_base_and_locale_str(), test_slash_locale_keys_exist_in_both_languages(), test_translator_returns_russian_command_name(), test_translator_returns_russian_description(), Group, Locale, locale_str, _apply_name_localizations() (+13 more)

### Community 135 - "test_warns_routes.py"
Cohesion: 0.15
Nodes (23): applyBunkerAbility(), BunkerCardPools, BunkerCharacter, BunkerGameDetail, BunkerGameSummary, BunkerPlayerRef, BunkerSettings, fetchBunkerCardPools() (+15 more)

### Community 136 - "Supply.tsx"
Cohesion: 0.23
Nodes (11): Request, Response, wordle_get(), wordle_put(), test_is_valid_announce_time(), test_settings_defaults(), test_settings_roundtrip(), get_settings() (+3 more)

### Community 137 - ".__init__"
Cohesion: 0.18
Nodes (18): Request, Response, verification_get(), verification_put(), isolated_config(), Тесты ядра верификации: настройки (выключена по умолчанию), проверка конфигураци, test_is_configured_does_not_require_unverified_role(), test_is_configured_requires_verified_role() (+10 more)

### Community 138 - "Docs.tsx"
Cohesion: 0.06
Nodes (48): make_moderation_app(), build(), isolated_config(), test_get_defaults(), test_put_allows_unlimited_max_bet(), test_put_then_get(), test_put_validation(), test_requires_login() (+40 more)

### Community 139 - "EventDetailPanel.tsx"
Cohesion: 0.22
Nodes (18): add(), connect(), get_by_user(), get_db_path(), init(), list_all(), _now(), Connection (+10 more)

### Community 140 - "format_voice_time"
Cohesion: 0.07
Nodes (23): SelectOption, CreateTeamCodeModal, DraftEvent, EventBuilderView, EventManageSelect, EventNotifyModal, EventPublishSelect, Events (+15 more)

### Community 141 - "test_feedback_panel_routes.py"
Cohesion: 0.17
Nodes (8): OwnerAlertsCog, Bot, Guild, Member, User, Owner alerts: DM/channel notify on missing perms, mass bans, module errors., Callable from other modules when they hit repeated failures., setup()

### Community 142 - "setup_session"
Cohesion: 0.06
Nodes (40): BracketFormat, BracketSummary, closeEvent(), createBracket(), createEvent(), CreateEventSpec, createGiveaway(), deleteEvent() (+32 more)

### Community 143 - "FakeResponse"
Cohesion: 0.24
Nodes (18): create_embed_message(), create_embed_template(), delete_embed_template(), get_embed_message(), _get_guild_or_none(), _is_role_assignable(), list_embed_templates(), _parse_body() (+10 more)

### Community 144 - "FakeResponse"
Cohesion: 0.14
Nodes (14): ChetBot, command_sync_mode(), get_main_guild_id(), main(), on_guild_join(), on_guild_remove(), on_ready(), Embed (+6 more)

### Community 145 - "test_news_routes.py"
Cohesion: 0.32
Nodes (12): Client, get_log_channel_id(), log_action(), log_error(), log_security(), log_unhide_action(), Color, Exception (+4 more)

### Community 146 - "test_auto_roles_routes.py"
Cohesion: 0.33
Nodes (6): Application, Path, setup_static_routes(), test_asset_path_serves_asset_file(), test_root_path_serves_index_html(), test_unmatched_path_serves_index_html()

### Community 147 - "test_supply_routes.py"
Cohesion: 0.05
Nodes (90): force_login(), Log in for dashboard tests. Default active guild is 1 (app main).      Pass ``, build(), test_get_auto_roles_defaults_to_empty_when_file_missing(), test_get_auto_roles_requires_auth(), test_get_auto_roles_returns_stored_values(), test_update_auto_roles_persists_valid_roles(), test_update_auto_roles_rejects_managed_role() (+82 more)

### Community 148 - "lockdown.py"
Cohesion: 0.20
Nodes (7): Invite, InvitesCog, Bot, Guild, Member, Invite tracker cog: snapshot invites, attribute joins., setup()

### Community 149 - "test_xp_routes.py"
Cohesion: 0.18
Nodes (11): MemberLookupResult, resolve_guild_member(), FakeBot, FakeGuild, _StubHTTPException, _StubNotFound, test_falls_back_to_fetch_when_not_cached(), test_not_found_when_fetch_raises_notfound() (+3 more)

### Community 150 - "mafia.py"
Cohesion: 0.29
Nodes (18): create_feedback_category(), decide_feedback_case(), delete_feedback_category(), get_feedback_case(), get_feedback_panel_settings(), _get_guild_or_none(), list_feedback_cases(), list_feedback_categories() (+10 more)

### Community 151 - "format_voice_time"
Cohesion: 0.33
Nodes (5): Lockdown, Choice, Guild, Interaction, setup()

### Community 152 - "FakeVoiceChannel"
Cohesion: 0.18
Nodes (17): build(), FakeFollowup, FakeInteraction, FakeResponse, Тесты команд /xp (add/set/clear) и /leaders в XPCog — вызов через .callback(),, test_leaders_disabled_module(), test_leaders_empty_leaderboard(), test_leaders_footer_shows_page_and_total() (+9 more)

### Community 153 - "Fun.tsx"
Cohesion: 0.08
Nodes (22): get_spam_settings(), Request, Response, update_spam_settings(), test_message_limit_with_attachments(), test_spam_settings_defaults(), test_spam_settings_roundtrip(), get_settings() (+14 more)

### Community 154 - "FakeResponse"
Cohesion: 0.29
Nodes (10): build(), Saving toggles with empty channel/dm embed stubs must not fail as empty_embed., test_get_welcome_settings_defaults_to_enabled_when_file_missing(), test_get_welcome_settings_requires_auth(), test_get_welcome_settings_returns_stored_values(), test_update_welcome_settings_allows_empty_embeds_in_text_mode(), test_update_welcome_settings_persists(), test_update_welcome_settings_rejects_non_dict_body() (+2 more)

### Community 155 - "_FakeMember"
Cohesion: 0.20
Nodes (4): Interaction, Invite, setup(), Welcome

### Community 156 - "Casino.tsx"
Cohesion: 0.21
Nodes (19): test_xp_add_text_and_get_scoped_per_guild(), test_xp_add_text_increments_messages_and_ts(), build(), test_leaderboard_guild_unavailable(), test_leaderboard_keeps_members_who_left(), test_leaderboard_pagination_over_merged_roster(), test_leaderboard_search_filters_by_display_name(), test_leaderboard_shows_every_guild_member_even_without_xp() (+11 more)

### Community 157 - "lang_for"
Cohesion: 0.22
Nodes (16): get(), load_config(), migrate_from_env_if_needed(), Invite link for tempban DM and other modules (no hardcoded fallback)., resolve_server_invite_link(), isolated_settings_db(), test_get_returns_default_when_key_missing(), test_get_returns_stored_value() (+8 more)

### Community 158 - "AntiRaidCog"
Cohesion: 0.22
Nodes (13): build(), test_get_moderation_log_requires_auth(), test_get_moderation_log_respects_limit(), test_get_moderation_log_returns_events_newest_first(), test_append_event_defaults_moderator_to_none_for_automatic_events(), test_append_event_stores_all_fields(), test_append_event_trims_to_max_entries(), test_append_then_load_returns_newest_first() (+5 more)

### Community 159 - "resolve_ticket"
Cohesion: 0.25
Nodes (4): BirthdaysCog, Bot, Interaction, setup()

### Community 160 - "welcome.py"
Cohesion: 0.10
Nodes (31): polls_end(), polls_get(), polls_list(), _public_poll(), Request, Response, isolated(), test_create_vote_tallies_end() (+23 more)

### Community 161 - "test_auto_roles_routes.py"
Cohesion: 0.16
Nodes (9): activity, admin, auth, common, community, docsShell, en, legal (+1 more)

### Community 162 - "load_dashboard_config"
Cohesion: 0.19
Nodes (20): AppRunner, create_app(), Application, start_dashboard(), FakeBot, A non-ConfigError, non-OSError failure during app construction/startup     must, On a real port-bind conflict (OSError from TCPSite.start), the     http_session, test_bracket_routes_are_registered() (+12 more)

### Community 163 - "EventDetailPanel.tsx"
Cohesion: 0.17
Nodes (24): Guild-wide birthday calendar cog., Request, Response, scheduled_messages_create(), scheduled_messages_delete(), scheduled_messages_get(), scheduled_messages_settings(), scheduled_messages_update() (+16 more)

### Community 164 - "test_members_list.py"
Cohesion: 0.05
Nodes (56): isolated_settings(), Тесты состояния панели голосовых комнат (voice_rooms) — per-guild в settings_db., test_on_ready_publishes_panel_for_each_guild(), test_panel_state_defaults_empty(), test_panel_state_is_per_guild(), test_panel_state_round_trip(), GuildChannel, Modal (+48 more)

### Community 167 - "test_ctd_routes.py"
Cohesion: 0.18
Nodes (17): audit_middleware(), describe_action(), normalize_stored_action(), Request, Аудит действий дашборда: каждое мутирующее действие модератора пишется в stats.d, Map legacy 'PUT /api/wordle' (and similar) rows to i18n keys., audit_list(), Request (+9 more)

### Community 168 - "Giveaways.tsx"
Cohesion: 0.27
Nodes (14): Code(), DocSection, H(), H3(), Note(), OL(), P(), Table() (+6 more)

### Community 169 - "birthdays_db.py"
Cohesion: 0.19
Nodes (19): connect(), delete_birthday(), for_date(), get_birthday(), get_db_path(), init(), is_valid_mm_dd(), list_birthdays() (+11 more)

### Community 170 - "test_feedback_panel_routes.py"
Cohesion: 0.11
Nodes (28): _bot_py_files(), _collect_literal_i18n_keys(), Path, EN/RU strings for the same key should declare the same {placeholders}., Catch blackjack-style mismatches: code key not present in locale dicts., Regression: buttons/footer must not show raw keys like casino.bj.btn.hit., test_blackjack_locale_keys_resolve(), test_guild_t_uses_server_language() (+20 more)

### Community 171 - "test_roles.py"
Cohesion: 0.67
Nodes (3): main(), One-off generator for locales/{ru,en}/slash.py — run from repo root., render()

### Community 172 - "test_access.py"
Cohesion: 0.22
Nodes (12): build(), _StubForbidden, _StubNotFound, test_ban_calls_discord_and_logs(), test_ban_discord_not_found_maps_to_404(), test_ban_forbidden_maps_to_403(), test_ban_invalid_json_body_returns_400(), test_ban_missing_member_maps_to_404() (+4 more)

### Community 173 - "test_wordle_routes.py"
Cohesion: 0.19
Nodes (17): invites_get(), invites_put(), Request, Response, isolated(), test_snapshot_and_stats(), connect(), get_db_path() (+9 more)

### Community 174 - "casino_db.py"
Cohesion: 0.12
Nodes (27): connect(), _ensure_row(), get_db_path(), init(), leaderboard(), Connection, SQLite-хранилище статистики казино (победы/поражения), per-guild., mode: 'slots', 'bj', 'total'        stat_type: 'wins', 'losses' (+19 more)

### Community 175 - "Mafia.tsx"
Cohesion: 0.20
Nodes (17): Request, Response, timed_roles_delete(), timed_roles_list(), isolated(), test_add_and_expired(), add(), connect() (+9 more)

### Community 176 - "test_ctd_routes.py"
Cohesion: 0.27
Nodes (13): _role(), test_activate_collects_errors_and_continues(), test_activate_respects_exempts(), test_activate_strips_permissions_and_saves_backup(), test_deactivate_restores_from_backup(), test_deactivate_without_backup_returns_none(), activate_antispam(), antispam_status() (+5 more)

### Community 177 - "EmbedBuilder.tsx"
Cohesion: 0.21
Nodes (12): createEmbedMessage(), deleteEmbedTemplate(), EmbedMessagePayload, EmbedTemplate, fetchEmbedMessage(), fetchEmbedTemplates(), saveEmbedTemplate(), updateEmbedMessage() (+4 more)

### Community 180 - "test_auto_roles_routes.py"
Cohesion: 0.10
Nodes (23): owner_alerts_get(), owner_alerts_put(), Request, Response, preview_template(), Request, Response, Dry-run placeholder substitution for text/embed templates. Does not send to Disc (+15 more)

### Community 181 - "test_supply_routes.py"
Cohesion: 0.47
Nodes (8): _check_channel(), _check_role(), get_config(), Request, Response, update_config(), _validate_relations(), _validate_structure()

### Community 182 - "Docs.tsx"
Cohesion: 0.23
Nodes (11): Documentation Banner Image, DocsBanner(), DocNavItem, DocsSearch(), DocsSearchProps, DocsSidebar(), DocsSidebarProps, GROUP_ICONS (+3 more)

### Community 183 - "auto_roles.py"
Cohesion: 0.48
Nodes (6): get_auto_roles(), _get_guild_or_none(), _is_role_assignable(), Request, Response, update_auto_roles()

### Community 184 - "ctd.py"
Cohesion: 0.57
Nodes (6): get_ctd(), put_ctd(), Request, Response, CTD (тикеты) — привилегия основного сервера (Фаза 2b MULTIGUILD_PLAN.md).  Настр, _require_main_guild()

### Community 185 - "resolve_ticket"
Cohesion: 0.17
Nodes (8): ApplicationModalPart1, ApplicationModalPart2, ContinueApplicationView, OpenTicketView, Button, Interaction, setup(), TicketControlView

### Community 186 - "CustomCommandsCog"
Cohesion: 0.27
Nodes (7): CustomCommandsCog, _embed_from_spec(), Bot, Embed, Message, Custom commands / auto-replies cog., setup()

### Community 187 - "test_antiraid_cog.py"
Cohesion: 0.36
Nodes (14): utcnow(), build(), fresh_member(), isolated_state(), Тесты кога «Антирейд»: выключен по умолчанию, детект всплеска, действия., test_below_threshold_does_not_trigger(), test_cooldown_prevents_immediate_retrigger(), test_disabled_by_default_does_nothing() (+6 more)

### Community 188 - "test_feedback_panel_routes.py"
Cohesion: 0.23
Nodes (7): Lock, Bot, Message, Sticky messages: repost sticky content when new messages arrive., setup(), StickyCog, TextChannel

### Community 189 - "TimedRolesCog"
Cohesion: 0.16
Nodes (8): Role, Bot, Interaction, Member, Range, Timed roles: slash assign + background sweeper., setup(), TimedRolesCog

### Community 190 - "BracketView.tsx"
Cohesion: 0.17
Nodes (7): BracketDetail, BracketMatch, fetchPublicBracket(), BracketView(), PickHandler, PublicBracketPage(), baseBracket

### Community 191 - "wordle_core.py"
Cohesion: 0.15
Nodes (12): test_guess_error_cases(), test_normalize_lowers_and_replaces_yo(), test_training_word_from_answers(), test_word_for_day_wraps_around(), _answers_shuffled(), guess_error(), normalize(), Ядро русского Вордла: оценка догадок, слово дня, настройки.  Без импорта discord (+4 more)

### Community 192 - "pick_bunker_conditions"
Cohesion: 0.23
Nodes (8): build(), FakeFollowup, FakeInteraction, FakeResponse, Тесты /ранг: подтягивание экипированной косметики (рамка/титул) из магазина., test_rank_command_ignores_unequipped_owned_cosmetics(), test_rank_command_passes_equipped_frame_and_title(), test_rank_command_without_cosmetics_passes_none()

### Community 193 - "format_voice_time"
Cohesion: 0.36
Nodes (12): automod_create_escalation(), automod_delete_escalation(), automod_get(), automod_update_enabled(), automod_update_escalation(), automod_update_filter(), automod_update_manual_warn_duration(), _is_str_list() (+4 more)

### Community 194 - "resolve_ticket"
Cohesion: 0.12
Nodes (25): test_status_color_and_label(), Ядро модуля «Семья» (портировано из FamQ): конфигурация, парсинг дат ДР, цвета/л, status_color(), status_label(), add_custom_emoji_reaction(), build_full_embed(), build_mini_embed(), build_ticket_result_embed() (+17 more)

### Community 195 - "ScheduledMessagesCog"
Cohesion: 0.28
Nodes (4): Bot, Scheduled messages cog: posts due one-shot / daily messages., ScheduledMessagesCog, setup()

### Community 196 - "test_feedback_panel_routes.py"
Cohesion: 0.26
Nodes (10): build(), FakeAutoModCog, isolated_db(), test_create_warn(), test_create_warn_validation(), test_create_warn_without_cog_still_succeeds(), test_delete_warn(), test_delete_warn_rejects_other_guild() (+2 more)

### Community 198 - "useLanguage"
Cohesion: 0.19
Nodes (6): PublicLayout(), useLanguage(), HeadingAnchor(), PrivacyPage(), TABLE_ROW_KEYS, TermsPage()

### Community 199 - "setup_session"
Cohesion: 0.30
Nodes (10): cookie_secure_flag(), derive_fernet_key(), Application, Whether Set-Cookie should use Secure.      Explicit `DASHBOARD_COOKIE_SECURE`, setup_session(), test_cookie_secure_flag_detects_https_frontend(), test_cookie_secure_flag_from_env(), test_derive_fernet_key_differs_per_secret() (+2 more)

### Community 200 - "test_supply_routes.py"
Cohesion: 0.27
Nodes (8): build(), FakeSupplyCog, test_close_and_cancel(), test_create_supply(), test_create_supply_validation(), test_overview_empty(), test_overview_with_data(), test_requires_auth()

### Community 201 - "save_config"
Cohesion: 0.44
Nodes (10): save_config(), build_cog(), isolated_config(), make_joining_member(), Тесты кога приветствий: канал/тумблеры/тексты берутся строго из настроек сервера, test_dm_title_uses_event_guild_name(), test_dm_toggle_off_suppresses_dm(), test_per_guild_isolation_of_welcome_channel() (+2 more)

### Community 202 - "SupplyView"
Cohesion: 0.42
Nodes (4): Button, Interaction, Persistent view: кнопки работают и после перезапуска бота., SupplyView

### Community 203 - "get_settings"
Cohesion: 0.29
Nodes (9): get_settings(), Настройки модуля сервера с дефолтами. enabled=False по умолчанию — модуль не, save_config(), antiraid_get(), antiraid_put(), Request, Response, test_settings_disabled_by_default() (+1 more)

### Community 204 - "AntiRaidCog"
Cohesion: 0.33
Nodes (4): AntiRaidCog, Bot, Ког «Антирейд»: автоматический Lockdown при всплеске входов новых участников.  В, setup()

### Community 205 - "test_fun_routes.py"
Cohesion: 0.39
Nodes (8): build(), isolated_config(), test_get_defaults(), test_put_auto_emoji_roundtrip_and_validation(), test_put_then_get(), test_put_validation(), test_put_zero_disables_punishment_and_cooldown(), test_requires_auth()

### Community 206 - "lang_for"
Cohesion: 0.54
Nodes (7): lockdown_activate(), lockdown_deactivate(), lockdown_status(), _log(), Request, Response, lang_for()

### Community 207 - "board_lines"
Cohesion: 0.29
Nodes (7): test_board_lines_pads_empty_rows(), test_share_grid_has_no_letters(), board_lines(), Строки эфемерной доски: квадраты + слово, пустые ряды — ⬜., Спойлер-фри сетка результата (только квадраты, без букв)., share_grid(), squares()

### Community 208 - "_recent_audit_entry"
Cohesion: 0.33
Nodes (5): AuditLogAction, AuditLogEntry, VoiceState, Эвристика: ищет только что созданную запись аудита по действию/цели., _recent_audit_entry()

### Community 209 - "day_number"
Cohesion: 0.60
Nodes (5): test_day_number_epoch(), date, day_number(), Номер сегодняшнего Вордла (день эпохи = №1)., today_msk()

### Community 210 - "DocsToc.tsx"
Cohesion: 0.50
Nodes (4): DocsToc(), DocsTocProps, slugify(), TocItem

### Community 211 - "guild_context.py"
Cohesion: 0.50
Nodes (3): guild_context_middleware(), Request, Per-request guild-контекст (Фаза 2.3).  Раньше гильдия была одна на всё приложен

### Community 213 - "result_score_text"
Cohesion: 0.67
Nodes (3): test_result_score_text(), «4/6» или «X/6» — как в оригинальном шеринге., result_score_text()

## Knowledge Gaps
- **249 isolated node(s):** `EmbedMessageResult`, `FeedbackCaseField`, `EventParticipantSolo`, `EventParticipantTeamCaptain`, `EventParticipantTeamCodeMember` (+244 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SelectOption` connect `format_voice_time` to `Test Fake Channels`, `test_warns_routes.py`?**
  _High betweenness centrality (0.212) - this node is a cross-community bridge._
- **Why does `load_events()` connect `Event Publish Tests` to `Bot Entrypoint & Auth Middleware`, `format_voice_time`, `Test Fake Bot`?**
  _High betweenness centrality (0.150) - this node is a cross-community bridge._
- **Why does `get()` connect `Bot Entrypoint & Auth Middleware` to `Supply Module`, `Test Fake Bot`, `Tournament Brackets`, `Feedback Cases`, `Giveaways Routes`, `.__init__`, `Supply.tsx`, `Automod Filter Core`, `Daily Topic Module`, `Bunker Game Core`, `Moderation Routes`, `Embed Builder Routes`, `mafia.py`, `Lockdown API Client`, `Mafia Core Tests`, `Fun.tsx`, `Feedback Panel Tests`, `Reaction Roles Tests`, `Stream Notifications`, `AntiRaidCog`, `EventDetailPanel.tsx`, `test_members_list.py`, `Button Forms`, `Family Core Tests`, `test_ctd_routes.py`, `Event Publish Tests`, `XP Core Tests`, `test_auto_roles_routes.py`, `Anti-Spam Cog`, `news.py`, `test_feedback_category_routes.py`, `ensure_owner()`, `get_settings`, `test_access.py`, `Leaderboard.tsx`, `Giveaways.tsx`, `renderWithI18n.tsx`, `test_mafia_routes.py`, `access_middleware.py`, `test_members_list.py`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `FakeMember` (e.g. with `_StubForbidden` and `_StubNotFound`) actually correct?**
  _`FakeMember` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `FakeGuild` (e.g. with `_StubForbidden` and `_StubNotFound`) actually correct?**
  _`FakeGuild` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `FakeBot` (e.g. with `_StubForbidden` and `_StubNotFound`) actually correct?**
  _`FakeBot` has 35 INFERRED edges - model-reasoned connections that need verification._
- **What connects `EmbedMessageResult`, `FeedbackCaseField`, `EventParticipantSolo` to the rest of the system?**
  _249 weakly-connected nodes found - possible documentation gaps or missing edges._