import auth from './en/auth'
import common from './en/common'
import shell from './en/shell'
import admin from './en/admin'
import community from './en/community'
import type { TranslationDict } from './types'
import activity from './en/activity'
import customs from './en/customs'
import bannerRotation from './en/bannerRotation'
import docsShell from './en/docsShell'
import legal from './en/legal'
import landing from './en/landing'
import whatsNew from './en/whatsNew'
import credits from './en/credits'
import sans from './en/sans'
import egg from './en/egg'
import valorant from './en/valorant'

const en: TranslationDict = {
  ...shell,
  ...common,
  ...auth,
  ...admin,
  ...activity,
  ...customs,
  ...bannerRotation,
  ...community,
  ...docsShell,
  ...legal,
  ...landing,
  ...whatsNew,
  ...credits,
  ...sans,
  ...egg,
  ...valorant,
}

export default en
