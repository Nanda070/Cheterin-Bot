import type { TranslationDict } from '../types'

const bannerRotation: TranslationDict = {
  'bannerRotation.title': 'Banner & Icon Rotation',
  'bannerRotation.intro':
    'Automatically rotate the server banner and server icon on a schedule. For the banner, choose a static playlist or a dynamic banner (most active by voice, member count, and who’s in voice now). Requires Manage Server. Discord “internal_error” usually means a bad image payload, not missing boost/permissions.',
  'bannerRotation.moduleOn': 'Module on',
  'bannerRotation.moduleOff': 'Module off',

  'bannerRotation.section.settings': 'Settings',
  'bannerRotation.section.banners': 'Banner playlist',
  'bannerRotation.section.icons': 'Icon images',

  'bannerRotation.bannerEnabled': 'Rotate server banner',
  'bannerRotation.bannerMode': 'Banner mode',
  'bannerRotation.bannerMode.playlist': 'Playlist',
  'bannerRotation.bannerMode.dynamic': 'Dynamic',
  'bannerRotation.bannerModeHint':
    'Dynamic banners are generated from voice-tracker data: most active member (avatar + nickname), member count, and people currently in voice. Icons still use the playlist.',
  'bannerRotation.iconEnabled': 'Rotate server icon',
  'bannerRotation.interval': 'Rotation interval (minutes)',
  'bannerRotation.intervalHint': 'Min 15, max 2880 (48 h). Both banners and icons share this interval.',
  'bannerRotation.logChannel': 'Log channel (optional)',
  'bannerRotation.logChannelNone': 'No log channel',

  'bannerRotation.upload': 'Upload images',
  'bannerRotation.uploadHint': 'PNG, JPEG, GIF or WEBP, max 8 MB each.',
  'bannerRotation.uploading': 'Uploading…',
  'bannerRotation.noImages': 'No images yet — upload some to start rotating.',
  'bannerRotation.playlistDisabledHint': 'Banner playlist is unused while dynamic mode is on.',
  'bannerRotation.delete': 'Delete',

  'bannerRotation.lastRotated': 'Last rotated: {date}',
  'bannerRotation.nextRotation': 'Next rotation: {date}',
  'bannerRotation.neverRotated': 'Not rotated yet',

  'bannerRotation.rotateNow': 'Rotate now',
  'bannerRotation.rotating': 'Rotating…',
  'bannerRotation.rotatedOk': 'Rotation triggered',

  'bannerRotation.errorLoad': 'Failed to load rotation settings',
  'bannerRotation.errorSave': 'Failed to save settings',
  'bannerRotation.errorUpload': 'Failed to upload image',
  'bannerRotation.errorDelete': 'Failed to delete image',
  'bannerRotation.errorRotate': 'Discord rejected the rotation.',
  'bannerRotation.errorBoost': 'Discord rejected the banner — the server needs a boost level that allows a custom banner.',
  'bannerRotation.errorInvalidImage': 'Discord rejected the image (often 500/internal_error): use 960×540 JPEG/PNG without alpha.',
  'bannerRotation.errorRateLimited': 'Discord rate-limited banner/icon changes — wait and try again.',
  'bannerRotation.errorEmpty': 'Nothing to rotate: enable a banner mode with content, or upload icons.',
}

export default bannerRotation
