import type { TranslationDict } from '../types'

/** Privacy policy and terms of service (public pages). */
const legal: TranslationDict = {
  'privacy.title': 'Privacy Policy',
  'privacy.lastUpdated': 'Last updated: July 23, 2026',

  'privacy.s1.title': '1. General provisions',
  'privacy.s1.p1':
    '1.1. This policy describes what data the Cheterin Discord bot and its web control panel (the "Service") process, why they are used, where they are stored, and how to delete them.',
  'privacy.s1.p2':
    '1.2. The Service is a centrally hosted bot that can operate on multiple Discord servers at once. Each server\'s data is isolated and tied to its identifier (guild_id): one server\'s actions and settings are not visible to or do not affect others. The Service developer manages the infrastructure (hosting); each server\'s administration controls that server\'s settings and data through the dashboard. Data is not sold or shared with third parties.',
  'privacy.s1.p3':
    '1.3. We follow data minimization: the Service stores only what is strictly necessary for its features to work.',

  'privacy.s2.title': '2. What data is processed',
  'privacy.s2.p1': '2.1. When signing in to the dashboard (via official Discord OAuth2 with "identify" and "guilds" scopes):',
  'privacy.s2.li1': 'your Discord account identifier (ID);',
  'privacy.s2.li2': 'username and avatar;',
  'privacy.s2.li3':
    'the list of servers you belong to, with your permission flags on each — to show which servers you can manage and let you choose one;',
  'privacy.s2.li4.prefix': 'on the selected server, your',
  'privacy.s2.li4.bold': 'Manage Server',
  'privacy.s2.li4.suffix': 'or Administrator permission is verified — that is what grants access to that server\'s settings.',
  'privacy.s2.p2':
    'Discord tokens (access/refresh) obtained during authorization are stored server-side only for your current session (to fetch an up-to-date list of your servers) and are removed when you sign out of the panel.',
  'privacy.s2.p3.bold':
    'Passwords, email, phone numbers, and payment data are not available to the Service and are never requested.',
  'privacy.s2.p4': '2.2. When bot modules are in use:',
  'privacy.table.colModule': 'Module',
  'privacy.table.colData': 'What data',
  'privacy.table.colRetention': 'Retention period',
  'privacy.table.tickets.module': 'Tickets and feedback',
  'privacy.table.tickets.data': 'Author ID, category, request text, status, who reviewed it and when',
  'privacy.table.tickets.retention': 'Until deleted by administration',
  'privacy.table.invites.module': 'Invite statistics',
  'privacy.table.invites.data': 'Inviter and invitee IDs, joins/leaves/invites counters',
  'privacy.table.invites.retention': 'Until deleted by administration',
  'privacy.table.supply.module': 'Supply runs',
  'privacy.table.supply.data': 'Initiator and participant IDs, objective, time, run status; visit counter',
  'privacy.table.supply.retention': 'Limited history (older records are removed automatically)',
  'privacy.table.voiceRooms.module': 'Private voice rooms',
  'privacy.table.voiceRooms.data': 'Owner ID, room name, user limit, individual access rules (allow/deny)',
  'privacy.table.voiceRooms.retention': 'Removed immediately when the room is deleted',
  'privacy.table.modlog.module': 'Moderation log',
  'privacy.table.modlog.data': 'Action type (ban/kick/spam/tempban), offender and moderator IDs, reason, time',
  'privacy.table.modlog.retention': 'Until deleted by administration',
  'privacy.table.rating.module': 'Member ranking',
  'privacy.table.rating.data': 'Member ID, XP, level, message count, total voice activity time',
  'privacy.table.rating.retention': 'Until rating reset or deletion on request',
  'privacy.table.voiceSessions.module': 'Voice sessions',
  'privacy.table.voiceSessions.data': 'Member ID, channel, join/leave time, active seconds — for stats and voice XP',
  'privacy.table.voiceSessions.retention': 'Raw sessions — limited period, then aggregated totals only',
  'privacy.table.audit.module': 'Dashboard audit',
  'privacy.table.audit.data': 'Moderator ID and name, panel action type, time — successful mutating actions only',
  'privacy.table.audit.retention': 'Until deleted by administration',
  'privacy.table.streams.module': 'Stream subscriptions',
  'privacy.table.streams.data':
    'Streamer logins/IDs and YouTube channel IDs, notification settings; member personal data is not involved',
  'privacy.table.streams.retention': 'Until the subscription is removed',
  'privacy.table.events.module': 'Events and brackets',
  'privacy.table.events.data': 'Event participant IDs, nicknames/team names in brackets',
  'privacy.table.events.retention': 'Until the event/bracket is deleted',
  'privacy.table.reactionRoles.module': 'Reaction roles, buttons, embeds',
  'privacy.table.reactionRoles.data': 'Message, channel, and role IDs; form and button text',
  'privacy.table.reactionRoles.retention': 'Until the binding is removed',
  'privacy.table.economy.module': 'Economy and casino',
  'privacy.table.economy.data':
    'Member ID, balance, shop purchases, transfer and bet history, casino game results; optional weekly report channel ID',
  'privacy.table.economy.retention': 'Until deleted by administration or balance reset',
  'privacy.table.wordle.module': 'Wordle and fun games',
  'privacy.table.wordle.data': 'Member ID, daily Wordle progress and streaks; game cooldowns (per server)',
  'privacy.table.wordle.retention': 'Until deleted by administration',
  'privacy.table.polls.module': 'Polls',
  'privacy.table.polls.data': 'Question text, options, voter IDs and choices, end time, status',
  'privacy.table.polls.retention': 'Until deleted by administration',
  'privacy.table.sticky.module': 'Sticky messages',
  'privacy.table.sticky.data': 'Channel ID, sticky text, last posted message ID',
  'privacy.table.sticky.retention': 'Until the sticky is removed',
  'privacy.table.customCommands.module': 'Custom commands',
  'privacy.table.customCommands.data': 'Trigger text, match mode, reply text configured by administration',
  'privacy.table.customCommands.retention': 'Until the command is deleted',
  'privacy.table.scheduledMessages.module': 'Scheduled messages',
  'privacy.table.scheduledMessages.data': 'Channel ID, message content, schedule, last/next run time',
  'privacy.table.scheduledMessages.retention': 'Until the schedule is deleted',
  'privacy.table.timedRoles.module': 'Timed roles',
  'privacy.table.timedRoles.data': 'Member ID, role ID, grant and expiry time',
  'privacy.table.timedRoles.retention': 'Removed automatically when the role expires or is cancelled',
  'privacy.table.birthdays.module': 'Server birthdays',
  'privacy.table.birthdays.data': 'Member ID and birthday date (day/month; year optional)',
  'privacy.table.birthdays.retention': 'Until deleted by the member or administration',
  'privacy.table.ownerAlerts.module': 'Owner alerts',
  'privacy.table.ownerAlerts.data':
    'Alert thresholds and channel ID; no member message content — only operational signals (missing permissions, mass bans, module errors)',
  'privacy.table.ownerAlerts.retention': 'Settings — until changed',
  'privacy.table.games.module': 'Mafia and Bunker',
  'privacy.table.games.data':
    'Active game state, participant IDs, roles/traits for the current match; public action tokens for personal links',
  'privacy.table.games.retention': 'Cleared when the game ends (or after a short cleanup window)',
  'privacy.table.news.module': 'News relay (main server feature)',
  'privacy.table.news.data': 'Source server, bot, and channel IDs; forwarded message content is not stored',
  'privacy.table.news.retention': 'Settings — until changed',
  'privacy.table.config.module': 'Configuration',
  'privacy.table.config.data': 'Channel and role IDs selected by administration for modules (per server)',
  'privacy.table.config.retention': 'Until settings are changed',
  'privacy.s2.p5.label': 'Message content.',
  'privacy.s2.p5.rest':
    'The bot does not archive chat history. Message content is processed only to the extent required by features explicitly enabled by administration: anti-spam analyzes recent messages in a temporary cache (cleared every few minutes); sticky, scheduled, and custom-command modules store only the texts configured by administration (not the full channel history); the news relay module forwards source-bot messages without storing them; and the logging module publishes deleted and edited message content to a Discord log channel if administration enabled that event type. For the level system, message content is not stored — only the fact of a message is recorded for XP.',

  'privacy.s3.title': '3. What the Service does not do',
  'privacy.s3.li1': 'Does not sell or share data with third parties in any form.',
  'privacy.s3.li2': 'Does not use data for advertising, behavioral analytics, or profiling.',
  'privacy.s3.li3': 'Does not read users\' direct messages (DMs), except to send its own notifications.',
  'privacy.s3.li4':
    'Does not collect data from servers where it is not installed; on each installed server, data is processed in isolation. Exception — news relay (main server feature): public messages from bots on the source server are read but not stored.',
  'privacy.s3.li5': 'Does not install third-party trackers, pixels, or analytics cookies on the website.',

  'privacy.s4.title': '4. Processing purposes',
  'privacy.s4.li1':
    'Operating user-requested features: tickets, supply runs, rooms, roles, events, economy, polls, sticky and scheduled messages, custom commands, timed roles, birthdays, and games.',
  'privacy.s4.li2': 'Verifying dashboard access rights.',
  'privacy.s4.li3': 'Server moderation and safety (anti-spam, action log, owner alerts).',
  'privacy.s4.li4': 'Showing statistics (invites, supply run attendance, economy tops) to administrators and moderators.',

  'privacy.s5.title': '5. Where and how data is stored',
  'privacy.s5.p1':
    '5.1. All data is stored on the host running the bot: SQLite databases (including a unified settings database split by server) and some legacy configuration files. External databases and cloud storage are not used. Different servers\' data is separated by server identifier (guild_id).',
  'privacy.s5.p2':
    '5.2. Only the team operating the bot hosting has file-level access to data. Dashboard access to a specific server\'s data is limited to members with Manage Server or Administrator on that server and is verified on every request.',
  'privacy.s5.p3':
    '5.3. Dashboard sessions are protected by encryption (secret key at least 32 characters); authorization is delegated to Discord OAuth2.',

  'privacy.s6.title': '6. Cookies',
  'privacy.s6.p1':
    'The site uses a single encrypted session cookie — solely to keep you signed in to the dashboard. It does not contain personal data in plain text and is not used for tracking. Public pages (documentation, terms, this policy) work without cookies.',

  'privacy.s7.title': '7. Data sharing',
  'privacy.s7.p1.prefix':
    '7.1. Data is not shared with third parties. The only external service the Service interacts with is the Discord platform (API), without which the bot cannot operate. Discord\'s data processing is governed by the',
  'privacy.s7.discordPrivacyLink': 'Discord Privacy Policy',
  'privacy.s7.p2':
    '7.2. If administration configured a webhook for form buttons, user form responses are sent to the webhook URL they specified (usually a channel on the same Discord server).',
  'privacy.s7.p3':
    '7.3. For stream alerts, the Service calls public Twitch APIs and YouTube RSS feeds. Only logins/IDs of tracked streamers specified by administration are sent; server member data is not shared with those services.',

  'privacy.s8.title': '8. Retention and deletion',
  'privacy.s8.p1': '8.1. Automatic deletion:',
  'privacy.s8.li1': 'private room records — immediately after the channel is deleted;',
  'privacy.s8.li2': 'supply run history — older completed runs are removed when the storage limit is exceeded;',
  'privacy.s8.li3': 'anti-spam cache — every few minutes;',
  'privacy.s8.li4': 'raw voice sessions — after the retention period (aggregated stats remain);',
  'privacy.s8.li5': 'role bindings to deleted messages — on bot startup;',
  'privacy.s8.li6': 'dashboard session — when you sign out of the panel;',
  'privacy.s8.li7': 'timed role grants — when they expire or are cancelled;',
  'privacy.s8.li8': 'finished Mafia/Bunker game state — after the match ends (or a short cleanup window).',
  'privacy.s8.p2.label': 'Deletion on request.',
  'privacy.s8.p2.rest':
    'You may request deletion of data linked to your account (invite stats, applications, participation history, rating and XP, economy balance, birthday entry). Contact your server\'s administration (or open a ticket via the CTD panel on the main server) — resetting an individual member\'s rating or balance is available to administration in the dashboard. A server owner may request full deletion of all their server\'s data when removing the bot from the server.',

  'privacy.s9.title': '9. Your rights',
  'privacy.s9.li1': 'find out what data the Service stores about you (request via server administration or a ticket);',
  'privacy.s9.li2': 'request correction of inaccurate data;',
  'privacy.s9.li3':
    'request deletion of your data (except moderation log entries required for server safety);',
  'privacy.s9.li4': 'stop using the Service at any time.',

  'privacy.s10.title': '10. Age restrictions',
  'privacy.s10.p1':
    'The Service is intended for users who meet Discord\'s minimum age in their country (typically 13 or older). The Service does not knowingly collect data from children below that age.',

  'privacy.s11.title': '11. Policy changes',
  'privacy.s11.p1':
    'The current policy is always published on this page; the last update date is shown at the top. Material changes are announced in the server announcements channel.',

  'privacy.s12.title': '12. Contact',
  'privacy.s12.p1':
    'Questions about data processing: contact your server\'s administration (or open a ticket via the CTD panel on the main server). For bot and hosting questions — developer Nandak070.',

  'terms.title': 'Terms of Service',
  'terms.lastUpdated': 'Last updated: July 23, 2026',

  'terms.s1.title': '1. Terms and definitions',
  'terms.s1.li1.prefix': '"Service"',
  'terms.s1.li1.rest':
    '— the Cheterin Discord bot, web control panel (dashboard), public website, and all related features.',
  'terms.s1.li2.prefix': '"Bot"',
  'terms.s1.li2.rest': '— the Cheterin Discord application account added to a server.',
  'terms.s1.li3.prefix': '"Dashboard"',
  'terms.s1.li3.rest':
    '— the web interface for managing bot settings, available after signing in through Discord.',
  'terms.s1.li4.prefix': '"Server"',
  'terms.s1.li4.rest':
    '— a community (guild) on Discord where the bot runs. One Cheterin instance can serve multiple servers; each server\'s data and settings are isolated.',
  'terms.s1.li5.prefix': '"Main server"',
  'terms.s1.li5.rest':
    '— the developer\'s server tied to utility features (CTD tickets, news relay, Super Admin section).',
  'terms.s1.li6.prefix': '"User"',
  'terms.s1.li6.rest':
    '— any server member interacting with the bot: commands, buttons, forms, voice channels, or the dashboard.',
  'terms.s1.li7.prefix': '"Administration"',
  'terms.s1.li7.rest': '— the server owner and people authorized by them to manage the Service.',
  'terms.s1.li8.prefix': '"Private room"',
  'terms.s1.li8.rest':
    '— a voice channel automatically created by the bot when a user joins a lobby channel.',

  'terms.s2.title': '2. Acceptance of terms',
  'terms.s2.p1':
    '2.1. These terms are a public offer. By using the Service in any way — being on a server where the bot runs, calling its commands, clicking its buttons, creating private rooms, signing up for supply runs, or signing in to the dashboard — you confirm that you have read and fully accept these terms.',
  'terms.s2.p2':
    '2.2. If you do not agree, stop using the Service. For server owners, that means removing the bot from the server.',
  'terms.s2.p3.prefix': '2.3. Use of the Service is allowed only when complying with Discord\'s',
  'terms.s2.discordTerms': 'Terms of Service',
  'terms.s2.p3.and': 'and',
  'terms.s2.discordGuidelines': 'Community Guidelines',
  'terms.s2.p3.suffix': ', including the minimum age Discord sets for your country.',

  'terms.s3.title': '3. Service description',
  'terms.s3.p1': '3.1. The Service provides Discord server automation tools, including but not limited to:',
  'terms.s3.li1': 'moderation: anti-spam, temporary bans, lockdown mode, action log;',
  'terms.s3.li2': 'level and ranking system: XP for text and voice activity, reward roles, rank cards, leaderboards;',
  'terms.s3.li3': 'server event logging and voice activity statistics;',
  'terms.s3.li4': 'ticket system (CTD) and feedback with categories and resolutions;',
  'terms.s3.li5': 'welcome messages, invite statistics, auto-roles, and reaction roles;',
  'terms.s3.li6': 'embed message builder, templates, and interactive form buttons;',
  'terms.s3.li7':
    'events, dedicated polls, giveaways, and tournament brackets (Single/Double Elimination, Round Robin) with public links;',
  'terms.s3.li8': 'supply runs with a waitlist and reminders;',
  'terms.s3.li9': 'private voice rooms with a control panel;',
  'terms.s3.li10': 'Twitch stream and YouTube video alerts (optional mention settings);',
  'terms.s3.li11': 'message relay from a source server (main server feature);',
  'terms.s3.li12':
    'economy and casino: server currency, shop, transfers, slots/coinflip/blackjack, optional weekly report;',
  'terms.s3.li13':
    'entertainment: Russian roulette, Wordle, Auto-Emoji, and other fun commands;',
  'terms.s3.li14':
    'custom commands, scheduled and sticky messages, command preview in the dashboard;',
  'terms.s3.li15': 'timed roles, server-wide birthday calendar, and owner operational alerts;',
  'terms.s3.li16': 'role-playing games Mafia and Bunker with personal web action links;',
  'terms.s3.li17':
    'web dashboard to manage all of the above, with server selection, RU/EN bot language per server, and moderator action audit.',
  'terms.s3.p2':
    '3.2. Cheterin uses a multi-server model: you can add the bot to your server via an invite link, then select the active server in the dashboard and configure its modules independently of other servers. Modules are disabled by default on a new server.',
  'terms.s3.p3':
    '3.3. Certain utility features (CTD tickets, news relay, Super Admin section) are main-server privileges and are unavailable on other servers.',
  'terms.s3.p4':
    '3.4. Features may change: modules may be added, modified, or removed without prior notice.',

  'terms.s4.title': '4. Rules of use',
  'terms.s4.p1': '4.1. When using the Service, you must not:',
  'terms.s4.li1':
    'use the Service for spam, raids, harassment, fraud, or any other harmful activity;',
  'terms.s4.li2':
    'attempt unauthorized access to the dashboard, API, other users\' data, or other servers;',
  'terms.s4.li3':
    'interfere with the Service: overload it with requests, exploit vulnerabilities, or bypass limits (cooldowns, caps, permission checks);',
  'terms.s4.li4':
    'artificially inflate XP and ranking (farming bots, coordinated voice "hangouts" that bypass activity mechanics, etc.) — administration may reset inflated ranking and remove reward roles;',
  'terms.s4.li5':
    'impersonate Service administration or use the Cheterin name and branding to mislead others;',
  'terms.s4.li6':
    'publish content through bot features (room names, supply run text, forms, tickets) that violates law or Discord rules.',
  'terms.s4.p2':
    '4.2. Administration may restrict or fully block access to Service features for users who violate these terms, without prior notice.',

  'terms.s5.title': '5. Private voice rooms',
  'terms.s5.sub1.title': '5.1. Naming rules',
  'terms.s5.sub1.p1':
    'Private room names are set by users but must not contain ads for third-party projects, direct insults, malicious links, or content that violates Discord\'s global rules. The system and administration may forcibly reset a name or delete a channel without warning.',
  'terms.s5.sub2.title': '5.2. Visibility and transparency',
  'terms.s5.sub2.p1':
    'Room owners may moderate access themselves (grant invites, kick, deny connection). However, manually hiding a channel (removing @everyone\'s view permission) is treated as a violation of project architectural standards. Infrastructure will automatically force visibility for such rooms.',
  'terms.s5.sub3.title': '5.3. Lifecycle',
  'terms.s5.sub3.p1':
    'To optimize server resources, empty private rooms are automatically removed. A channel exists only while at least one member is in it.',
  'terms.s5.sub4.title': '5.4. Owner responsibility',
  'terms.s5.sub4.p1':
    'The creator of a private voice channel is responsible for moderating the local community inside their room.',

  'terms.s6.title': '6. Dashboard and access',
  'terms.s6.p1':
    '6.1. Dashboard sign-in is exclusively through official Discord authorization (OAuth2, "identify" and "guilds" scopes). The Service never asks for passwords, two-factor codes, or payment data.',
  'terms.s6.p2.prefix':
    '6.2. After sign-in, you choose a server to manage from those where you have the required permissions. Access to a specific server\'s settings is granted only to members with',
  'terms.s6.p2.bold': 'Manage Server',
  'terms.s6.p2.suffix':
    'or Administrator on that server. Every API request is re-verified — you cannot retain access after losing permissions.',
  'terms.s6.p3':
    '6.3. The server owner is fully responsible for whom they grant server management permissions and for all actions those people take through the panel (bans, kicks, setting changes, bulk role grants).',
  'terms.s6.p4':
    '6.4. All mutating actions in the dashboard are recorded in an audit log (who changed what and when). By using the panel, you agree to such logging.',
  'terms.s6.p5':
    '6.5. Public pages (documentation, terms, privacy policy, public tournament brackets, public leaderboard) are available without authorization.',

  'terms.s7.title': '7. User content',
  'terms.s7.p1':
    '7.1. Room names, supply run text, feedback requests, form responses, ticket messages, and other content are created by users. Authors are responsible for that content.',
  'terms.s7.p2':
    '7.2. Administration does not pre-moderate user content but may remove content that violates Discord rules or these terms and apply sanctions to its authors.',
  'terms.s7.p3':
    '7.3. By submitting content through Service features, you grant the Service the right to process, store, and display that content as needed for the relevant features (for example, showing your request to moderators in the dashboard).',

  'terms.s8.title': '8. Service availability',
  'terms.s8.p1':
    '8.1. The Service is provided free of charge and "as is", without any express or implied warranties: uninterrupted operation, error-free performance, or fitness for a particular purpose.',
  'terms.s8.p2':
    '8.2. The Service depends on Discord and its API. Outages, limits, and changes on Discord\'s side may affect the Service; administration is not liable for such disruptions.',
  'terms.s8.p3':
    '8.3. We make reasonable efforts for resilience: active supply runs, private rooms, tickets, and module settings are restored automatically after a bot restart. However, we do not guarantee data survival during hardware failures and recommend that server administration not use the Service as the sole store of critical information.',
  'terms.s8.p4':
    '8.4. Maintenance may occur without prior notice and may temporarily make the bot and dashboard unavailable.',

  'terms.s9.title': '9. Limitation of liability',
  'terms.s9.p1':
    '9.1. To the maximum extent permitted by law, Cheterin developers and administration are not liable for any direct or indirect damages, data loss, lost profits, or other harm arising from use or inability to use the Service.',
  'terms.s9.p2':
    '9.2. The Service is not affiliated with Discord Inc. and is not its product or partner. Discord is a trademark of Discord Inc.',

  'terms.s10.title': '10. Termination of access',
  'terms.s10.p1':
    '10.1. You may stop using the Service at any time. A server owner may remove the bot from the server — server settings and data may be deleted on request (see the Privacy Policy).',
  'terms.s10.p2':
    '10.2. Administration may terminate or suspend the Service fully or partially, including for individual users or servers, when these terms are violated.',

  'terms.s11.title': '11. Changes to terms',
  'terms.s11.p1':
    '11.1. Terms may be updated. The current version is always published on this page; the last update date is shown at the top.',
  'terms.s11.p2':
    '11.2. Material changes are announced in the server announcements channel. Continued use of the Service after changes are published means acceptance of the new version.',

  'terms.s12.title': '12. Contact',
  'terms.s12.p1':
    'For Service questions, open a ticket via the CTD panel on the server or contact server administration. For bot-related questions, contact the developer — Nandak070.',
}

export default legal
