MESSAGES: dict[str, str] = {
    "relations.disabled": "Модуль «Отношения» выключен на этом сервере.",
    "relations.self": "Нельзя выбрать себя — укажите другого участника.",
    "relations.bot_target": "На ботов действия не действуют.",
    "relations.action_disabled": "Это действие выключено админами.",
    "relations.daily_limit": "Дневной лимит действий исчерпан ({limit}). Завтра снова можно.",
    "relations.cooldown": "Подождите ещё {seconds} сек. перед этим действием с этим участником.",
    "relations.action.hug": "обнял(а)",
    "relations.action.kiss": "поцеловал(а)",
    "relations.action.slap": "шлёпнул(а)",
    "relations.action.pat": "погладил(а)",
    "relations.action.highfive": "дал(а) пять",
    "relations.action.cuddle": "прижался(ась)",
    "relations.action.poke": "ткнул(а)",
    "relations.action_title": "{emoji} {action}",
    "relations.action_body": (
        "{actor} → {target}\n"
        "+{hp} HP отношений · всего **{total}** · уровень **{level}**\n"
        "{progress}"
    ),
    "relations.married_bonus_note": "💍 Бонус супругов +{pct}% HP",
    "relations.progress": "Прогресс до следующего уровня: {into}/{need}",
    "relations.progress_max": "Максимальный уровень отношений!",
    "relations.card_need_other": "Укажите участника, с которым показать карточку.",
    "relations.card_empty": "С {user} ещё нет HP отношений — сделайте действие!",
    "relations.card_title": "Карточка отношений",
    "relations.card_body": (
        "{a} × {b}\n"
        "Уровень **{level}** · **{hp}** HP\n"
        "{progress}"
    ),
    "relations.card_married": "💍 В браке · **{days}** дн. вместе",
    "relations.top_empty": "Пока нет пар с HP — начните с `/отношения hug` или другого действия.",
    "relations.top_title": "Топ отношений сервера",
    "relations.top_line": "**#{n}** {a} × {b} — ур. {level} · {hp} HP",
    "relations.announce.title": "Новый уровень отношений!",
    "relations.announce.body": "{a} и {b} достигли уровня **{level}** ({hp} HP).",
    "relations.role.add_reason": "Награда за уровень отношений",
    "relations.role.remove_reason": "Снятие награды отношений",
    # Romance
    "relations.marriage.disabled": "Романтика (брак) выключена на этом сервере.",
    "relations.marriage.already": "Вы уже в браке с {user}.",
    "relations.marriage.you_taken": "Вы уже в браке. Сначала /развод.",
    "relations.marriage.they_taken": "{user} уже в браке.",
    "relations.marriage.proposer_taken": "Предложивший уже в другом браке.",
    "relations.marriage.target_taken": "Вы уже в другом браке.",
    "relations.marriage.level_low": (
        "Для предложения нужен уровень отношений **{need}** (сейчас **{level}**). "
        "Копите HP действиями!"
    ),
    "relations.marriage.wed_title": "💍 Вы поженились!",
    "relations.marriage.wed_body": "{a} и {b} теперь супруги. Поздравляем!",
    "relations.marriage.announce_title": "Свадьба на сервере!",
    "relations.marriage.announce_body": "💍 {a} и {b} поженились!",
    "relations.marriage.role_add": "Роль супругов",
    "relations.marriage.role_remove": "Снятие роли супругов",
    "relations.propose.title": "Предложение руки и сердца",
    "relations.propose.body": (
        "{proposer} предлагает брак {target}!\n"
        "На ответ есть **{seconds}** сек."
    ),
    "relations.propose.btn_accept": "Согласиться",
    "relations.propose.btn_decline": "Отклонить",
    "relations.propose.only_target": "Ответить может только тот, кому сделали предложение.",
    "relations.propose.only_parties": "Только участники предложения могут нажать.",
    "relations.propose.declined_title": "Предложение отклонено",
    "relations.propose.declined_body": "{target} отклонил(а) предложение от {proposer}.",
    "relations.propose.expired": "Предложение истекло.",
    "relations.propose.already_out": "У вас уже есть активное предложение. Дождитесь ответа.",
    "relations.divorce.title": "Развод",
    "relations.divorce.mutual_body": (
        "{initiator} хочет развестись с {spouse}.\n"
        "Супруг(а) должен(на) подтвердить или остаться вместе."
    ),
    "relations.divorce.solo_body": "Подтвердите развод с {spouse}.",
    "relations.divorce.btn_accept": "Согласиться на развод",
    "relations.divorce.btn_stay": "Остаться вместе",
    "relations.divorce.btn_confirm": "Развестись",
    "relations.divorce.btn_cancel": "Отмена",
    "relations.divorce.only_spouse": "Подтвердить может только супруг(а).",
    "relations.divorce.only_initiator": "Подтвердить может только инициатор.",
    "relations.divorce.only_parties": "Только супруги могут нажать.",
    "relations.divorce.cancelled_title": "Развод отменён",
    "relations.divorce.cancelled_body": "Вы остаётесь вместе.",
    "relations.divorce.done_title": "Развод оформлен",
    "relations.divorce.done_body": "{a} и {b} больше не супруги.",
    "relations.divorce.announce_title": "Развод",
    "relations.divorce.announce_body": "{a} и {b} развелись.",
    "relations.divorce.not_married": "Этот брак уже не существует.",
    "relations.divorce.not_married_you": "Вы не в браке.",
    "relations.divorce.not_with": "Вы не в браке с {user}.",
    "relations.divorce.pick_spouse": "Укажите супруга: `/отношения divorce участник:…`",
    "relations.spouse.title": "💍 {user}",
    "relations.spouse.none_self": "Вы пока не в браке. Предложение: `/отношения marry`.",
    "relations.spouse.none_other": "{user} не в браке.",
    "relations.spouse.line": "♥ {spouse} · **{days}** дн. · ур. {level} · {hp} HP",
    "relations.marriages_top.empty": "Пока нет браков на сервере.",
    "relations.marriages_top.title": "Топ браков (дольше вместе)",
    "relations.marriages_top.line": (
        "**#{n}** {a} × {b} — **{days}** дн. · ур. {level} · {hp} HP"
    ),
    "relations.ship.title": "Ship meter",
    "relations.ship.body": "{a} × {b}\n{bar}\n**{score}%** — {tier}",
    "relations.ship.same": "Нужны два разных участника.",
    "relations.ship.tier.soulmates": "родственные души",
    "relations.ship.tier.hot": "горячо",
    "relations.ship.tier.spark": "есть искра",
    "relations.ship.tier.friendzone": "френдзона",
    "relations.ship.tier.awkward": "неловко…",
    "relations.date.need_spouse": "Свидание только с супругом(ой).",
    "relations.date.title": "🌹 Свидание",
    "relations.date.body": (
        "{a} и {b} провели свидание!\n"
        "+{hp} HP · всего **{total}** · уровень **{level}**\n"
        "{progress}"
    ),
}
