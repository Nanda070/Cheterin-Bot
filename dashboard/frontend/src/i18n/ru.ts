import auth from './ru/auth'
import common from './ru/common'
import shell from './ru/shell'
import admin from './ru/admin'
import community from './ru/community'
import type { TranslationDict } from './types'
import activity from './ru/activity'
import docsShell from './ru/docsShell'
import legal from './ru/legal'
import landing from './ru/landing'
import whatsNew from './ru/whatsNew'
import credits from './ru/credits'

const ru: TranslationDict = {
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
}

export default ru
