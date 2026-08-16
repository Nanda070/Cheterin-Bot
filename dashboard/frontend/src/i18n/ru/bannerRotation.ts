import type { TranslationDict } from '../types'

const bannerRotation: TranslationDict = {
  'bannerRotation.title': 'Смена баннера и иконки',
  'bannerRotation.intro':
    'Автоматически меняет баннер и иконку сервера по расписанию. Для баннера — плейлист или динамический баннер. Нужно «Управление сервером». Ошибка Discord «internal_error» чаще значит неверная картинка, а не буст/права.',
  'bannerRotation.moduleOn': 'Модуль включён',
  'bannerRotation.moduleOff': 'Модуль выключен',

  'bannerRotation.section.settings': 'Настройки',
  'bannerRotation.section.banners': 'Баннеры (плейлист)',
  'bannerRotation.section.icons': 'Иконки',

  'bannerRotation.bannerEnabled': 'Менять баннер сервера',
  'bannerRotation.bannerMode': 'Режим баннера',
  'bannerRotation.bannerMode.playlist': 'Плейлист',
  'bannerRotation.bannerMode.dynamic': 'Динамический',
  'bannerRotation.bannerMode.both': 'Динамический баннер + плейлист иконок',
  'bannerRotation.bannerModeHint':
    'Динамический баннер генерируется по данным войс-трекера: самый активный (аватар и ник), число участников и сколько сейчас в войсе. Иконка по-прежнему из плейлиста.',
  'bannerRotation.iconEnabled': 'Менять иконку сервера',
  'bannerRotation.dynamicWindowDays': 'Окно активности (дни)',
  'bannerRotation.dynamicWindowDaysHint': 'Участник для динамического баннера выбирается только из голосовой активности этого сервера.',
  'bannerRotation.interval': 'Интервал смены (минуты)',
  'bannerRotation.intervalHint': 'От 15 до 2880 (48 ч). Баннеры и иконки используют один интервал.',
  'bannerRotation.logChannel': 'Канал для логов (необязательно)',
  'bannerRotation.logChannelNone': 'Без лог-канала',

  'bannerRotation.upload': 'Загрузить изображения',
  'bannerRotation.uploadHint': 'PNG, JPEG, GIF или WEBP, до 8 МБ каждый.',
  'bannerRotation.uploading': 'Загрузка…',
  'bannerRotation.noImages': 'Нет изображений — загрузите, чтобы начать смену.',
  'bannerRotation.playlistDisabledHint': 'Плейлист баннеров не используется, пока включён динамический режим.',
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
  'bannerRotation.errorRotate': 'Discord отклонил смену оформления.',
  'bannerRotation.errorBoost': 'Discord отклонил баннер — нужен уровень буста сервера для кастомного баннера.',
  'bannerRotation.errorInvalidImage': 'Discord отклонил картинку (часто 500/internal_error): используйте 960×540 JPEG/PNG без альфы.',
  'bannerRotation.errorRateLimited': 'Discord ограничил частоту смены — подождите и попробуйте снова.',
  'bannerRotation.errorEmpty': 'Нечего менять: включите режим баннера с контентом или загрузите иконки.',
}

export default bannerRotation
