import type { TranslationDict } from '../types'

/** Privacy policy and terms of service (public pages). */
const legal: TranslationDict = {
  'privacy.title': 'Privacy Policy',
  'privacy.lastUpdated': 'Last updated: September 6, 2026',

  'privacy.s1.title': '1. General provisions',
  'privacy.s1.p1':
    '1.1. This policy explains what data the Cheterin Discord bot and its web control panel (the "Service") process, why they are used, where they are stored, and how to delete them.',
  'privacy.s1.p2':
    '1.2. Cheterin is one hosted bot that can run on many Discord servers at once. Each server\'s data is kept separate by server ID: one server\'s settings and activity are not visible to others. The team that hosts the bot manages the infrastructure; each server\'s admins manage that server\'s settings and data in the dashboard. We do not sell or share data with third parties.',
  'privacy.s1.p3':
    '1.3. We store only what is needed for the features you use.',

  'privacy.s2.title': '2. What data is processed',
  'privacy.s2.p1': '2.1. When you sign in to the dashboard through Discord:',
  'privacy.s2.li1': 'your Discord account ID;',
  'privacy.s2.li2': 'username and avatar;',
  'privacy.s2.li3':
    'the list of servers you belong to, with your permission flags — so we can show which servers you can manage;',
  'privacy.s2.li4.prefix': 'on the selected server, your',
  'privacy.s2.li4.bold': 'Manage Server',
  'privacy.s2.li4.suffix': 'or Administrator permission is checked — that is what grants access to that server\'s settings.',
  'privacy.s2.p2':
    'Sign-in tokens from Discord are kept only for your current dashboard session (to refresh your server list) and are removed when you sign out.',
  'privacy.s2.p3.bold':
    'Passwords, email, phone numbers, and payment details are never requested and are not available to the Service.',
  'privacy.s2.p4': '2.2. When bot modules are enabled:',
  'privacy.table.colModule': 'Feature',
  'privacy.table.colData': 'What data',
  'privacy.table.colRetention': 'How long',
  'privacy.table.tickets.module': 'Tickets and feedback',
  'privacy.table.tickets.data': 'Author ID, category, request text, status, who reviewed it and when',
  'privacy.table.tickets.retention': 'Until deleted by admins',
  'privacy.table.invites.module': 'Invite statistics',
  'privacy.table.invites.data': 'Inviter and invitee IDs; join, leave, and invite counts',
  'privacy.table.invites.retention': 'Until deleted by admins',
  'privacy.table.supply.module': 'Supply runs',
  'privacy.table.supply.data': 'Organizer and participant IDs, objective, time, run status; visit counter',
  'privacy.table.supply.retention': 'Limited history (older records are removed automatically)',
  'privacy.table.voiceRooms.module': 'Private voice rooms',
  'privacy.table.voiceRooms.data': 'Owner ID, room name, user limit, who may or may not join',
  'privacy.table.voiceRooms.retention': 'Removed when the room is deleted',
  'privacy.table.modlog.module': 'Server logging',
  'privacy.table.modlog.data': 'Action type (ban, kick, spam, spam trap, and similar), offender and moderator IDs, reason, time',
  'privacy.table.modlog.retention': 'Until deleted by admins',
  'privacy.table.verification.module': 'Verification',
  'privacy.table.verification.data':
    'Role and channel settings chosen by admins; member ID and time of rule acceptance (for re-verification)',
  'privacy.table.verification.retention': 'Settings — until changed; consent records — until deleted by admins',
  'privacy.table.rating.module': 'Levels and ranking',
  'privacy.table.rating.data': 'Member ID, XP, level, message count, total voice time',
  'privacy.table.rating.retention': 'Until reset or deletion on request',
  'privacy.table.voiceSessions.module': 'Voice sessions',
  'privacy.table.voiceSessions.data': 'Member ID, channel, join/leave time, active seconds — for stats and voice XP',
  'privacy.table.voiceSessions.retention': 'Detailed sessions — limited period, then totals only',
  'privacy.table.audit.module': 'Dashboard audit',
  'privacy.table.audit.data': 'Moderator ID and name, panel action type, time — successful changes only',
  'privacy.table.audit.retention': 'Until deleted by admins',
  'privacy.table.streams.module': 'Stream alerts',
  'privacy.table.streams.data':
    'Streamer logins/IDs and YouTube channel IDs, notification settings; member personal data is not involved',
  'privacy.table.streams.retention': 'Until the subscription is removed',
  'privacy.table.events.module': 'Events and brackets',
  'privacy.table.events.data': 'Event participant IDs, nicknames or team names in brackets',
  'privacy.table.events.retention': 'Until the event or bracket is deleted',
  'privacy.table.reactionRoles.module': 'Reaction roles, buttons, embeds',
  'privacy.table.reactionRoles.data': 'Message, channel, and role IDs; form and button text',
  'privacy.table.reactionRoles.retention': 'Until the binding is removed',
  'privacy.table.economy.module': 'Economy and casino',
  'privacy.table.economy.data':
    'Member ID, balance, shop purchases, transfer and bet history, casino results; optional weekly report channel ID',
  'privacy.table.economy.retention': 'Until deleted by admins or balance reset',
  'privacy.table.wordle.module': 'Wordle and fun games',
  'privacy.table.wordle.data': 'Member ID, daily Wordle progress and streaks; game cooldowns (per server)',
  'privacy.table.wordle.retention': 'Until deleted by admins',
  'privacy.table.polls.module': 'Polls',
  'privacy.table.polls.data': 'Question text, options, voter IDs and choices, end time, status',
  'privacy.table.polls.retention': 'Until deleted by admins',
  'privacy.table.sticky.module': 'Sticky messages',
  'privacy.table.sticky.data': 'Channel ID, sticky text, last posted message ID',
  'privacy.table.sticky.retention': 'Until the sticky is removed',
  'privacy.table.customCommands.module': 'Custom commands',
  'privacy.table.customCommands.data': 'Trigger text, match mode, reply text set by admins',
  'privacy.table.customCommands.retention': 'Until the command is deleted',
  'privacy.table.scheduledMessages.module': 'Scheduled messages',
  'privacy.table.scheduledMessages.data': 'Channel ID, message content, schedule, last and next run time',
  'privacy.table.scheduledMessages.retention': 'Until the schedule is deleted',
  'privacy.table.timedRoles.module': 'Timed roles',
  'privacy.table.timedRoles.data': 'Member ID, role ID, grant and expiry time',
  'privacy.table.timedRoles.retention': 'Removed when the role expires or is cancelled',
  'privacy.table.birthdays.module': 'Server birthdays',
  'privacy.table.birthdays.data': 'Member ID and birthday date (day/month; year optional)',
  'privacy.table.birthdays.retention': 'Until deleted by the member or admins',
  'privacy.table.ownerAlerts.module': 'Owner alerts',
  'privacy.table.ownerAlerts.data':
    'Alert thresholds and channel ID; weekly settings digest summaries; no member message content — only operational signals (missing permissions, mass bans, module errors)',
  'privacy.table.ownerAlerts.retention': 'Settings — until changed',
  'privacy.table.starboard.module': 'Starboard',
  'privacy.table.starboard.data': 'Starred message IDs, reaction counts, starboard channel post IDs',
  'privacy.table.starboard.retention': 'Until removed from starboard or deleted by admins',
  'privacy.table.relations.module': 'Relations',
  'privacy.table.relations.data': 'Member pair IDs, relationship HP/level, marriages/proposals, action cooldowns',
  'privacy.table.relations.retention': 'Until cleared by admins / guild removed',
  'privacy.table.autoReactions.module': 'Auto-reactions',
  'privacy.table.autoReactions.data': 'Emoji and channel scope settings only — no message content stored',
  'privacy.table.autoReactions.retention': 'Settings — until changed',
  'privacy.table.quote.module': 'Make it a Quote',
  'privacy.table.quote.data':
    'Trigger settings only; quote images are generated on demand and posted to Discord (not archived by the Service)',
  'privacy.table.quote.retention': 'Settings — until changed',
  'privacy.table.botProfile.module': 'Bot profile',
  'privacy.table.botProfile.data': 'Per-guild nick and asset URLs for avatar/banner',
  'privacy.table.botProfile.retention': 'Until changed or cleared by admins',
  'privacy.table.stickyRoles.module': 'Sticky roles',
  'privacy.table.stickyRoles.data': 'Member ID and role IDs remembered on leave for restore on rejoin',
  'privacy.table.stickyRoles.retention': 'Until restored, expired, or deleted by admins',
  'privacy.table.games.module': 'Mafia and Bunker',
  'privacy.table.games.data':
    'Active game state, participant IDs, roles for the current match; short-lived tokens for personal action links',
  'privacy.table.games.retention': 'Cleared when the game ends (or after a short cleanup window)',
  'privacy.table.valchecker.module': 'ValChecker (Valorant)',
  'privacy.table.valchecker.data':
    'Discord user ID linked to Riot ID (name#tag), region, PUUID, optional match-tracking flag and last match cursor; optional match cache (stats). Channel IDs for match posts and status alerts. Data is fetched from HenrikDev / valorant-api when you use the commands.',
  'privacy.table.valchecker.retention':
    'Link and track settings — until you unlink or admins delete; match cache — until cleared; module settings — until changed',
  'privacy.table.customs.module': 'Customs (Valorant lobbies)',
  'privacy.table.customs.data':
    'Per-server lobby settings; participant Discord IDs, ranks, team codes, map bans, scores, win/loss stats; optional schedule and channel/role IDs; temporary voice channel IDs while a match is active',
  'privacy.table.customs.retention':
    'Active lobby data until the lobby finishes or is cancelled; stats and settings until cleared by admins',
  'privacy.table.bannerRotation.module': 'Banner and icon rotation',
  'privacy.table.bannerRotation.data':
    'Uploaded banner and server-icon image files (per server), banner mode (playlist or dynamic), rotation interval, optional log channel ID, last-rotation timestamps; dynamic banners use already-collected voice stats and are not stored as separate files',
  'privacy.table.bannerRotation.retention':
    'Images and settings until deleted or changed by admins; files are stored only for the selected server',
  'privacy.table.news.module': 'News relay (main server feature)',
  'privacy.table.news.data': 'Source server, bot, and channel IDs; forwarded message content is not stored',
  'privacy.table.news.retention': 'Settings — until changed',
  'privacy.table.config.module': 'Server settings',
  'privacy.table.config.data': 'Channel and role IDs chosen by admins for modules (per server)',
  'privacy.table.config.retention': 'Until settings are changed',
  'privacy.s2.p5.label': 'Message content.',
  'privacy.s2.p5.rest':
    'The bot does not archive chat history. Message text is handled only when a feature you enabled needs it: anti-spam keeps a short temporary cache; sticky, scheduled, and custom-command tools store only the texts admins configured; news relay forwards messages without storing them; server logging can post deleted or edited message text to a Discord log channel if that event is turned on. Levels store that a message was sent for XP — not the message text.',

  'privacy.s3.title': '3. What the Service does not do',
  'privacy.s3.li1': 'Does not sell or share data with third parties.',
  'privacy.s3.li2': 'Does not use data for advertising, behavioral analytics, or profiling.',
  'privacy.s3.li3': 'Does not read users\' direct messages (DMs), except to send its own notifications.',
  'privacy.s3.li4':
    'Does not collect data from servers where it is not installed. On each installed server, data stays isolated. Exception — news relay (main server feature): public messages from bots on the source server are read but not stored.',
  'privacy.s3.li5': 'Does not install third-party trackers, pixels, or analytics cookies on the website.',

  'privacy.s4.title': '4. Why we process data',
  'privacy.s4.li1':
    'To run features you use: tickets, supply runs, rooms, roles, verification, events, economy, polls, sticky and scheduled messages, custom commands, timed roles, birthdays, Customs lobbies, banner/icon rotation, and games.',
  'privacy.s4.li2': 'To check who may use the dashboard.',
  'privacy.s4.li3': 'For moderation and safety (anti-spam, server logging, owner alerts).',
  'privacy.s4.li4': 'To show statistics (invites, supply attendance, economy tops) to admins and moderators.',

  'privacy.s5.title': '5. Where and how data is stored',
  'privacy.s5.p1':
    '5.1. Data is stored on the machine that hosts the bot (local database files, separated by server). We do not use external cloud databases for this. Servers do not see each other\'s data.',
  'privacy.s5.p2':
    '5.2. Only the team that operates the bot hosting can access the data files. Dashboard access to a server is limited to members with Manage Server or Administrator on that server, and is checked on every request.',
  'privacy.s5.p3':
    '5.3. Dashboard sessions are encrypted. Sign-in is handled by Discord — we never ask for your Discord password.',

  'privacy.s6.title': '6. Cookies',
  'privacy.s6.p1':
    'The site uses one encrypted session cookie — only to keep you signed in to the dashboard. It is not used for tracking. Public pages (docs, terms, this policy) work without cookies.',

  'privacy.s7.title': '7. Data sharing',
  'privacy.s7.p1.prefix':
    '7.1. We do not share data with third parties. The only external platform the Service needs is Discord. Discord\'s own processing is covered by the',
  'privacy.s7.discordPrivacyLink': 'Discord Privacy Policy',
  'privacy.s7.p2':
    '7.2. If admins set a webhook for form buttons, form replies go to the webhook URL they chose (usually a channel on the same Discord server).',
  'privacy.s7.p3':
    '7.3. For stream alerts, the Service calls public Twitch APIs and YouTube RSS feeds. Only streamer logins/IDs chosen by admins are sent; server member data is not shared with those services.',
  'privacy.s7.p4':
    '7.4. For ValChecker, the Service calls HenrikDev and valorant-api.com to fetch Valorant profiles, matches, and status. When you use those commands, your linked Riot ID (name#tag), region, and related identifiers are sent to those APIs. Unlink with /val setup to stop tracking.',

  'privacy.s8.title': '8. Retention and deletion',
  'privacy.s8.p1': '8.1. Automatic deletion:',
  'privacy.s8.li1': 'private room records — when the channel is deleted;',
  'privacy.s8.li2': 'supply run history — older completed runs when the storage limit is reached;',
  'privacy.s8.li3': 'anti-spam cache — every few minutes;',
  'privacy.s8.li4': 'detailed voice sessions — after a limited period (totals remain);',
  'privacy.s8.li5': 'role bindings to deleted messages — when the bot starts;',
  'privacy.s8.li6': 'dashboard session — when you sign out;',
  'privacy.s8.li7': 'timed roles — when they expire or are cancelled;',
  'privacy.s8.li8': 'finished Mafia/Bunker games — after the match ends (or a short cleanup window).',
  'privacy.s8.li9': 'ValChecker Riot link — when you unlink in /val setup or admins clear data.',
  'privacy.s8.p2.label': 'Deletion on request.',
  'privacy.s8.p2.rest':
    'You can ask to delete data linked to your account (invite stats, applications, participation history, ranking and XP, economy balance, birthday entry, ValChecker Riot link). Contact your server\'s admins (or open a ticket on the main server) — admins can reset a member\'s ranking or balance in the dashboard. A server owner may request full deletion of that server\'s data when removing the bot.',

  'privacy.s9.title': '9. Your rights',
  'privacy.s9.li1': 'ask what data the Service stores about you (via server admins or a ticket);',
  'privacy.s9.li2': 'ask to correct inaccurate data;',
  'privacy.s9.li3':
    'ask to delete your data (except server logging entries kept for server safety);',
  'privacy.s9.li4': 'stop using the Service at any time.',

  'privacy.s10.title': '10. Age restrictions',
  'privacy.s10.p1':
    'The Service is for users who meet Discord\'s minimum age in their country (typically 13 or older). We do not knowingly collect data from children below that age.',

  'privacy.s11.title': '11. Policy changes',
  'privacy.s11.p1':
    'The current policy is always on this page; the last update date is at the top. Material changes are announced in the server announcements channel.',

  'privacy.s12.title': '12. Contact',
  'privacy.s12.p1':
    'Questions about data: contact your server\'s admins (or open a ticket on the main server). The Service is operated by Cheterin Group Ø. For bot and hosting questions — Nandak070.',

  'terms.title': 'Terms of Use',
  'terms.lastUpdated': 'Last updated: September 6, 2026',

  'terms.s1.title': '1. Terms and definitions',
  'terms.s1.li1.prefix': '"Service"',
  'terms.s1.li1.rest':
    '— the Cheterin Discord bot, web control panel (dashboard), public website, and related features.',
  'terms.s1.li2.prefix': '"Bot"',
  'terms.s1.li2.rest': '— the Cheterin Discord application added to a server.',
  'terms.s1.li3.prefix': '"Dashboard"',
  'terms.s1.li3.rest':
    '— the web interface for managing bot settings, available after signing in with Discord.',
  'terms.s1.li4.prefix': '"Server"',
  'terms.s1.li4.rest':
    '— a Discord community where the bot runs. One Cheterin instance can serve many servers; each server\'s data and settings stay separate.',
  'terms.s1.li5.prefix': '"Main server"',
  'terms.s1.li5.rest':
    '— the operator\'s server with extra tools (ticket panel, news relay, Super Admin section).',
  'terms.s1.li6.prefix': '"User"',
  'terms.s1.li6.rest':
    '— any server member who uses the bot: commands, buttons, forms, voice channels, or the dashboard.',
  'terms.s1.li7.prefix': '"Administration"',
  'terms.s1.li7.rest': '— the server owner and people they authorize to manage the Service on that server.',
  'terms.s1.li8.prefix': '"Private room"',
  'terms.s1.li8.rest':
    '— a voice channel the bot creates when someone joins a lobby channel.',

  'terms.s2.title': '2. Acceptance of terms',
  'terms.s2.p1':
    '2.1. By using the Service — being on a server where the bot runs, using its commands or buttons, creating private rooms, joining supply runs, or signing in to the dashboard — you accept these terms.',
  'terms.s2.p2':
    '2.2. If you do not agree, stop using the Service. For server owners, that means removing the bot from the server.',
  'terms.s2.p3.prefix': '2.3. You may use the Service only while following Discord\'s',
  'terms.s2.discordTerms': 'Terms of Service',
  'terms.s2.p3.and': 'and',
  'terms.s2.discordGuidelines': 'Community Guidelines',
  'terms.s2.p3.suffix': ', including Discord\'s minimum age for your country.',

  'terms.s3.title': '3. What the Service provides',
  'terms.s3.p1': '3.1. The Service helps automate Discord servers. Features may include:',
  'terms.s3.li1':
    'moderation: anti-spam, AutoMod filters, spam traps (softban/ban), lockdown, verification, unified action log, case timeline;',
  'terms.s3.li2':
    'levels and ranking: XP for text and voice, reward roles (optional remove previous level roles on level-up), rank/profile cards, cosmetics, leaderboards;',
  'terms.s3.li3': 'server logging and voice activity statistics;',
  'terms.s3.li4': 'tickets and feedback with categories and resolutions;',
  'terms.s3.li5':
    'welcome messages, invite statistics, auto-roles, sticky roles, reaction roles, starboard, and auto-reactions;',
  'terms.s3.li6': 'embed builder / Embed Studio, templates, and interactive form buttons;',
  'terms.s3.li7':
    'events, polls, giveaways, and tournament brackets with public links;',
  'terms.s3.li8': 'supply runs with a waitlist and reminders;',
  'terms.s3.li9': 'private voice rooms with a control panel;',
  'terms.s3.li10': 'Twitch and YouTube alerts;',
  'terms.s3.li11': 'news relay from a source server (main server feature);',
  'terms.s3.li12':
    'economy and casino: server currency, shop, transfers, games, optional weekly report;',
  'terms.s3.li13':
    'fun commands: Russian roulette, Wordle, Auto-Emoji, Make it a Quote, and similar;',
  'terms.s3.li14': 'custom commands, scheduled and sticky messages;',
  'terms.s3.li15':
    'timed roles, birthday calendar, per-guild bot profile, and owner alerts (including weekly settings digest);',
  'terms.s3.li16': 'Mafia and Bunker games with personal web action links and host controls;',
  'terms.s3.li16b':
    'ValChecker: Valorant account link, profiles, match history/tracking, compare, server leaderboard, and status alerts (uses HenrikDev / valorant-api);',
  'terms.s3.li16b2':
    'Customs: Valorant custom lobbies with solo/team-code join, rank roles, map pool/votes, team balance, voice move, scores, rematch, bans, and schedules;',
  'terms.s3.li16b3':
    'banner and server-icon rotation: scheduled per-server image rotation with dashboard uploads and optional log channel;',
  'terms.s3.li16c': 'member /help command with short paginated feature overview;',
  'terms.s3.li17':
    'a web dashboard to manage the above, with server selection, RU/EN UI and bot language, Ctrl+K navigation, and an audit of panel actions.',
  'terms.s3.p2':
    '3.2. You can invite the bot to your server, then pick that server in the dashboard and configure modules independently of other servers. Modules start disabled on a new server.',
  'terms.s3.p3':
    '3.3. Some tools (tickets on the main server, news relay, Super Admin) are available only on the main server.',
  'terms.s3.p4':
    '3.4. Features may change: modules can be added, updated, or removed without prior notice.',

  'terms.s4.title': '4. Rules of use',
  'terms.s4.p1': '4.1. You must not:',
  'terms.s4.li1':
    'use the Service for spam, raids, harassment, fraud, or other harmful activity;',
  'terms.s4.li2':
    'try to access the dashboard, other users\' data, or other servers without permission;',
  'terms.s4.li3':
    'disrupt the Service: overload it, exploit bugs, or bypass limits (cooldowns, caps, permission checks);',
  'terms.s4.li4':
    'farm XP or ranking unfairly (bots, fake voice activity, and similar) — admins may reset inflated ranking and remove reward roles;',
  'terms.s4.li5':
    'pretend to be Service staff or misuse the Cheterin name and branding;',
  'terms.s4.li6':
    'post illegal or Discord-prohibited content through bot features (room names, supply text, forms, tickets, and similar).',
  'terms.s4.p2':
    '4.2. Administration may limit or block access for users who break these rules, without prior notice.',

  'terms.s5.title': '5. Private voice rooms',
  'terms.s5.sub1.title': '5.1. Naming',
  'terms.s5.sub1.p1':
    'Room names must not include third-party ads, insults, harmful links, or content that breaks Discord rules. Names may be reset and rooms deleted without warning.',
  'terms.s5.sub2.title': '5.2. Visibility',
  'terms.s5.sub2.p1':
    'Room owners may manage who can join (invite, kick, deny). Hiding the channel from @everyone is not allowed — the bot will restore visibility.',
  'terms.s5.sub3.title': '5.3. Lifecycle',
  'terms.s5.sub3.p1':
    'Empty private rooms are deleted automatically. A room exists only while at least one person is in it.',
  'terms.s5.sub4.title': '5.4. Owner responsibility',
  'terms.s5.sub4.p1':
    'The room creator is responsible for moderating activity inside their room.',

  'terms.s6.title': '6. Dashboard and access',
  'terms.s6.p1':
    '6.1. Dashboard sign-in is only through official Discord authorization. The Service never asks for passwords, two-factor codes, or payment details.',
  'terms.s6.p2.prefix':
    '6.2. After sign-in, you choose a server you can manage. Access requires',
  'terms.s6.p2.bold': 'Manage Server',
  'terms.s6.p2.suffix':
    'or Administrator on that server. Permissions are checked on every request — losing them ends access.',
  'terms.s6.p3':
    '6.3. The server owner is responsible for who receives management permissions and for actions those people take in the panel (bans, kicks, setting changes, bulk role grants).',
  'terms.s6.p4':
    '6.4. Changes made in the dashboard are recorded in an audit log (who changed what and when). Using the panel means you accept that logging.',
  'terms.s6.p5':
    '6.5. Public pages (documentation, terms, privacy policy, public brackets, public leaderboard) work without signing in.',

  'terms.s7.title': '7. User content',
  'terms.s7.p1':
    '7.1. Room names, supply text, feedback, form replies, ticket messages, and similar content are created by users. Authors are responsible for that content.',
  'terms.s7.p2':
    '7.2. Administration does not pre-approve user content, but may remove content that breaks Discord rules or these terms and take action against its authors.',
  'terms.s7.p3':
    '7.3. By submitting content through the Service, you allow it to be processed, stored, and shown as needed for those features (for example, showing your request to moderators in the dashboard).',

  'terms.s8.title': '8. Availability',
  'terms.s8.p1':
    '8.1. The Service is free and provided "as is", without warranties of uninterrupted or error-free operation, or fitness for a particular purpose.',
  'terms.s8.p2':
    '8.2. The Service depends on Discord. Outages, limits, or changes on Discord\'s side may affect the Service; we are not responsible for those disruptions.',
  'terms.s8.p3':
    '8.3. We try to keep things resilient: active supply runs, private rooms, tickets, and module settings are restored after a bot restart. We do not guarantee data survival after hardware failures — do not rely on the Service as the only copy of important information.',
  'terms.s8.p4':
    '8.4. Maintenance may happen without prior notice and may temporarily make the bot or dashboard unavailable.',

  'terms.s9.title': '9. Limitation of liability',
  'terms.s9.p1':
    '9.1. To the fullest extent allowed by law, Cheterin Group Ø, its operators, and server administration are not liable for direct or indirect damages, data loss, lost profits, or other harm from using or being unable to use the Service.',
  'terms.s9.p2':
    '9.2. The Service is not affiliated with Discord Inc. and is not its product or partner. Discord is a trademark of Discord Inc.',

  'terms.s10.title': '10. Ending access',
  'terms.s10.p1':
    '10.1. You may stop using the Service at any time. A server owner may remove the bot — server settings and data may be deleted on request (see the Privacy Policy).',
  'terms.s10.p2':
    '10.2. Administration may suspend or end the Service fully or partly, including for individual users or servers, when these terms are broken.',

  'terms.s11.title': '11. Changes to terms',
  'terms.s11.p1':
    '11.1. These terms may be updated. The current version is always on this page; the last update date is at the top.',
  'terms.s11.p2':
    '11.2. Material changes are announced in the server announcements channel. Continued use after publication means you accept the new version.',

  'terms.s12.title': '12. Contact',
  'terms.s12.p1':
    'For Service questions, open a ticket on the main server or contact your server\'s admins. The Service is operated by Cheterin Group Ø. For bot questions — Nandak070.',

  'terms.s13.title': '13. Cheterin Lookup',
  'terms.s13.p1':
    '13.1. Cheterin Lookup (`/lookup`) is part of the same Service ecosystem: a public tool that shows open Discord data returned by the official API for IDs and invite codes you enter.',
  'terms.s13.p2':
    '13.2. Lookup uses a separate Discord Application and token from the Cheterin bot. It does not require dashboard OAuth login. Abuse of Lookup may lead to rate limits, CAPTCHA, or blocking without affecting your right to remove the bot from a server.',
  'terms.s13.p3':
    '13.3. Do not use Lookup for harassment, doxxing, stalking, or bulk scraping of IDs. Lookup is not an OSINT agency and does not promise complete profiles, private guild data, Group DM lookup, or a public feed of other users’ searches.',

  'privacy.s13.title': '13. Cheterin Lookup',
  'privacy.s13.p1':
    '13.1. Lookup does not use Discord OAuth login. You may enter Discord snowflake IDs or invite codes; we query the official Discord API through a dedicated Lookup application.',
  'privacy.s13.p2':
    '13.2. Successful Lookup responses may be cached briefly (about 15 minutes for user/bot, about 10 minutes for invites) to reduce load on Discord. There is no public recent-searches feed.',
  'privacy.s13.p3':
    '13.3. Anti-abuse logs store hashed IP and hashed queried id for up to 48 hours for operators only — not shown in the UI.',
  'privacy.s13.p4':
    '13.4. After repeated requests (about 30 per minute per IP), Lookup may require CAPTCHA. Avatar/banner downloads primarily use Discord CDN; a same-origin proxy may be used as a download fallback and does not permanently host files.',
  'privacy.s13.p5':
    '13.5. Language preference uses the shared `chetbot_ui_lang` key (see Cookies).',

  'cookies.title': 'Cookie notice',
  'cookies.lastUpdated': 'Last updated: September 6, 2026',
  'cookies.s1.title': '1. What this notice covers',
  'cookies.s1.p1':
    '1.1. This page describes cookies and similar browser storage used by the Cheterin web control panel and Cheterin Lookup on cheterin.online. It does not describe cookies set by Discord.com, Discord’s CDN, or third-party sites you open from outbound links.',
  'cookies.s2.title': '2. What we store',
  'cookies.s2.p1': '2.1. We keep storage minimal and operational:',
  'cookies.s2.li1':
    'Session cookie for the control panel — set after Discord OAuth so you remain signed in while using guild settings. It is cleared when you sign out or when the session expires. Lookup itself does not require this cookie.',
  'cookies.s2.li2':
    '`chetbot_ui_lang` — stores your interface language preference (Russian or English). It is shared across About, docs, legal pages, the panel chrome, and Lookup so the RU/EN toggle stays consistent.',
  'cookies.s2.li3':
    'CAPTCHA provider cookies (Turnstile or hCaptcha) — only when the operator has enabled anti-abuse CAPTCHA and Lookup asks you to complete a challenge after repeated requests. Those cookies belong to the CAPTCHA vendor’s challenge flow, not to advertising.',
  'cookies.s2.p2':
    '2.2. We do not place advertising cookies, marketing pixels, social tracking pixels, or third-party analytics trackers on the panel or Lookup. We do not sell browsing data.',
  'cookies.s2.p3':
    '2.3. Lookup queries may transit Discord’s public API and Discord CDN for avatars/banners. Those requests are subject to Discord’s own privacy practices; we do not permanently host avatar/banner files on cheterin.online beyond short-lived proxy responses when used as a download fallback.',
  'cookies.s3.title': '3. Retention and purpose',
  'cookies.s3.p1':
    '3.1. The panel session cookie exists only to keep an authenticated dashboard session. Language preference remains until you change it or clear site data. CAPTCHA cookies last as long as the provider needs to validate the challenge (typically short-lived).',
  'cookies.s3.p2':
    '3.2. We do not keep a long-term “recent searches” cookie for Lookup. Rate-limit state, when used, is operational and short-lived on the Lookup API side — not a marketing profile.',
  'cookies.s4.title': '4. Your controls',
  'cookies.s4.p1':
    '4.1. You can clear cookies and site data in your browser, or sign out of the panel. Blocking the session cookie prevents staying signed in to the dashboard. Language can be changed anytime with the RU/EN control. If CAPTCHA is required and you block its cookies, Lookup may refuse further requests until the challenge can complete.',

  'disclaimer.title': 'Disclaimer',
  'disclaimer.lastUpdated': 'Last updated: September 6, 2026',
  'disclaimer.s1.title': '1. Not affiliated with Discord',
  'disclaimer.s1.p1':
    '1.1. Cheterin (bot, control panel, and Lookup) is an independent project operated by Cheterin Group Ø / Nandak070. It is not affiliated with, endorsed by, sponsored by, or partnered with Discord Inc. “Discord” is a trademark of Discord Inc.',
  'disclaimer.s2.title': '2. Public Discord API limits',
  'disclaimer.s2.p1':
    '2.1. Bot features, panel views, and Lookup results depend on what Discord’s official API returns to our applications. Data can be incomplete, delayed, rate-limited, redacted, or unavailable. Empty fields usually mean Discord did not return that field — not that we “hid” it.',
  'disclaimer.s2.p2':
    '2.2. Do not treat panel, bot, or Lookup output as a complete official audit of Discord activity, membership, or moderation history. Lookup shows public user/application fields and public invite snapshots only. Server lookup requires an invite code; bare Guild ID lookup is not supported.',
  'disclaimer.s2.p3':
    '2.3. Lookup honesty: we do not invent “full profiles”, private guild data, Group DM contents, or fake DSA violation statuses. If a live DSA upstream source is unavailable, the DSA page remains an honest skeleton with official outbound links only.',
  'disclaimer.s3.title': '3. No doxxing or harassment',
  'disclaimer.s3.p1':
    '3.1. Do not use the Service — including Lookup — to harass, stalk, dox, or otherwise harm people. Public IDs and invite codes do not grant permission to misuse data. Server administrators remain responsible for how they configure moderation, logging, and access on their own servers.',
  'disclaimer.s4.title': '4. Responsibility',
  'disclaimer.s4.p1':
    '4.1. Use of the Service is at your own risk and is subject to the Terms of Use and Privacy Policy. Discord API outages, token revocation, or network limits may interrupt Lookup without prior notice.',
}
export default legal
