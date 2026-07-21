# Graph Report - Cheterin_Bot_Dashboard  (2026-07-21)

## Corpus Check
- 377 files · ~224,258 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 4663 nodes · 12671 edges · 177 communities (165 shown, 12 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 229 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ce905986`
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
- PublicMafiaAction.tsx
- Welcome
- access_middleware.py
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
- test_wordle_routes.py
- format_voice_time
- test_feedback_panel_routes.py
- DocsSearch.tsx
- FakeResponse
- FakeResponse
- test_news_routes.py
- test_auto_roles_routes.py
- test_supply_routes.py
- lockdown.py
- test_xp_routes.py
- test_wordle_routes.py
- format_voice_time
- FakeVoiceChannel
- test_economy_routes.py
- auto_roles.py
- _FakeMember
- require_dashboard_access
- SupplyView
- config.py
- ReactionRoles
- .start_lobby
- test_audit.py
- test_news_routes.py
- test_feedback_panel_routes.py
- test_bunker_cog.py
- test_button_config.py
- test_fun_routes.py
- test_auto_roles_routes.py
- Phase 2.3: OAuth Guilds Scope and Server Selection
- FakeResponse
- Phase 3: RU/EN i18n Infrastructure
- daily_topic.py
- ._auto_close_tickets_error
- test_ctd_routes.py
- Embed
- Guild
- init

## God Nodes (most connected - your core abstractions)
1. `force_login()` - 331 edges
2. `FakeMember` - 318 edges
3. `FakeGuild` - 253 edges
4. `FakeBot` - 230 edges
5. `FakeChannel` - 131 edges
6. `apiFetch()` - 126 edges
7. `FakeRole` - 114 edges
8. `make_moderation_app()` - 89 edges
9. `jsonInit()` - 77 edges
10. `get()` - 75 edges

## Surprising Connections (you probably didn't know these)
- `Unified settings.db Per-Guild Storage` --references--> `get_settings()`  [INFERRED]
  MULTIGUILD_PLAN.md → bunker_core.py
- `Phase 2.4: Bot Detached from GUILD_ID` --references--> `ChetBot`  [EXTRACTED]
  MULTIGUILD_PLAN.md → main.py
- `Phase 2.3: OAuth Guilds Scope and Server Selection` --references--> `callback()`  [EXTRACTED]
  MULTIGUILD_PLAN.md → dashboard/backend/auth.py
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

## Communities (177 total, 12 thin omitted)

### Community 0 - "Game Settings & Bunker DB"
Cohesion: 0.09
Nodes (25): BlackjackCog, BlackjackView, build_embed(), GameResult, payout(), Сумма к зачислению на баланс (0 при проигрыше, возврат при ничье).      При Doub, Bot, Button (+17 more)

### Community 1 - "Supply Module"
Cohesion: 0.09
Nodes (49): _display_name(), _finalize(), Request, Response, _serialize_supply(), supply_cancel(), supply_close(), supply_create() (+41 more)

### Community 2 - "Dashboard App Bootstrap"
Cohesion: 0.05
Nodes (45): DashboardUser, fetchCurrentUser(), fetchInviteUrl(), fetchManageableGuilds(), fetchPublicLeaderboard(), fetchSuperAdminGuilds(), fetchVoiceStats(), logout() (+37 more)

### Community 3 - "Test Fake Channels"
Cohesion: 0.05
Nodes (85): FakeChannel, FakeComponentRow, FakeCustomEmoji, FakeMessage, FakeRole, test_parse_role_button_ids_extracts_matching_custom_ids(), test_parse_role_button_ids_handles_no_components(), test_parse_role_button_ids_ignores_non_role_buttons() (+77 more)

### Community 4 - "API Client Types"
Cohesion: 0.03
Nodes (80): AuditEntry, AutoRolesSettings, BracketStandingsRow, BunkerAbilityAnnouncement, BunkerAdditionalInfo, BunkerAgeInfo, BunkerBodyType, BunkerGamePhase (+72 more)

### Community 5 - "Test Fake Bot"
Cohesion: 0.06
Nodes (56): FakeBot, FakeGuild, make_client_app(), test_guild_unavailable_gets_503(), test_member_not_in_guild_gets_403(), test_member_with_access_reaches_handler(), test_member_without_access_role_gets_403(), test_no_session_returns_401() (+48 more)

### Community 6 - "Automod Route Tests"
Cohesion: 0.13
Nodes (15): FakeMember, build(), _StubForbidden, _StubNotFound, test_ban_calls_discord_and_logs(), test_ban_discord_not_found_maps_to_404(), test_ban_forbidden_maps_to_403(), test_ban_invalid_json_body_returns_400() (+7 more)

### Community 7 - "Tournament Brackets"
Cohesion: 0.07
Nodes (61): create_bracket(), create_bracket_v2(), _de_get_match(), _de_match(), _de_recompute_match(), _de_resolve(), extract_entries_from_event(), generate_de() (+53 more)

### Community 8 - "Feedback Cases"
Cohesion: 0.07
Nodes (56): create_feedback_category(), decide_feedback_case(), delete_feedback_category(), get_feedback_case(), _get_guild_or_none(), list_feedback_cases(), list_feedback_categories(), publish_feedback_panel_route() (+48 more)

### Community 9 - "Giveaways Routes"
Cohesion: 0.08
Nodes (55): _display_name(), giveaways_create(), giveaways_end(), giveaways_overview(), giveaways_reroll(), Request, Response, _serialize_giveaway() (+47 more)

### Community 10 - "Automod Cog"
Cohesion: 0.06
Nodes (43): AutoMod, _consecutive_run_length(), BaseException, Bot, Guild, Interaction, Message, Ког «Автомодерация»: 9 настраиваемых фильтров сообщений, эскалация по количеству (+35 more)

### Community 11 - "Server Event Logging"
Cohesion: 0.07
Nodes (37): AuditLogAction, AuditLogEntry, Command, Request, Response, serverlog_get(), serverlog_put(), _Role (+29 more)

### Community 12 - "Automod Filter Core"
Cohesion: 0.08
Nodes (43): add_escalation_rule(), _default_filter(), delete_escalation_rule(), detect_bad_words(), detect_caps_lock(), detect_emoji_spam(), detect_invites(), detect_links() (+35 more)

### Community 13 - "Test Fake Members"
Cohesion: 0.20
Nodes (36): eliminate_player(), update_game(), build(), _character(), _setup_game(), test_ability_already_used(), test_ability_dead_player(), test_ability_game_not_active() (+28 more)

### Community 14 - "Daily Topic Module"
Cohesion: 0.11
Nodes (41): add_topic(), already_posted_today(), delete_topic(), get_settings(), get_today_post_time(), is_valid_time(), mark_posted_today(), _normalized() (+33 more)

### Community 15 - "API Client Functions"
Cohesion: 0.06
Nodes (38): BlackjackGame, _build_deck(), can_double(), card_rank(), card_suit(), _deal_card(), dealer_play(), format_hand() (+30 more)

### Community 16 - "Bunker Game Core"
Cohesion: 0.07
Nodes (47): _Deck, default_bunker_capacity(), generate_characters(), has_moderator_access(), is_game_over(), _pick_additional_info(), _pick_age(), _pick_backpack_item() (+39 more)

### Community 17 - "Moderation Routes"
Cohesion: 0.05
Nodes (53): _assignable_roles(), ban_member(), dashboard_reason(), _get_guild_or_none(), get_moderation_log(), _get_target_or_response(), grant_role(), kick_member() (+45 more)

### Community 18 - "Bunker Discord Cog"
Cohesion: 0.08
Nodes (26): build_expulsion_result_embed(), build_game_started_embed(), build_lobby_cancelled_embed(), build_lobby_embed(), build_result_embed(), build_vote_embed(), BunkerCog, BunkerLobbyView (+18 more)

### Community 19 - "Mass Role Assignment"
Cohesion: 0.17
Nodes (18): FakePayload, _setup_config(), test_cleanup_missing_messages_keeps_entries_for_existing_messages(), test_cleanup_missing_messages_removes_entries_for_deleted_messages(), test_handle_reaction_change_add_grants_role_using_payload_member(), test_handle_reaction_change_ignores_bots_own_reaction(), test_handle_reaction_change_ignores_unconfigured_message(), test_handle_reaction_change_ignores_unmatched_emoji() (+10 more)

### Community 20 - "Embed Builder Routes"
Cohesion: 0.08
Nodes (55): create_embed_message(), create_embed_template(), delete_embed_template(), get_embed_message(), _get_guild_or_none(), _is_role_assignable(), list_embed_templates(), _parse_body() (+47 more)

### Community 21 - "Bot Entrypoint & Auth Middleware"
Cohesion: 0.20
Nodes (7): CTD, CTDCloseView, CTDView, _is_main_guild(), Button, Interaction, setup()

### Community 22 - "Frontend Package Deps"
Cohesion: 0.04
Nodes (46): dependencies, @phosphor-icons/react, react, react-dom, react-router-dom, tailwindcss, @tailwindcss/vite, devDependencies (+38 more)

### Community 23 - "Lockdown API Client"
Cohesion: 0.16
Nodes (25): add_round_event(), connect(), count_players(), create_ability_announcement(), get_ability_announcement(), get_active_game_in_channel(), get_db_path(), get_game_by_lobby_message() (+17 more)

### Community 24 - "Mafia DB Tests"
Cohesion: 0.10
Nodes (55): _display_name(), _is_id(), mafia_games_list(), mafia_get(), mafia_public_action(), mafia_public_state(), mafia_public_vote(), mafia_put() (+47 more)

### Community 25 - "Mafia Core Tests"
Cohesion: 0.08
Nodes (36): _FakeMember, _FakePermissions, isolated_config(), test_assign_roles_matches_scale_and_covers_all_players(), test_check_win_condition_mafia_wins_at_parity(), test_check_win_condition_no_winner_yet(), test_check_win_condition_town_wins_when_no_mafia(), test_get_settings_defaults() (+28 more)

### Community 26 - "Stream Notifications"
Cohesion: 0.10
Nodes (23): _public_sub(), Request, Response, streams_create(), streams_delete(), streams_list(), streams_update(), add_subscription() (+15 more)

### Community 27 - "Feedback Panel Tests"
Cohesion: 0.10
Nodes (33): bet_error(), flip_coin(), get_settings(), payout_amount(), Ядро модуля «Казино»: слоты и монетка на серверную валюту.  Без импорта discord, Настройки модуля сервера с дефолтами (выключен по умолчанию)., None — ставка допустима, иначе текст ошибки для игрока., Выигрыш с учётом преимущества казино (округление вниз). (+25 more)

### Community 28 - "Reaction Roles Tests"
Cohesion: 0.14
Nodes (29): create_reaction_role(), delete_reaction_role(), _get_guild_or_none(), _is_role_assignable(), list_channels(), list_emojis(), list_reaction_roles(), Request (+21 more)

### Community 29 - "Streams API Client"
Cohesion: 0.20
Nodes (19): add(), connect(), get_by_user(), get_db_path(), init(), list_all(), _now(), Connection (+11 more)

### Community 30 - "Voice Rooms Routes"
Cohesion: 0.11
Nodes (32): Request, Response, voice_panel_publish(), voice_room_delete(), voice_rooms_list(), build(), FakeVoiceChannel, isolated_db() (+24 more)

### Community 31 - "XP API Client"
Cohesion: 0.12
Nodes (30): test_audit_add_list_count_scoped_per_guild(), test_audit_list_orders_desc_and_filters_by_moderator(), test_voice_leaderboard_orders_by_voice_seconds(), test_xp_all_members_returns_only_guild_rows(), test_xp_leaderboard_and_rank_scoped_per_guild(), test_xp_reset_all_only_targets_one_guild(), test_xp_set_level_and_set_xp(), audit_add() (+22 more)

### Community 32 - "Mafia Discord Cog"
Cohesion: 0.12
Nodes (18): build_game_started_embed(), build_lobby_cancelled_embed(), build_lynch_result_embed(), build_morning_embed(), build_result_embed(), build_vote_embed(), role_label(), _frontend_url() (+10 more)

### Community 33 - "Feedback API Client"
Cohesion: 0.08
Nodes (39): Request, Response, verification_get(), verification_put(), build(), FakeInteraction, FakeResponse, Тесты кога «Верификация»: выключена по умолчанию, join-роль, кнопка. (+31 more)

### Community 34 - "Family DB Tests"
Cohesion: 0.12
Nodes (42): _create_legacy_schema(), isolated_db(), Тесты family_db: per-guild ростер/заявки/дни рождения + миграция старой схемы., Схема до Фазы 2.2б: синглтоны roster_msg/birthday_msg (id=1), single-PK     pen, test_birthday_message_roundtrip_and_isolation(), test_birthday_roundtrip_and_queries(), test_list_and_count_tickets_scoped_and_filtered(), test_migration_assigns_legacy_rows_to_main_guild() (+34 more)

### Community 35 - "Events & Embeds Client"
Cohesion: 0.09
Nodes (26): createEmbedMessage(), createEvent(), CreateEventSpec, deleteEmbedTemplate(), EmbedFieldSpec, EmbedMessagePayload, EmbedSpec, EmbedTemplate (+18 more)

### Community 36 - "Lockdown Routes"
Cohesion: 0.33
Nodes (11): _role(), test_activate_collects_errors_and_continues(), test_activate_respects_exempts(), test_activate_strips_permissions_and_saves_backup(), test_deactivate_restores_from_backup(), test_deactivate_without_backup_returns_none(), activate_antispam(), antispam_status() (+3 more)

### Community 37 - "Events Route Tests"
Cohesion: 0.12
Nodes (20): Messageable, _config_int(), generate_embed(), get_reminder_minutes(), _main_guild_id(), Bot, Button, Color (+12 more)

### Community 38 - "Mafia Public Route Tests"
Cohesion: 0.18
Nodes (31): build(), _setup_game(), test_action_dead_player(), test_action_deadline_passed(), test_action_game_not_active(), test_action_happy_path_and_resubmit(), test_action_invalid_target_not_alive(), test_action_self_target_allowed_for_doctor() (+23 more)

### Community 39 - "Family Tickets"
Cohesion: 0.13
Nodes (25): test_status_color_and_label(), status_color(), status_label(), add_custom_emoji_reaction(), ApplicationModalPart2, build_full_embed(), build_mini_embed(), build_ticket_result_embed() (+17 more)

### Community 40 - "Button Forms"
Cohesion: 0.12
Nodes (12): ButtonCreate, DynamicQuestionsModal, _get_allowed_role_ids(), _load_buttons_config(), BaseException, Interaction, Удаляет устаревшие записи кулдаунов., Возвращает оставшиеся секунды если кулдаун активен, иначе None. (+4 more)

### Community 41 - "Audit Log & Stats DB"
Cohesion: 0.06
Nodes (42): isolated_config(), Тесты ядра Вордла: целостность словаря, оценка догадок, слово дня, настройки., test_board_lines_pads_empty_rows(), test_day_number_epoch(), test_evaluate_all_green(), test_evaluate_duplicate_letters_consume_stock(), test_evaluate_green_priority_over_yellow(), test_evaluate_yellow_and_gray() (+34 more)

### Community 42 - "Giveaway Cog"
Cohesion: 0.11
Nodes (13): generate_embed(), GiveawayCog, GiveawayView, Bot, Button, Embed, Interaction, Range (+5 more)

### Community 43 - "Brackets Client Tests"
Cohesion: 0.08
Nodes (25): BracketDetail, BracketFormat, BracketMatch, BracketSummary, createBracket(), deleteBracket(), disableBracketShare(), enableBracketShare() (+17 more)

### Community 44 - "Bunker API Client"
Cohesion: 0.11
Nodes (23): applyBunkerAbility(), BunkerCardPools, BunkerCharacter, BunkerGameDetail, BunkerGameSummary, BunkerPlayerRef, BunkerSettings, fetchBunkerCardPools() (+15 more)

### Community 45 - "Automod API Client"
Cohesion: 0.11
Nodes (23): AutomodFilter, AutomodPunishment, AutomodSettings, createEscalationRule(), deleteEscalationRule(), EscalationAction, EscalationRule, fetchAutomod() (+15 more)

### Community 46 - "Reaction Roles Client"
Cohesion: 0.11
Nodes (24): fun_get(), fun_put(), Request, Response, test_spin_trigger_chance_grows(), test_spin_trigger_guaranteed_on_last_chamber(), isolated_config(), test_get_settings_defaults() (+16 more)

### Community 47 - "Event Builder UI"
Cohesion: 0.16
Nodes (7): EventBuilderView, EventPublishSelect, LimitsModal, OptionsModal, Interaction, TextModal, TextChannel

### Community 48 - "Family Core Tests"
Cohesion: 0.13
Nodes (20): _FakeGuild, _FakeGuildRef, _FakeMember, isolated_config(), test_build_birthday_text_groups_by_month_and_resolves_mentions(), test_can_manage_tickets_requires_configured_role(), test_has_staff_access_admin_bypasses_role_check(), test_has_staff_access_via_role() (+12 more)

### Community 49 - "XP Core Tests"
Cohesion: 0.11
Nodes (29): isolated_config(), test_deserved_roles(), test_level_formula_monotonic(), test_level_from_xp_roundtrip(), test_level_progress(), test_render_announce(), test_roll_text_xp_respects_multiplier(), test_voice_member_multiplier_lookup() (+21 more)

### Community 50 - "Event Publish Tests"
Cohesion: 0.20
Nodes (22): _poll_spec(), test_publish_event_poll_creates_matching_event_obj_and_view(), test_publish_event_role_reward_none_stays_none(), test_publish_event_tournament_creates_matching_event_obj_and_view(), test_validate_event_spec_accepts_valid_poll_spec(), test_validate_event_spec_accepts_valid_tournament_spec(), test_validate_event_spec_allows_missing_team_size_check_for_solo_mode(), test_validate_event_spec_rejects_description_too_long() (+14 more)

### Community 51 - "TypeScript Config"
Cohesion: 0.08
Nodes (23): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+15 more)

### Community 52 - "Bot Config Store"
Cohesion: 0.20
Nodes (21): get(), load_config(), migrate_from_env_if_needed(), save_config(), isolated_settings_db(), test_get_returns_default_when_key_missing(), test_get_returns_stored_value(), test_load_config_returns_empty_dict_when_missing() (+13 more)

### Community 53 - "Family Birthdays"
Cohesion: 0.15
Nodes (11): BirthdayCog, build_birthday_embed(), BaseException, Bot, Embed, Guild, Interaction, User (+3 more)

### Community 54 - "Anti-Spam Cog"
Cohesion: 0.09
Nodes (23): AuditPage, cancelSupply(), closeSupply(), createSupply(), fetchAudit(), fetchAutoRoles(), fetchSupplyOverview(), fetchWelcomeSettings() (+15 more)

### Community 55 - "news.py"
Cohesion: 0.15
Nodes (18): _is_id_like(), news_get(), news_put(), Request, Response, get_channel_map(), get_settings(), _main_guild_id() (+10 more)

### Community 56 - "events.py"
Cohesion: 0.14
Nodes (13): casino_top_command(), CasinoCog, CasinoLeaderboardView, check_loss_roles(), Bot, Button, Choice, Embed (+5 more)

### Community 57 - "test_feedback_routes.py"
Cohesion: 0.11
Nodes (29): FakeThread, test_fake_bot_fetch_user_falls_back_when_not_in_guild(), test_fake_bot_fetch_user_raises_when_nowhere_found(), test_fake_bot_get_channel_finds_channel_and_thread(), test_fake_bot_update_file_records_calls(), test_fake_thread_edit_records_archived_and_locked(), test_fake_thread_fetch_message_raises_not_found(), test_fake_thread_send_creates_and_stores_message() (+21 more)

### Community 58 - "FeedbackCategories.tsx"
Cohesion: 0.39
Nodes (4): LeaderboardView, Button, Interaction, Интерактивный лидерборд: сортировка по Опыту / Голосу + пагинация.

### Community 59 - "Docs.tsx"
Cohesion: 0.08
Nodes (17): Documentation Banner Image, DocsBanner(), DocNavItem, DocsSearch(), DocsSearchProps, DocsSidebar(), DocsSidebarProps, GROUP_ICONS (+9 more)

### Community 60 - "voice_rooms.py"
Cohesion: 0.08
Nodes (37): Тесты синглтона состояния панели голосовых комнат (voice_rooms, Фаза 2.2б).  Ран, test_panel_state_defaults_empty(), test_panel_state_round_trip(), Modal, VCTheme, apply_owner_permissions(), build_embed(), ChannelControlView (+29 more)

### Community 61 - "XPCog"
Cohesion: 0.14
Nodes (9): _Member, _Perms, XP_ADMIN_MAX, XP_ADMIN_MIN, Embed, Range, Пересчитывает уровень, синхронизирует роли-награды, шлёт уведомление., Приводит роли-награды участника в соответствие с его прогрессом. (+1 more)

### Community 62 - "auth.py"
Cohesion: 0.14
Nodes (33): callback(), _frontend(), invite_url(), list_guilds(), login(), logout(), me(), Request (+25 more)

### Community 63 - "resolve_guild_member()"
Cohesion: 0.18
Nodes (11): MemberLookupResult, resolve_guild_member(), FakeBot, FakeGuild, _StubHTTPException, _StubNotFound, test_falls_back_to_fetch_when_not_cached(), test_not_found_when_fetch_raises_notfound() (+3 more)

### Community 64 - "xp.py"
Cohesion: 0.20
Nodes (21): _int_in(), _is_id_list(), Request, Response, Вкладка «Участники» дашборда: весь ростер гильдии, а не только те,     кто уже, _serialize_row(), xp_card_bg_delete(), xp_card_bg_upload() (+13 more)

### Community 65 - "test_feedback_category_routes.py"
Cohesion: 0.13
Nodes (18): can_manage_guild_permissions(), has_dashboard_access(), has_manage_server(), has_super_admin_access(), manageable_guilds(), Контроль доступа к дашборду (модель MEE6, Фаза 2.3).  Доступ к серверу = право, DEPRECATED (Фаза 1, роль-модель). Оставлено до перевода auth/middleware на, Доступ к настройкам сервера: Manage Server или Administrator на этой гильдии. (+10 more)

### Community 66 - "Supply.tsx"
Cohesion: 0.10
Nodes (22): createFeedbackCategory(), deleteFeedbackCategory(), FeedbackCategoryFieldSpec, FeedbackCategorySpec, fetchFeedbackCategories(), fetchMassAssignStatus(), MassAssignStatus, MassAssignTarget (+14 more)

### Community 67 - "MassAssignModal.tsx"
Cohesion: 0.22
Nodes (17): build(), FakeChoice, FakeInteraction, FakeResponse, Тесты кога «Казино»: /слоты и /монетка — через .callback(), паттерн test_fun_cog, test_coinflip_disabled_module(), test_coinflip_house_edge_reduces_payout(), test_coinflip_loss() (+9 more)

### Community 68 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+11 more)

### Community 69 - ".__init__()"
Cohesion: 0.16
Nodes (9): CLEAR_MAX, CLEAR_MIN, ModerationCommandsCog, Bot, Interaction, Range, User, Ког слэш-команд модерации: /ban /kick /mute /unmute /unban /clear.  Каждое дейст (+1 more)

### Community 70 - "VoiceTracker"
Cohesion: 0.14
Nodes (8): is_active(), BaseException, Bot, VoiceState, Войс-трекер: единый учёт голосовых сессий.  Кормит сразу два модуля: - статис, setup(), VoiceSession, VoiceTracker

### Community 71 - "Interaction"
Cohesion: 0.20
Nodes (7): ApplicationModalPart1, ContinueApplicationView, OpenTicketView, Button, Interaction, setup(), TicketControlView

### Community 72 - "ensure_owner()"
Cohesion: 0.09
Nodes (37): Тесты ядра экономики: курс от XP, комиссии, валидация ставок, хук award_for_xp., test_award_for_xp_disabled_gives_nothing(), test_bet_error_cases(), test_bet_error_unlimited_when_max_zero(), test_claim_daily_bonus_consecutive_day_extends_streak(), test_claim_daily_bonus_first_time(), test_claim_daily_bonus_gap_resets_streak(), test_claim_daily_bonus_same_day_rejected() (+29 more)

### Community 73 - "family.py"
Cohesion: 0.29
Nodes (17): _decide_ticket(), _display_name(), family_birthday_delete(), family_birthday_set(), family_birthdays_list(), family_get(), family_put(), family_roster() (+9 more)

### Community 74 - "test_family_routes.py"
Cohesion: 0.09
Nodes (44): economy_get(), economy_put(), economy_set_balance(), economy_top(), Request, Response, Тесты economy_db: атомарные списания, переводы, топ, журнал., test_add_ignores_non_positive() (+36 more)

### Community 75 - "test_access.py"
Cohesion: 0.16
Nodes (19): isolated_db(), _create_legacy_schema(), isolated_db(), Тесты stats_db: per-guild изоляция XP/войс/аудита и миграция старой схемы.  Фаза, Схема до Фазы 2.2а: без guild_id (как в проде на мейн-сервере)., После миграции один user_id может существовать на разных серверах., test_migration_assigns_legacy_rows_to_main_guild(), test_migration_is_idempotent() (+11 more)

### Community 76 - "test_config_routes.py"
Cohesion: 0.30
Nodes (10): build(), test_get_auto_roles_defaults_to_empty_when_file_missing(), test_get_auto_roles_requires_auth(), test_get_auto_roles_returns_stored_values(), test_update_auto_roles_persists_valid_roles(), test_update_auto_roles_rejects_managed_role(), test_update_auto_roles_rejects_non_list_body(), test_update_auto_roles_rejects_role_above_bot() (+2 more)

### Community 77 - "RosterCog"
Cohesion: 0.21
Nodes (8): generate_roster_text(), Bot, Guild, Interaction, Live-ростер семьи: список участников по настроенным ролям.  Портировано из FamQ, Debounce: аккумулирует изменения и обновляет сообщение через 10 секунд., RosterCog, setup()

### Community 78 - "reaction_roles.py"
Cohesion: 0.14
Nodes (13): build_topic_message(), DailyTopicCog, BaseException, Bot, Ког «Ежедневная рубрика»: раз в день публикует тему/вопрос дня в заданный канал,, Публикует тему дня немедленно (используется циклом и ручным триггером         из, setup(), build() (+5 more)

### Community 79 - "PublicBunkerAction.tsx"
Cohesion: 0.09
Nodes (21): test_build_board_embed_finished_loss_reveals_answer(), File, _avatar_bytes(), BoardView, build_board_embed(), _card_file(), GuessModal, PlayNowView (+13 more)

### Community 80 - "Leaderboard.tsx"
Cohesion: 0.10
Nodes (36): _auto_emoji_config(), build(), enable_economy(), FakeInteraction, FakeMsg, FakeResponse, Тесты кога «Развлечения»: русская рулетка (исходы, таймаут, кулдаун) и эмодзи-ру, test_auto_emoji_channel_interval_limits_frequency() (+28 more)

### Community 81 - "VoiceManager"
Cohesion: 0.21
Nodes (21): get_settings(), Настройки модуля сервера с дефолтами (выключен по умолчанию)., assign_character(), create_game(), build(), _sample_character(), test_apply_ability_announcement(), test_apply_ability_announcement_not_found() (+13 more)

### Community 82 - "mafia.py"
Cohesion: 0.09
Nodes (9): command_reason(), format_duration(), parse_duration(), parse_mute_duration(), Ядро команд модерации (/ban /kick /unban /clear): парсинг и форматирование срока, Секунды из строки вида 10m/2h/7d/30s. ValueError с понятным текстом при неверном, Как parse_duration, но с проверкой лимита Discord в 28 дней., Человекочитаемое представление уже провалидированной строки длительности (10m -> (+1 more)

### Community 83 - "events.py"
Cohesion: 0.22
Nodes (24): build(), FakeInteraction, Тесты кога слэш-команд модерации: /ban /kick /unban /clear.  Команды вызываютс, test_ban_forbidden_reports_ephemeral_error(), test_ban_invalid_duration_format(), test_ban_permanent_default(), test_ban_requires_guild_context(), test_ban_with_duration_schedules_unban() (+16 more)

### Community 84 - "ChetBot"
Cohesion: 0.15
Nodes (14): Web Dashboard Index HTML, React Root Mount Element, React Entry Point Script, ChetBot, ChetBot Web Dashboard, ChetBot Official Documentation, aiohttp Dependency, aiohttp-session Dependency (+6 more)

### Community 85 - "ChannelInfo"
Cohesion: 0.08
Nodes (42): AppRunner, create_app(), json_error_middleware(), Application, Path, start_dashboard(), ConfigError, load_dashboard_config() (+34 more)

### Community 86 - "MafiaLobbyView"
Cohesion: 0.25
Nodes (16): build(), test_birthday_set_invalid_date(), test_birthday_set_unknown_member(), test_birthdays_crud(), test_get_defaults(), test_put_then_get(), test_put_validation(), test_requires_auth() (+8 more)

### Community 87 - "voice_logs.py"
Cohesion: 0.11
Nodes (33): isolated_state(), isolated_db(), Тесты wordle_db: игры дня, статистика со стриками, мета сервера., test_add_guess_accumulates_and_finishes(), test_group_streak_gap_resets(), test_group_streak_grows_and_resets(), test_last_announced_day_roundtrip(), test_list_day_games_filters_by_day() (+25 more)

### Community 88 - "test_auto_roles_routes.py"
Cohesion: 0.23
Nodes (17): build(), build_with_guild(), _full_config(), PUT /api/config не должен затирать ключи других разделов (авто-роли, приветствия, test_get_config_requires_auth(), test_get_config_returns_defaults_when_file_missing(), test_get_config_returns_stored_values(), test_put_config_preserves_foreign_keys() (+9 more)

### Community 89 - "Giveaways.tsx"
Cohesion: 0.14
Nodes (14): Embed, Guild, ChetBot, command_sync_mode(), get_main_guild_id(), main(), on_guild_join(), on_guild_remove() (+6 more)

### Community 90 - "PublicMafiaAction.tsx"
Cohesion: 0.21
Nodes (21): add_player(), get_player(), _make_game(), База, созданная до появления voice_channel_id/vote_message_id/unique_cards,, _sample_character(), test_add_player_rejects_duplicate(), test_assign_character_and_get_by_token(), test_create_and_get_game() (+13 more)

### Community 91 - "Welcome"
Cohesion: 0.20
Nodes (8): test_load_events_reads_fresh_after_external_write(), test_load_events_returns_empty_events_dict_when_file_missing(), test_save_then_load_roundtrips(), SelectOption, create_participation_view(), EventManageSelect, load_events(), View

### Community 92 - "access_middleware.py"
Cohesion: 0.12
Nodes (19): _has_legacy_role_access(), Переходный грант по роли на активном сервере (если задан DASHBOARD_ACCESS_ROLE_I, Гейт доступа к серверу (Фаза 2.3): сессия → активный сервер → Manage Server., Гейт для списка серверов бота — намеренно хардкод-роль, см. access.py., require_dashboard_access(), require_super_admin(), get_auto_roles(), _get_guild_or_none() (+11 more)

### Community 93 - "test_mafia_routes.py"
Cohesion: 0.27
Nodes (10): isolated_db(), isolated_state(), build(), isolated_state(), test_games_list(), test_get_defaults(), test_put_then_get(), test_put_validation() (+2 more)

### Community 94 - "test_warns_routes.py"
Cohesion: 0.18
Nodes (13): announceBunkerAbility(), BUNKER_FIELD_KEYS, BunkerFieldKey, BunkerPublicState, fetchPublicBunker(), revealBunkerFields(), submitBunkerVote(), FIELD_LABEL (+5 more)

### Community 95 - "test_xp_routes.py"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does SelectOption connect Mafia Game Engine to Discord Embed Builder, Supply Cog Tests?, Source Nodes

### Community 96 - "config.py"
Cohesion: 0.05
Nodes (41): activateLockdown(), AntiRaidSettings, ApiError, deactivateLockdown(), decideFeedbackCase(), FeedbackCaseDetail, FeedbackCaseSummary, fetchAntiRaidSettings() (+33 more)

### Community 97 - "setup_static_routes()"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Why does force_login() connect Mock Services & Unit Tests to a wide array of system modules and tests?, Source Nodes

### Community 98 - "FakeAsset"
Cohesion: 0.07
Nodes (42): make_moderation_app(), build(), isolated_config(), test_get_defaults_disabled(), test_put_then_get(), test_put_validation(), test_requires_login(), build() (+34 more)

### Community 99 - "plugins"
Cohesion: 0.22
Nodes (8): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema, oxc, typescript, warn

### Community 100 - "DocsSearch.tsx"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: Are the inferred relationships involving mock objects (FakeMember, FakeGuild, FakeBot, FakeRole) with DashboardConfig and _StubForbidden correct?, Source Nodes

### Community 101 - "xp_card.py"
Cohesion: 0.23
Nodes (8): build(), FakeFollowup, FakeInteraction, FakeResponse, Тесты /ранг: подтягивание экипированной косметики (рамка/титул) из магазина., test_rank_command_ignores_unequipped_owned_cosmetics(), test_rank_command_passes_equipped_frame_and_title(), test_rank_command_without_cosmetics_passes_none()

### Community 102 - "auto_roles.py"
Cohesion: 0.11
Nodes (12): CreateTeamCodeModal, DraftEvent, EventNotifyModal, Events, handle_registration(), JoinTeamCodeModal, Embed, rebuild_event_embed() (+4 more)

### Community 103 - "icons.svg"
Cohesion: 0.38
Nodes (6): Bluesky Icon, Discord Icon, Documentation Icon, GitHub Icon, Social Icon, X Icon

### Community 104 - "format_voice_time()"
Cohesion: 0.20
Nodes (4): Interaction, Invite, setup(), Welcome

### Community 105 - "DocsToc.tsx"
Cohesion: 0.40
Nodes (4): Answer, Outcome, Q: What connects schema, typescript, oxc to the rest of the system?, Source Nodes

### Community 108 - "Hero Image Graphic"
Cohesion: 1.00
Nodes (3): Hero Image Graphic, Cheterin Isometric Branding Concept, Layered Isometric Architecture Illustration

### Community 111 - "DocsSearch.tsx"
Cohesion: 0.26
Nodes (9): closeEvent(), deleteEvent(), EventParticipantTeamCode, fetchEventDetail(), notifyEventParticipants(), EventDetailPanel(), Props, pollDetail (+1 more)

### Community 112 - "test_fun_routes.py"
Cohesion: 0.20
Nodes (14): Тесты рендера карточки ранга: базовый рендер, кастомная рамка и титул., test_hex_to_rgb(), test_render_rank_card_long_title_does_not_crash(), test_render_rank_card_with_custom_frame_and_title(), test_render_rank_card_without_cosmetics_produces_png(), _background(), _circle_avatar(), _font() (+6 more)

### Community 120 - "DocsSearch.tsx"
Cohesion: 0.24
Nodes (12): build(), FakeDailyTopicCog, test_create_topic_validation(), test_get_defaults(), test_post_now(), test_post_now_no_cog(), test_post_now_requires_channel(), test_post_now_requires_topics() (+4 more)

### Community 121 - "test_members_list.py"
Cohesion: 0.19
Nodes (24): get_player_by_token(), Полная перезапись карточки — используется админ-панелью при ручном применении сп, set_player_character(), bunker_apply_ability(), bunker_card_pools(), bunker_game_detail(), bunker_games_list(), bunker_get() (+16 more)

### Community 122 - "test_member_detail.py"
Cohesion: 0.41
Nodes (13): utcnow(), build(), fresh_member(), Тесты кога «Антирейд»: выключен по умолчанию, детект всплеска, действия., test_below_threshold_does_not_trigger(), test_cooldown_prevents_immediate_retrigger(), test_disabled_by_default_does_nothing(), test_explicitly_disabled_ignores_burst() (+5 more)

### Community 123 - "DocsToc.tsx"
Cohesion: 0.24
Nodes (23): build(), FakeInteraction, Тесты кога Вордла — вызов через .callback()/методы кога, паттерн test_xp_command, test_announce_nobody_played(), test_announce_nobody_won_reveals_word(), test_announce_with_winner_crowns_best_and_streak(), test_commands_disabled_module(), test_daily_guess_edits_existing_live_card() (+15 more)

### Community 124 - "init"
Cohesion: 0.08
Nodes (46): apiFetch(), banMember(), createDailyTopic(), createMemberWarn(), DailyTopicSettings, decideFamilyTicket(), deleteDailyTopic(), deleteFamilyBirthday() (+38 more)

### Community 125 - "Request"
Cohesion: 0.14
Nodes (15): is_suspicious_account(), JoinTracker, datetime, Ядро модуля «Антирейд»: детект всплеска входов новых участников.  Без импорта di, Считается ли аккаунт «свежим» (подозрительным) на момент входа., Скользящее окно недавних «подозрительных» входов на один сервер.      Чистая стр, Добавить вход и вернуть текущее число подозрительных входов в окне., isolated_config() (+7 more)

### Community 126 - "Response"
Cohesion: 0.19
Nodes (8): CosmeticsView, Bot, Ког «Экономика»: баланс, переводы, топ и магазин ролей.  Монеты начисляются ав, Кнопки покупки по товарам магазина (эфемерное сообщение)., Селекторы «Рамка» / «Титул» из уже купленных предметов (эфемерное сообщение)., setup(), ShopView, Select

### Community 127 - "Button.tsx"
Cohesion: 0.21
Nodes (6): BALANCE_ADMIN_MAX, EconomyCog, Guild, Interaction, Range, Строка товара в /магазин — раньше пыталась резолвить role_id для         ЛЮБОГО

### Community 128 - "events.py"
Cohesion: 0.22
Nodes (14): Phase 2.4: Bot Detached from GUILD_ID, CTD Main-Guild Gate, Phase 2.2: Guild Dimension for Module Data, MAIN_GUILD_ID Constant, Multi-Guild Migration Plan (MEE6-level), News Relay as Super-Admin Feature, Phase 1: Text Cleanup and Explicit Limits, Phase 4: Load and Resilience (MEE6 Level) (+6 more)

### Community 129 - "wordle_card.py"
Cohesion: 0.21
Nodes (16): ImageDraw, _avatar_image(), _circle_avatar(), _draw_grid(), _font(), _grid_size(), _placeholder_avatar(), FreeTypeFont (+8 more)

### Community 130 - "events.py"
Cohesion: 0.32
Nodes (13): close_event_route(), create_event(), delete_event_route(), get_event(), list_events(), notify_event_route(), Request, Response (+5 more)

### Community 131 - "load_events"
Cohesion: 0.11
Nodes (21): ChannelInfo, fetchMafiaGames(), fetchMafiaSettings(), fetchNewsSettings(), fetchServerLog(), MafiaGameSummary, MafiaSettings, NewsSettings (+13 more)

### Community 132 - "test_supply_routes.py"
Cohesion: 0.15
Nodes (47): build(), cosmetics_shop_config(), FakeInteraction, Тесты кога «Экономика»: /баланс /перевести /монеты-топ /магазин — через .callbac, shop_config(), test_balance_disabled_module(), test_balance_shows_amount_and_rank(), test_cosmetics_command_empty() (+39 more)

### Community 133 - "PublicMafiaAction.tsx"
Cohesion: 0.22
Nodes (10): fetchPublicMafia(), MafiaPublicState, submitMafiaAction(), submitMafiaVote(), PHASE_LABEL, PublicMafiaActionPage(), ROLE_HINT, ROLE_LABEL (+2 more)

### Community 134 - "wordle.py"
Cohesion: 0.29
Nodes (9): get_settings(), Настройки модуля сервера с дефолтами. enabled=False по умолчанию — модуль не, save_config(), antiraid_get(), antiraid_put(), Request, Response, test_settings_disabled_by_default() (+1 more)

### Community 135 - "test_warns_routes.py"
Cohesion: 0.22
Nodes (9): createGiveaway(), endGiveaway(), fetchGiveawayOverview(), Giveaway, GiveawayOverview, rerollGiveaway(), GiveawaysPage(), STATUS_LABEL (+1 more)

### Community 136 - "Supply.tsx"
Cohesion: 0.29
Nodes (9): Request, Response, wordle_get(), wordle_put(), test_settings_defaults(), test_settings_roundtrip(), get_settings(), Настройки модуля сервера с дефолтами (выключен по умолчанию).      channel_id — (+1 more)

### Community 137 - ".__init__"
Cohesion: 0.11
Nodes (29): createReactionRole(), createStreamSubscription(), CtdConfig, CustomEmoji, deleteReactionRole(), deleteStreamSubscription(), fetchChannels(), fetchCtdConfig() (+21 more)

### Community 138 - "test_roles.py"
Cohesion: 0.27
Nodes (7): build_lobby_embed(), MafiaLobbyView, Button, Interaction, PLAYERS_CEIL, PLAYERS_FLOOR, Range

### Community 139 - "test_wordle_routes.py"
Cohesion: 0.16
Nodes (21): get_stats(), build(), FakeInteraction, FakeMessage, FakeResponse, make_game(), Тесты кога «Блэкджек»: гейты, ставки, натуральный BJ, кнопки Ещё/Стоп/Удвоить., start_view_game() (+13 more)

### Community 140 - "format_voice_time"
Cohesion: 0.21
Nodes (12): build(), Test that partial failures during deactivate are logged with Ошибки field in emb, Test that activate returns 503 when guild is unavailable., Test that partial failures are logged with Ошибки field in embed., _StubForbidden, test_activate_guild_unavailable_503(), test_activate_then_status_then_deactivate(), test_activate_with_partial_errors_logs_error_field() (+4 more)

### Community 141 - "test_feedback_panel_routes.py"
Cohesion: 0.10
Nodes (37): reset_settings_db(), Тесты settings_db: хранилище настроек модулей per-guild (Фаза 2.1)., test_get_missing_returns_empty_dict(), test_get_returns_a_copy_not_the_cached_reference(), test_get_uses_cache_without_hitting_db_again(), test_has_reflects_existing_rows(), test_isolated_by_guild_id(), test_isolated_by_module() (+29 more)

### Community 142 - "DocsSearch.tsx"
Cohesion: 0.29
Nodes (16): FakeAuditLogEntry, Одна запись аудита для guild.audit_logs() — только то, что нужно     serverlog., build(), enable(), last_embed(), Embed, Тесты кога «Логирование»: стиль эмбедов (description+footer+thumbnail), формати, test_member_join_embed_style() (+8 more)

### Community 143 - "FakeResponse"
Cohesion: 0.57
Nodes (6): get_ctd(), put_ctd(), Request, Response, CTD (тикеты) — привилегия основного сервера (Фаза 2b MULTIGUILD_PLAN.md).  Настр, _require_main_guild()

### Community 144 - "FakeResponse"
Cohesion: 0.52
Nodes (6): build_client_app(), test_invalid_pagination_returns_400(), test_lists_members_with_pagination_fields(), test_pagination_slices_and_caps_page_size(), test_requires_auth(), test_search_matches_name_and_display_name_case_insensitive()

### Community 145 - "test_news_routes.py"
Cohesion: 0.33
Nodes (4): AntiRaidCog, Bot, Ког «Антирейд»: автоматический Lockdown при всплеске входов новых участников.  В, setup()

### Community 146 - "test_auto_roles_routes.py"
Cohesion: 0.09
Nodes (32): connect(), _ensure_row(), get_db_path(), init(), leaderboard(), Connection, SQLite-хранилище статистики казино (победы/поражения)., result: 'win', 'lose', 'push (+24 more)

### Community 147 - "test_supply_routes.py"
Cohesion: 0.06
Nodes (86): force_login(), build(), test_create_bracket_from_event(), test_create_bracket_from_event_rejects_tampered_entries(), test_create_bracket_from_missing_event_404s(), test_create_bracket_manual(), test_create_bracket_rejects_blank_title(), test_create_bracket_rejects_fewer_than_two_entries() (+78 more)

### Community 148 - "lockdown.py"
Cohesion: 0.39
Nodes (8): lockdown_activate(), lockdown_deactivate(), lockdown_status(), _log(), Request, Response, get_mention_exempt_ids(), get_mentionable_exempt_ids()

### Community 149 - "test_xp_routes.py"
Cohesion: 0.17
Nodes (20): MassAssignJob, run_mass_assign(), build(), test_mass_assign_all_except_bots_completes(), test_mass_assign_concurrent_requests_only_one_job_starts(), test_mass_assign_job_marked_failed_on_unexpected_exception(), test_mass_assign_rejects_role_above_bot(), test_mass_assign_rejects_second_job_while_running() (+12 more)

### Community 150 - "test_wordle_routes.py"
Cohesion: 0.17
Nodes (9): channel_allowed(), _fmt_voice(), member_has_ignored_role(), Bot, Guild, Message, Ког системы уровней: XP за текст, обработка уровней и наград, /ранг.  XP за во, Формат времени голоса Ч:ММ:СС (как в JuniperBot). (+1 more)

### Community 151 - "format_voice_time"
Cohesion: 0.33
Nodes (5): Lockdown, Choice, Guild, Interaction, setup()

### Community 152 - "FakeVoiceChannel"
Cohesion: 0.26
Nodes (19): test_xp_add_text_and_get_scoped_per_guild(), test_xp_add_text_increments_messages_and_ts(), test_xp_reset_member_only_targets_one_guild(), build(), FakeInteraction, Тесты команд /xp (add/set/clear) и /leaders в XPCog — вызов через .callback(),, test_leaders_disabled_module(), test_leaders_empty_leaderboard() (+11 more)

### Community 153 - "test_economy_routes.py"
Cohesion: 0.36
Nodes (12): automod_create_escalation(), automod_delete_escalation(), automod_get(), automod_update_enabled(), automod_update_escalation(), automod_update_filter(), automod_update_manual_warn_duration(), _is_str_list() (+4 more)

### Community 154 - "auto_roles.py"
Cohesion: 0.36
Nodes (11): Client, get_log_channel_id(), log_action(), log_error(), log_security(), log_unhide_action(), Color, Exception (+3 more)

### Community 155 - "_FakeMember"
Cohesion: 0.43
Nodes (7): build(), isolated_config(), test_get_defaults(), test_put_allows_unlimited_max_bet(), test_put_then_get(), test_put_validation(), test_requires_login()

### Community 156 - "require_dashboard_access"
Cohesion: 0.30
Nodes (11): build(), isolated_config(), test_escalation_crud(), test_escalation_validation(), test_get_defaults(), test_requires_auth(), test_update_filter(), test_update_filter_not_found() (+3 more)

### Community 158 - "config.py"
Cohesion: 0.47
Nodes (8): _check_channel(), _check_role(), get_config(), Request, Response, update_config(), _validate_relations(), _validate_structure()

### Community 160 - ".start_lobby"
Cohesion: 0.09
Nodes (28): BotConfig, deleteCardBg(), fetchConfig(), fetchXpLeaderboard(), fetchXpOverview(), resetAllXp(), resetMemberXp(), setMemberXp() (+20 more)

### Community 161 - "test_audit.py"
Cohesion: 0.07
Nodes (27): audit_middleware(), describe_action(), Request, Аудит действий дашборда: каждое мутирующее действие модератора пишется в stats.d, DashboardConfig, guild_context_middleware(), Request, Per-request guild-контекст (Фаза 2.3).  Раньше гильдия была одна на всё приложен (+19 more)

### Community 162 - "test_news_routes.py"
Cohesion: 0.31
Nodes (10): build(), isolated_config(), Ретрансляция новостей — привилегия мейна (Фаза 2b): доступ только у супер-админа, test_forbidden_for_non_super_admin(), test_get_defaults(), test_put_rejects_log_channel_outside_main_guild(), test_put_rejects_target_channel_outside_main_guild(), test_put_then_get() (+2 more)

### Community 163 - "test_feedback_panel_routes.py"
Cohesion: 0.36
Nodes (8): build(), test_get_welcome_settings_defaults_to_enabled_when_file_missing(), test_get_welcome_settings_requires_auth(), test_get_welcome_settings_returns_stored_values(), test_update_welcome_settings_persists(), test_update_welcome_settings_rejects_non_boolean(), test_update_welcome_settings_rejects_non_dict_body(), test_update_welcome_settings_requires_auth()

### Community 164 - "test_bunker_cog.py"
Cohesion: 0.40
Nodes (13): get_game(), upsert_vote(), build(), _cleanup_timer(), _make_lobby(), Тесты игрового цикла кога «Бункер»: старт игры (раздача карточек, голосовой кана, Полный цикл: старт (4 игрока, вместимость 2) -> два раунда голосований -> игра з, test_end_game_deletes_voice_channel() (+5 more)

### Community 166 - "test_fun_routes.py"
Cohesion: 0.39
Nodes (8): build(), isolated_config(), test_get_defaults(), test_put_auto_emoji_roundtrip_and_validation(), test_put_then_get(), test_put_validation(), test_put_zero_disables_punishment_and_cooldown(), test_requires_auth()

### Community 167 - "test_auto_roles_routes.py"
Cohesion: 0.33
Nodes (6): Request, Response, voice_stats(), test_format_voice_time(), format_voice_time(), Человекочитаемое время войса: «2 нед. 1 д. 3 ч.»

### Community 168 - "Phase 2.3: OAuth Guilds Scope and Server Selection"
Cohesion: 0.50
Nodes (4): require_dashboard_access Middleware, Manage Server Access Model, Phase 2.3: OAuth Guilds Scope and Server Selection, Super-Admin Check Against Main Guild

### Community 170 - "Phase 3: RU/EN i18n Infrastructure"
Cohesion: 0.50
Nodes (4): Bilingual Bunker Game Cards, Phase 3: RU/EN i18n Infrastructure, Slash Command Localization, Two-Level Language Model

### Community 171 - "daily_topic.py"
Cohesion: 0.67
Nodes (3): audit_list(), Request, Response

### Community 173 - "test_ctd_routes.py"
Cohesion: 0.36
Nodes (8): build(), isolated_settings_db(), CTD-настройки — привилегия мейна (Фаза 2b): роут доступен только когда активный, test_ctd_forbidden_when_active_guild_not_main(), test_ctd_requires_auth(), test_get_ctd_defaults_on_main_guild(), test_put_and_get_ctd_round_trip(), test_put_ctd_404_when_role_missing()

### Community 180 - "init"
Cohesion: 0.40
Nodes (5): init(), isolated_state(), isolated_db(), isolated_state(), isolated_state()

## Knowledge Gaps
- **251 isolated node(s):** `$schema`, `typescript`, `oxc`, `react/rules-of-hooks`, `warn` (+246 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SelectOption` connect `Welcome` to `.start_lobby`, `Bunker API Client`?**
  _High betweenness centrality (0.258) - this node is a cross-community bridge._
- **Why does `load_events()` connect `Welcome` to `events.py`, `Test Fake Bot`, `auto_roles.py`, `Tournament Brackets`, `test_feedback_panel_routes.py`, `Event Publish Tests`?**
  _High betweenness centrality (0.212) - this node is a cross-community bridge._
- **Why does `get()` connect `test_feedback_panel_routes.py` to `Supply Module`, `Test Fake Channels`, `Test Fake Bot`, `wordle.py`, `Tournament Brackets`, `Feedback Cases`, `Giveaways Routes`, `Supply.tsx`, `Server Event Logging`, `Automod Filter Core`, `Daily Topic Module`, `Moderation Routes`, `Embed Builder Routes`, `Mafia Core Tests`, `Stream Notifications`, `Feedback Panel Tests`, `Reaction Roles Tests`, `Feedback API Client`, `Lockdown Routes`, `Button Forms`, `Reaction Roles Client`, `Family Core Tests`, `news.py`, `voice_rooms.py`, `xp.py`, `ensure_owner()`, `VoiceManager`, `Welcome`?**
  _High betweenness centrality (0.121) - this node is a cross-community bridge._
- **Are the 36 inferred relationships involving `FakeMember` (e.g. with `DashboardConfig` and `_StubForbidden`) actually correct?**
  _`FakeMember` has 36 INFERRED edges - model-reasoned connections that need verification._
- **Are the 36 inferred relationships involving `FakeGuild` (e.g. with `DashboardConfig` and `_StubForbidden`) actually correct?**
  _`FakeGuild` has 36 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `FakeBot` (e.g. with `DashboardConfig` and `_StubForbidden`) actually correct?**
  _`FakeBot` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `FakeChannel` (e.g. with `DashboardConfig` and `FakeDailyTopicCog`) actually correct?**
  _`FakeChannel` has 12 INFERRED edges - model-reasoned connections that need verification._