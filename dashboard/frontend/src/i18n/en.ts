import auth from './en/auth'
import common from './en/common'
import shell from './en/shell'
import admin from './en/admin'
import community from './en/community'
import type { TranslationDict } from './types'
import activity from './en/activity'
import docsShell from './en/docsShell'
import legal from './en/legal'
import landing from './en/landing'
import whatsNew from './en/whatsNew'
import credits from './en/credits'
import sans from './en/sans'

const en: TranslationDict = {
  ...shell,
  ...common,
  ...auth,
  ...admin,
  ...activity,
  ...community,
  ...docsShell,
  ...legal,
  ...landing,
  ...whatsNew,
  ...credits,
  ...sans,
}

export default en
