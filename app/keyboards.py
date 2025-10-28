from random import choice

from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)

start = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='🎡 Главное меню'), KeyboardButton(text='📨 Рассылка')],
    [KeyboardButton(text='👨‍💻 Поддержка'), KeyboardButton(text='🌐 Язык')]
],resize_keyboard=True)
start_eng = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='🎡 Main menu'), KeyboardButton(text='📨 Mailing')],
    [KeyboardButton(text='👨‍💻 Support'), KeyboardButton(text='🌐 Language')]
],resize_keyboard=True)


choice_lang = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🇺🇸 English', callback_data='eng'),
     InlineKeyboardButton(text='🇷🇺 Русский', callback_data='rus')],
])
choice_lang_main_key = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🇺🇸 English', callback_data='eng_key'),
     InlineKeyboardButton(text='🇷🇺 Русский', callback_data='rus_key')],
])


m_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🧸 Профиль', callback_data='profile')],
    [InlineKeyboardButton(text='🎟 Подписка', callback_data='subscription')],
    [InlineKeyboardButton(text='🏷️ Реферальная система', callback_data='referral')],
    [InlineKeyboardButton(text='🗣 Отзывы', url='https://t.me/urtwinews/60')],
    [InlineKeyboardButton(text='📖 Как работает Be twin', url='https://telegra.ph/Logistika-i-eyo-sekrety-09-24')]
])
m_menu_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🧸 Profile', callback_data='profile')],
    [InlineKeyboardButton(text='🎟 Subscription', callback_data='subscription')],
    [InlineKeyboardButton(text='🏷️ Referral system', callback_data='referral')],
    [InlineKeyboardButton(text='🗣 Reviews', url='https://t.me/urtwinews/60')],
    [InlineKeyboardButton(text='📖 How does Be Twin work?', url='https://telegra.ph/Logistika-i-eyo-sekrety-09-24')]
])

back_to_menu_with_reg = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🖨 Регистрация', callback_data='reg')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_menu_with_reg')]
])
back_to_menu_with_reg_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🖨 Registration', callback_data='reg')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_menu_with_reg')]
])


back_to_menu_with_quit = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='👣 Выйти', callback_data='quit')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_menu_with_reg')]
])
back_to_menu_with_quit_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='👣 Logout', callback_data='quit')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_menu_with_reg')]
])


are_you_sure_profile = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Выйти', callback_data='sure_to_quit')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_profile')]
])
are_you_sure_profile_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Logout', callback_data='sure_to_quit')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_profile')]
])

backtosub = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Назад', callback_data='subscription')]
])
backtosub_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Back', callback_data='subscription')]
])

back_to_menu_from_ref = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Реферальная программа', url='https://telegra.ph/ℹ--Referalnaya-programma-08-09')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_menu_with_reg')]
])
back_to_menu_from_ref_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Referral program', url='https://telegra.ph/ℹ--Referalnaya-programma-08-09')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_menu_with_reg')]
])


back_to_profile = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🧸 В профиль', callback_data='back_to_profile')]
])
back_to_profile_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🧸 To profile', callback_data='back_to_profile')]
])

back_to_auto_extra = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_auto_extra')]
])
back_to_auto_extra_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_auto_extra')]
])


back_to_extra = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="↩️ Назад", callback_data="cancel_delete_beats")]
])
back_to_extra_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="↩️ Back", callback_data="cancel_delete_beats")]
])


back_to_extra_text_subject = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🚫 Без заголовка', callback_data='without_title_text_extra')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='cancel_delete_beats')]
])
back_to_extra_text_subject_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🚫 No subject', callback_data='without_title_text_extra')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='cancel_delete_beats')]
])


back_to_extra_text = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🚫 Без текста', callback_data='without_title_text_extra')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='cancel_delete_beats')]
])
back_to_extra_text_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🚫 No body text', callback_data='without_title_text_extra')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='cancel_delete_beats')]
])


back_to_group = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_group")]
])
back_to_group_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="↩️ Back", callback_data="back_to_group")]
])


back_to_actions = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_actions")]
])
back_to_actions_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="↩️ Back", callback_data="back_to_actions")]
])


back_to_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_menu_with_reg')]
])
back_to_menu_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_menu_with_reg')]
])


reg_in_mail = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🖨 Регистрация', callback_data='reg')],
    [InlineKeyboardButton(text='📖 Как работает Be twin', url='https://telegra.ph/Logistika-i-eyo-sekrety-09-24')]
])
reg_in_mail_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🖨 Registration', callback_data='reg')],
    [InlineKeyboardButton(text='📖 How does Be Twin work?', url='https://telegra.ph/Logistika-i-eyo-sekrety-09-24')]
])

turn_off_notifications = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔕 Отключить уведомления', callback_data='turn_off_notifications')]
])
turn_off_notifications_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔕 Turn off notifications', callback_data='turn_off_notifications')]
])

turn_off_notifications_sub = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔕 Отключить уведомления', callback_data='turn_off_notifications_sub')]
])
turn_off_notifications_eng_sub = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔕 Turn off notifications', callback_data='turn_off_notifications_sub')]
])

menu_notifications_reg = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔕 Подтвердить', callback_data='confirm_off_notifications')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_new_ref')]
])
menu_notifications_reg_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔕 Confirm', callback_data='confirm_off_notifications')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_new_ref')]
])

menu_notifications_sub = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔕 Подтвердить', callback_data='confirm_off_notifications_sub')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_new_ref_sub')]
])
menu_notifications_sub_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔕 Confirm', callback_data='confirm_off_notifications_sub')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_new_ref_sub')]
])

support_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='👨‍💻 Support', callback_data='support')]
])
support = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='👨‍💻 Поддержка', callback_data='support')]
])

passw = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🛫 Перейти", url='https://myaccount.google.com/apppasswords')],
    [InlineKeyboardButton(text="📒 Инструкция", url='https://telegra.ph/Itogi-2023-goda-ili-servis-kotoryj-smog-01-01')]
])
passw_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🛫 Go to the required section", url='https://myaccount.google.com/apppasswords')],
    [InlineKeyboardButton(text="📒 Instruction", url='https://telegra.ph/Itogi-2023-goda-ili-servis-kotoryj-smog-01-01')]
])


extra_auto = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="EXTRA", callback_data='extra'),InlineKeyboardButton(text="AUTO", callback_data='auto')]
])


def auto_navigation(current_group, user):
    page_auto_info = InlineKeyboardButton(
        text=f"{current_group}", callback_data="page_auto_info"
    )
    if user.subscription == 'free' or user.subscription == 'неактивна':
        auto_buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✉️ Почты", callback_data='mail'),
             InlineKeyboardButton(text="🎹 Биты", callback_data='beats')],
            [InlineKeyboardButton(text="⚙️ Настройки", callback_data='settings')]
        ])
        return auto_buttons
    else:
        auto_buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❮", callback_data="auto_page_prev"),
             page_auto_info,
             InlineKeyboardButton(text="❯", callback_data="auto_page_next")],
            [InlineKeyboardButton(text="✉️ Почты", callback_data='mail'),
             InlineKeyboardButton(text="🎹 Биты", callback_data='beats')],
            [InlineKeyboardButton(text="⚙️ Настройки", callback_data='settings')]
        ])
        return auto_buttons
def auto_navigation_eng(current_group, user):
    page_auto_info = InlineKeyboardButton(
        text=f"{current_group}", callback_data="page_auto_info"
    )
    if user.subscription == 'free' or user.subscription == 'неактивна':
        auto_buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✉️ Addresses", callback_data='mail'),
             InlineKeyboardButton(text="🎹 Beats", callback_data='beats')],
            [InlineKeyboardButton(text="⚙️ Settings", callback_data='settings')]
        ])
        return auto_buttons
    else:
        auto_buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❮", callback_data="auto_page_prev"),
             page_auto_info,
             InlineKeyboardButton(text="❯", callback_data="auto_page_next")],
            [InlineKeyboardButton(text="✉️ Addresses", callback_data='mail'),
             InlineKeyboardButton(text="🎹 Beats", callback_data='beats')],
            [InlineKeyboardButton(text="⚙️ Settings", callback_data='settings')]
        ])
        return auto_buttons


zero_mail = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📩 Пополнить", callback_data='add_mail')],
    [InlineKeyboardButton(text="↩️ Назад", callback_data='back_to_auto')]
])
zero_mail_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📩 Add addresses", callback_data='add_mail')],
    [InlineKeyboardButton(text="↩️ Back", callback_data='back_to_auto')]
])


zero_beats = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="➕ Пополнить", callback_data='add_beat')],
    [InlineKeyboardButton(text="↩️ Назад", callback_data='back_to_auto')]
])
zero_beats_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="➕ Add beats", callback_data='add_beat')],
    [InlineKeyboardButton(text="↩️ Back", callback_data='back_to_auto')]
])


back_to_beat = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="↩️ Назад", callback_data='back_to_beat')]
])
back_to_beat_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="↩️ Back", callback_data='back_to_beat')]
])


confirm_upload_beat = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Готово", callback_data="finish_beat_upload")],
    [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_beat")]
])
confirm_upload_beat_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Ready", callback_data="finish_beat_upload")],
    [InlineKeyboardButton(text="↩️ Back", callback_data="back_to_beat")]
])


back_to_mail = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="↩️ Назад", callback_data='back_to_mail')]
])
back_to_mail_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="↩️ Back", callback_data='back_to_mail')]
])


back_to_mail_with_complete = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Готово", callback_data="finish_mail_upload")],
    [InlineKeyboardButton(text="↩️ Назад", callback_data='back_to_mail')]
])
back_to_mail_with_complete_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Ready", callback_data="finish_mail_upload")],
    [InlineKeyboardButton(text="↩️ Back", callback_data='back_to_mail')]
])


def mail_navigation(current_page, total_pages):
    prev_page = total_pages if current_page == 1 else current_page - 1
    next_page = 1 if current_page == total_pages else current_page + 1

    page_info = InlineKeyboardButton(
        text=f"{current_page}/{total_pages}", callback_data="page_info"
    )

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❮", callback_data=f"mailpage_{prev_page}"),
         page_info,
         InlineKeyboardButton(text="❯", callback_data=f"mailpage_{next_page}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data="delete_mail"),
         InlineKeyboardButton(text="📩 Пополнить", callback_data="add_mail")],
        [InlineKeyboardButton(text='↩️ Назад', callback_data='mail_back')]
    ])
    return buttons
def mail_navigation_eng(current_page, total_pages):
    prev_page = total_pages if current_page == 1 else current_page - 1
    next_page = 1 if current_page == total_pages else current_page + 1

    page_info = InlineKeyboardButton(
        text=f"{current_page}/{total_pages}", callback_data="page_info"
    )

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❮", callback_data=f"mailpage_{prev_page}"),
         page_info,
         InlineKeyboardButton(text="❯", callback_data=f"mailpage_{next_page}")],
        [InlineKeyboardButton(text="🗑 Delete", callback_data="delete_mail"),
         InlineKeyboardButton(text="📩 Add", callback_data="add_mail")],
        [InlineKeyboardButton(text='↩️ Back', callback_data='mail_back')]
    ])
    return buttons


letter_title = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🚫 Без заголовка', callback_data='without_title')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_settings')]
])
letter_title_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🚫 No subject', callback_data='without_title')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_settings')]
])


letter_text = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🚫 Без текста', callback_data='without_text')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_settings')]
])
letter_text_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🚫 No body text', callback_data='without_text')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_settings')]
])


back_to_mail_extra = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_mail_extra')]
])
back_to_mail_extra_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_mail_extra')]
])


back_to_beats_extra = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_beats_extra')]
])
back_to_beats_extra_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_beats_extra')]
])


back_to_settings = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_settings')]
])
back_to_settings_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_settings')]
])


back_to_interval = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_interval')]
])
back_to_interval_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_interval')]
])


back_to_one_time_interval = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_one_time_interval')]
])
back_to_one_time_interval_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_one_time_interval')]
])


back_to_one_time_settings = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_one_time_settings')]
])
back_to_one_time_settings_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_one_time_settings')]
])


back_to_dispatch_time = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_dispatch_time')]
])
back_to_dispatch_time_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_dispatch_time')]
])


back_to_onetime_time = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_onetime_time')]
])
back_to_onetime_time_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_onetime_time')]
])


def settings_button(on_off, sub, one_on_off):
    on_off_inf = InlineKeyboardButton(
        text=f"{on_off}", callback_data="on_off_data"
    )
    if sub != 'free' and sub != 'неактивна':
        buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='📋 Заголовок письма', callback_data='letter_header'),
             InlineKeyboardButton(text='📄 Текст письма', callback_data='letter_text')],
            [InlineKeyboardButton(text='🗓 Периодичность отправки', callback_data='dispatch_frequency'),
             InlineKeyboardButton(text='⏰ Время отправки', callback_data='dispatch_time')],
            [InlineKeyboardButton(text='🔉 Количество аудио', callback_data='audio_quantity'),
             InlineKeyboardButton(text='↔️ Интервал', callback_data='pack_interval')],
             [InlineKeyboardButton(text=f'{'🟢🔂Разовое письмо' if one_on_off == True else '🔂 Разовое письмо'}', callback_data='one_time_message'),on_off_inf],
            [InlineKeyboardButton(text='↩️ Назад', callback_data='settings_back')]
        ])
    else:
        buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='📋 Заголовок письма', callback_data='letter_header'),
             InlineKeyboardButton(text='📄 Текст письма', callback_data='letter_text')],
            [InlineKeyboardButton(text='🗓 Периодичность отправки', callback_data='dispatch_frequency'),
             InlineKeyboardButton(text='⏰ Время отправки', callback_data='dispatch_time')],
            [InlineKeyboardButton(text='🔉 Количество аудио', callback_data='audio_quantity'), on_off_inf],
            [InlineKeyboardButton(text='↩️ Назад', callback_data='settings_back')]
        ])
    return buttons
def settings_button_eng(on_off, sub, one_on_off):
    on_off_inf = InlineKeyboardButton(
        text=f"{on_off}", callback_data="on_off_data"
    )
    if sub != 'free' and sub != 'неактивна':
        buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='📋 Email subject', callback_data='letter_header'),
             InlineKeyboardButton(text='📄 Email body', callback_data='letter_text')],
            [InlineKeyboardButton(text='🗓 Sending frequency', callback_data='dispatch_frequency'),
             InlineKeyboardButton(text='⏰ Sending time', callback_data='dispatch_time')],
            [InlineKeyboardButton(text='🔉 Number of audios', callback_data='audio_quantity'),
             InlineKeyboardButton(text='↔️ Interval', callback_data='pack_interval')],
            [InlineKeyboardButton(text=f'{"🟢🔂One-time email" if one_on_off else "🔂 One-time email"}',
                                  callback_data='one_time_message'), on_off_inf],
            [InlineKeyboardButton(text='↩️ Back', callback_data='settings_back')]
        ])
    else:
        buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='📋 Email subject', callback_data='letter_header'),
             InlineKeyboardButton(text='📄 Email body', callback_data='letter_text')],
            [InlineKeyboardButton(text='🗓 Sending frequency', callback_data='dispatch_frequency'),
             InlineKeyboardButton(text='⏰ Sending time', callback_data='dispatch_time')],
            [InlineKeyboardButton(text='🔉 Number of audio', callback_data='audio_quantity'), on_off_inf],
            [InlineKeyboardButton(text='↩️ Back', callback_data='settings_back')]
        ])
    return buttons


pack_interval = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='ℹ️ Интервал', url='https://telegra.ph/ℹ-Dlya-chego-nuzhen-interval-05-06'),
    InlineKeyboardButton(text='🚫 Без интервала', callback_data='no_interval')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_settings')]
])
pack_interval_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='ℹ️ Interval', url='https://telegra.ph/ℹ-Dlya-chego-nuzhen-interval-05-06'),
    InlineKeyboardButton(text='🚫 No interval', callback_data='no_interval')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_settings')]
])


pack_interval_one_time = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='ℹ️ Интервал', url='https://telegra.ph/ℹ-Dlya-chego-nuzhen-interval-05-06'),
    InlineKeyboardButton(text='🚫 Без интервала', callback_data='one_no_interval')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_one_time_settings')]
])
pack_interval_one_time_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='ℹ️ Interval', url='https://telegra.ph/ℹ-Dlya-chego-nuzhen-interval-05-06'),
    InlineKeyboardButton(text='🚫 No interval', callback_data='one_no_interval')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_one_time_settings')]
])


for_what = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='ℹ️ Интервал', url='https://telegra.ph/ℹ-Dlya-chego-nuzhen-interval-05-06')],
])
for_what_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='ℹ️ Interval', url='https://telegra.ph/ℹ-Dlya-chego-nuzhen-interval-05-06')],
])


def one_time_settings_button(on_off, quantity_on_off):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📋 Заголовок письма', callback_data='one_time_subject'),
        InlineKeyboardButton(text='📄 Текст письма', callback_data='one_time_message_text')],
        [InlineKeyboardButton(text='⏰ Время отправки', callback_data='one_time_time'),
        InlineKeyboardButton(text=f'{quantity_on_off}', callback_data='one_time_quantity')],
         [InlineKeyboardButton(text=f'ℹ️ Разовое письмо', url='https://telegra.ph/%E2%84%B9-CHto-takoe-razovoe-pismo-05-06'),
        InlineKeyboardButton(text=f'{on_off}', callback_data='one_time_toggle')],
        [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_settings')]
    ])
def one_time_settings_button_eng(on_off, quantity_on_off):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📋 Email subject', callback_data='one_time_subject'),
         InlineKeyboardButton(text='📄 Email body', callback_data='one_time_message_text')],
        [InlineKeyboardButton(text='⏰ Sending time', callback_data='one_time_time'),
         InlineKeyboardButton(text=f'{quantity_on_off}', callback_data='one_time_quantity')],
        [InlineKeyboardButton(text='ℹ️ One-time email',
                              url='https://telegra.ph/%E2%84%B9-CHto-takoe-razovoe-pismo-05-06'),
         InlineKeyboardButton(text=f'{on_off}', callback_data='one_time_toggle')],
        [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_settings')]
    ])


one_time_dispatch_time = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='19:00', callback_data='onetime_19pm'),
    InlineKeyboardButton(text='20:00', callback_data='onetime_20pm')],
    [InlineKeyboardButton(text='21:00', callback_data='onetime_21pm'),
    InlineKeyboardButton(text='ввести вручную', callback_data='onetime_choise')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_one_time_settings')]
])
one_time_dispatch_time_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='19:00', callback_data='onetime_19pm'),
    InlineKeyboardButton(text='20:00', callback_data='onetime_20pm')],
    [InlineKeyboardButton(text='21:00', callback_data='onetime_21pm'),
    InlineKeyboardButton(text='enter manually', callback_data='onetime_choise')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_one_time_settings')]
])


one_time_audio_quantity = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='2', callback_data='onetime_two'),
    InlineKeyboardButton(text='3', callback_data='onetime_three')],
    [InlineKeyboardButton(text='4', callback_data='onetime_four'),
    InlineKeyboardButton(text='5', callback_data='onetime_five')],
    [InlineKeyboardButton(text='🚫 Без битов', callback_data='one_time_without_beat')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_one_time_settings')]
])
one_time_audio_quantity_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='2', callback_data='onetime_two'),
    InlineKeyboardButton(text='3', callback_data='onetime_three')],
    [InlineKeyboardButton(text='4', callback_data='onetime_four'),
    InlineKeyboardButton(text='5', callback_data='onetime_five')],
    [InlineKeyboardButton(text='🚫 No beats', callback_data='one_time_without_beat')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_one_time_settings')]
])


one_time_letter_title = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🚫 Без заголовка', callback_data='one_time_without_title')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_one_time_settings')]
])
one_time_letter_title_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🚫 No subject', callback_data='one_time_without_title')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_one_time_settings')]
])


one_time_letter_text = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🚫 Без текста', callback_data='one_time_without_text')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_one_time_settings')]
])
one_time_letter_text_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🚫 No body text', callback_data='one_time_without_text')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_one_time_settings')]
])


def confirm_email_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Готово", callback_data="confirm_add_emails")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_mail_extra")]
    ])
def confirm_email_keyboard_eng():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ready", callback_data="confirm_add_emails")],
        [InlineKeyboardButton(text="↩️ Back", callback_data="back_to_mail_extra")]
    ])


adm_back = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⚙️ ADMIN PANEL', callback_data='adm_back')]
])
adm_start = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🎟️ Выдать подписку', callback_data='sub')],
    [InlineKeyboardButton(text='🪪 Проверить подписку', callback_data='gsub')],
    [InlineKeyboardButton(text='📪 Рассылка', callback_data='mail_2_sub')],
    [InlineKeyboardButton(text='🎫 Промокоды', callback_data='promo')]
])
adm_add = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Выдать подписку на 30 дней', callback_data='adm_give')],
    [InlineKeyboardButton(text='⚙️ ADMIN PANEL', callback_data='adm_back')]

])
mail_2_sub = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='📪 Общая рассылка', callback_data='for_all')],
    [InlineKeyboardButton(text='PREMIUM', callback_data='who_premium')],
    [InlineKeyboardButton(text='BASIC', callback_data='who_basic')],
    [InlineKeyboardButton(text='FREE', callback_data='who_free')],
])
free_discount = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='⏳ Бесплатные Дни', callback_data='promo_type_freedays')],
    [InlineKeyboardButton(text='💸 Скидка', callback_data='promo_type_discount')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='promo')]
])
promo_basic_gold = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='BASIC', callback_data='promo_sub1_basic')],
    [InlineKeyboardButton(text='PREMIUM', callback_data='promo_sub1_premium')],
    [InlineKeyboardButton(text='BASIC+PREMIUM', callback_data='promo_sub1_premiumbasic')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='promo')]
])
promo_basic_gold_without_basicgold = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='BASIC', callback_data='promo_sub1_basic')],
    [InlineKeyboardButton(text='PREMIUM', callback_data='promo_sub1_premium')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='promo')]
])

create_group = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='➕ Создать группу', callback_data='create_group')]
])
create_group_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='➕ Add Group', callback_data='create_group')]
])


if_free_sub = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='💲Подписаться', callback_data='get_sub')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_menu_with_reg')]
])
if_free_sub_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='💲Subscribe', callback_data='get_sub')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_menu_with_reg')]
])


if_not_free_sub = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔁 Сменить подписку',callback_data='change_sub'),
    InlineKeyboardButton(text='💲Оплатить', callback_data='get_sub')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_menu_with_reg')]
])
if_not_free_sub_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔁 Change subscription', callback_data='change_sub'),
     InlineKeyboardButton(text='💲Pay', callback_data='get_sub')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_menu_with_reg')]
])


are_you_sure = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Подтвердить', callback_data='user_yes')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_sub')]
])
are_you_sure_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Confirm', callback_data='user_yes')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_sub')]
])


premium_basic = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Premium', callback_data='give_premium')],
    [InlineKeyboardButton(text='Basic', callback_data='give_basic')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='adm_back')]
])
premium_basic_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Premium', callback_data='give_premium')],
    [InlineKeyboardButton(text='Basic', callback_data='give_basic')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='adm_back')]
])


dispatch_frequency = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='ежедневно', callback_data='everyday'),
    InlineKeyboardButton(text='раз в 2 дня', callback_data='everyday_2')],
    [InlineKeyboardButton(text='раз в 3 дня', callback_data='everyday_3'),
    InlineKeyboardButton(text='раз в 4 дня', callback_data='everyday_4')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_settings')]
])
dispatch_frequency_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='daily', callback_data='everyday'),
    InlineKeyboardButton(text='every 2 days', callback_data='everyday_2')],
    [InlineKeyboardButton(text='every 3 days', callback_data='everyday_3'),
    InlineKeyboardButton(text='every 4 days', callback_data='everyday_4')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_settings')]
])


dispatch_time = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='19:00', callback_data='19pm'),
    InlineKeyboardButton(text='20:00', callback_data='20pm')],
    [InlineKeyboardButton(text='21:00', callback_data='21pm'),
    InlineKeyboardButton(text='ввести вручную', callback_data='main_time_choise')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_settings')]
])
dispatch_time_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='19:00', callback_data='19pm'),
    InlineKeyboardButton(text='20:00', callback_data='20pm')],
    [InlineKeyboardButton(text='21:00', callback_data='21pm'),
    InlineKeyboardButton(text='enter manually', callback_data='main_time_choise')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_settings')]
])


audio_quantity = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='2', callback_data='two'),
    InlineKeyboardButton(text='3', callback_data='three')],
    [InlineKeyboardButton(text='4', callback_data='four'),
    InlineKeyboardButton(text='5', callback_data='five')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_settings')]
])
audio_quantity_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='2', callback_data='two'),
    InlineKeyboardButton(text='3', callback_data='three')],
    [InlineKeyboardButton(text='4', callback_data='four'),
    InlineKeyboardButton(text='5', callback_data='five')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_settings')]
])


in_main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🎡 В главное меню', callback_data='back_to_menu_with_reg')]
])
in_main_menu_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🎡 To main menu', callback_data='back_to_menu_with_reg')]
])


end_sub = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='💲Продлить', callback_data='get_sub')],
    [InlineKeyboardButton(text='💾 Продолжить с бесплатной', callback_data='go_2_free')]
])
end_sub_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='💲Renew', callback_data='get_sub')],
    [InlineKeyboardButton(text='💾 Go to free plan', callback_data='go_2_free')]
])


end_sub_confirmation = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Подтвердить', callback_data='agree_to_free_sub')],
    [InlineKeyboardButton(text='↩️ Назад', callback_data='back_to_end_sub')]
])
end_sub_confirmation_eng = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Confirm', callback_data='agree_to_free_sub')],
    [InlineKeyboardButton(text='↩️ Back', callback_data='back_to_end_sub')]
])

