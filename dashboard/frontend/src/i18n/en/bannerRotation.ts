import type { TranslationDict } from '../types'

const bannerRotation: TranslationDict = {
  'bannerRotation.title': 'Banner & Icon Rotation',
  'bannerRotation.intro':
    'Automatically rotate the server banner and server icon on a schedule. Requires Manage Server permission and, for banners, a boost level that unlocks the banner feature.',
  'bannerRotation.moduleOn': 'Module on',
  'bannerRotation.moduleOff': 'Module off',

  'bannerRotation.section.settings': 'Settings',
  'bannerRotation.section.banners': 'Banner images',
  'bannerRotation.section.icons': 'Icon images',

  'bannerRotation.bannerEnabled': 'Rotate server banner',
  'bannerRotation.iconEnabled': 'Rotate server icon',
  'bannerRotation.interval': 'Rotation interval (minutes)',
  'bannerRotation.intervalHint': 'Min 15, max 2880 (48 h). Both banners and icons share this interval.',
  'bannerRotation.logChannel': 'Log channel (optional)',
  'bannerRotation.logChannelNone': 'No log channel',

  'bannerRotation.upload': 'Upload images',
  'bannerRotation.uploadHint': 'PNG, JPEG, GIF or WEBP, max 8 MB each.',
  'bannerRotation.uploading': 'Uploading…',
  'bannerRotation.noImages': 'No images yet — upload some to start rotating.',
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
  'bannerRotation.errorRotate': 'Failed to trigger rotation',
}

export default bannerRotation
