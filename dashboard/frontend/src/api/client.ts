export interface DashboardUser {
  id: string
  username?: string
  avatar?: string | null
  is_admin?: boolean
  is_super_admin: boolean
  is_main_guild?: boolean
  active_guild_id: string | null
  active_guild_name?: string | null
  active_guild_icon?: string | null
}

export async function fetchCurrentUser(): Promise<DashboardUser | null> {
  const response = await fetch('/api/auth/me', { credentials: 'include' })
  if (response.status === 401) {
    return null
  }
  if (response.status === 403) {
    const err = new Error('access_denied')
    err.name = 'AccessDeniedError'
    throw err
  }
  if (!response.ok) {
    throw new Error(`Failed to fetch current user: ${response.status}`)
  }
  return response.json()
}

export async function logout(): Promise<void> {
  await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
}

export function loginUrl(): string {
  return '/api/auth/login'
}

export interface ManageableGuild {
  id: string
  name: string
  icon: string | null
  has_bot: boolean
}

export async function fetchManageableGuilds(): Promise<ManageableGuild[]> {
  const data = await apiFetch<{ guilds: ManageableGuild[] }>('/api/auth/guilds')
  return data.guilds
}

export async function selectGuild(guildId: string): Promise<void> {
  await apiFetch('/api/auth/select-guild', jsonInit('POST', { guild_id: guildId }))
}

export async function fetchInviteUrl(guildId?: string): Promise<string> {
  const query = guildId ? `?guild_id=${encodeURIComponent(guildId)}` : ''
  const data = await apiFetch<{ url: string }>(`/api/auth/invite-url${query}`)
  return data.url
}

export interface ServerLanguage {
  code: 'ru' | 'en'
}

export async function fetchLanguage(): Promise<ServerLanguage> {
  return apiFetch<ServerLanguage>('/api/language')
}

/** moduleKey -> enabled, aggregated across the guild's *_core settings. Powers the sidebar's disabled-module filter. */
export async function fetchModules(): Promise<Record<string, boolean>> {
  const data = await apiFetch<{ modules: Record<string, boolean> }>('/api/modules')
  return data.modules
}

export async function updateLanguage(code: ServerLanguage['code']): Promise<ServerLanguage> {
  return apiFetch<ServerLanguage>('/api/language', jsonInit('PUT', { code }))
}

export class ApiError extends Error {
  status: number
  body: Record<string, unknown>

  constructor(status: number, message: string, body: Record<string, unknown> = {}) {
    super(message)
    this.status = status
    this.body = body
    this.name = 'ApiError'
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { credentials: 'include', ...init })
  if (!response.ok) {
    let body: Record<string, unknown> = {}
    let detail = ''
    try {
      const parsed = (await response.json()) as Record<string, unknown>
      if (parsed && typeof parsed === 'object') {
        body = parsed
        detail = typeof parsed.error === 'string' ? parsed.error : ''
      }
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(response.status, detail || `HTTP ${response.status}`, body)
  }
  return response.json() as Promise<T>
}

const jsonInit = (method: string, body?: unknown): RequestInit => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
})

export interface MemberSummary {
  id: string
  username: string
  display_name: string
  avatar: string | null
  role_count: number
  joined_at: string | null
  is_bot: boolean
}

export interface MembersPage {
  total: number
  page: number
  page_size: number
  members: MemberSummary[]
}

export interface RoleChip {
  id: string
  name: string
  color: string
}

export interface MemberDetail extends Omit<MemberSummary, 'role_count'> {
  created_at: string
  roles: RoleChip[]
  invite_stats: { joins: number; leaves: number; invites: number }
  feedback_case_count: number
}

export interface RoleInfo extends RoleChip {
  position: number
}

export interface LockdownStatus {
  active: boolean
  role_count: number
}

export function fetchMembers(search: string, page: number, pageSize = 20): Promise<MembersPage> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
  if (search) params.set('search', search)
  return apiFetch(`/api/members?${params}`)
}

export function fetchMemberDetail(id: string): Promise<MemberDetail> {
  return apiFetch(`/api/members/${id}`)
}

export async function banMember(id: string, reason: string, deleteMessageDays: 0 | 1 | 7): Promise<void> {
  await apiFetch(`/api/members/${id}/ban`, jsonInit('POST', { reason, delete_message_days: deleteMessageDays }))
}

export async function kickMember(id: string, reason: string): Promise<void> {
  await apiFetch(`/api/members/${id}/kick`, jsonInit('POST', { reason }))
}

export async function timeoutMember(id: string, reason: string, duration: string): Promise<void> {
  await apiFetch(`/api/members/${id}/timeout`, jsonInit('POST', { reason, duration }))
}

export async function untimeoutMember(id: string, reason = ''): Promise<void> {
  await apiFetch(`/api/members/${id}/timeout`, jsonInit('DELETE', { reason }))
}

export async function fetchRoles(): Promise<RoleInfo[]> {
  const body = await apiFetch<{ roles: RoleInfo[] }>('/api/roles')
  return body.roles
}

export async function grantRole(memberId: string, roleId: string): Promise<void> {
  await apiFetch(`/api/members/${memberId}/roles`, jsonInit('POST', { role_id: roleId }))
}

export async function revokeRole(memberId: string, roleId: string): Promise<void> {
  await apiFetch(`/api/members/${memberId}/roles/${roleId}`, jsonInit('DELETE'))
}

export function fetchLockdownStatus(): Promise<LockdownStatus> {
  return apiFetch('/api/lockdown/status')
}

export async function activateLockdown(): Promise<void> {
  await apiFetch('/api/lockdown/activate', jsonInit('POST'))
}

export async function deactivateLockdown(): Promise<void> {
  await apiFetch('/api/lockdown/deactivate', jsonInit('POST'))
}

export interface ModerationLogEntry {
  type:
    | 'spam_punish'
    | 'tempban'
    | 'manual_ban'
    | 'manual_kick'
    | 'warn_manual'
    | 'command_ban'
    | 'command_kick'
    | 'command_mute'
    | 'command_unmute'
    | 'command_unban'
    | 'command_clear'
    | 'antiraid_trigger'
    | 'verification_pass'
    | 'verification_expired'
  timestamp: string
  user_id: string
  user_display: string
  moderator_id: string | null
  moderator_display: string | null
  reason: string
  extra: string
}

export async function fetchModerationLog(): Promise<ModerationLogEntry[]> {
  const body = await apiFetch<{ events: ModerationLogEntry[] }>('/api/moderation-log')
  return body.events
}

export type MassAssignTarget = 'all' | 'all_except_bots' | 'selected'

export interface MassAssignStatus {
  status: 'running' | 'completed' | 'failed'
  total: number
  processed: number
  succeeded: number
  skipped: number
  failed: number
  errors: string[]
}

export async function startMassAssign(
  roleId: string,
  target: MassAssignTarget,
  memberIds?: string[],
): Promise<string> {
  const body: Record<string, unknown> = { target }
  if (memberIds) body.member_ids = memberIds
  const result = await apiFetch<{ job_id: string }>(`/api/roles/${roleId}/mass-assign`, jsonInit('POST', body))
  return result.job_id
}

export function fetchMassAssignStatus(jobId: string): Promise<MassAssignStatus> {
  return apiFetch(`/api/roles/mass-assign/${jobId}`)
}

export interface ReactionRolePair {
  emoji: string
  role_id: string
}

export interface ReactionRoleEntry {
  message_id: string
  channel_id: string
  pairs: ReactionRolePair[]
}

export interface CustomEmoji {
  id: string
  name: string
  url: string
}

export interface ChannelInfo {
  id: string
  name: string
  category?: string
  /** Bot can View Channel in this channel. Omitted/true = usable. */
  bot_can_view?: boolean
  /** Bot can Send Messages in this channel. Omitted/true = usable. */
  bot_can_send?: boolean
  /** Synthetic client-side flag: a saved channel_id no longer present in fetchChannels() — the channel was deleted. */
  deleted?: boolean
}

/** Channel is unusable for the bot (not visible, cannot send, or no longer exists). */
export function isChannelDead(ch: {
  bot_can_view?: boolean
  bot_can_send?: boolean
  deleted?: boolean
}): boolean {
  return ch.deleted === true || ch.bot_can_view === false || ch.bot_can_send === false
}

/** Synthesizes a placeholder option for a saved channel_id missing from fetchChannels() so it still
 * renders (marked deleted) instead of silently falling back to a blank/placeholder Select. */
export function syntheticDeletedChannel(id: string): ChannelInfo {
  return { id, name: `#${id}`, deleted: true }
}

/** Same as syntheticDeletedChannel, but labeled as a role (`@id`) for role pickers. */
export function syntheticDeletedRole(id: string): ChannelInfo {
  return { id, name: `@${id}`, deleted: true }
}

export async function fetchReactionRoles(): Promise<ReactionRoleEntry[]> {
  const body = await apiFetch<{ reaction_roles: ReactionRoleEntry[] }>('/api/reaction-roles')
  return body.reaction_roles
}

export function createReactionRole(
  channelId: string,
  messageId: string,
  pairs: ReactionRolePair[],
): Promise<ReactionRoleEntry> {
  return apiFetch(
    '/api/reaction-roles',
    jsonInit('POST', { channel_id: channelId, message_id: messageId, pairs }),
  )
}

export function updateReactionRole(messageId: string, pairs: ReactionRolePair[]): Promise<ReactionRoleEntry> {
  return apiFetch(`/api/reaction-roles/${messageId}`, jsonInit('PUT', { pairs }))
}

export async function deleteReactionRole(messageId: string): Promise<void> {
  await apiFetch(`/api/reaction-roles/${messageId}`, jsonInit('DELETE'))
}

export async function fetchEmojis(): Promise<CustomEmoji[]> {
  const body = await apiFetch<{ emojis: CustomEmoji[] }>('/api/emojis')
  return body.emojis
}

export async function fetchChannels(): Promise<ChannelInfo[]> {
  const body = await apiFetch<{ channels: ChannelInfo[] }>('/api/channels')
  return body.channels
}

export interface EmbedFieldSpec {
  name: string
  value: string
  inline: boolean
}

export interface EmbedSpec {
  title: string
  description: string
  url: string
  color: string
  author: { name: string; url: string; icon_url: string }
  footer: { text: string; icon_url: string }
  image: { url: string }
  thumbnail: { url: string }
  timestamp: string | null
  fields: EmbedFieldSpec[]
}

export interface EmbedMessagePayload {
  content: string
  embed: EmbedSpec
  role_ids: string[]
}

export interface EmbedMessageResult {
  message_id: string
  channel_id: string
}

export function createEmbedMessage(channelId: string, payload: EmbedMessagePayload): Promise<EmbedMessageResult> {
  return apiFetch('/api/embed-messages', jsonInit('POST', { channel_id: channelId, ...payload }))
}

export function fetchEmbedMessage(channelId: string, messageId: string): Promise<EmbedMessagePayload> {
  return apiFetch(`/api/embed-messages/${channelId}/${messageId}`)
}

export function updateEmbedMessage(
  channelId: string,
  messageId: string,
  payload: EmbedMessagePayload,
): Promise<EmbedMessageResult> {
  return apiFetch(`/api/embed-messages/${channelId}/${messageId}`, jsonInit('PUT', payload))
}

export interface FeedbackCaseSummary {
  case_id: string
  category_key: string
  category_title: string
  submitter_id: string
  submitter_display: string
  status: 'pending' | 'approved' | 'denied'
  created_at: string | null
}

export interface FeedbackCaseField {
  key: string
  label: string
  value: string
}

export interface FeedbackCaseDetail extends FeedbackCaseSummary {
  fields: FeedbackCaseField[]
  public_channel_id: string | null
  public_message_id: string | null
  thread_id: string | null
}

export async function fetchFeedbackCases(status?: string): Promise<FeedbackCaseSummary[]> {
  const path = status ? `/api/feedback-cases?status=${status}` : '/api/feedback-cases'
  const body = await apiFetch<{ cases: FeedbackCaseSummary[] }>(path)
  return body.cases
}

export function fetchFeedbackCaseDetail(caseId: string): Promise<FeedbackCaseDetail> {
  return apiFetch(`/api/feedback-cases/${caseId}`)
}

export async function decideFeedbackCase(caseId: string, approved: boolean): Promise<void> {
  await apiFetch(`/api/feedback-cases/${caseId}/decide`, jsonInit('POST', { approved }))
}

export interface FeedbackCategoryFieldSpec {
  key: string
  label: string
  style: 'short' | 'paragraph'
  required: boolean
  max_length: number
}

export interface FeedbackCategorySpec {
  key: string
  title: string
  button_label: string
  channel_id: string
  case_prefix: string
  case_title: string
  thread_name: string
  review_role_ids: string[]
  approved_text: string
  denied_text: string
  modal_title: string
  fields: FeedbackCategoryFieldSpec[]
  mini_summary_key: string
}

export async function fetchFeedbackCategories(): Promise<FeedbackCategorySpec[]> {
  const body = await apiFetch<{ categories: FeedbackCategorySpec[] }>('/api/feedback-categories')
  return body.categories
}

export function createFeedbackCategory(spec: FeedbackCategorySpec): Promise<FeedbackCategorySpec> {
  return apiFetch('/api/feedback-categories', jsonInit('POST', spec))
}

export function updateFeedbackCategory(
  key: string,
  spec: Omit<FeedbackCategorySpec, 'key'>,
): Promise<FeedbackCategorySpec> {
  return apiFetch(`/api/feedback-categories/${key}`, jsonInit('PUT', spec))
}

export async function deleteFeedbackCategory(key: string): Promise<void> {
  await apiFetch(`/api/feedback-categories/${key}`, jsonInit('DELETE'))
}

export function publishFeedbackPanel(channelId: string): Promise<{ ok: boolean; message_id: string }> {
  return apiFetch('/api/feedback-panel/publish', jsonInit('POST', { channel_id: channelId }))
}

export interface EventParticipantSolo {
  user_id: string
  ign: string
}

export interface EventParticipantTeamCaptain {
  user_id: string
  team_name: string
  members: string
}

export interface EventParticipantTeamCodeMember {
  user_id: string
  ign: string
  is_captain: boolean
}

export interface EventParticipantTeamCode {
  team_code: string
  team_name: string
  members: EventParticipantTeamCodeMember[]
}

export interface EventPollOption {
  label: string
  votes: number
  percent: number
}

export interface EventSummary {
  message_id: string
  type: 'tournament' | 'poll'
  title: string
  status: 'open' | 'closed'
  channel_id: string
  count: number
}

export interface EventDetail extends EventSummary {
  description: string
  role_reward: string | null
  mode?: 'solo' | 'team_captain' | 'team_code'
  max_limit?: number
  team_size?: number
  participants?: (EventParticipantSolo | EventParticipantTeamCaptain | EventParticipantTeamCode)[]
  multi_select?: boolean
  options?: EventPollOption[]
}

export async function fetchEvents(status?: string): Promise<EventSummary[]> {
  const path = status ? `/api/events?status=${status}` : '/api/events'
  const body = await apiFetch<{ events: EventSummary[] }>(path)
  return body.events
}

export function fetchEventDetail(messageId: string): Promise<EventDetail> {
  return apiFetch(`/api/events/${messageId}`)
}

export async function closeEvent(messageId: string): Promise<void> {
  await apiFetch(`/api/events/${messageId}/close`, jsonInit('POST'))
}

export async function deleteEvent(messageId: string): Promise<void> {
  await apiFetch(`/api/events/${messageId}`, jsonInit('DELETE'))
}

export async function notifyEventParticipants(
  messageId: string,
  message: string,
): Promise<{ success: number; failed: number }> {
  const result = await apiFetch<{ success: number; failed: number }>(`/api/events/${messageId}/notify`, jsonInit('POST', { message }))
  return { success: result.success, failed: result.failed }
}

export interface CreateEventSpec {
  channel_id: string
  type: 'tournament' | 'poll'
  title: string
  description: string
  banner_url: string
  ping: 'none' | 'everyone' | 'here'
  mode: 'solo' | 'team_captain' | 'team_code'
  require_info: boolean
  max_limit: number
  team_size: number
  role_reward: string | null
  options: string[]
  multi_select: boolean
}

export function createEvent(spec: CreateEventSpec): Promise<EventDetail> {
  return apiFetch('/api/events', jsonInit('POST', spec))
}

export interface BotConfig {
  LOG_CHANNEL_ID: string
  SPAM_EXCEPTION_CHANNELS: string[]
  TEMPBAN_CHANNEL_ID: string
  TEMPBAN_LOG_CHANNEL_ID: string
  SPAM_LOG_CHANNEL_ID: string
  SPAM_LOG_ROLE_ID: string
  WELCOME_CHANNEL_ID: string
  INVITE_LOG_CHANNEL_ID: string
  ANNOUNCEMENTS_CHANNEL_ID: string
  RULES_CHANNEL_ID: string
  ROLES_CHANNEL_ID: string
  SEARCH_PLAYERS_CHANNEL_ID: string
  BUTTON_CREATE_ALLOWED_ROLES: string[]
  BUTTON_WEBHOOK_URL: string
  BUTTON_WEBHOOK_USERNAME: string
  BUTTON_WEBHOOK_AVATAR_URL: string
  SERVER_INVITE_LINK: string
  VOICE_LOBBY_CHANNEL_ID: string
  VOICE_PANEL_CHANNEL_ID: string
  VOICE_LOG_CHANNEL_ID: string
  VOICE_PANEL_THUMB_URL: string
  SUPPLY_ROLE_ID: string
  SUPPLY_VOICE_CHANNEL_ID: string
  SUPPLY_LOG_CHANNEL_ID: string
  SUPPLY_REMINDER_MINUTES: string
}

export function fetchConfig(): Promise<BotConfig> {
  return apiFetch('/api/config')
}

export function updateConfig(config: BotConfig): Promise<BotConfig> {
  return apiFetch('/api/config', jsonInit('PUT', config))
}

// CTD â€” Ð¿Ñ€Ð¸Ð²Ð¸Ð»ÐµÐ³Ð¸Ñ Ð¾ÑÐ½Ð¾Ð²Ð½Ð¾Ð³Ð¾ ÑÐµÑ€Ð²ÐµÑ€Ð° (Ð¤Ð°Ð·Ð° 2b): Ð¾Ñ‚Ð´ÐµÐ»ÑŒÐ½Ñ‹Ð¹ Ñ€Ð¾ÑƒÑ‚, Ð´Ð¾ÑÑ‚ÑƒÐ¿ÐµÐ½ Ñ‚Ð¾Ð»ÑŒÐºÐ¾ Ð½Ð° Ð¼ÐµÐ¹Ð½Ðµ.
export interface CtdConfig {
  CTD_ROLE_ID: string
  CTD_CHANNEL_ID: string
}

export function fetchCtdConfig(): Promise<CtdConfig> {
  return apiFetch('/api/ctd')
}

export function updateCtdConfig(config: CtdConfig): Promise<CtdConfig> {
  return apiFetch('/api/ctd', jsonInit('PUT', config))
}

export interface SupplyMember {
  id: string
  display: string
}

export interface Supply {
  id: string
  initiator_id: string
  initiator_display: string
  opponent: string
  limit: number
  time_str: string
  target_ts: number
  status: 'active' | 'finished' | 'cancelled'
  participants: SupplyMember[]
  reserve: SupplyMember[]
  channel_id: string
  created_at: string
  closed_at: string | null
}

export interface SupplyStatEntry {
  user_id: string
  display: string
  count: number
}

export interface SupplyOverview {
  active: Supply[]
  history: Supply[]
  stats: SupplyStatEntry[]
}

export function fetchSupplyOverview(): Promise<SupplyOverview> {
  return apiFetch('/api/supply')
}

export function createSupply(input: {
  channel_id: string
  opponent: string
  limit: number
  time_str: string
}): Promise<Supply> {
  return apiFetch('/api/supply', jsonInit('POST', input))
}

export async function closeSupply(id: string): Promise<void> {
  await apiFetch(`/api/supply/${id}/close`, jsonInit('POST'))
}

export async function cancelSupply(id: string): Promise<void> {
  await apiFetch(`/api/supply/${id}/cancel`, jsonInit('POST'))
}

export interface VoiceRoom {
  channel_id: string
  name: string
  owner_id: string
  owner_display: string
  is_closed: boolean
  user_limit: number
  member_count: number
  exists: boolean
}

export async function fetchVoiceRooms(): Promise<VoiceRoom[]> {
  const body = await apiFetch<{ rooms: VoiceRoom[] }>('/api/voice/rooms')
  return body.rooms
}

export async function deleteVoiceRoom(channelId: string): Promise<void> {
  await apiFetch(`/api/voice/rooms/${channelId}`, { method: 'DELETE' })
}

export async function publishVoicePanel(): Promise<void> {
  await apiFetch('/api/voice/panel/publish', jsonInit('POST'))
}

export interface NewsMapping {
  source_channel_id: string
  target_channel_id: string
  label: string
}

export interface NewsSettings {
  enabled: boolean
  source_guild_id: string
  source_bot_ids: string[]
  log_channel_id: string
  mappings: NewsMapping[]
}

export function fetchNewsSettings(): Promise<NewsSettings> {
  return apiFetch('/api/news')
}

export function updateNewsSettings(settings: NewsSettings): Promise<NewsSettings> {
  return apiFetch('/api/news', jsonInit('PUT', settings))
}

export interface BracketMatch {
  slot_a: string | null
  slot_b: string | null
  winner: 'a' | 'b' | 'draw' | null
}

export type BracketFormat = 'single_elim' | 'double_elim' | 'round_robin'

export interface BracketStandingsRow {
  entry: string
  played: number
  wins: number
  draws: number
  losses: number
  points: number
}

export interface BracketSummary {
  id: string
  title: string
  format: BracketFormat
  source_event_id: string | null
  entry_count: number
  created_at: string
}

export interface BracketDetail {
  id: string
  title: string
  format: BracketFormat
  source_event_id: string | null
  entries: string[]
  rounds: BracketMatch[][]
  share_token: string | null
  de?: {
    winners: BracketMatch[][]
    losers: BracketMatch[][]
    final: BracketMatch
  }
  rr_rounds?: BracketMatch[][]
  standings?: BracketStandingsRow[]
}

export async function fetchBrackets(): Promise<BracketSummary[]> {
  const body = await apiFetch<{ brackets: BracketSummary[] }>('/api/brackets')
  return body.brackets
}

export function fetchBracketDetail(id: string): Promise<BracketDetail> {
  return apiFetch(`/api/brackets/${id}`)
}

export async function fetchEventEntries(eventId: string): Promise<string[]> {
  const body = await apiFetch<{ entries: string[] }>(`/api/brackets/entries-from-event/${eventId}`)
  return body.entries
}

export function createBracket(
  title: string,
  entries: string[],
  sourceEventId: string | null,
  format: BracketFormat = 'single_elim',
): Promise<BracketDetail> {
  return apiFetch('/api/brackets', jsonInit('POST', { title, entries, source_event_id: sourceEventId, format }))
}

export async function deleteBracket(id: string): Promise<void> {
  await apiFetch(`/api/brackets/${id}`, jsonInit('DELETE'))
}

export function setBracketMatchWinner(
  id: string,
  roundIndex: number,
  matchIndex: number,
  winner: 'a' | 'b' | 'draw' | null,
  segment: 'W' | 'L' | 'F' = 'W',
): Promise<BracketDetail> {
  return apiFetch(
    `/api/brackets/${id}/matches/${roundIndex}/${matchIndex}/winner`,
    jsonInit('POST', { winner, segment }),
  )
}

export async function enableBracketShare(id: string): Promise<string> {
  const result = await apiFetch<{ share_token: string }>(`/api/brackets/${id}/share`, jsonInit('POST'))
  return result.share_token
}

export async function disableBracketShare(id: string): Promise<void> {
  await apiFetch(`/api/brackets/${id}/share`, jsonInit('DELETE'))
}

export function fetchPublicBracket(token: string): Promise<BracketDetail> {
  return apiFetch(`/api/public/brackets/${token}`)
}

export interface WelcomeMessageSettings {
  channel_mode: 'text' | 'embed'
  channel_text: string
  channel_embed: EmbedSpec
  dm_content: string
  dm_embed: EmbedSpec
  dm_thumbnail_url: string
  dm_fallback_thumbnail_url: string
  dm_footer_text: string
  dm_use_guild_icon: boolean
  goodbye_text: string
}

export interface WelcomeSettings {
  channel_enabled: boolean
  dm_enabled: boolean
  goodbye_channel_enabled: boolean
  goodbye_channel_id: string
  messages: WelcomeMessageSettings
}

export type TempbanAction = 'softban' | 'ban' | 'disabled'

export interface TempbanSettings {
  action: TempbanAction
  dm_enabled: boolean
  dm_message: string
  log_enabled: boolean
  log_message: string
  unban_reason: string
  warning_message: string
  warning_thumbnail_url: string
  warning_message_id: string
  ban_count: number
}

export interface FeedbackPanelSettings {
  content: string
  embed: EmbedSpec
  banner_url: string
}

export function fetchTempbanSettings(): Promise<TempbanSettings> {
  return apiFetch('/api/tempban-settings')
}

export function updateTempbanSettings(settings: TempbanSettings): Promise<TempbanSettings> {
  return apiFetch('/api/tempban-settings', jsonInit('PUT', settings))
}

export function publishTempbanWarning(): Promise<{
  ok: boolean
  message_id: string
  ban_count: number
  warning_message_id: string
}> {
  return apiFetch('/api/tempban-settings/publish-warning', jsonInit('POST', {}))
}

export interface QuoteSettings {
  enabled: boolean
  delete_trigger: boolean
  min_length: number
}

export function fetchQuoteSettings(): Promise<QuoteSettings> {
  return apiFetch('/api/quote')
}

export function updateQuoteSettings(settings: QuoteSettings): Promise<QuoteSettings> {
  return apiFetch('/api/quote', jsonInit('PUT', settings))
}

export function fetchFeedbackPanelSettings(): Promise<FeedbackPanelSettings> {
  return apiFetch('/api/feedback-panel-settings')
}

export function updateFeedbackPanelSettings(settings: FeedbackPanelSettings): Promise<FeedbackPanelSettings> {
  return apiFetch('/api/feedback-panel-settings', jsonInit('PUT', settings))
}

export function fetchWelcomeSettings(): Promise<WelcomeSettings> {
  return apiFetch('/api/welcome-settings')
}

export function updateWelcomeSettings(settings: Partial<WelcomeSettings>): Promise<WelcomeSettings> {
  return apiFetch('/api/welcome-settings', jsonInit('PUT', settings))
}

export function testWelcomeSettings(target: 'channel' | 'dm' | 'both' = 'channel'): Promise<{ ok: boolean; sent: { channel: boolean; dm: boolean } }> {
  return apiFetch('/api/welcome-settings/test', jsonInit('POST', { target }))
}

export interface AutoRolesSettings {
  role_ids: string[]
}

export function fetchAutoRoles(): Promise<AutoRolesSettings> {
  return apiFetch('/api/auto-roles')
}

export function updateAutoRoles(roleIds: string[]): Promise<AutoRolesSettings> {
  return apiFetch('/api/auto-roles', jsonInit('PUT', { role_ids: roleIds }))
}

// â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Ð›Ð¾Ð³Ð¸Ñ€Ð¾Ð²Ð°Ð½Ð¸Ðµ ÑÐ¾Ð±Ñ‹Ñ‚Ð¸Ð¹ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export interface ServerLogEventConfig {
  enabled: boolean
  channel_id: string
}

export interface ServerLogSettings {
  labels: Record<string, string>
  events: Record<string, ServerLogEventConfig>
}

export function fetchServerLog(): Promise<ServerLogSettings> {
  return apiFetch('/api/serverlog')
}

export function updateServerLog(events: Record<string, ServerLogEventConfig>): Promise<ServerLogSettings> {
  return apiFetch('/api/serverlog', jsonInit('PUT', { events }))
}

// â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Ð¡Ð¸ÑÑ‚ÐµÐ¼Ð° ÑƒÑ€Ð¾Ð²Ð½ÐµÐ¹ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export interface XpScopeSettings {
  enabled: boolean
  ignored_roles: string[]
  target_channels: string[]
  ignored_channels: string[]
  multiplier: number
}

export interface XpVoiceSettings extends XpScopeSettings {
  max_count: number
  base_per_minute: number
  member_multipliers: Record<string, number>
}

export interface XpLevelReward {
  level: number
  role_ids: string[]
}

export interface XpVoiceReward {
  minutes: number
  role_ids: string[]
}

export interface XpSettings {
  enabled: boolean
  public_leaderboard: boolean
  reset_on_leave: boolean
  remove_old_level_roles: boolean
  text: XpScopeSettings
  voice: XpVoiceSettings
  announce: {
    enabled: boolean
    channel_id: string
    template: string
    delete_after: number
  }
  level_rewards: XpLevelReward[]
  voice_rewards: XpVoiceReward[]
}

export interface XpOverview {
  settings: XpSettings
  member_count: number
  has_card_bg: boolean
}

export interface XpLeaderboardEntry {
  user_id: string
  display: string
  avatar: string | null
  on_server: boolean
  xp: number
  level: number
  xp_into_level: number
  xp_step: number
  messages: number
  voice_seconds: number
  voice_time_text: string
  rank: number
  frame_color: string | null
  title_text: string | null
}

export interface XpLeaderboardPage {
  total: number
  page: number
  page_size: number
  entries: XpLeaderboardEntry[]
}

export function fetchXpOverview(): Promise<XpOverview> {
  return apiFetch('/api/xp')
}

export function updateXpSettings(settings: XpSettings): Promise<{ settings: XpSettings }> {
  return apiFetch('/api/xp', jsonInit('PUT', settings))
}

export function fetchXpLeaderboard(page: number, search = ''): Promise<XpLeaderboardPage> {
  const params = new URLSearchParams({ page: String(page) })
  if (search) params.set('search', search)
  return apiFetch(`/api/xp/leaderboard?${params}`)
}

export async function setMemberXp(userId: string, xp: number): Promise<void> {
  await apiFetch(`/api/xp/members/${userId}`, jsonInit('PUT', { xp }))
}

export async function resetMemberXp(userId: string): Promise<void> {
  await apiFetch(`/api/xp/members/${userId}/reset`, jsonInit('POST'))
}

export async function resetAllXp(): Promise<void> {
  await apiFetch('/api/xp/reset-all', jsonInit('POST'))
}

export async function uploadCardBg(file: Blob): Promise<void> {
  const response = await fetch('/api/xp/card-bg', { method: 'POST', credentials: 'include', body: file })
  if (!response.ok) {
    let code = 'upload_failed'
    try {
      const body = (await response.json()) as { error?: string }
      if (body?.error) code = body.error
    } catch {
      /* keep fallback */
    }
    throw new ApiError(response.status, code)
  }
}

export async function deleteCardBg(): Promise<void> {
  await apiFetch('/api/xp/card-bg', { method: 'DELETE' })
}

/** URL for the PNG profile-card preview (credentials via cookie on <img> need same-origin). */
export function profileCardPreviewUrl(userId?: string): string {
  const params = new URLSearchParams()
  if (userId) params.set('user_id', userId)
  const q = params.toString()
  return q ? `/api/xp/profile-card-preview?${q}` : '/api/xp/profile-card-preview'
}

/** URL for the animated GIF profile-card preview (same cosmetics, mirrors the bot's /levels profile command). */
export function profileCardPreviewGifUrl(userId?: string): string {
  const params = new URLSearchParams()
  if (userId) params.set('user_id', userId)
  const q = params.toString()
  return q ? `/api/xp/profile-card-preview.gif?${q}` : '/api/xp/profile-card-preview.gif'
}

async function fetchPreviewBlobUrl(url: string): Promise<string> {
  const response = await fetch(url, { credentials: 'include' })
  if (!response.ok) {
    let code = 'preview_failed'
    try {
      const body = (await response.json()) as { error?: string }
      if (body?.error) code = body.error
    } catch {
      /* keep fallback */
    }
    throw new ApiError(response.status, code)
  }
  const blob = await response.blob()
  return URL.createObjectURL(blob)
}

/** Fetch preview as a blob object URL (auth cookies included). Caller should revoke when done. */
export async function fetchProfileCardPreview(userId?: string): Promise<string> {
  return fetchPreviewBlobUrl(profileCardPreviewUrl(userId))
}

/** Fetch the animated GIF preview as a blob object URL. Caller should revoke when done. */
export async function fetchProfileCardPreviewGif(userId?: string): Promise<string> {
  return fetchPreviewBlobUrl(profileCardPreviewGifUrl(userId))
}

export interface PublicLeaderboardEntry {
  rank: number
  display: string
  avatar: string | null
  level: number
  xp: number
  voice_seconds: number
  voice_time_text: string
  frame_color: string | null
  title_text: string | null
}

export interface PublicLeaderboardResponse {
  guild_id?: string
  guild_name: string
  entries: PublicLeaderboardEntry[]
}

export function fetchPublicLeaderboard(guildId: string): Promise<PublicLeaderboardResponse> {
  return apiFetch(`/api/public/leaderboard/${encodeURIComponent(guildId)}`)
}

// â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Ð¡Ñ‚Ð°Ñ‚Ð¸ÑÑ‚Ð¸ÐºÐ° Ð²Ð¾Ð¹ÑÐ° â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export interface VoiceStats {
  days: number
  timezone?: string
  session_count: number
  total_seconds: number
  total_time_text: string
  peak_concurrent: number
  by_hour_minutes: number[]
  by_weekday_minutes: number[]
  top_channels: { name: string; seconds: number; time_text: string }[]
  top_users: { user_id: string; display: string; avatar: string | null; seconds: number; time_text: string }[]
}

export function fetchVoiceStats(days: number): Promise<VoiceStats> {
  return apiFetch(`/api/voice-stats?days=${days}`)
}

// â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ ÐÑƒÐ´Ð¸Ñ‚ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export interface AuditEntry {
  ts: number
  moderator_id: string
  moderator_name: string
  method: string
  path: string
  action: string
  status: number
  details: string
}

export interface AuditModerator {
  id: string
  name: string
}

export interface AuditPage {
  total: number
  page: number
  page_size: number
  entries: AuditEntry[]
  moderators: AuditModerator[]
}

export function fetchAudit(page: number, moderator?: string, q?: string): Promise<AuditPage> {
  const params = new URLSearchParams({ page: String(page) })
  if (moderator) params.set('moderator', moderator)
  if (q?.trim()) params.set('q', q.trim())
  return apiFetch(`/api/audit?${params}`)
}

// â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Ð¡Ñ‚Ñ€Ð¸Ð¼-ÑƒÐ²ÐµÐ´Ð¾Ð¼Ð»ÐµÐ½Ð¸Ñ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export interface StreamSubscription {
  id: string
  platform: 'twitch' | 'youtube' | 'tiktok'
  identifier: string
  display_name: string
  avatar_url: string
  enabled: boolean
  channel_id: string
  ping_role_id: string
  template: string
  keywords: string[]
  keyword_mode: 'any' | 'all'
  min_interval_minutes: number
  mention_everyone: boolean
  use_embed: boolean
  embed_color: string
  video_template: string
  live_template: string
  video_embed_color: string
  live_embed_color: string
  video_mention_everyone: boolean
  live_mention_everyone: boolean
  video_use_embed: boolean
  live_use_embed: boolean
  live_title_style: 'live_dot' | 'title_only' | 'live_badge'
  last_stream_id: string
}

export function fetchStreams(): Promise<{ twitch_configured: boolean; subscriptions: StreamSubscription[] }> {
  return apiFetch('/api/streams')
}

export function createStreamSubscription(input: {
  platform: 'twitch' | 'youtube' | 'tiktok'
  query: string
  channel_id: string
}): Promise<StreamSubscription> {
  return apiFetch('/api/streams', jsonInit('POST', input))
}

export function updateStreamSubscription(
  id: string,
  fields: Partial<
    Pick<
      StreamSubscription,
      | 'enabled'
      | 'channel_id'
      | 'ping_role_id'
      | 'template'
      | 'keywords'
      | 'keyword_mode'
      | 'min_interval_minutes'
      | 'mention_everyone'
      | 'use_embed'
      | 'embed_color'
      | 'video_template'
      | 'live_template'
      | 'video_embed_color'
      | 'live_embed_color'
      | 'video_mention_everyone'
      | 'live_mention_everyone'
      | 'video_use_embed'
      | 'live_use_embed'
      | 'live_title_style'
    >
  >,
): Promise<StreamSubscription> {
  return apiFetch(`/api/streams/${id}`, jsonInit('PATCH', fields))
}

export async function deleteStreamSubscription(id: string): Promise<void> {
  await apiFetch(`/api/streams/${id}`, { method: 'DELETE' })
}

export async function testStreamSubscription(id: string): Promise<void> {
  await apiFetch(`/api/streams/${id}/test`, { method: 'POST' })
}

// â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Ð¨Ð°Ð±Ð»Ð¾Ð½Ñ‹ ÑÐ¼Ð±ÐµÐ´Ð¾Ð² â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export interface EmbedTemplate {
  id: string
  name: string
  content: string
  embed: EmbedSpec
  role_ids: string[]
}

export async function fetchEmbedTemplates(): Promise<EmbedTemplate[]> {
  const body = await apiFetch<{ templates: EmbedTemplate[] }>('/api/embed-templates')
  return body.templates
}

export function saveEmbedTemplate(input: {
  name: string
  content: string
  embed: EmbedSpec
  role_ids: string[]
}): Promise<EmbedTemplate> {
  return apiFetch('/api/embed-templates', jsonInit('POST', input))
}

export async function deleteEmbedTemplate(id: string): Promise<void> {
  await apiFetch(`/api/embed-templates/${id}`, { method: 'DELETE' })
}

// â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Ð¡ÐµÐ¼ÑŒÑ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export interface FamilyTargetRole {
  label: string
  role_id: string
}

export interface FamilySettings {
  enabled: boolean
  roster: {
    list_channel_id: string
    target_roles: FamilyTargetRole[]
  }
  applications: {
    application_channel_id: string
    log_channel_id: string
    staff_role_ids: string[]
    ticket_manager_role_id: string
    notify_role_id: string
    ticket_active_role_id: string
    approve_role_ids: string[]
    yes_emoji_id: string
    no_emoji_id: string
    thread_archive_minutes: number
  }
  birthdays: {
    channel_id: string
    list_channel_id: string
  }
}

export function fetchFamilySettings(): Promise<FamilySettings> {
  return apiFetch('/api/family')
}

export function updateFamilySettings(settings: FamilySettings): Promise<FamilySettings> {
  return apiFetch('/api/family', jsonInit('PUT', settings))
}

export interface FamilyRosterGroup {
  label: string
  role_id: string
  role_found: boolean
  members: { id: string; display: string }[]
}

export function fetchFamilyRoster(): Promise<{ groups: FamilyRosterGroup[] }> {
  return apiFetch('/api/family/roster')
}

export type FamilyTicketStatus = 'open' | 'approved' | 'denied' | 'closed'

export interface FamilyTicket {
  user_id: string
  display: string
  status: FamilyTicketStatus
  nickname: string
  game_level: string
  faction_pref: string
  online_timezone: string
  real_name: string
  real_age: string
  about_text: string
  why_join: string
  inviter_nickname: string | null
  created_at: string
  handled_by: string | null
  thread_id: string | null
}

export interface FamilyTicketsPage {
  total: number
  page: number
  page_size: number
  entries: FamilyTicket[]
}

export function fetchFamilyTickets(status: FamilyTicketStatus | '', page: number): Promise<FamilyTicketsPage> {
  const params = new URLSearchParams({ page: String(page) })
  if (status) params.set('status', status)
  return apiFetch(`/api/family/tickets?${params}`)
}

export async function decideFamilyTicket(userId: string, decision: 'approve' | 'deny' | 'close'): Promise<void> {
  await apiFetch(`/api/family/tickets/${userId}/${decision}`, jsonInit('POST'))
}

export interface FamilyBirthday {
  user_id: string
  display: string
  day: number
  month: number
  date_display: string
}

export function fetchFamilyBirthdays(): Promise<{ entries: FamilyBirthday[] }> {
  return apiFetch('/api/family/birthdays')
}

export async function setFamilyBirthday(userId: string, date: string): Promise<{ date_display: string }> {
  return apiFetch('/api/family/birthdays', jsonInit('POST', { user_id: userId, date }))
}

export async function deleteFamilyBirthday(userId: string): Promise<void> {
  await apiFetch(`/api/family/birthdays/${userId}`, { method: 'DELETE' })
}

// â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ ÐœÐ°Ñ„Ð¸Ñ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export interface MafiaSettings {
  enabled: boolean
  default_min_players: number
  default_max_players: number
  default_night_timer_sec: number
  default_day_discussion_timer_sec: number
  default_day_vote_timer_sec: number
  log_channel_id: string
}

export function fetchMafiaSettings(): Promise<MafiaSettings> {
  return apiFetch('/api/mafia')
}

export function updateMafiaSettings(settings: MafiaSettings): Promise<MafiaSettings> {
  return apiFetch('/api/mafia', jsonInit('PUT', settings))
}

export type MafiaGameStatus = 'lobby' | 'active' | 'finished' | 'cancelled'
export type MafiaGamePhase = 'lobby' | 'night' | 'day_discussion' | 'day_vote' | 'ended'

export interface MafiaGameSummary {
  id: number
  channel_id: string
  channel_name: string
  status: MafiaGameStatus
  phase: MafiaGamePhase
  round_number: number
  player_count: number
  alive_count: number
  created_at: string
}

export async function fetchMafiaGames(): Promise<MafiaGameSummary[]> {
  const body = await apiFetch<{ games: MafiaGameSummary[] }>('/api/mafia/games')
  return body.games
}

export interface MafiaGameDetailPlayer {
  user_id: string
  display_name: string
  alive: boolean
  role: MafiaRole
  action_submitted: boolean
}

export interface MafiaGameEvent {
  round_number: number
  event_type: string
  payload: string
  created_at: string
}

export interface MafiaGameDetail {
  game: MafiaGameSummary
  players: MafiaGameDetailPlayer[]
  events: MafiaGameEvent[]
}

export function fetchMafiaGameDetail(id: number): Promise<MafiaGameDetail> {
  return apiFetch(`/api/mafia/games/${id}`)
}

export async function endMafiaGame(id: number): Promise<void> {
  await apiFetch(`/api/mafia/games/${id}/end`, jsonInit('POST'))
}

export async function advanceMafiaGamePhase(id: number): Promise<void> {
  await apiFetch(`/api/mafia/games/${id}/advance-phase`, jsonInit('POST'))
}

export type MafiaRole = 'mafia' | 'citizen' | 'doctor' | 'sheriff'

export interface MafiaPlayerRef {
  user_id: string
  display_name: string
  avatar_url?: string | null
}

export interface MafiaRosterEntry {
  user_id: string
  display_name: string
  avatar_url?: string | null
  alive: boolean
  role?: MafiaRole
}

export interface MafiaVoteTallyEntry {
  target: string | null
  target_display: string | null
  count: number
}

export interface MafiaPublicState {
  game_status: MafiaGameStatus
  phase: MafiaGamePhase
  round_number: number
  phase_deadline_ts: number | null
  your_role: MafiaRole | null
  your_alive: boolean
  action_required: boolean
  your_action_submitted: boolean
  your_submitted_target: string | null
  alive_players: MafiaPlayerRef[]
  roster: MafiaRosterEntry[]
  teammates?: MafiaPlayerRef[]
  mafia_votes?: { actor: string; target: string | null }[]
  vote_tally?: MafiaVoteTallyEntry[]
  language?: 'ru' | 'en'
}

export function fetchPublicMafia(token: string): Promise<MafiaPublicState> {
  return apiFetch(`/api/public/mafia/${token}`)
}

export async function submitMafiaAction(token: string, targetUserId: string | null): Promise<void> {
  await apiFetch(`/api/public/mafia/${token}/action`, jsonInit('POST', { target_user_id: targetUserId }))
}

export async function submitMafiaVote(token: string, targetUserId: string | null): Promise<void> {
  await apiFetch(`/api/public/mafia/${token}/vote`, jsonInit('POST', { target_user_id: targetUserId }))
}

// â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Ð¡ÑƒÐ¿ÐµÑ€-Ð°Ð´Ð¼Ð¸Ð½ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export interface SuperAdminGuild {
  id: string
  name: string
  icon: string | null
  member_count: number
  owner_id: string | null
}

export async function fetchSuperAdminGuilds(): Promise<SuperAdminGuild[]> {
  const body = await apiFetch<{ guilds: SuperAdminGuild[] }>('/api/superadmin/guilds')
  return body.guilds
}

export interface HostHealth {
  platform: string
  hostname: string | null
  python_version: string
  cpu_percent: number | null
  cpu_count: number | null
  load_avg: [number, number, number] | null
  ram: { used_bytes: number | null; total_bytes: number | null; percent: number | null }
  disk: {
    used_bytes: number | null
    total_bytes: number | null
    percent: number | null
    path: string
  }
  uptime_seconds: number | null
  boot_time: number | null
  process: {
    pid: number
    name: string | null
    rss_bytes: number | null
    create_time: number | null
  } | null
  collected_at: number
}

export async function fetchHostHealth(): Promise<HostHealth> {
  return apiFetch<HostHealth>('/api/superadmin/host-health')
}

// â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Ð Ð¾Ð·Ñ‹Ð³Ñ€Ñ‹ÑˆÐ¸ (Giveaways) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export interface GiveawayEntrant {
  id: string
  display: string
}

export type GiveawayStatus = 'active' | 'finished' | 'cancelled'

export interface Giveaway {
  id: string
  initiator_id: string
  initiator_display: string
  prize: string
  winners_count: number
  duration_str: string
  target_ts: number
  status: GiveawayStatus
  entrants: GiveawayEntrant[]
  winners: GiveawayEntrant[]
  channel_id: string
  created_at: string
  closed_at: string | null
}

export interface GiveawayOverview {
  active: Giveaway[]
  history: Giveaway[]
}

export function fetchGiveawayOverview(): Promise<GiveawayOverview> {
  return apiFetch('/api/giveaways')
}

export function createGiveaway(payload: {
  channel_id: string
  prize: string
  duration_str: string
  winners_count: number
}): Promise<Giveaway> {
  return apiFetch('/api/giveaways', jsonInit('POST', payload))
}

export async function rerollGiveaway(id: string): Promise<{ winners: string[] }> {
  return apiFetch(`/api/giveaways/${id}/reroll`, jsonInit('POST'))
}

export async function endGiveaway(id: string): Promise<void> {
  await apiFetch(`/api/giveaways/${id}/end`, jsonInit('POST'))
}

// â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Ð•Ð¶ÐµÐ´Ð½ÐµÐ²Ð½Ð°Ñ Ñ€ÑƒÐ±Ñ€Ð¸ÐºÐ° â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export interface DailyTopic {
  id: string
  text: string
}

export interface DailyTopicSettings {
  enabled: boolean
  channel_id: string
  post_times: string[]
  topics: DailyTopic[]
}

export function fetchDailyTopic(): Promise<DailyTopicSettings> {
  return apiFetch('/api/daily-topic')
}

export function updateDailyTopicSettings(input: {
  enabled: boolean
  channel_id: string
  post_times: string[]
}): Promise<DailyTopicSettings> {
  return apiFetch('/api/daily-topic/settings', jsonInit('PUT', input))
}

export function createDailyTopic(text: string): Promise<DailyTopic> {
  return apiFetch('/api/daily-topic/topics', jsonInit('POST', { text }))
}

export function updateDailyTopic(id: string, text: string): Promise<DailyTopic> {
  return apiFetch(`/api/daily-topic/topics/${id}`, jsonInit('PATCH', { text }))
}

export async function deleteDailyTopic(id: string): Promise<void> {
  await apiFetch(`/api/daily-topic/topics/${id}`, { method: 'DELETE' })
}

export function postDailyTopicNow(): Promise<{ ok: boolean; topic: DailyTopic }> {
  return apiFetch('/api/daily-topic/post-now', jsonInit('POST'))
}

// â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ ÐÐ²Ñ‚Ð¾Ð¼Ð¾Ð´ÐµÑ€Ð°Ñ†Ð¸Ñ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export type AutomodPunishment = 'none' | 'warn' | 'mute' | 'kick' | 'ban'
export type EscalationAction = 'mute' | 'kick' | 'ban'

export interface AutomodFilter {
  label: string
  description: string
  enabled: boolean
  delete_message: boolean
  punishment: AutomodPunishment
  duration_minutes: number
  notify_member: boolean
  notify_channel_id: string
  notify_template: string
  whitelist_domains?: string[]
  allow_own_server?: boolean
  blocklist_keywords?: string[]
  words?: string[]
  max_repeats?: number
  consecutive_only?: boolean
  reset_on_trigger?: boolean
  max_percent?: number
  min_length?: number
  max_count?: number
}

export interface EscalationRule {
  id: string
  count: number
  action: EscalationAction
  duration_minutes: number
}

export interface AutomodSettings {
  enabled: boolean
  filters: Record<string, AutomodFilter>
  escalation: EscalationRule[]
  manual_warn_duration_minutes: number
}

export function fetchAutomod(): Promise<AutomodSettings> {
  return apiFetch('/api/automod')
}

export function updateAutomodEnabled(enabled: boolean): Promise<AutomodSettings> {
  return apiFetch('/api/automod', jsonInit('PUT', { enabled }))
}

export function updateAutomodFilter(key: string, fields: Partial<AutomodFilter>): Promise<AutomodFilter> {
  return apiFetch(`/api/automod/filters/${key}`, jsonInit('PUT', fields))
}

export function updateManualWarnDuration(duration_minutes: number): Promise<AutomodSettings> {
  return apiFetch('/api/automod/manual-warn-duration', jsonInit('PUT', { duration_minutes }))
}

export function createEscalationRule(input: {
  count: number
  action: EscalationAction
  duration_minutes: number
}): Promise<EscalationRule> {
  return apiFetch('/api/automod/escalation', jsonInit('POST', input))
}

export function updateEscalationRule(
  id: string,
  fields: Partial<Pick<EscalationRule, 'count' | 'action' | 'duration_minutes'>>,
): Promise<EscalationRule> {
  return apiFetch(`/api/automod/escalation/${id}`, jsonInit('PATCH', fields))
}

export async function deleteEscalationRule(id: string): Promise<void> {
  await apiFetch(`/api/automod/escalation/${id}`, { method: 'DELETE' })
}

// â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ ÐŸÑ€ÐµÐ´ÑƒÐ¿Ñ€ÐµÐ¶Ð´ÐµÐ½Ð¸Ñ (Ð²Ð°Ñ€Ð½Ñ‹) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export interface Warn {
  id: number
  guild_id: string
  user_id: string
  reason: string
  moderator_id: string | null
  source: string
  created_at: string
  expires_at: string | null
  removed: boolean
  removed_by: string | null
  removed_at: string | null
}

export function fetchMemberWarns(memberId: string): Promise<{ warns: Warn[]; active_count: number }> {
  return apiFetch(`/api/members/${memberId}/warns`)
}

export function createMemberWarn(memberId: string, reason: string): Promise<{ warn: Warn; active_count: number }> {
  return apiFetch(`/api/members/${memberId}/warns`, jsonInit('POST', { reason }))
}

export async function deleteWarn(warnId: number): Promise<void> {
  await apiFetch(`/api/warns/${warnId}`, { method: 'DELETE' })
}

export type CaseTimelineKind =
  | 'warn'
  | 'warn_manual'
  | 'warn_escalation'
  | 'spam_punish'
  | 'tempban'
  | 'manual_ban'
  | 'manual_kick'
  | 'manual_mute'
  | 'manual_unmute'
  | 'command_ban'
  | 'command_kick'
  | 'command_mute'
  | 'command_unmute'
  | 'command_unban'
  | 'command_clear'
  | 'antiraid_trigger'
  | 'verification_pass'
  | 'verification_expired'
  | `automod_${string}`
  | (string & {})

export interface CaseTimelineItem {
  id: string
  kind: CaseTimelineKind
  timestamp: string
  reason: string
  moderator_id: string | null
  moderator_display: string | null
  extra: string
  meta: Record<string, unknown>
}

export interface CaseTimeline {
  user: {
    id: string
    username: string
    display_name: string
    avatar: string | null
  }
  in_guild: boolean
  items: CaseTimelineItem[]
}

export function fetchCaseTimeline(memberId: string): Promise<CaseTimeline> {
  return apiFetch(`/api/members/${memberId}/case-timeline`)
}

// â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Ð‘ÑƒÐ½ÐºÐµÑ€ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export interface BunkerSettings {
  enabled: boolean
  default_min_players: number
  default_max_players: number
  default_discussion_timer_sec: number
  default_vote_timer_sec: number
  default_unique_cards: boolean
  log_channel_id: string
}

export function fetchBunkerSettings(): Promise<BunkerSettings> {
  return apiFetch('/api/bunker')
}

export function updateBunkerSettings(settings: BunkerSettings): Promise<BunkerSettings> {
  return apiFetch('/api/bunker', jsonInit('PUT', settings))
}

export type BunkerGameStatus = 'lobby' | 'active' | 'finished' | 'cancelled'
export type BunkerGamePhase = 'lobby' | 'discussion' | 'vote' | 'ended'

export interface BunkerGameSummary {
  id: number
  channel_id: string
  channel_name: string
  status: BunkerGameStatus
  phase: BunkerGamePhase
  round_number: number
  bunker_capacity: number | null
  unique_cards: boolean
  player_count: number
  alive_count: number
  created_at: string
}

export async function fetchBunkerGames(): Promise<BunkerGameSummary[]> {
  const body = await apiFetch<{ games: BunkerGameSummary[] }>('/api/bunker/games')
  return body.games
}

export interface BunkerProfession {
  name: string
  category: string
  experience_level: string
  has_ability: boolean
}

export interface BunkerAgeInfo {
  key: string
  label: string
}

export interface BunkerBodyType {
  key: string
  name: string
  agility: string
  stamina: string
  strength: string
  disease_note: string
  food_requirement: string
  heat_tolerance: string
  cold_tolerance: string
  reproduction: string
}

export interface BunkerHealth {
  severity: string
  disease_name: string | null
  category: string | null
}

export interface BunkerHobby {
  name: string
  category: string
  experience_level: string
}

export interface BunkerPhobia {
  name: string
  type: string
}

export interface BunkerItem {
  name: string
  category: string
}

export interface BunkerTrait {
  trait: string
  category: string
  behavior_example: string
  possible_bunker_behavior: string
}

export interface BunkerAdditionalInfo {
  name: string
  category: string
  linked_user_id: string | null
}

export interface BunkerSpecialAbility {
  name: string
  category: string
  effect: string
  used: boolean
}

export interface BunkerCharacter {
  profession?: BunkerProfession
  age?: BunkerAgeInfo
  gender?: string
  body_type?: BunkerBodyType
  health?: BunkerHealth
  hobby?: BunkerHobby
  phobia?: BunkerPhobia
  backpack_item?: BunkerItem
  large_item?: BunkerItem
  trait?: BunkerTrait
  additional_info?: BunkerAdditionalInfo
  special_abilities?: BunkerSpecialAbility[]
}

export const BUNKER_FIELD_KEYS = [
  'profession', 'age', 'gender', 'body_type', 'health',
  'hobby', 'phobia', 'backpack_item', 'large_item', 'trait', 'additional_info',
] as const

export type BunkerFieldKey = (typeof BUNKER_FIELD_KEYS)[number]

export interface BunkerPlayerAdminEntry {
  user_id: string
  display_name: string
  alive: boolean
  character: BunkerCharacter | null
  revealed_fields: string[]
}

export interface BunkerAbilityAnnouncement {
  id: number
  round_number: number
  player_user_id: string
  player_display_name: string
  card_index: number
  card_name: string
  target_user_id: string | null
  target_display_name: string | null
  note: string
  applied: boolean
  created_at: string
}

export interface BunkerCardPools {
  genders: string[]
  ages: BunkerAgeInfo[]
  body_types: BunkerBodyType[]
  professions: { id: number; name: string; category: string }[]
  profession_experience_levels: { level: string; duration: string; has_ability: boolean }[]
  hobbies: { id: number; name: string; category: string }[]
  hobby_experience_levels: { level: string; duration: string }[]
  health_severities: string[]
  health_diseases: { id: number; name: string; category: string }[]
  phobias: { id: number; name: string; type: string }[]
  backpack_items: { id: number; name: string; category: string }[]
  large_items: { id: number; name: string; category: string }[]
  traits: BunkerTrait[]
  additional_info: { id: number; name: string; category: string }[]
  special_abilities: { id: number; name: string; category: string; effect: string }[]
}

export function fetchBunkerCardPools(): Promise<BunkerCardPools> {
  return apiFetch('/api/bunker/card-pools')
}

export interface BunkerGameDetail {
  game: BunkerGameSummary
  players: BunkerPlayerAdminEntry[]
  ability_announcements: BunkerAbilityAnnouncement[]
}

export function fetchBunkerGameDetail(id: number): Promise<BunkerGameDetail> {
  return apiFetch(`/api/bunker/games/${id}`)
}

export function patchBunkerPlayerCharacter(
  gameId: number,
  userId: string,
  patch: Partial<BunkerCharacter>,
): Promise<{ character: BunkerCharacter }> {
  return apiFetch(`/api/bunker/games/${gameId}/players/${userId}`, jsonInit('PATCH', { character: patch }))
}

export async function endBunkerGame(id: number): Promise<void> {
  await apiFetch(`/api/bunker/games/${id}/end`, jsonInit('POST'))
}

export async function advanceBunkerGamePhase(id: number): Promise<void> {
  await apiFetch(`/api/bunker/games/${id}/advance-phase`, jsonInit('POST'))
}

export async function applyBunkerAbility(gameId: number, announcementId: number): Promise<void> {
  await apiFetch(`/api/bunker/games/${gameId}/ability/${announcementId}/apply`, jsonInit('POST'))
}

export interface BunkerPlayerRef {
  user_id: string
  display_name: string
  avatar_url?: string | null
}

export interface BunkerRosterEntry {
  user_id: string
  display_name: string
  avatar_url?: string | null
  alive: boolean
  character: BunkerCharacter
  revealed_fields: string[]
}

export interface BunkerVoteTallyEntry {
  target: string | null
  target_display: string | null
  count: number
}

export interface BunkerPublicState {
  game_status: BunkerGameStatus
  phase: BunkerGamePhase
  round_number: number
  phase_deadline_ts: number | null
  bunker_capacity: number | null
  catastrophe_name: string | null
  catastrophe_description: string | null
  bunker_conditions_name: string | null
  bunker_conditions_description: string | null
  your_alive: boolean
  your_character: BunkerCharacter | null
  your_revealed_fields: string[]
  action_required: boolean
  your_vote_submitted: boolean
  your_submitted_target: string | null
  alive_players: BunkerPlayerRef[]
  roster: BunkerRosterEntry[]
  vote_tally?: BunkerVoteTallyEntry[]
  language?: 'ru' | 'en'
}

export function fetchPublicBunker(token: string): Promise<BunkerPublicState> {
  return apiFetch(`/api/public/bunker/${token}`)
}

export async function revealBunkerFields(token: string, fieldKeys: string[]): Promise<void> {
  await apiFetch(`/api/public/bunker/${token}/reveal`, jsonInit('POST', { field_keys: fieldKeys }))
}

export async function submitBunkerVote(token: string, targetUserId: string | null): Promise<void> {
  await apiFetch(`/api/public/bunker/${token}/vote`, jsonInit('POST', { target_user_id: targetUserId }))
}

export async function announceBunkerAbility(
  token: string,
  cardIndex: 1 | 2,
  targetUserId: string | null,
  note: string,
): Promise<void> {
  await apiFetch(`/api/public/bunker/${token}/ability`, jsonInit('POST', {
    card_index: cardIndex, target_user_id: targetUserId, note,
  }))
}

// â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Ð Ð°Ð·Ð²Ð»ÐµÑ‡ÐµÐ½Ð¸Ñ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export interface FunSettings {
  enabled: boolean
  roulette_timeout_minutes: number
  roulette_cooldown_sec: number
  auto_emoji_enabled: boolean
  auto_emoji_chance_percent: number
  auto_emoji_min_interval_sec: number
  auto_emoji_remove_after_sec: number
}

export function fetchFunSettings(): Promise<FunSettings> {
  return apiFetch('/api/fun')
}

export function updateFunSettings(settings: FunSettings): Promise<FunSettings> {
  return apiFetch('/api/fun', jsonInit('PUT', settings))
}

export interface WordleSettings {
  enabled: boolean
  // Ð¡Ñ‚Ñ€Ð¾ÐºÐ°, Ð½Ðµ Ñ‡Ð¸ÑÐ»Ð¾: Discord ID (snowflake) Ð¿Ñ€ÐµÐ²Ñ‹ÑˆÐ°ÐµÑ‚ Number.MAX_SAFE_INTEGER
  channel_id: string
  announce_time: string
}

export function fetchWordleSettings(): Promise<WordleSettings> {
  return apiFetch('/api/wordle')
}

export function updateWordleSettings(settings: WordleSettings): Promise<WordleSettings> {
  return apiFetch('/api/wordle', jsonInit('PUT', settings))
}

// â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Ð­ÐºÐ¾Ð½Ð¾Ð¼Ð¸ÐºÐ° â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export type ShopItemType = 'role' | 'frame_color' | 'title'

export interface ShopItem {
  id: string
  type: ShopItemType
  role_id: string
  color_hex: string
  title_text: string
  price: number
  name: string
}

export interface EconomySettings {
  enabled: boolean
  currency_name: string
  currency_emoji: string
  text_rate_percent: number
  voice_rate_percent: number
  transfer_enabled: boolean
  transfer_fee_percent: number
  roulette_bets_enabled: boolean
  roulette_max_bet: number
  daily_bonus_enabled: boolean
  daily_base_amount: number
  daily_growth_per_day: number
  daily_max_streak_days: number
  shop_items: ShopItem[]
  weekly_report_enabled: boolean
  weekly_report_channel_id: string
  weekly_report_days: number
  last_weekly_report_date?: string
}

export interface EconomyWeeklyReportRow {
  user_id: string
  display_name: string
  earned: number
  spent: number
  net: number
}

export interface EconomyWeeklyReport {
  days: number
  weekly_report_enabled: boolean
  weekly_report_channel_id: string
  rows: EconomyWeeklyReportRow[]
}

export interface EconomyTopEntry {
  user_id: string
  display_name: string
  balance: number
}

export function fetchEconomySettings(): Promise<EconomySettings> {
  return apiFetch('/api/economy')
}

export function updateEconomySettings(settings: EconomySettings): Promise<EconomySettings> {
  return apiFetch('/api/economy', jsonInit('PUT', settings))
}

export function fetchEconomyTop(): Promise<EconomyTopEntry[]> {
  return apiFetch('/api/economy/top')
}

export function fetchEconomyWeeklyReport(): Promise<EconomyWeeklyReport> {
  return apiFetch('/api/economy/weekly-report')
}

export function setEconomyBalance(userId: string, balance: number): Promise<{ user_id: string; balance: number }> {
  return apiFetch('/api/economy/balance', jsonInit('PUT', { user_id: userId, balance }))
}

export async function resetAllEconomyBalances(): Promise<{ ok: boolean; cleared: number }> {
  return apiFetch('/api/economy/reset-all', jsonInit('POST'))
}

// â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ ÐšÐ°Ð·Ð¸Ð½Ð¾ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export interface CasinoLossRole {
  game: 'slots' | 'bj' | 'total'
  threshold: number
  role_id: string
}

export interface CasinoSettings {
  enabled: boolean
  house_edge_percent: number
  cooldown_sec: number
  min_bet: number
  max_bet: number
  loss_roles: CasinoLossRole[]
}

export function fetchCasinoSettings(): Promise<CasinoSettings> {
  return apiFetch('/api/casino')
}

export function updateCasinoSettings(settings: CasinoSettings): Promise<CasinoSettings> {
  return apiFetch('/api/casino', jsonInit('PUT', settings))
}

export interface CasinoLeaderboardEntry {
  user_id: string
  username: string
  avatar: string | null
  slots_losses: number
  slots_wins: number
  bj_losses: number
  bj_wins: number
}

export interface CasinoLeaderboardResponse {
  entries: CasinoLeaderboardEntry[]
  total: number
  page: number
  page_size: number
}

export function fetchCasinoLeaderboard(mode: 'slots' | 'bj' | 'total', type: 'wins' | 'losses', page: number): Promise<CasinoLeaderboardResponse> {
  return apiFetch(`/api/casino/leaderboard?mode=${mode}&type=${type}&page=${page}`)
}

// â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ ÐÐ½Ñ‚Ð¸Ñ€ÐµÐ¹Ð´ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export interface AntiRaidSettings {
  enabled: boolean
  join_window_sec: number
  join_threshold: number
  min_account_age_hours: number
  action_lockdown: boolean
  action_slowmode_sec: number
  cooldown_minutes: number
}

export function fetchAntiRaidSettings(): Promise<AntiRaidSettings> {
  return apiFetch('/api/antiraid')
}

export function updateAntiRaidSettings(settings: AntiRaidSettings): Promise<AntiRaidSettings> {
  return apiFetch('/api/antiraid', jsonInit('PUT', settings))
}

export interface SpamSettings {
  limit_with_attachments: number
  limit_without_attachments: number
  time_window_sec: number
}

export function fetchSpamSettings(): Promise<SpamSettings> {
  return apiFetch('/api/spam-settings')
}

export function updateSpamSettings(settings: SpamSettings): Promise<SpamSettings> {
  return apiFetch('/api/spam-settings', jsonInit('PUT', settings))
}

// â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Ð’ÐµÑ€Ð¸Ñ„Ð¸ÐºÐ°Ñ†Ð¸Ñ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export interface VerificationSettings {
  enabled: boolean
  // Ð¡Ñ‚Ñ€Ð¾ÐºÐ¸, Ð½Ðµ Ñ‡Ð¸ÑÐ»Ð°: Discord ID (snowflake) Ð¿Ñ€ÐµÐ²Ñ‹ÑˆÐ°ÐµÑ‚ Number.MAX_SAFE_INTEGER
  unverified_role_id: string
  verified_role_id: string
  welcome_text: string
  rules_consent_enabled: boolean
  reverify_enabled: boolean
  reverify_days: number
}

export function fetchVerificationSettings(): Promise<VerificationSettings> {
  return apiFetch('/api/verification')
}

export function updateVerificationSettings(settings: VerificationSettings): Promise<VerificationSettings> {
  return apiFetch('/api/verification', jsonInit('PUT', settings))
}

export function publishVerificationPanel(channelId: string): Promise<{ ok: boolean; message_id: string }> {
  return apiFetch('/api/verification/publish', jsonInit('POST', { channel_id: channelId }))
}

// ────────────────────────── New modules ──────────────────────────

export interface CustomCommand {
  id: string
  trigger: string
  match: 'exact' | 'contains'
  reply_text: string
  embed: Record<string, unknown> | null
  enabled: boolean
}

export interface CustomCommandsSettings {
  enabled: boolean
  commands: CustomCommand[]
}

export function fetchCustomCommands(): Promise<CustomCommandsSettings> {
  return apiFetch('/api/custom-commands')
}

export function setCustomCommandsEnabled(enabled: boolean): Promise<CustomCommandsSettings> {
  return apiFetch('/api/custom-commands/settings', jsonInit('PUT', { enabled }))
}

export function createCustomCommand(input: {
  trigger: string
  match?: 'exact' | 'contains'
  reply_text?: string
  embed?: Record<string, unknown> | null
  enabled?: boolean
}): Promise<CustomCommand> {
  return apiFetch('/api/custom-commands', jsonInit('POST', input))
}

export function updateCustomCommand(
  id: string,
  fields: Partial<Pick<CustomCommand, 'trigger' | 'match' | 'reply_text' | 'embed' | 'enabled'>>,
): Promise<CustomCommand> {
  return apiFetch(`/api/custom-commands/${id}`, jsonInit('PATCH', fields))
}

export async function deleteCustomCommand(id: string): Promise<void> {
  await apiFetch(`/api/custom-commands/${id}`, { method: 'DELETE' })
}

export interface ScheduledMessage {
  id: string
  channel_id: string
  content: string
  schedule_type: 'once' | 'daily'
  run_at: string
  daily_time: string
  enabled: boolean
  last_posted_date: string
  posted: boolean
}

export interface ScheduledMessagesSettings {
  enabled: boolean
  messages: ScheduledMessage[]
}

export function fetchScheduledMessages(): Promise<ScheduledMessagesSettings> {
  return apiFetch('/api/scheduled-messages')
}

export function setScheduledMessagesEnabled(enabled: boolean): Promise<ScheduledMessagesSettings> {
  return apiFetch('/api/scheduled-messages/settings', jsonInit('PUT', { enabled }))
}

export function createScheduledMessage(input: {
  channel_id: string
  content: string
  schedule_type: 'once' | 'daily'
  run_at?: string
  daily_time?: string
  enabled?: boolean
}): Promise<ScheduledMessage> {
  return apiFetch('/api/scheduled-messages', jsonInit('POST', input))
}

export function updateScheduledMessage(
  id: string,
  fields: Partial<Pick<ScheduledMessage, 'channel_id' | 'content' | 'schedule_type' | 'run_at' | 'daily_time' | 'enabled'>>,
): Promise<ScheduledMessage> {
  return apiFetch(`/api/scheduled-messages/${id}`, jsonInit('PATCH', fields))
}

export async function deleteScheduledMessage(id: string): Promise<void> {
  await apiFetch(`/api/scheduled-messages/${id}`, { method: 'DELETE' })
}

export interface InvitesSettings {
  enabled: boolean
  welcome_mention: boolean
  log_channel_id: string
  stats: { inviter_id: string; inviter_display?: string; joins: number }[]
  recent_joins: {
    invitee_id: string
    invitee_display?: string
    inviter_id: string | null
    inviter_display?: string | null
    code: string | null
    joined_at: string
  }[]
}

export function fetchInvites(): Promise<InvitesSettings> {
  return apiFetch('/api/invites')
}

export function updateInvitesSettings(input: {
  enabled: boolean
  welcome_mention: boolean
  log_channel_id: string
}): Promise<{ enabled: boolean; welcome_mention: boolean; log_channel_id: string }> {
  return apiFetch('/api/invites', jsonInit('PUT', input))
}

export interface TimedRoleEntry {
  id: number
  user_id: string
  display_name: string
  role_id: string
  role_name: string
  expires_at: string
  created_at: string
}

export function fetchTimedRoles(): Promise<{ timed_roles: TimedRoleEntry[] }> {
  return apiFetch('/api/timed-roles')
}

export async function deleteTimedRole(id: number): Promise<void> {
  await apiFetch(`/api/timed-roles/${id}`, { method: 'DELETE' })
}

export interface BirthdayEntry {
  user_id: string
  display_name: string
  mm_dd: string
}

export interface BirthdaysPayload {
  enabled: boolean
  channel_id: string
  ping_role_id: string
  last_announced_date: string
  birthdays: BirthdayEntry[]
}

export function fetchBirthdays(): Promise<BirthdaysPayload> {
  return apiFetch('/api/birthdays')
}

export function updateBirthdaySettings(input: {
  enabled: boolean
  channel_id: string
  ping_role_id: string
}): Promise<{ enabled: boolean; channel_id: string; ping_role_id: string; last_announced_date: string }> {
  return apiFetch('/api/birthdays/settings', jsonInit('PUT', input))
}

export function setBirthday(userId: string, mmDd: string): Promise<{ user_id: string; mm_dd: string }> {
  return apiFetch(`/api/birthdays/${userId}`, jsonInit('PUT', { mm_dd: mmDd }))
}

export async function deleteBirthday(userId: string): Promise<void> {
  await apiFetch(`/api/birthdays/${userId}`, { method: 'DELETE' })
}

export async function testBirthdayAnnounce(): Promise<void> {
  await apiFetch('/api/birthdays/test', { method: 'POST' })
}

export interface PollEntry {
  id: number
  guild_id: string
  channel_id: string
  message_id: string | null
  question: string
  options: string[]
  ends_at: string
  ended: boolean
  created_by: string | null
  created_at: string
  tallies: number[]
  total_votes: number
}

export function fetchPolls(): Promise<{ polls: PollEntry[] }> {
  return apiFetch('/api/polls')
}

export function endPoll(id: number): Promise<PollEntry> {
  return apiFetch(`/api/polls/${id}/end`, jsonInit('POST', {}))
}

export interface StickyEntry {
  id: string
  channel_id: string
  content: string
  message_id: string
  enabled: boolean
}

export interface StickySettings {
  enabled: boolean
  stickies: StickyEntry[]
}

export function fetchSticky(): Promise<StickySettings> {
  return apiFetch('/api/sticky')
}

export function setStickyEnabled(enabled: boolean): Promise<StickySettings> {
  return apiFetch('/api/sticky/settings', jsonInit('PUT', { enabled }))
}

export function upsertSticky(input: {
  channel_id: string
  content: string
  enabled?: boolean
  id?: string
}): Promise<StickyEntry> {
  return apiFetch('/api/sticky', jsonInit('POST', input))
}

export async function deleteSticky(id: string): Promise<void> {
  await apiFetch(`/api/sticky/${id}`, { method: 'DELETE' })
}

export async function testSticky(id: string): Promise<void> {
  await apiFetch(`/api/sticky/${id}/test`, { method: 'POST' })
}

export interface OwnerAlertsSettings {
  enabled: boolean
  notify_dm: boolean
  channel_id: string
  mass_ban_threshold: number
  mass_ban_window_sec: number
  module_error_threshold: number
  alert_missing_perms: boolean
  alert_mass_ban: boolean
  alert_module_errors: boolean
  weekly_digest_enabled: boolean
  weekly_digest_channel_id: string
}

export function fetchOwnerAlerts(): Promise<OwnerAlertsSettings> {
  return apiFetch('/api/owner-alerts')
}

export function updateOwnerAlerts(settings: OwnerAlertsSettings): Promise<OwnerAlertsSettings> {
  return apiFetch('/api/owner-alerts', jsonInit('PUT', settings))
}

export async function testOwnerAlerts(): Promise<void> {
  await apiFetch('/api/owner-alerts/test', { method: 'POST' })
}

export interface SetupHealthModuleIssue {
  module: string
  kind: 'missing_channel' | 'missing_role'
  detail: string
}

export interface SetupHealth {
  ok: boolean
  missing_permissions: string[]
  module_issues: SetupHealthModuleIssue[]
  guild_id: string
  guild_name: string
}

export function fetchSetupHealth(): Promise<SetupHealth> {
  return apiFetch('/api/setup-health')
}

export interface TimezoneSettings {
  code: string
  supported: string[]
}

export function fetchTimezone(): Promise<TimezoneSettings> {
  return apiFetch('/api/timezone')
}

export function updateTimezone(code: string): Promise<TimezoneSettings> {
  return apiFetch('/api/timezone', jsonInit('PUT', { code }))
}

export interface StickyRolesSettings {
  enabled: boolean
  tracked_role_ids: string[]
  ignored_role_ids: string[]
}

export function fetchStickyRoles(): Promise<StickyRolesSettings> {
  return apiFetch('/api/sticky-roles')
}

export function updateStickyRoles(settings: {
  enabled: boolean
  tracked_role_ids: string[]
  ignored_role_ids: string[]
}): Promise<StickyRolesSettings> {
  return apiFetch('/api/sticky-roles', jsonInit('PUT', settings))
}

export interface TemplatePreviewResult {
  content?: string
  embed?: Record<string, unknown>
  variables?: Record<string, string>
}

export function previewTemplate(input: {
  content?: string
  embed?: Record<string, unknown>
  variables?: Record<string, string>
}): Promise<TemplatePreviewResult> {
  return apiFetch('/api/preview/template', jsonInit('POST', input))
}

// ── Bot profile (per-guild nick / avatar / banner) ──

export interface BotProfileSettings {
  nick: string
  has_custom_avatar: boolean
  has_custom_banner: boolean
}

export interface BotProfileResponse {
  nick: string
  display_name: string
  avatar_url: string | null
  banner_url: string | null
  settings: BotProfileSettings
  ok?: boolean
}

export function fetchBotProfile(): Promise<BotProfileResponse> {
  return apiFetch('/api/bot-profile')
}

export function updateBotProfile(input: {
  nick?: string | null
  avatar?: string | null
  banner?: string | null
}): Promise<BotProfileResponse> {
  return apiFetch('/api/bot-profile', jsonInit('PUT', input))
}

// ── Starboard ──

export interface StarboardSettings {
  enabled: boolean
  channel_id: string
  emoji: string
  threshold: number
  self_star: boolean
  ignore_nsfw: boolean
}

export function fetchStarboard(): Promise<StarboardSettings> {
  return apiFetch('/api/starboard')
}

export function updateStarboard(settings: StarboardSettings): Promise<StarboardSettings> {
  return apiFetch('/api/starboard', jsonInit('PUT', settings))
}

// ── Relations ──

export interface RelationsAction {
  id: string
  emoji: string
  hp_gain: number
  cooldown_sec: number
  enabled: boolean
}

export interface RelationsSettings {
  enabled: boolean
  announce_channel_id: string
  max_actions_per_day: number
  actions: RelationsAction[]
  level_thresholds: number[]
  reward_roles: Record<string, string>
  marriage_enabled: boolean
  min_level_to_marry: number
  married_role_id: string
  allow_polygamy: boolean
  proposal_timeout_sec: number
  married_hp_bonus_percent: number
  divorce_requires_accept: boolean
  date_hp_gain: number
  date_cooldown_sec: number
}

export interface RelationsPairRow {
  user_a: string | number
  user_b: string | number
  hp: number
  level: number
  updated_at: number
}

export interface RelationsMarriageRow {
  user_a: string | number
  user_b: string | number
  married_at: number
  hp: number
  level: number
}

export function fetchRelations(): Promise<RelationsSettings> {
  return apiFetch('/api/relations')
}

export function updateRelations(settings: RelationsSettings): Promise<RelationsSettings> {
  return apiFetch('/api/relations', jsonInit('PUT', settings))
}

export async function fetchRelationsTop(limit = 15): Promise<RelationsPairRow[]> {
  const body = await apiFetch<{ pairs: RelationsPairRow[] }>(`/api/relations/top?limit=${limit}`)
  return body.pairs
}

export async function fetchRelationsMarriages(limit = 15): Promise<RelationsMarriageRow[]> {
  const body = await apiFetch<{ marriages: RelationsMarriageRow[] }>(
    `/api/relations/marriages?limit=${limit}`,
  )
  return body.marriages
}

// ── ValChecker ──

export interface ValCheckerSettings {
  enabled: boolean
  match_channel_id: string
  alert_channel_id: string
  poll_interval_sec: number
}

export function fetchValCheckerSettings(): Promise<ValCheckerSettings> {
  return apiFetch('/api/valchecker')
}

export function saveValCheckerSettings(settings: ValCheckerSettings): Promise<ValCheckerSettings> {
  return apiFetch('/api/valchecker', jsonInit('PUT', settings))
}

// ── Auto-reactions ──

export interface AutoReactionRule {
  id: string
  /** `list` = use `emojis`; `all_guild` = react with every custom emoji on the server (up to Discord’s 20-reaction limit). */
  emoji_mode: 'list' | 'all_guild'
  emojis: string[]
  keywords: string[]
  channel_mode: 'all' | 'include'
  channel_ids: string[]
  exclude_channel_ids: string[]
  ignore_bots: boolean
}

export interface AutoReactionsSettings {
  enabled: boolean
  rules: AutoReactionRule[]
}

export function fetchAutoReactions(): Promise<AutoReactionsSettings> {
  return apiFetch('/api/auto-reactions')
}

export function updateAutoReactions(settings: AutoReactionsSettings): Promise<AutoReactionsSettings> {
  return apiFetch('/api/auto-reactions', jsonInit('PUT', settings))
}

export interface CustomsRankInfo {
  id: string
  name: string
  weight: number
}

export interface CustomsMapInfo {
  id: string
  name: string
  enabled: boolean
}

export interface CustomsSettings {
  enabled: boolean
  channel_id: string
  host_role_id: string
  /** Optional Discord category for auto-created lobby/team voice channels. */
  voice_category_id: string
  /** Create a waiting voice lobby on publish (default on). */
  auto_lobby_vc: boolean
  /** Create team VCs and move players on Start (default on). */
  auto_move_on_start: boolean
  rank_roles: Record<string, string>
  map_pool: Record<string, boolean>
  require_rank_role: boolean
  /** Legacy; check-in UI removed from lobby embed. */
  checkin_enabled?: boolean
  vote_seconds: number
  xp_on_win: number
  default_mode: 'solo' | 'team_code'
  default_name: string
  default_notes: string
  default_ping: CustomsPingMode
  ping_role_id: string
  default_signup_minutes: number
  avoid_last_map: boolean
  results_channel_id: string
  announcement_template: string
  reminder_minutes: number
  reminder_mode: 'lobby' | 'dm'
  audit_channel_id: string
  default_banned_maps: string[]
  features: {
    side_random: boolean
    voting: boolean
  }
  last_map_id: string
  schedules: CustomsSchedule[]
  ranks: CustomsRankInfo[]
  maps: CustomsMapInfo[]
}

export type CustomsPingMode = 'none' | 'participants' | 'role'

export interface CustomsPlayer {
  user_id: string
  rank: string
  rank_name: string
  team_code: string
  team: string | null
  nick?: string
  username?: string
  global_name?: string
  display_name?: string
}

/** Prefer guild nick → display_name → global_name → username; fall back to id. */
export function customsPlayerLabel(p: Pick<CustomsPlayer, 'user_id' | 'nick' | 'username' | 'global_name' | 'display_name'>): string {
  return (
    (p.nick || '').trim() ||
    (p.display_name || '').trim() ||
    (p.global_name || '').trim() ||
    (p.username || '').trim() ||
    p.user_id
  )
}

export interface CustomsLobbySummary {
  id: string
  name: string
  notes: string
  status: string
  join_mode: 'solo' | 'team_code'
  channel_id: string
  message_id: string
  host_id: string
  players: number
  max_players: number
  map_id: string
  map_name: string
  side: string
  ping: CustomsPingMode
  banned_maps: string[]
  signup_minutes: number
  signup_ends_at: number
  score: { a: number; b: number }
  players_list: CustomsPlayer[]
  subs_list: CustomsPlayer[]
  team_a: CustomsPlayer[]
  team_b: CustomsPlayer[]
  created_at: number
  jump_url?: string
}

export interface CreateCustomsLobbySpec {
  name: string
  notes?: string
  join_mode: 'solo' | 'team_code'
  channel_id: string
  ping?: CustomsPingMode
  signup_minutes?: number
  banned_maps?: string[]
}

export interface CustomsSchedule {
  id: string
  enabled: boolean
  weekday: number
  hour: number
  minute: number
  name: string
  notes: string
  join_mode: 'solo' | 'team_code'
  channel_id: string
  ping: CustomsPingMode
  signup_minutes: number
  last_run?: string
}

export async function fetchCategories(): Promise<ChannelInfo[]> {
  const body = await apiFetch<{ categories: { id: string; name: string }[] }>('/api/customs/categories')
  return body.categories.map((c) => ({ id: c.id, name: c.name }))
}

export function fetchCustomsSettings(): Promise<CustomsSettings> {
  return apiFetch('/api/customs')
}

export function updateCustomsSettings(settings: Partial<CustomsSettings>): Promise<CustomsSettings> {
  return apiFetch('/api/customs', jsonInit('PUT', settings))
}

export function fetchCustomsLobbies(status: string = 'active'): Promise<CustomsLobbySummary[]> {
  return apiFetch<{ lobbies: CustomsLobbySummary[] }>(`/api/customs/lobbies?status=${encodeURIComponent(status)}`).then(
    (r) => r.lobbies,
  )
}

export function createCustomsLobby(spec: CreateCustomsLobbySpec): Promise<CustomsLobbySummary> {
  return apiFetch('/api/customs/lobbies', jsonInit('POST', spec))
}

export function rematchCustomsLobby(lobbyId: string): Promise<CustomsLobbySummary> {
  return apiFetch(`/api/customs/lobbies/${encodeURIComponent(lobbyId)}/rematch`, jsonInit('POST', {}))
}

export function kickCustomsPlayer(lobbyId: string, userId: string): Promise<{ ok: boolean; lobby: CustomsLobbySummary }> {
  return apiFetch(`/api/customs/lobbies/${encodeURIComponent(lobbyId)}/kick`, jsonInit('POST', { user_id: userId }))
}

export function setCustomsLobbyBans(
  lobbyId: string,
  mapIds: string[],
): Promise<{ ok: boolean; lobby: CustomsLobbySummary }> {
  return apiFetch(`/api/customs/lobbies/${encodeURIComponent(lobbyId)}/bans`, jsonInit('PUT', { map_ids: mapIds }))
}

export function setCustomsLobbyTeams(
  lobbyId: string,
  teamA: string[],
  teamB: string[],
): Promise<{ ok: boolean; lobby: CustomsLobbySummary }> {
  return apiFetch(
    `/api/customs/lobbies/${encodeURIComponent(lobbyId)}/teams`,
    jsonInit('PUT', { team_a: teamA, team_b: teamB }),
  )
}

export function setCustomsLobbyScore(
  lobbyId: string,
  scoreA: number,
  scoreB: number,
): Promise<{ ok: boolean; lobby: CustomsLobbySummary }> {
  return apiFetch(
    `/api/customs/lobbies/${encodeURIComponent(lobbyId)}/score`,
    jsonInit('POST', { score_a: scoreA, score_b: scoreB }),
  )
}

export function cancelCustomsLobby(lobbyId: string): Promise<{ ok: boolean; lobby: CustomsLobbySummary }> {
  return apiFetch(`/api/customs/lobbies/${encodeURIComponent(lobbyId)}/cancel`, jsonInit('POST', {}))
}

export function createCustomsSchedule(spec: Omit<CustomsSchedule, 'id' | 'last_run'>): Promise<CustomsSchedule> {
  return apiFetch('/api/customs/schedules', jsonInit('POST', spec))
}

export function deleteCustomsSchedule(scheduleId: string): Promise<{ ok: boolean }> {
  return apiFetch(`/api/customs/schedules/${encodeURIComponent(scheduleId)}`, jsonInit('DELETE'))
}

export interface CustomsBlacklistEntry {
  user_id: string
  remaining_games: number
  reason: string
}

export function fetchCustomsBlacklist(): Promise<CustomsBlacklistEntry[]> {
  return apiFetch<{ entries: CustomsBlacklistEntry[] }>('/api/customs/blacklist').then((body) => body.entries)
}

export function setCustomsBlacklist(userId: string, games: number, reason = ''): Promise<CustomsBlacklistEntry> {
  return apiFetch(`/api/customs/blacklist/${encodeURIComponent(userId)}`, jsonInit('PUT', { games, reason }))
}

export async function removeCustomsBlacklist(userId: string): Promise<void> {
  await apiFetch(`/api/customs/blacklist/${encodeURIComponent(userId)}`, { method: 'DELETE' })
}

// ──────────────────────── Banner Rotation ────────────────────────

export interface BannerRotationImage {
  id: string
  filename: string
  original_name: string
  uploaded_at: number
  url: string
}

export interface BannerRotationSettings {
  enabled: boolean
  banner_enabled: boolean
  banner_mode: 'playlist' | 'dynamic' | 'both'
  dynamic_window_days: number
  icon_enabled: boolean
  interval_minutes: number
  log_channel_id: string
  banners: BannerRotationImage[]
  icons: BannerRotationImage[]
  last_banner_id: string
  last_icon_id: string
  last_banner_at: number
  last_icon_at: number
  next_run_at: number
}

export function fetchBannerRotationSettings(): Promise<BannerRotationSettings> {
  return apiFetch('/api/banner-rotation')
}

export function updateBannerRotationSettings(
  settings: Partial<
    Pick<
      BannerRotationSettings,
      'enabled' | 'banner_enabled' | 'banner_mode' | 'dynamic_window_days' | 'icon_enabled' | 'interval_minutes' | 'log_channel_id'
    >
  >,
): Promise<BannerRotationSettings> {
  return apiFetch('/api/banner-rotation', jsonInit('PUT', settings))
}

export async function uploadBannerRotationImage(
  kind: 'banner' | 'icon',
  file: File,
): Promise<{ ok: boolean; image: BannerRotationImage }> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await fetch(`/api/banner-rotation/${kind}s`, {
    method: 'POST',
    credentials: 'include',
    body: formData,
  })
  if (!response.ok) {
    let detail = ''
    try {
      detail = ((await response.json()) as { error?: string }).error ?? ''
    } catch {
      /* non-JSON */
    }
    throw new ApiError(response.status, detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export function deleteBannerRotationImage(
  kind: 'banner' | 'icon',
  imageId: string,
): Promise<{ ok: boolean }> {
  return apiFetch(`/api/banner-rotation/${kind}s/${encodeURIComponent(imageId)}`, jsonInit('DELETE'))
}

export function triggerBannerRotation(): Promise<{ ok: boolean; settings: BannerRotationSettings }> {
  return apiFetch('/api/banner-rotation/rotate-now', jsonInit('POST', {}))
}

export interface PremierSettings { enabled: boolean; channel_id: string; faq_url: string }
export interface ValorantPanelSettings {
  enabled: boolean; button_role_id: string; button_label: string
  agent_roles: Record<string, string>; playstyle_roles: Record<string, string>
  notification_roles: Record<string, string>; server_roles: Record<string, string>
  notification_channels: Record<string, string>
}
export interface ValorantPanelCatalog {
  agent_classes: Record<string, { key: string; name: string }[]>
  playstyles: { key: string; name: string }[]
  notifications: { key: string; name: string }[]
  servers: { key: string; name: string }[]
}
export interface IdeasSettings {
  enabled: boolean; intake_channel_id: string; review_channel_id: string; channel_id: string
  prompt: string; vote_emojis: string[]
}
export interface IdeaCase { case_id: string; submitter_id: string; submitter_display: string; text: string; status: string; created_at: string }
export const fetchPremierSettings = () => apiFetch<PremierSettings>('/api/valorant/premier')
export const updatePremierSettings = (data: Partial<PremierSettings>) => apiFetch<PremierSettings>('/api/valorant/premier', jsonInit('PUT', data))
export const fetchValorantPanels = () => apiFetch<{ settings: ValorantPanelSettings; catalog: ValorantPanelCatalog }>('/api/valorant/panels')
export const updateValorantPanels = (data: Partial<ValorantPanelSettings>) => apiFetch<{ settings: ValorantPanelSettings; catalog: ValorantPanelCatalog }>('/api/valorant/panels', jsonInit('PUT', data))
export const fetchValorantCommands = () => apiFetch<{ enabled: boolean }>('/api/valorant/commands')
export const updateValorantCommands = (enabled: boolean) => apiFetch<{ enabled: boolean }>('/api/valorant/commands', jsonInit('PUT', { enabled }))
export const fetchIdeasSettings = () => apiFetch<IdeasSettings>('/api/ideas/settings')
export const updateIdeasSettings = (data: Partial<IdeasSettings>) => apiFetch<IdeasSettings>('/api/ideas/settings', jsonInit('PUT', data))
export const fetchIdeaCases = (status?: string) => apiFetch<{ cases: IdeaCase[] }>(`/api/ideas/cases${status ? `?status=${encodeURIComponent(status)}` : ''}`).then((body) => body.cases)
export const decideIdeaCase = (caseId: string, approved: boolean) => apiFetch<{ ok: boolean }>(`/api/ideas/cases/${encodeURIComponent(caseId)}/decide`, jsonInit('POST', { approved }))

