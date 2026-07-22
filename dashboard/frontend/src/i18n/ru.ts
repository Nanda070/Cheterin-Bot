import auth from './ru/auth'
import common from './ru/common'
import shell from './ru/shell'
import admin from './ru/admin'
import community from './ru/community'
import type { TranslationDict } from './types'
import activity from './ru/activity'
import docsShell from './ru/docsShell'
import legal from './ru/legal'

const ru: TranslationDict = {
  ...shell,
  ...common,
  ...auth,
  ...admin,
  ...activity,
  ...community,
  ...docsShell,
  ...legal,
}

export default ru
