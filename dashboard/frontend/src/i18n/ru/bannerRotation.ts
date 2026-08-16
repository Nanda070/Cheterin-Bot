import type { TranslationDict } from '../types'

const bannerRotation: TranslationDict = {
  'bannerRotation.title': 'Смена баннера и иконки',
  'bannerRotation.intro':
    'Автоматически меняет баннер и иконку сервера по расписанию. Требуется право «Управление сервером», а для баннеров — уровень буста, открывающий функцию баннера.',
  'bannerRotation.moduleOn': 'Модуль включён',
  'bannerRotation.moduleOff': 'Модуль выключен',

  'bannerRotation.section.settings': 'Настройки',
  'bannerRotation.section.banners': 'Баннеры',
  'bannerRotation.section.icons': 'Иконки',

  'bannerRotation.bannerEnabled': 'Менять баннер сервера',
  'bannerRotation.iconEnabled': 'Менять иконку сервера',
  'bannerRotation.interval': 'Интервал смены (минуты)',
  'bannerRotation.intervalHint': 'От 15 до 2880 (48 ч). Баннеры и иконки используют один интервал.',
  'bannerRotation.logChannel': 'Канал для логов (необязательно)',
  'bannerRotation.logChannelNone': 'Без лог-канала',

  'bannerRotation.upload': 'Загрузить изображения',
  'bannerRotation.uploadHint': 'PNG, JPEG, GIF или WEBP, до 8 МБ каждый.',
  'bannerRotation.uploading': 'Загрузка…',
  'bannerRotation.noImages': 'Нет изображений — загрузите, чтобы начать смену.',
  'bannerRotation.delete': 'Удалить',

  'bannerRotation.lastRotated': 'Последняя смена: {date}',
  'bannerRotation.nextRotation': 'Следующая смена: {date}',
  'bannerRotation.neverRotated': 'Ещё не менялось',

  'bannerRotation.rotateNow': 'Сменить сейчас',
  'bannerRotation.rotating': 'Меняем…',
  'bannerRotation.rotatedOk': 'Смена запущена',

  'bannerRotation.errorLoad': 'Не удалось загрузить настройки смены',
  'bannerRotation.errorSave': 'Не удалось сохранить настройки',
  'bannerRotation.errorUpload': 'Не удалось загрузить изображение',
  'bannerRotation.errorDelete': 'Не удалось удалить изображение',
  'bannerRotation.errorRotate': 'Не удалось запустить смену',
}

export default bannerRotation
