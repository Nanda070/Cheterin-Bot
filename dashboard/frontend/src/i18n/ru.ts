import auth from './ru/auth'
import common from './ru/common'
import shell from './ru/shell'
import admin from './ru/admin'
import community from './ru/community'
import type { TranslationDict } from './types'
import activity from './ru/activity'
import customs from './ru/customs'
import bannerRotation from './ru/bannerRotation'
import docsShell from './ru/docsShell'
import legal from './ru/legal'
import landing from './ru/landing'
import whatsNew from './ru/whatsNew'
import credits from './ru/credits'
import sans from './ru/sans'
import egg from './ru/egg'

const ru: TranslationDict = {
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
}

export default ru
