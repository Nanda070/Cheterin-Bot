# Graph Report - Cheterin_Bot_Dashboard  (2026-07-31)

## Corpus Check
- 586 files · ~420,231 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5891 nodes · 16665 edges · 216 communities (197 shown, 19 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 255 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8424240f`
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
- renderWithI18n.tsx
- Welcome
- access_middleware.py
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
- InvitesCog
- _FakeMember
- Casino.tsx
- lang_for
- Fun.tsx
- resolve_ticket
- welcome.py
- test_auto_roles_routes.py
- load_dashboard_config
- EventDetailPanel.tsx
- test_members_list.py
- test_button_config.py
- test_supply_routes.py
- test_ctd_routes.py
- test_news_routes.py
- birthdays_db.py
- test_feedback_panel_routes.py
- test_roles.py
- test_access.py
- test_wordle_routes.py
- casino_db.py
- Mafia.tsx
- custom_commands.py
- test_warns_routes.py
- Welcome.tsx
- __init__.py
- moderation_log.py
- save_config
- test_news_routes.py
- test_members_list.py
- VerificationCog
- test_voice_panel_state.py
- Mafia.tsx
- test_giveaway_routes.py
- test_feedback_panel_routes.py
- test_supply_routes.py
- test_auto_roles_routes.py
- voice_logs.py
- setup_session
- build_game_started_embed
- Mafia.tsx
- test_module_test_send.py
- test_mafia_test_game.py
- test_supply_routes.py
- test_casino_routes.py
- SupplyView
- FakeResponse
- localize_character
- guild_context.py
- test_news_routes.py
- test_voice_stats_routes.py
- _FakeResponse
- README.md
- aiohttp Dependency
- aiohttp-session Dependency
- cryptography Dependency
- discord.py Dependency
- Pillow Dependency
- pytest Dependency
- pytest-aiohttp Dependency
- python-dotenv Dependency

## God Nodes (most connected - your core abstractions)
1. `force_login()` - 377 edges
2. `FakeMember` - 360 edges
3. `FakeGuild` - 288 edges
4. `FakeBot` - 263 edges
5. `apiFetch()` - 173 edges
6. `useT()` - 155 edges
7. `FakeChannel` - 152 edges
8. `FakeRole` - 117 edges
9. `make_moderation_app()` - 112 edges
10. `t()` - 111 edges

## Surprising Connections (you probably didn't know these)
- `BlackjackView` --uses--> `CasinoCog`  [INFERRED]
  blackjack.py → casino.py
- `BlackjackCog` --uses--> `CasinoCog`  [INFERRED]
  blackjack.py → casino.py
- `_FakeFollowup` --uses--> `BunkerCog`  [INFERRED]
  dashboard/backend/tests/test_bunker_cog.py → bunker.py
- `_FakeInteraction` --uses--> `BunkerCog`  [INFERRED]
  dashboard/backend/tests/test_bunker_cog.py → bunker.py
- `_FakeResponse` --uses--> `BunkerCog`  [INFERRED]
  dashboard/backend/tests/test_bunker_cog.py → bunker.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Backend Runtime Dependencies** — requirements_discord_py, requirements_python_dotenv, requirements_aiohttp, requirements_aiohttp_session, requirements_cryptography, requirements_pillow [INFERRED 0.95]
- **External Platform and Social Icons Set** — dashboard_frontend_public_icons_bluesky_icon, dashboard_frontend_public_icons_discord_icon, dashboard_frontend_public_icons_github_icon, dashboard_frontend_public_icons_x_icon, dashboard_frontend_public_icons_social_icon [INFERRED 0.85]
- **Dashboard UI Icon Asset Set** — dashboard_frontend_public_icons_bluesky_icon, dashboard_frontend_public_icons_discord_icon, dashboard_frontend_public_icons_documentation_icon, dashboard_frontend_public_icons_github_icon, dashboard_frontend_public_icons_social_icon, dashboard_frontend_public_icons_x_icon [EXTRACTED 1.00]
- **Docs Page User Interface** — dashboard_frontend_src_pages_docs, dashboard_frontend_src_components_docs_docsbanner, dashboard_frontend_src_assets_docs_banner [INFERRED 0.90]
- **Hero Page Visual Branding Elements** — dashboard_frontend_src_assets_hero, dashboard_frontend_src_assets_hero_branding, dashboard_frontend_src_assets_hero_layered_stack [INFERRED 0.85]

## Communities (216 total, 19 thin omitted)

### Community 0 - "Game Settings & Bunker DB"
Cohesion: 0.09
Nodes (53): add_player(), add_round_event(), connect(), count_players(), create_ability_announcement(), get_ability_announcement(), get_active_game_in_channel(), get_db_path() (+45 more)

### Community 1 - "Supply Module"
Cohesion: 0.06
Nodes (67): _display_name(), _finalize(), Request, Response, _serialize_supply(), supply_cancel(), supply_close(), supply_create() (+59 more)

### Community 2 - "Dashboard App Bootstrap"
Cohesion: 0.06
Nodes (64): apiFetch(), banMember(), createDailyTopic(), createMemberWarn(), createStreamSubscription(), DailyTopicSettings, decideFamilyTicket(), deleteBracket() (+56 more)

### Community 3 - "Test Fake Channels"
Cohesion: 0.18
Nodes (38): eliminate_player(), update_game(), build(), _character(), Fake-lobby bots use negative user ids; vote + roster must accept them., _setup_game(), test_ability_already_used(), test_ability_dead_player() (+30 more)

### Community 4 - "API Client Types"
Cohesion: 0.03
Nodes (95): AutoRolesSettings, BirthdayEntry, BracketStandingsRow, BunkerAbilityAnnouncement, BunkerAdditionalInfo, BunkerAgeInfo, BunkerBodyType, BunkerGamePhase (+87 more)

### Community 5 - "Test Fake Bot"
Cohesion: 0.05
Nodes (92): FakeBot, FakeGuild, make_moderation_app(), make_client_app(), test_guild_unavailable_gets_503(), test_member_not_in_guild_gets_403(), test_member_with_access_reaches_handler(), test_member_without_access_role_gets_403() (+84 more)

### Community 6 - "Automod Route Tests"
Cohesion: 0.08
Nodes (28): activity, admin, auth, common, community, credits, docsShell, en (+20 more)

### Community 7 - "Tournament Brackets"
Cohesion: 0.06
Nodes (64): create_bracket(), create_bracket_v2(), _de_get_match(), _de_match(), _de_recompute_match(), _de_resolve(), extract_entries_from_event(), find_by_share_token() (+56 more)

### Community 8 - "Feedback Cases"
Cohesion: 0.20
Nodes (22): isolated_config(), test_load_categories_returns_empty_dict_when_file_missing(), test_migrate_from_env_if_needed_creates_config_from_env(), test_migrate_from_env_if_needed_skips_when_env_vars_missing(), test_migrate_from_env_if_needed_skips_when_file_already_exists(), test_save_then_load_round_trip(), test_validate_category_spec_accepts_valid_spec(), test_validate_category_spec_allows_own_case_prefix_on_edit() (+14 more)

### Community 9 - "Giveaways Routes"
Cohesion: 0.08
Nodes (55): _display_name(), giveaways_create(), giveaways_end(), giveaways_overview(), giveaways_reroll(), Request, Response, _serialize_giveaway() (+47 more)

### Community 10 - "Automod Cog"
Cohesion: 0.08
Nodes (42): FakeThread, test_fake_bot_fetch_user_falls_back_when_not_in_guild(), test_fake_bot_fetch_user_raises_when_nowhere_found(), test_fake_bot_get_channel_finds_channel_and_thread(), test_fake_bot_update_file_records_calls(), test_fake_member_send_raises_when_configured(), test_fake_member_send_records_dm(), test_fake_thread_edit_records_archived_and_locked() (+34 more)

### Community 11 - "Server Event Logging"
Cohesion: 0.07
Nodes (37): AuditLogAction, AuditLogEntry, Request, Response, serverlog_get(), serverlog_put(), _Role, test_format_stay_duration() (+29 more)

### Community 12 - "Automod Filter Core"
Cohesion: 0.07
Nodes (54): _default_filter(), _default_notify_template(), detect_bad_words(), detect_caps_lock(), detect_emoji_spam(), detect_invites(), detect_links(), detect_mentions() (+46 more)

### Community 13 - "Test Fake Members"
Cohesion: 0.10
Nodes (30): Documentation Banner Image, DocsBanner(), DocNavItem, DocsSearch(), DocsSearchProps, DocsSidebar(), DocsSidebarProps, GROUP_ICONS (+22 more)

### Community 14 - "Daily Topic Module"
Cohesion: 0.10
Nodes (45): add_topic(), already_posted_today(), delete_topic(), get_settings(), get_today_post_time(), is_valid_time(), mark_posted_today(), _normalized() (+37 more)

### Community 15 - "API Client Functions"
Cohesion: 0.08
Nodes (41): build_embed(), BlackjackGame, _build_deck(), can_double(), card_rank(), card_suit(), _deal_card(), dealer_play() (+33 more)

### Community 16 - "Bunker Game Core"
Cohesion: 0.13
Nodes (22): generate_characters(), is_game_over(), Раздаёт полную карточку персонажа каждому игроку.      unique_cards=True (по умо, Большинство голосов за исключение; ничья среди лидеров — никто не исключён., resolve_expulsion_vote(), save_config(), isolated_config(), test_generate_characters_covers_all_players_with_full_field_set() (+14 more)

### Community 17 - "Moderation Routes"
Cohesion: 0.19
Nodes (27): _assignable_roles(), ban_member(), dashboard_reason(), _get_guild_or_none(), get_moderation_log(), _get_target_or_response(), grant_role(), kick_member() (+19 more)

### Community 18 - "Bunker Discord Cog"
Cohesion: 0.06
Nodes (26): decideFeedbackCase(), FeedbackCaseDetail, FeedbackCaseSummary, fetchFeedbackCaseDetail(), fetchFeedbackCases(), baseGameSummary, emptySettings, mockPools (+18 more)

### Community 19 - "Mass Role Assignment"
Cohesion: 0.04
Nodes (80): DashboardUser, fetchCurrentUser(), fetchInviteUrl(), fetchManageableGuilds(), fetchPublicLeaderboard(), fetchSuperAdminGuilds(), fetchVoiceStats(), loginUrl() (+72 more)

### Community 20 - "Embed Builder Routes"
Cohesion: 0.11
Nodes (36): test_build_embed_omits_color_when_absent(), test_build_embed_sets_author_footer_image_thumbnail(), test_build_embed_sets_basic_fields(), test_build_embed_sets_fields(), test_build_embed_sets_timestamp(), test_delete_template_missing_returns_false(), test_delete_template_removes_only_target_and_guild(), test_embed_to_spec_returns_empty_color_when_absent() (+28 more)

### Community 21 - "Bot Entrypoint & Auth Middleware"
Cohesion: 0.07
Nodes (53): ApiError, BirthdaysPayload, ChannelInfo, createReactionRole(), CtdConfig, CustomEmoji, deleteBirthday(), deleteReactionRole() (+45 more)

### Community 22 - "Frontend Package Deps"
Cohesion: 0.04
Nodes (46): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, tailwindcss, @tailwindcss/vite, devDependencies (+38 more)

### Community 23 - "Lockdown API Client"
Cohesion: 0.12
Nodes (17): isolated_state(), isolated_settings_db(), isolated_config(), isolated_config(), isolated_state(), isolated_config(), isolated_feedback_categories(), isolated_config() (+9 more)

### Community 24 - "Mafia DB Tests"
Cohesion: 0.13
Nodes (25): audit_middleware(), describe_action(), normalize_stored_action(), Request, Аудит действий дашборда: каждое мутирующее действие модератора пишется в stats.d, Map legacy 'PUT /api/wordle' (and similar) rows to i18n keys., cookie_secure_flag(), derive_fernet_key() (+17 more)

### Community 25 - "Mafia Core Tests"
Cohesion: 0.08
Nodes (37): _FakeMember, _FakePermissions, isolated_config(), test_assign_roles_matches_scale_and_covers_all_players(), test_check_win_condition_mafia_wins_at_parity(), test_check_win_condition_no_winner_yet(), test_check_win_condition_town_wins_when_no_mafia(), test_get_settings_defaults() (+29 more)

### Community 26 - "Stream Notifications"
Cohesion: 0.09
Nodes (26): _public_sub(), Request, Response, streams_create(), streams_delete(), streams_list(), streams_test(), streams_update() (+18 more)

### Community 27 - "Feedback Panel Tests"
Cohesion: 0.10
Nodes (34): bet_error(), flip_coin(), get_settings(), payout_amount(), Ядро модуля «Казино»: слоты, монетка и блэкджек на серверную валюту.  Без импорт, Настройки модуля сервера с дефолтами (выключен по умолчанию)., None — ставка допустима, иначе текст ошибки для игрока., Выигрыш с учётом преимущества казино (округление вниз). (+26 more)

### Community 28 - "Reaction Roles Tests"
Cohesion: 0.09
Nodes (38): _bot_channel_flags(), create_reaction_role(), delete_reaction_role(), _get_guild_or_none(), _is_role_assignable(), list_channels(), list_emojis(), list_reaction_roles() (+30 more)

### Community 29 - "Streams API Client"
Cohesion: 0.14
Nodes (32): build(), _poll_create_spec(), _poll_event(), test_close_event_route_404(), test_close_event_route_requires_auth(), test_close_event_route_success(), test_create_event_404_when_channel_missing(), test_create_event_404_when_role_reward_missing() (+24 more)

### Community 30 - "Voice Rooms Routes"
Cohesion: 0.11
Nodes (35): Request, Response, voice_panel_publish(), voice_room_delete(), voice_rooms_list(), build(), FakeVoiceChannel, isolated_db() (+27 more)

### Community 31 - "XP API Client"
Cohesion: 0.07
Nodes (60): audit_list(), Request, Response, _create_legacy_schema(), isolated_db(), Тесты stats_db: per-guild изоляция XP/войс/аудита и миграция старой схемы.  Фаза, Схема до Фазы 2.2а: без guild_id (как в проде на мейн-сервере)., После миграции один user_id может существовать на разных серверах. (+52 more)

### Community 32 - "Mafia Discord Cog"
Cohesion: 0.08
Nodes (29): AutomodFilter, AutomodPunishment, AutomodSettings, createEscalationRule(), deleteEscalationRule(), EscalationAction, EscalationRule, fetchAutomod() (+21 more)

### Community 33 - "Feedback API Client"
Cohesion: 0.11
Nodes (26): announceBunkerAbility(), BUNKER_FIELD_KEYS, BunkerFieldKey, BunkerPublicState, fetchPublicBunker(), fetchPublicMafia(), MafiaPublicState, MafiaRole (+18 more)

### Community 34 - "Family DB Tests"
Cohesion: 0.10
Nodes (48): _create_legacy_schema(), isolated_db(), _main(), Тесты family_db: per-guild ростер/заявки/дни рождения + миграция старой схемы., Схема до Фазы 2.2б: синглтоны roster_msg/birthday_msg (id=1), single-PK     pen, test_birthday_message_roundtrip_and_isolation(), test_birthday_roundtrip_and_queries(), test_list_and_count_tickets_scoped_and_filtered() (+40 more)

### Community 35 - "Events & Embeds Client"
Cohesion: 0.14
Nodes (30): _cmd(), _grp(), _key(), Any, Apply slash command localizations for every cog (Phase 3.2(3))., register_automod(), register_birthdays(), register_blackjack() (+22 more)

### Community 36 - "Lockdown Routes"
Cohesion: 0.18
Nodes (31): build(), _setup_game(), test_action_dead_player(), test_action_deadline_passed(), test_action_game_not_active(), test_action_happy_path_and_resubmit(), test_action_invalid_target_not_alive(), test_action_self_target_allowed_for_doctor() (+23 more)

### Community 37 - "Events Route Tests"
Cohesion: 0.14
Nodes (33): callback(), _frontend(), invite_url(), list_guilds(), login(), logout(), me(), Request (+25 more)

### Community 38 - "Mafia Public Route Tests"
Cohesion: 0.24
Nodes (15): get(), load_config(), migrate_from_env_if_needed(), Invite link for tempban DM and other modules (no hardcoded fallback)., resolve_server_invite_link(), test_get_returns_default_when_key_missing(), test_get_returns_stored_value(), test_load_config_returns_empty_dict_when_missing() (+7 more)

### Community 39 - "Family Tickets"
Cohesion: 0.18
Nodes (12): test_supply_config_is_per_guild(), Messageable, _config_int(), generate_embed(), get_reminder_minutes(), Bot, Color, Embed (+4 more)

### Community 40 - "Button Forms"
Cohesion: 0.12
Nodes (12): ButtonCreate, DynamicQuestionsModal, _get_allowed_role_ids(), _load_buttons_config(), BaseException, Interaction, Удаляет устаревшие записи кулдаунов., Возвращает оставшиеся секунды если кулдаун активен, иначе None. (+4 more)

### Community 41 - "Audit Log & Stats DB"
Cohesion: 0.06
Nodes (44): isolated_config(), Тесты ядра Вордла: целостность словаря, оценка догадок, слово дня, настройки., test_board_lines_pads_empty_rows(), test_day_number_epoch(), test_evaluate_all_green(), test_evaluate_duplicate_letters_consume_stock(), test_evaluate_green_priority_over_yellow(), test_evaluate_yellow_and_gray() (+36 more)

### Community 42 - "Giveaway Cog"
Cohesion: 0.11
Nodes (13): generate_embed(), GiveawayCog, GiveawayView, Bot, Button, Embed, Interaction, Range (+5 more)

### Community 43 - "Brackets Client Tests"
Cohesion: 0.08
Nodes (37): activateLockdown(), createGiveaway(), deactivateLockdown(), endGiveaway(), fetchGiveawayOverview(), fetchLockdownStatus(), fetchModerationLog(), fetchSetupHealth() (+29 more)

### Community 44 - "Bunker API Client"
Cohesion: 0.07
Nodes (42): createEmbedMessage(), deleteEmbedTemplate(), EmbedFieldSpec, EmbedMessagePayload, EmbedSpec, EmbedTemplate, FeedbackPanelSettings, fetchAutoRoles() (+34 more)

### Community 45 - "Automod API Client"
Cohesion: 0.05
Nodes (53): AutoMod, _consecutive_run_length(), BaseException, Bot, Guild, Interaction, Message, Ког «Автомодерация»: 9 настраиваемых фильтров сообщений, эскалация по количеству (+45 more)

### Community 47 - "Event Builder UI"
Cohesion: 0.09
Nodes (23): createFeedbackCategory(), deleteFeedbackCategory(), FeedbackCategoryFieldSpec, FeedbackCategorySpec, fetchFeedbackCategories(), fetchMassAssignStatus(), MassAssignStatus, MassAssignTarget (+15 more)

### Community 48 - "Family Core Tests"
Cohesion: 0.13
Nodes (20): _FakeGuild, _FakeGuildRef, _FakeMember, isolated_config(), test_build_birthday_text_groups_by_month_and_resolves_mentions(), test_can_manage_tickets_requires_configured_role(), test_has_staff_access_admin_bypasses_role_check(), test_has_staff_access_via_role() (+12 more)

### Community 49 - "XP Core Tests"
Cohesion: 0.09
Nodes (32): isolated_config(), test_deserved_roles(), test_get_settings_voice_new_fields_defaults(), test_level_formula_monotonic(), test_level_from_xp_roundtrip(), test_level_progress(), test_render_announce(), test_roll_text_xp_respects_multiplier() (+24 more)

### Community 50 - "Event Publish Tests"
Cohesion: 0.20
Nodes (22): _poll_spec(), test_publish_event_poll_creates_matching_event_obj_and_view(), test_publish_event_role_reward_none_stays_none(), test_publish_event_tournament_creates_matching_event_obj_and_view(), test_validate_event_spec_accepts_valid_poll_spec(), test_validate_event_spec_accepts_valid_tournament_spec(), test_validate_event_spec_allows_missing_team_size_check_for_solo_mode(), test_validate_event_spec_rejects_description_too_long() (+14 more)

### Community 51 - "TypeScript Config"
Cohesion: 0.08
Nodes (23): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+15 more)

### Community 52 - "Bot Config Store"
Cohesion: 0.12
Nodes (22): BotConfig, cancelSupply(), closeSupply(), createSupply(), fetchConfig(), fetchSupplyOverview(), isChannelDead(), Supply (+14 more)

### Community 53 - "Family Birthdays"
Cohesion: 0.10
Nodes (42): get_player_by_token(), Полная перезапись карточки — используется админ-панелью при ручном применении сп, set_player_character(), localize_game_scenario(), Catastrophe + bunker conditions names/descriptions for embeds and public API., _avatar_url(), bunker_apply_ability(), bunker_card_pools() (+34 more)

### Community 54 - "Anti-Spam Cog"
Cohesion: 0.10
Nodes (40): get_welcome_settings(), Request, Response, Send a sample welcome (channel and/or DM) using the dashboard user as the member, _serialize_messages(), update_welcome_settings(), _validate_messages_payload(), welcome_test() (+32 more)

### Community 55 - "news.py"
Cohesion: 0.15
Nodes (18): _is_id_like(), news_get(), news_put(), Request, Response, get_channel_map(), get_settings(), _main_guild_id() (+10 more)

### Community 56 - "events.py"
Cohesion: 0.26
Nodes (5): CasinoLeaderboardView, Button, Embed, Guild, Interaction

### Community 57 - "test_feedback_routes.py"
Cohesion: 0.10
Nodes (37): _auto_emoji_config(), build(), enable_economy(), FakeInteraction, FakeMsg, FakeResponse, Тесты кога «Развлечения»: русская рулетка (исходы, таймаут, кулдаун) и эмодзи-ру, test_auto_emoji_channel_interval_limits_frequency() (+29 more)

### Community 58 - "FeedbackCategories.tsx"
Cohesion: 0.27
Nodes (7): _fmt_voice(), LeaderboardView, Button, Guild, Interaction, Формат времени голоса Ч:ММ:СС (как в JuniperBot)., Интерактивный лидерборд: сортировка по Опыту / Голосу + пагинация.

### Community 59 - "Docs.tsx"
Cohesion: 0.09
Nodes (27): add(), connect(), get_by_user(), get_db_path(), init(), list_all(), _now(), Connection (+19 more)

### Community 60 - "voice_rooms.py"
Cohesion: 0.20
Nodes (20): _make_game(), test_add_player_rejects_duplicate(), test_assign_player_role_and_get_by_token(), test_create_and_get_game(), test_get_active_game_in_channel_filters_by_status(), test_get_day_vote_single_row(), test_get_game_by_lobby_and_vote_message(), test_get_night_actions_filters_by_role() (+12 more)

### Community 61 - "XPCog"
Cohesion: 0.12
Nodes (14): _Member, XP_ADMIN_MAX, XP_ADMIN_MIN, channel_allowed(), member_has_ignored_role(), Bot, Embed, Message (+6 more)

### Community 62 - "auth.py"
Cohesion: 0.18
Nodes (5): MafiaCog, Bot, Вызывается дашбордом после каждой отправки ночного действия., Вызывается дашбордом после каждой отправки дневного голоса., setup()

### Community 63 - "resolve_guild_member()"
Cohesion: 0.18
Nodes (8): CTD, CTDCloseView, CTDView, _is_main_guild(), BaseException, Button, Interaction, setup()

### Community 64 - "xp.py"
Cohesion: 0.20
Nodes (22): _int_in(), _is_id_list(), _public_leaderboard_payload(), Request, Response, Вкладка «Участники» дашборда: весь ростер гильдии, а не только те,     кто уже, Legacy URL: require guild_id query param. Prefer /api/public/leaderboard/{guild_, _serialize_row() (+14 more)

### Community 65 - "test_feedback_category_routes.py"
Cohesion: 0.07
Nodes (49): add_escalation_rule(), delete_escalation_rule(), update_escalation_rule(), get_settings(), mark_announced(), Birthday calendar settings: channel + optional ping role., save_settings(), reset_settings_db() (+41 more)

### Community 66 - "Supply.tsx"
Cohesion: 0.14
Nodes (21): test_localize_command_sets_english_base_and_locale_str(), test_slash_locale_keys_exist_in_both_languages(), test_translator_returns_russian_command_name(), test_translator_returns_russian_description(), Group, Locale, locale_str, _apply_name_localizations() (+13 more)

### Community 67 - "MassAssignModal.tsx"
Cohesion: 0.20
Nodes (4): Interaction, Invite, setup(), Welcome

### Community 68 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+11 more)

### Community 69 - ".__init__()"
Cohesion: 0.09
Nodes (23): owner_alerts_get(), owner_alerts_put(), owner_alerts_test(), Request, Response, setup_health_get(), test_owner_alerts_mass_ban_threshold(), critical_perms_missing() (+15 more)

### Community 70 - "VoiceTracker"
Cohesion: 0.14
Nodes (8): is_active(), BaseException, Bot, VoiceState, Войс-трекер: единый учёт голосовых сессий.  Кормит сразу два модуля: - статис, setup(), VoiceSession, VoiceTracker

### Community 71 - "Interaction"
Cohesion: 0.07
Nodes (33): build_expulsion_result_embed(), build_game_started_embed(), build_lobby_cancelled_embed(), build_lobby_embed(), build_result_embed(), build_vote_embed(), BunkerCog, BunkerLobbyView (+25 more)

### Community 72 - "ensure_owner()"
Cohesion: 0.08
Nodes (41): Тесты ядра экономики: курс от XP, комиссии, валидация ставок, хук award_for_xp., test_award_for_xp_disabled_gives_nothing(), test_bet_error_cases(), test_bet_error_unlimited_when_max_zero(), test_claim_daily_bonus_consecutive_day_extends_streak(), test_claim_daily_bonus_first_time(), test_claim_daily_bonus_gap_resets_streak(), test_claim_daily_bonus_same_day_rejected() (+33 more)

### Community 73 - "family.py"
Cohesion: 0.15
Nodes (11): BirthdayCog, build_birthday_embed(), BaseException, Bot, Embed, Guild, Interaction, User (+3 more)

### Community 74 - "test_family_routes.py"
Cohesion: 0.06
Nodes (73): economy_get(), economy_put(), economy_reset_all(), economy_set_balance(), economy_top(), economy_weekly_report(), Request, Response (+65 more)

### Community 75 - "test_access.py"
Cohesion: 0.20
Nodes (16): Request, Response, sticky_roles_get(), sticky_roles_put(), isolated_settings(), connect(), filter_member_roles(), get_db_path() (+8 more)

### Community 76 - "test_config_routes.py"
Cohesion: 0.12
Nodes (39): _avatar_url(), _display_name(), _is_id(), mafia_games_list(), mafia_get(), mafia_public_action(), mafia_public_state(), mafia_public_vote() (+31 more)

### Community 77 - "RosterCog"
Cohesion: 0.21
Nodes (8): generate_roster_text(), Bot, Guild, Interaction, Live-ростер семьи: список участников по настроенным ролям.  Портировано из FamQ, Debounce: аккумулирует изменения и обновляет сообщение через 10 секунд., RosterCog, setup()

### Community 78 - "reaction_roles.py"
Cohesion: 0.18
Nodes (11): MemberLookupResult, resolve_guild_member(), FakeBot, FakeGuild, _StubHTTPException, _StubNotFound, test_falls_back_to_fetch_when_not_cached(), test_not_found_when_fetch_raises_notfound() (+3 more)

### Community 79 - "PublicBunkerAction.tsx"
Cohesion: 0.10
Nodes (19): test_build_board_embed_finished_loss_reveals_answer(), File, _avatar_bytes(), BoardView, build_board_embed(), _card_file(), GuessModal, PlayNowView (+11 more)

### Community 80 - "Leaderboard.tsx"
Cohesion: 0.15
Nodes (11): build_topic_message(), DailyTopicCog, BaseException, Bot, Ког «Ежедневная рубрика»: раз в день публикует тему/вопрос дня в заданный канал,, Публикует тему дня немедленно (используется циклом и ручным триггером         из, setup(), build() (+3 more)

### Community 81 - "VoiceManager"
Cohesion: 0.12
Nodes (11): BaseException, Guild, Interaction, Message, View, Удаляет устаревшие записи из кэша спам-детектора., Удаляет сообщения участника за последние 20 минут во всех каналах и тредах., Обработка кнопок спам-инцидентов — работает и после перезапуска бота. (+3 more)

### Community 82 - "mafia.py"
Cohesion: 0.15
Nodes (24): isolated_config(), Тесты ядра верификации: настройки (выключена по умолчанию), проверка конфигураци, test_clamp_reverify_days(), test_consent_expiry(), test_is_configured_does_not_require_unverified_role(), test_is_configured_requires_verified_role(), test_rules_panel_text_when_rules_consent_enabled(), test_settings_disabled_by_default() (+16 more)

### Community 83 - "events.py"
Cohesion: 0.22
Nodes (19): create_embed_message(), create_embed_template(), delete_embed_template(), get_embed_message(), _get_guild_or_none(), _is_role_assignable(), list_embed_templates(), _parse_body() (+11 more)

### Community 84 - "ChetBot"
Cohesion: 0.67
Nodes (3): Web Dashboard Index HTML, React Root Mount Element, React Entry Point Script

### Community 85 - "ChannelInfo"
Cohesion: 0.05
Nodes (63): FakeChannel, FakeComponentRow, FakeCustomEmoji, FakeMessage, FakePermissions, test_parse_role_button_ids_extracts_matching_custom_ids(), test_parse_role_button_ids_handles_no_components(), test_parse_role_button_ids_ignores_non_role_buttons() (+55 more)

### Community 86 - "MafiaLobbyView"
Cohesion: 0.15
Nodes (16): _pick_age(), _pick_body_type(), English card pools for the Bunker survival tabletop game., additional_info_en_template(), _en_item(), merge_additional_info(), merge_age(), merge_body_type() (+8 more)

### Community 87 - "voice_logs.py"
Cohesion: 0.10
Nodes (37): isolated_state(), isolated_db(), Тесты wordle_db: игры дня, статистика со стриками, мета сервера (per-guild)., test_add_guess_accumulates_and_finishes(), test_daily_games_isolated_per_guild(), test_group_streak_gap_resets(), test_group_streak_grows_and_resets(), test_group_streak_isolated_per_guild() (+29 more)

### Community 88 - "test_auto_roles_routes.py"
Cohesion: 0.23
Nodes (17): build(), build_with_guild(), _full_config(), PUT /api/config не должен затирать ключи других разделов (авто-роли, приветствия, test_get_config_requires_auth(), test_get_config_returns_defaults_when_file_missing(), test_get_config_returns_stored_values(), test_put_config_preserves_foreign_keys() (+9 more)

### Community 89 - "Giveaways.tsx"
Cohesion: 0.12
Nodes (25): casino_top_command(), CasinoCog, check_loss_roles(), _coinflip_label(), Bot, Choice, Ког «Казино»: /слоты и /монетка на серверную валюту.  Требует включённой «Экон, setup() (+17 more)

### Community 90 - "renderWithI18n.tsx"
Cohesion: 0.20
Nodes (21): add_command(), delete_command(), get_settings(), match_message(), _normalized(), Per-guild custom commands / auto-replies (exact or contains match)., Return first matching enabled command for message content, or None., update_command() (+13 more)

### Community 91 - "Welcome"
Cohesion: 0.10
Nodes (28): fun_get(), fun_put(), Request, Response, test_spin_trigger_chance_grows(), test_spin_trigger_guaranteed_on_last_chamber(), isolated_config(), test_get_settings_defaults() (+20 more)

### Community 93 - "test_mafia_routes.py"
Cohesion: 0.17
Nodes (13): isolated_settings(), Тесты состояния панели голосовых комнат (voice_rooms) — per-guild в settings_db., test_on_ready_publishes_panel_for_each_guild(), test_panel_state_defaults_empty(), test_panel_state_is_per_guild(), test_panel_state_round_trip(), build_embed(), load_panel_state() (+5 more)

### Community 94 - "test_warns_routes.py"
Cohesion: 0.11
Nodes (19): can_manage_guild_permissions(), has_dashboard_access(), has_manage_server(), has_super_admin_access(), manageable_guilds(), Контроль доступа к дашборду (модель MEE6, Фаза 2.3).  Доступ к серверу = право, DEPRECATED (Фаза 1, роль-модель). Оставлено до перевода auth/middleware на, Доступ к настройкам сервера: Manage Server или Administrator на этой гильдии. (+11 more)

### Community 95 - "test_xp_routes.py"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does SelectOption connect Mafia Game Engine to Discord Embed Builder, Supply Cog Tests?, Source Nodes

### Community 96 - "CTD"
Cohesion: 0.25
Nodes (16): build(), test_birthday_set_invalid_date(), test_birthday_set_unknown_member(), test_birthdays_crud(), test_get_defaults(), test_put_then_get(), test_put_validation(), test_requires_auth() (+8 more)

### Community 97 - "setup_static_routes()"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does force_login() connect Mock Services & Unit Tests to a wide array of system modules and tests?, Source Nodes

### Community 98 - "FakeAsset"
Cohesion: 0.16
Nodes (13): test_load_events_reads_fresh_after_external_write(), test_load_events_returns_empty_events_dict_when_file_missing(), test_save_then_load_roundtrips(), create_participation_view(), EventManageSelect, EventNotifyModal, Events, load_events() (+5 more)

### Community 99 - "plugins"
Cohesion: 0.22
Nodes (8): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema, oxc, typescript, warn

### Community 100 - "DocsSearch.tsx"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Are the inferred relationships involving mock objects (FakeMember, FakeGuild, FakeBot, FakeRole) with DashboardConfig and _StubForbidden correct?, Source Nodes

### Community 101 - "access_middleware.py"
Cohesion: 0.12
Nodes (19): publish_feedback_panel(), Embed, Message, upsert_embed_field(), add_reviewers(), build_mentions(), close_case(), create_feedback_case() (+11 more)

### Community 102 - "auto_roles.py"
Cohesion: 0.10
Nodes (28): build_game_started_embed(), build_lobby_cancelled_embed(), build_lobby_embed(), build_lynch_result_embed(), build_morning_embed(), build_result_embed(), build_vote_embed(), _display_name() (+20 more)

### Community 103 - "icons.svg"
Cohesion: 0.38
Nodes (6): Bluesky Icon, Discord Icon, Documentation Icon, GitHub Icon, Social Icon, X Icon

### Community 104 - "format_voice_time()"
Cohesion: 0.09
Nodes (31): BlackjackCog, BlackjackView, Bot, Button, Interaction, User, Кнопки игры: Ещё карту / Стоп / Удвоить., setup() (+23 more)

### Community 105 - "DocsToc.tsx"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: What connects schema, typescript, oxc to the rest of the system?, Source Nodes

### Community 108 - "Hero Image Graphic"
Cohesion: 1.00
Nodes (3): Hero Image Graphic, Cheterin Isometric Branding Concept, Layered Isometric Architecture Illustration

### Community 111 - "DocsSearch.tsx"
Cohesion: 0.18
Nodes (17): build(), FakeFollowup, FakeInteraction, FakeResponse, Тесты команд /xp (add/set/clear) и /leaders в XPCog — вызов через .callback(),, test_leaders_disabled_module(), test_leaders_empty_leaderboard(), test_leaders_footer_shows_page_and_total() (+9 more)

### Community 112 - "test_fun_routes.py"
Cohesion: 0.20
Nodes (14): Тесты рендера карточки ранга: базовый рендер, кастомная рамка и титул., test_hex_to_rgb(), test_render_rank_card_long_title_does_not_crash(), test_render_rank_card_with_custom_frame_and_title(), test_render_rank_card_without_cosmetics_produces_png(), _background(), _circle_avatar(), _font() (+6 more)

### Community 120 - "DocsSearch.tsx"
Cohesion: 0.19
Nodes (26): get_settings(), Настройки модуля сервера с дефолтами (выключен по умолчанию)., assign_character(), create_game(), build(), _sample_character(), test_apply_ability_announcement(), test_apply_ability_announcement_not_found() (+18 more)

### Community 121 - "test_members_list.py"
Cohesion: 0.10
Nodes (21): get_tempban_settings(), Request, Response, update_tempban_settings(), ban_reason_for_api(), build_log_embed(), default_dm_message(), get_settings() (+13 more)

### Community 122 - "test_member_detail.py"
Cohesion: 0.29
Nodes (18): create_feedback_category(), decide_feedback_case(), delete_feedback_category(), get_feedback_case(), get_feedback_panel_settings(), _get_guild_or_none(), list_feedback_cases(), list_feedback_categories() (+10 more)

### Community 123 - "DocsToc.tsx"
Cohesion: 0.17
Nodes (25): build(), FakeInteraction, FakeResponse, Тесты кога Вордла — вызов через .callback()/методы кога, паттерн test_xp_command, test_announce_nobody_played(), test_announce_nobody_won_reveals_word(), test_announce_with_winner_crowns_best_and_streak(), test_commands_disabled_module() (+17 more)

### Community 124 - "init"
Cohesion: 0.35
Nodes (16): get_game(), get_player(), build(), _cleanup_timer(), _FakeInteraction, _make_lobby(), Тесты игрового цикла кога «Бункер»: старт игры (раздача карточек, голосовой кана, Полный цикл: старт (4 игрока, вместимость 2) -> два раунда голосований -> игра з (+8 more)

### Community 125 - "Request"
Cohesion: 0.15
Nodes (13): is_suspicious_account(), JoinTracker, Считается ли аккаунт «свежим» (подозрительным) на момент входа., Скользящее окно недавних «подозрительных» входов на один сервер.      Чистая стр, Добавить вход и вернуть текущее число подозрительных входов в окне., isolated_config(), Тесты ядра антирейда: настройки (выключен по умолчанию), детект свежих аккаунто, test_fresh_account_is_suspicious() (+5 more)

### Community 126 - "EmbedBuilder.tsx"
Cohesion: 0.23
Nodes (11): get_spam_settings(), Request, Response, update_spam_settings(), test_message_limit_with_attachments(), test_spam_settings_defaults(), test_spam_settings_roundtrip(), get_settings() (+3 more)

### Community 127 - "Button.tsx"
Cohesion: 0.09
Nodes (17): BALANCE_ADMIN_MAX, CosmeticsView, EconomyCog, _item_label(), Bot, Embed, Guild, Interaction (+9 more)

### Community 128 - "events.py"
Cohesion: 0.22
Nodes (5): BirthdaysCog, Bot, Interaction, Guild-wide birthday calendar cog., setup()

### Community 129 - "wordle_card.py"
Cohesion: 0.21
Nodes (16): ImageDraw, _avatar_image(), _circle_avatar(), _draw_grid(), _font(), _grid_size(), _placeholder_avatar(), FreeTypeFont (+8 more)

### Community 130 - "events.py"
Cohesion: 0.06
Nodes (40): DashboardConfig, guild_context_middleware(), Request, Per-request guild-контекст (Фаза 2.3).  Раньше гильдия была одна на всё приложен, FakeAsset, FakeAuditLogEntry, FakeAuditLogExtra, _FakeChannelType (+32 more)

### Community 131 - "load_events"
Cohesion: 0.10
Nodes (36): AppRunner, create_app(), json_error_middleware(), Application, Path, start_dashboard(), ConfigError, load_dashboard_config() (+28 more)

### Community 132 - "test_supply_routes.py"
Cohesion: 0.13
Nodes (48): build(), cosmetics_shop_config(), FakeInteraction, FakeResponse, Тесты кога «Экономика»: /баланс /перевести /монеты-топ /магазин — через .callbac, shop_config(), test_balance_disabled_module(), test_balance_shows_amount_and_rank() (+40 more)

### Community 133 - "ru.ts"
Cohesion: 0.16
Nodes (5): FakeResponse, Guild, Interaction, VerificationCog, VerificationView

### Community 135 - "test_warns_routes.py"
Cohesion: 0.15
Nodes (23): applyBunkerAbility(), BunkerCardPools, BunkerCharacter, BunkerGameDetail, BunkerGameSummary, BunkerPlayerRef, BunkerSettings, fetchBunkerCardPools() (+15 more)

### Community 136 - "Supply.tsx"
Cohesion: 0.31
Nodes (9): Request, Response, wordle_get(), wordle_put(), test_settings_defaults(), test_settings_roundtrip(), get_settings(), Настройки модуля сервера с дефолтами (выключен по умолчанию).      channel_id — (+1 more)

### Community 137 - ".__init__"
Cohesion: 0.12
Nodes (8): _game(), Тесты ядра блэкджека: очки руки, ход дилера, итоги, выплаты, форматирование., test_resolve_both_naturals_push(), test_resolve_compare_values(), test_resolve_dealer_bust_wins(), test_resolve_natural_blackjack(), test_resolve_player_bust_loses_even_if_dealer_busts(), test_twenty_one_from_three_cards_beats_dealer_twenty()

### Community 138 - "Docs.tsx"
Cohesion: 0.07
Nodes (59): has_running_job(), MassAssignJob, run_mass_assign(), FakeRole, build(), _spec(), test_create_feedback_category_404_when_channel_missing(), test_create_feedback_category_404_when_role_missing() (+51 more)

### Community 139 - "EventDetailPanel.tsx"
Cohesion: 0.10
Nodes (25): test_status_color_and_label(), status_color(), status_label(), add_custom_emoji_reaction(), ApplicationModalPart1, ApplicationModalPart2, build_full_embed(), build_mini_embed() (+17 more)

### Community 140 - "format_voice_time"
Cohesion: 0.16
Nodes (7): EventBuilderView, EventPublishSelect, LimitsModal, OptionsModal, Interaction, TextChannel, TextModal

### Community 141 - "test_feedback_panel_routes.py"
Cohesion: 0.11
Nodes (15): Tests for shared fake-lobby seat builder used by bunker/mafia test commands., Fake-lobby bots use negative user ids; vote + roster must accept them., Night actions must accept synthetic negative bot seat ids., test_night_action_negative_bot_target(), test_vote_negative_bot_target_and_stored_display_name(), build_fake_seats(), fake_avatar_url(), fake_user_id() (+7 more)

### Community 142 - "setup_session"
Cohesion: 0.13
Nodes (6): CreateTeamCodeModal, DraftEvent, handle_registration(), JoinTeamCodeModal, RegisterSoloModal, RegisterTeamCaptainModal

### Community 143 - "FakeResponse"
Cohesion: 0.29
Nodes (17): _decide_ticket(), _display_name(), family_birthday_delete(), family_birthday_set(), family_birthdays_list(), family_get(), family_put(), family_roster() (+9 more)

### Community 144 - "FakeResponse"
Cohesion: 0.23
Nodes (8): build(), FakeFollowup, FakeInteraction, FakeResponse, Тесты /ранг: подтягивание экипированной косметики (рамка/титул) из магазина., test_rank_command_ignores_unequipped_owned_cosmetics(), test_rank_command_passes_equipped_frame_and_title(), test_rank_command_without_cosmetics_passes_none()

### Community 145 - "test_news_routes.py"
Cohesion: 0.28
Nodes (12): _Deck, _pick_additional_info(), _pick_backpack_item(), _pick_health(), _pick_hobby(), _pick_large_item(), _pick_phobia(), _pick_profession() (+4 more)

### Community 146 - "test_auto_roles_routes.py"
Cohesion: 0.31
Nodes (7): Application, Path, setup_static_routes(), test_asset_path_serves_asset_file(), test_root_path_serves_index_html(), test_unmatched_path_serves_index_html(), test_well_known_discord_not_spa_fallback()

### Community 147 - "test_supply_routes.py"
Cohesion: 0.04
Nodes (100): force_login(), Log in for dashboard tests. Default active guild is 1 (app main).      Pass ``, build(), isolated_config(), test_get_defaults_disabled(), test_put_then_get(), test_put_validation(), test_requires_login() (+92 more)

### Community 148 - "lockdown.py"
Cohesion: 0.36
Nodes (11): Client, get_log_channel_id(), log_action(), log_error(), log_security(), log_unhide_action(), Color, Exception (+3 more)

### Community 149 - "test_xp_routes.py"
Cohesion: 0.21
Nodes (15): isolated_state(), test_reverify_sweeper_expires_member(), Тесты SQLite-хранилища согласий верификации., test_record_get_clear_and_list(), clear_consent(), connect(), get_consent(), get_db_path() (+7 more)

### Community 150 - "mafia.py"
Cohesion: 0.21
Nodes (10): preview_template(), Request, Response, Dry-run placeholder substitution for text/embed templates. Does not send to Disc, isolated(), test_preview_text_and_slash(), preview_embed(), preview_slash_help() (+2 more)

### Community 151 - "format_voice_time"
Cohesion: 0.33
Nodes (5): Lockdown, Choice, Guild, Interaction, setup()

### Community 152 - "FakeVoiceChannel"
Cohesion: 0.20
Nodes (6): Bot, Interaction, Range, Timed roles: slash assign + background sweeper., setup(), TimedRolesCog

### Community 153 - "Fun.tsx"
Cohesion: 0.20
Nodes (9): Данные для игры «Бункер»: возраст, телосложение, профессии, хобби, здоровье, стр, get_card_pools(), localize_character(), Return a copy with RU text fields replaced by EN when lang == 'en'., Card pools for dashboard editor — full pool in requested language., _swap_field(), test_get_card_pools_en(), test_localize_character_en_swaps_text_fields() (+1 more)

### Community 154 - "InvitesCog"
Cohesion: 0.14
Nodes (12): _has_legacy_role_access(), Переходный грант по роли на активном сервере (если задан DASHBOARD_ACCESS_ROLE_I, Гейт доступа к серверу (Фаза 2.3): сессия → активный сервер → Manage Server., Гейт для списка серверов бота — намеренно хардкод-роль, см. access.py., require_dashboard_access(), require_super_admin(), _cached_display(), Resolve display names with cache-first lookup and deduped concurrent fetches. (+4 more)

### Community 155 - "_FakeMember"
Cohesion: 0.32
Nodes (13): close_event_route(), create_event(), delete_event_route(), get_event(), list_events(), notify_event_route(), Request, Response (+5 more)

### Community 156 - "Casino.tsx"
Cohesion: 0.23
Nodes (19): build(), test_leaderboard_guild_unavailable(), test_leaderboard_keeps_members_who_left(), test_leaderboard_pagination_over_merged_roster(), test_leaderboard_search_filters_by_display_name(), test_leaderboard_shows_every_guild_member_even_without_xp(), test_leaderboard_sorted_by_xp_desc(), test_public_leaderboard_disabled_returns_404() (+11 more)

### Community 157 - "lang_for"
Cohesion: 0.47
Nodes (8): _check_channel(), _check_role(), get_config(), Request, Response, update_config(), _validate_relations(), _validate_structure()

### Community 158 - "Fun.tsx"
Cohesion: 0.17
Nodes (7): BracketDetail, BracketMatch, fetchPublicBracket(), BracketView(), PickHandler, PublicBracketPage(), baseBracket

### Community 159 - "resolve_ticket"
Cohesion: 0.28
Nodes (4): Bot, Scheduled messages cog: posts due one-shot / daily messages., ScheduledMessagesCog, setup()

### Community 160 - "welcome.py"
Cohesion: 0.10
Nodes (31): polls_end(), polls_get(), polls_list(), _public_poll(), Request, Response, isolated(), test_create_vote_tallies_end() (+23 more)

### Community 161 - "test_auto_roles_routes.py"
Cohesion: 0.22
Nodes (13): build(), FakeDailyTopicCog, isolated_config(), test_create_topic_validation(), test_get_defaults(), test_post_now(), test_post_now_no_cog(), test_post_now_requires_channel() (+5 more)

### Community 162 - "load_dashboard_config"
Cohesion: 0.23
Nodes (12): isolated_db(), isolated_state(), build(), isolated_state(), test_games_list(), test_games_list_filters_by_guild(), test_get_defaults(), test_put_then_get() (+4 more)

### Community 163 - "EventDetailPanel.tsx"
Cohesion: 0.19
Nodes (24): Request, Response, scheduled_messages_create(), scheduled_messages_delete(), scheduled_messages_get(), scheduled_messages_settings(), scheduled_messages_update(), _validate_message_fields() (+16 more)

### Community 164 - "test_members_list.py"
Cohesion: 0.38
Nodes (9): build(), test_get_defaults(), test_put_roundtrip_with_cosmetic_items(), test_put_roundtrip_with_shop(), test_put_validation(), test_requires_login(), test_reset_all_balances(), test_set_balance() (+1 more)

### Community 166 - "test_supply_routes.py"
Cohesion: 0.32
Nodes (8): get_settings(), Настройки модуля сервера с дефолтами. enabled=False по умолчанию — модуль не, antiraid_get(), antiraid_put(), Request, Response, test_settings_disabled_by_default(), test_settings_roundtrip()

### Community 167 - "test_ctd_routes.py"
Cohesion: 0.14
Nodes (14): ChetBot, command_sync_mode(), get_main_guild_id(), main(), on_guild_join(), on_guild_remove(), on_ready(), Embed (+6 more)

### Community 168 - "test_news_routes.py"
Cohesion: 0.67
Nodes (4): Request, Response, verification_get(), verification_put()

### Community 169 - "birthdays_db.py"
Cohesion: 0.17
Nodes (21): connect(), delete_birthday(), for_date(), get_birthday(), get_db_path(), init(), is_valid_mm_dd(), list_birthdays() (+13 more)

### Community 170 - "test_feedback_panel_routes.py"
Cohesion: 0.06
Nodes (43): _bot_py_files(), _collect_literal_i18n_keys(), Path, EN/RU strings for the same key should declare the same {placeholders}., Catch blackjack-style mismatches: code key not present in locale dicts., Regression: buttons/footer must not show raw keys like casino.bj.btn.hit., test_blackjack_locale_keys_resolve(), test_guild_t_uses_server_language() (+35 more)

### Community 171 - "test_roles.py"
Cohesion: 0.67
Nodes (3): main(), One-off generator for locales/{ru,en}/slash.py — run from repo root., render()

### Community 172 - "test_access.py"
Cohesion: 0.33
Nodes (10): test_resolve_banner_url_returns_empty_when_unset(), test_resolve_banner_url_uses_custom_setting(), build_panel_payload(), default_panel_embed_spec(), get_settings(), _load_raw(), panel_banner_url(), Feedback panel appearance customization. (+2 more)

### Community 173 - "test_wordle_routes.py"
Cohesion: 0.09
Nodes (26): invites_get(), invites_put(), Request, Response, isolated(), test_snapshot_and_stats(), get_settings(), Invite tracker settings (welcome mention, channel). (+18 more)

### Community 174 - "casino_db.py"
Cohesion: 0.15
Nodes (21): connect(), _ensure_row(), get_db_path(), get_main_guild_id(), __getattr__(), init(), leaderboard(), Connection (+13 more)

### Community 175 - "Mafia.tsx"
Cohesion: 0.20
Nodes (17): Request, Response, timed_roles_delete(), timed_roles_list(), isolated(), test_add_and_expired(), add(), connect() (+9 more)

### Community 176 - "custom_commands.py"
Cohesion: 0.19
Nodes (20): lockdown_activate(), lockdown_deactivate(), lockdown_status(), _log(), Request, Response, _role(), test_activate_collects_errors_and_continues() (+12 more)

### Community 177 - "test_warns_routes.py"
Cohesion: 0.07
Nodes (40): AntiRaidSettings, createCustomCommand(), CustomCommandsSettings, deleteCustomCommand(), fetchAntiRaidSettings(), fetchCustomCommands(), fetchMafiaGames(), fetchMafiaSettings() (+32 more)

### Community 180 - "moderation_log.py"
Cohesion: 0.33
Nodes (9): test_append_event_defaults_moderator_to_none_for_automatic_events(), test_append_event_stores_all_fields(), test_append_event_trims_to_max_entries(), test_append_then_load_returns_newest_first(), test_load_events_returns_empty_list_on_corrupt_json(), test_load_events_returns_empty_list_when_file_missing(), append_event(), load_events() (+1 more)

### Community 181 - "save_config"
Cohesion: 0.29
Nodes (10): build(), Saving toggles with empty channel/dm embed stubs must not fail as empty_embed., test_get_welcome_settings_defaults_to_enabled_when_file_missing(), test_get_welcome_settings_requires_auth(), test_get_welcome_settings_returns_stored_values(), test_update_welcome_settings_allows_empty_embeds_in_text_mode(), test_update_welcome_settings_persists(), test_update_welcome_settings_rejects_non_dict_body() (+2 more)

### Community 182 - "test_news_routes.py"
Cohesion: 0.48
Nodes (6): build(), isolated_config(), test_get_defaults(), test_put_then_get(), test_put_validation(), test_requires_login()

### Community 183 - "test_members_list.py"
Cohesion: 0.10
Nodes (26): createScheduledMessage(), deleteScheduledMessage(), deleteSticky(), deleteVoiceRoom(), fetchScheduledMessages(), fetchSticky(), fetchVoiceRooms(), publishVoicePanel() (+18 more)

### Community 184 - "VerificationCog"
Cohesion: 0.26
Nodes (18): build(), FakeInteraction, Тесты кога «Верификация»: выключена по умолчанию, join-роль, кнопка, re-verify., test_explicitly_disabled_no_join_role(), test_join_assigns_unverified_role(), test_join_without_unverified_role_configured_does_nothing(), test_reverify_allows_click_when_consent_expired(), test_rules_consent_success_message() (+10 more)

### Community 185 - "test_voice_panel_state.py"
Cohesion: 0.38
Nodes (4): _button_label(), Bot, Ког «Верификация»: панель «Я не бот» / согласия с правилами для новичков.  ВЫКЛЮ, verify_custom_id()

### Community 186 - "Mafia.tsx"
Cohesion: 0.20
Nodes (14): AuditEntry, AuditModerator, AuditPage, fetchAudit(), AuditPage(), csvEscape(), downloadAuditCsv(), EntryRow() (+6 more)

### Community 187 - "test_giveaway_routes.py"
Cohesion: 0.33
Nodes (4): has_moderator_access(), _FakeMember, _FakePermissions, test_has_moderator_access()

### Community 188 - "test_feedback_panel_routes.py"
Cohesion: 0.09
Nodes (22): 0.1 Точечные фиксы (найдено 20.07, исправлено 21.07), 0.2 Для будущего масштаба (было «Фаза 4», актуально по мере роста числа серверов), 2.1 Хранилище настроек: `settings_db.py` (✅ ВЫПОЛНЕНО), 2.2 Данные модулей: guild-измерение, 2.3 Авторизация и выбор сервера (пункт №6) — ✅ ВЫПОЛНЕНО (21.07.2026), 2.4 Бот: отвязка от GUILD_ID (пункт №7) — ✅ ВЫПОЛНЕНО (21.07.2026), 3.1 Инфраструктура — ✅ ВЫПОЛНЕНО (22.07.2026), 3.1 (исходное ТЗ) (+14 more)

### Community 189 - "test_supply_routes.py"
Cohesion: 0.25
Nodes (17): datetime, Ядро модуля «Антирейд»: детект всплеска входов новых участников.  Без импорта di, save_config(), utcnow(), Ког «Антирейд»: автоматический Lockdown при всплеске входов новых участников.  В, build(), fresh_member(), Тесты кога «Антирейд»: выключен по умолчанию, детект всплеска, действия. (+9 more)

### Community 190 - "test_auto_roles_routes.py"
Cohesion: 0.40
Nodes (6): pick_bunker_conditions(), pick_catastrophe(), merge_bunker_conditions(), merge_catastrophe(), test_pick_catastrophe_and_bunker_conditions_return_known_entries(), test_localize_game_scenario_uses_keys()

### Community 191 - "voice_logs.py"
Cohesion: 0.10
Nodes (24): Modal, VCTheme, apply_owner_permissions(), ChannelControlView, _config_channel_id(), ensure_owner(), is_room_owner(), Bot (+16 more)

### Community 192 - "setup_session"
Cohesion: 0.21
Nodes (8): Lock, Bot, Message, TextChannel, Sticky messages: repost sticky content when new messages arrive., Repost sticky. Returns False if send failed (old message left intact)., setup(), StickyCog

### Community 193 - "build_game_started_embed"
Cohesion: 0.27
Nodes (7): CustomCommandsCog, _embed_from_spec(), Bot, Embed, Message, Custom commands / auto-replies cog., setup()

### Community 194 - "Mafia.tsx"
Cohesion: 0.24
Nodes (8): get_ticket_by_thread(), Guild, Thread, Результат resolve_ticket — единая точка для форматирования ответа и в Discord, и, Общая логика решения по тикету — используется и кнопками в Discord, и дашбордом., Точка входа для дашборда: находит тред по user_id и вызывает resolve_ticket., resolve_ticket(), TicketResolution

### Community 196 - "test_module_test_send.py"
Cohesion: 0.21
Nodes (21): Request, Response, sticky_delete(), sticky_get(), sticky_settings(), sticky_test(), sticky_upsert(), test_sticky_test_reports_send_failure() (+13 more)

### Community 197 - "test_mafia_test_game.py"
Cohesion: 0.21
Nodes (6): _cleanup_timer(), _FakeFollowup, _FakeInteraction, _FakeResponse, Тест slash-команды тестовой «Мафии» с ботами., test_start_test_game_fills_bots_and_returns_link()

### Community 198 - "test_supply_routes.py"
Cohesion: 0.67
Nodes (3): default_bunker_capacity(), Половина игроков (округление вниз, минимум 1) — если ведущий не задал своё число, test_default_bunker_capacity()

### Community 199 - "test_casino_routes.py"
Cohesion: 0.44
Nodes (10): save_config(), build_cog(), isolated_config(), make_joining_member(), Тесты кога приветствий: канал/тумблеры/тексты берутся строго из настроек сервера, test_dm_title_uses_event_guild_name(), test_dm_toggle_off_suppresses_dm(), test_per_guild_isolation_of_welcome_channel() (+2 more)

### Community 201 - "SupplyView"
Cohesion: 0.42
Nodes (4): Button, Interaction, Persistent view: кнопки работают и после перезапуска бота., SupplyView

### Community 202 - "FakeResponse"
Cohesion: 0.07
Nodes (55): FakeMember, build(), _StubForbidden, _StubNotFound, test_ban_calls_discord_and_logs(), test_ban_discord_not_found_maps_to_404(), test_ban_forbidden_maps_to_403(), test_ban_invalid_json_body_returns_400() (+47 more)

### Community 204 - "localize_character"
Cohesion: 0.48
Nodes (6): get_auto_roles(), _get_guild_or_none(), _is_role_assignable(), Request, Response, update_auto_roles()

### Community 205 - "guild_context.py"
Cohesion: 0.57
Nodes (6): get_ctd(), put_ctd(), Request, Response, CTD (тикеты) — привилегия основного сервера (Фаза 2b MULTIGUILD_PLAN.md).  Настр, _require_main_guild()

### Community 206 - "test_news_routes.py"
Cohesion: 0.08
Nodes (32): BracketFormat, BracketSummary, closeEvent(), createBracket(), createEvent(), CreateEventSpec, deleteEvent(), endPoll() (+24 more)

### Community 208 - "test_voice_stats_routes.py"
Cohesion: 0.43
Nodes (3): AntiRaidCog, Bot, setup()

## Knowledge Gaps
- **277 isolated node(s):** `$schema`, `typescript`, `oxc`, `react/rules-of-hooks`, `warn` (+272 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SelectOption` connect `Bot Config Store` to `FakeAsset`, `test_warns_routes.py`?**
  _High betweenness centrality (0.223) - this node is a cross-community bridge._
- **Why does `load_events()` connect `FakeAsset` to `test_feedback_category_routes.py`, `Test Fake Bot`, `Tournament Brackets`, `setup_session`, `Event Publish Tests`, `_FakeMember`?**
  _High betweenness centrality (0.169) - this node is a cross-community bridge._
- **Why does `get()` connect `test_feedback_category_routes.py` to `Supply Module`, `Tournament Brackets`, `Feedback Cases`, `Giveaways Routes`, `Docs.tsx`, `Automod Cog`, `Automod Filter Core`, `Server Event Logging`, `Daily Topic Module`, `Supply.tsx`, `Moderation Routes`, `Embed Builder Routes`, `Mafia Core Tests`, `Stream Notifications`, `Feedback Panel Tests`, `Reaction Roles Tests`, `Casino.tsx`, `EventDetailPanel.tsx`, `test_supply_routes.py`, `Button Forms`, `test_access.py`, `test_wordle_routes.py`, `Family Core Tests`, `custom_commands.py`, `moderation_log.py`, `Family Birthdays`, `Anti-Spam Cog`, `news.py`, `test_module_test_send.py`, `.__init__()`, `ensure_owner()`, `test_access.py`, `mafia.py`, `renderWithI18n.tsx`, `Welcome`, `test_mafia_routes.py`, `FakeAsset`, `access_middleware.py`, `DocsSearch.tsx`, `test_members_list.py`, `test_member_detail.py`, `EmbedBuilder.tsx`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Are the 42 inferred relationships involving `FakeMember` (e.g. with `DashboardConfig` and `_StubForbidden`) actually correct?**
  _`FakeMember` has 42 INFERRED edges - model-reasoned connections that need verification._
- **Are the 42 inferred relationships involving `FakeGuild` (e.g. with `DashboardConfig` and `_StubForbidden`) actually correct?**
  _`FakeGuild` has 42 INFERRED edges - model-reasoned connections that need verification._
- **Are the 41 inferred relationships involving `FakeBot` (e.g. with `DashboardConfig` and `_StubForbidden`) actually correct?**
  _`FakeBot` has 41 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `typescript`, `oxc` to the rest of the system?**
  _277 weakly-connected nodes found - possible documentation gaps or missing edges._