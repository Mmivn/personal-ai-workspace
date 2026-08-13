"""Language packs for the whole app: UI strings, computed-result labels

and the system instructions sent to the AI.

How to add a new language later:
1. Copy one of the existing entries in LOCALES (e.g. "en") to a new key
   (e.g. "es") and translate every string. Keep exactly the same nested
   keys — tests/test_locales.py checks all languages stay structurally
   identical, so a missing key fails fast instead of crashing at runtime.
2. Add a line to LANGUAGE_CHOICES: (next menu number, new language code).
That's it — the language-selection menu, onboarding, both branches and
error handling all read from LOCALES generically, nothing else needs
code changes.
"""

LOCALES = {
    "ru": {
        "language_name": "Русский",
        "common": {
            "exit_word": "exit",
            "empty_input": "Пожалуйста, введите текст.",
            "invalid_menu_choice": "Не понял выбор. Введи номер пункта меню.",
            "keyboard_interrupt": "\n\nПрервано пользователем. Пока!",
            "ai_thinking": "AI думает...",
            "ai_translating": "Переводим уже готовый расклад...",
            "goodbye": "До встречи!",
        },
        "onboarding": {
            "intro": (
                "Привет! Я помогу тебе узнать свой знак зодиака и числа "
                "нумерологии — это развлечение и повод для самоанализа, "
                "а не научный прогноз."
            ),
            "edit_intro": "Хорошо, обновим профиль.",
            "ask_name": "Как тебя зовут?",
            "empty_name": "Имя не может быть пустым. Попробуй ещё раз.",
            "ask_birth_date": (
                "Введи дату рождения (форматы: ДД.ММ.ГГГГ, ДД/ММ/ГГГГ "
                "или ГГГГ-ММ-ДД):"
            ),
            "invalid_date": (
                "Не удалось распознать дату. Используй один из форматов: "
                "ДД.ММ.ГГГГ, ДД/ММ/ГГГГ, ГГГГ-ММ-ДД."
            ),
            "date_in_future": "Дата рождения не может быть в будущем. Попробуй ещё раз.",
            "date_too_old": "Такая дата выглядит нереалистично. Попробуй ещё раз.",
            "profile_saved": (
                "Готово, {name}! Дата рождения: {birth_date}. "
                "Знак зодиака: {sign}. Число жизненного пути: {life_path}."
            ),
        },
        "main_menu": {
            "title": "\nГлавное меню:",
            "items": [
                ("zodiac", "♈ Знак зодиака"),
                ("numerology", "🔢 Нумерология"),
                ("change_language", "🌐 Сменить язык"),
                ("edit_profile", "✏️ Изменить профиль"),
                ("exit", "🚪 Выйти"),
            ],
        },
        "zodiac_menu": {
            "title": "\n♈ Меню знака зодиака:",
            "disclaimer": (
                "Астрологические прогнозы — это развлечение и повод для "
                "размышлений, а не научно доказанный способ предсказать будущее."
            ),
            "items": [
                ("my_sign", "Мой знак зодиака"),
                ("today", "Прогноз на сегодня"),
                ("month", "Прогноз на текущий месяц"),
                ("year", "Прогноз на текущий год"),
                ("compatibility", "Совместимость"),
                ("ask_ai", "Задать вопрос AI"),
                ("back", "Назад"),
            ],
        },
        "numerology_menu": {
            "title": "\n🔢 Меню нумерологии:",
            "disclaimer": (
                "Нумерология — это развлечение и инструмент для саморефлексии, "
                "а не научный метод предсказания будущего."
            ),
            "items": [
                ("life_path", "Моё число жизненного пути"),
                ("today", "Нумерология сегодняшнего дня"),
                ("month", "Нумерология текущего месяца"),
                ("year", "Нумерология текущего года"),
                ("full_reading", "Полный нумерологический разбор"),
                ("compatibility", "Совместимость"),
                ("ask_ai", "Задать вопрос AI"),
                ("back", "Назад"),
            ],
        },
        "zodiac": {
            "sign_names": {
                "aries": "Овен",
                "taurus": "Телец",
                "gemini": "Близнецы",
                "cancer": "Рак",
                "leo": "Лев",
                "virgo": "Дева",
                "libra": "Весы",
                "scorpio": "Скорпион",
                "sagittarius": "Стрелец",
                "capricorn": "Козерог",
                "aquarius": "Водолей",
                "pisces": "Рыбы",
            },
            "my_sign_result": "Твой знак зодиака: {sign}",
            "my_sign_cta": "Получить AI-расклад",
            "my_sign_reading_title": "AI-расклад: {sign}",
            "my_sign_preview_items": ["Характер", "Сильные стороны", "Точки роста"],
            "my_sign_preview_label": "AI-расклад включает:",
            "instructions": (
                "Ты — дружелюбный ассистент по западной астрологии. Всегда "
                "отвечай на русском языке, независимо от языка вопроса "
                "пользователя. Используй только факты, переданные тебе (имя, "
                "дата рождения, знак зодиака, сегодняшняя дата, период) — не "
                "пересчитывай и не меняй знак зодиака самостоятельно. Твои "
                "ответы — развлекательная интерпретация для саморефлексии, а "
                "не научно доказанный способ предсказать будущее; не делай "
                "категоричных обещаний."
            ),
            "ask_ai_prompt": "Что ты хочешь спросить про свой знак зодиака?",
            "requests": {
                "my_sign": (
                    "Дай краткую характеристику этого знака зодиака: главные "
                    "черты, сильные стороны и возможные сложности. Отвечай "
                    "структурированно, с подзаголовками."
                ),
                "today": "Дай персональный гороскоп на сегодня.",
                "month": "Дай персональный гороскоп на текущий месяц.",
                "year": "Дай персональный гороскоп на текущий год.",
                "compatibility": (
                    "Опиши астрологическую совместимость этих двух знаков "
                    "зодиака в дружеском развлекательном тоне."
                ),
            },
        },
        "numerology": {
            "instructions": (
                "Ты — дружелюбный ассистент по нумерологии. Всегда отвечай на "
                "русском языке, независимо от языка вопроса пользователя. Все "
                "числа уже точно рассчитаны программой и переданы тебе как "
                "факты — не пересчитывай и не придумывай их заново, только "
                "интерпретируй. Твои ответы — развлекательный инструмент для "
                "саморефлексии, а не научный метод предсказания будущего; не "
                "делай категоричных обещаний."
            ),
            "life_path_result": "Твоё число жизненного пути: {number}",
            "today_result": "Число сегодняшнего дня (Personal Day): {number}",
            "month_result": "Число текущего месяца (Personal Month): {number}",
            "year_result": "Число текущего года (Personal Year): {number}",
            "ask_ai_prompt": "Что ты хочешь спросить про свою нумерологию?",
            "requests": {
                "life_path": (
                    "Дай краткую интерпретацию числа жизненного пути: "
                    "главный смысл, сильные стороны и возможные сложности. "
                    "Отвечай структурированно, с подзаголовками."
                ),
                "today": "Дай персональную интерпретацию числа сегодняшнего дня.",
                "month": "Дай персональную интерпретацию числа текущего месяца.",
                "year": "Дай персональную интерпретацию числа текущего года.",
                "full_reading": (
                    "Дай полный нумерологический разбор на основе всех "
                    "переданных чисел: раскрой число жизненного пути, "
                    "сильные стороны, возможные сложности и дай несколько "
                    "советов для саморазвития. Отвечай структурированно, с "
                    "подзаголовками."
                ),
                "compatibility": (
                    "Опиши нумерологическую совместимость этих двух людей на "
                    "основе их чисел жизненного пути, в дружеском "
                    "развлекательном тоне."
                ),
            },
        },
        "compatibility": {
            "ask_companion_name": "Как зовут второго человека?",
            "ask_companion_birth_date": (
                "Введи дату рождения второго человека (форматы: ДД.ММ.ГГГГ, "
                "ДД/ММ/ГГГГ, ГГГГ-ММ-ДД):"
            ),
        },
        "gui": {
            "app_title": "✨ Зодиак и Нумерология",
            "app_subtitle": "Характер, циклы и отношения — через астрологию, нумерологию и AI",
            "hero_value_prop": "Твоя персональная карта: характер, текущие циклы и отношения — через астрологию, нумерологию и AI.",
            "onboarding_hint": "Это займёт меньше минуты",
            "onboarding_title": "Загляни в свою космическую карту",
            "onboarding_points": [
                "Точный расчёт знака и чисел",
                "Персональные AI-расклады",
                "3 языка, приватно и быстро",
            ],
            "language_label": "Язык",
            "profile_section_title": "Твой профиль",
            "consent_label": "Я соглашаюсь отправить своё имя и дату рождения AI для персонализированных раскладов.",
            "save_button": "Сохранить профиль",
            "profile_card_title": "Твой профиль",
            "profile_labels": {
                "name": "Имя",
                "birth_date": "Дата рождения",
                "zodiac_sign": "Знак зодиака",
                "life_path": "Число жизненного пути",
            },
            "companion_section_title": "Второй человек",
            "get_interpretation_button": "Получить персональный разбор",
            "get_forecast_button": "Получить прогноз",
            "get_full_reading_button": "Получить полный разбор",
            "get_compatibility_button": "Проверить совместимость",
            "ask_button": "Спросить",
            "cached_note": "Показан ранее полученный результат.",
            "hero_greeting": "Привет, {name}",
            "zodiac_card_descriptions": {
                "my_sign": "Черты, сильные стороны, сложности",
                "today": "Энергия дня для тебя",
                "month": "Настроение и темы месяца",
                "year": "Главные темы этого года",
                "compatibility": "Сравни два знака зодиака",
                "ask_ai": "Свой вопрос о твоём знаке",
            },
            "numerology_card_descriptions": {
                "life_path": "Главное число твоего пути",
                "today": "Число дня и его смысл",
                "month": "Число месяца и его смысл",
                "year": "Число года и его смысл",
                "full_reading": "Полный разбор всех чисел",
                "compatibility": "Сравни числа двух людей",
                "ask_ai": "Свой вопрос о нумерологии",
            },
        },
        "errors": {
            "api_key_missing": "Ошибка: не найден OPENAI_API_KEY в .env файле.",
            "consent_required": "Необходимо согласие на отправку данных перед вызовом AI.",
            "api_error": "Произошла ошибка при обращении к AI: {error}",
            "empty_ai_response": "AI вернул пустой ответ. Попробуй ещё раз.",
        },
    },
    "en": {
        "language_name": "English",
        "common": {
            "exit_word": "exit",
            "empty_input": "Please enter some text.",
            "invalid_menu_choice": "Didn't get that. Enter the number of a menu item.",
            "keyboard_interrupt": "\n\nInterrupted by user. Bye!",
            "ai_thinking": "AI is thinking...",
            "ai_translating": "Translating your existing reading...",
            "goodbye": "See you soon!",
        },
        "onboarding": {
            "intro": (
                "Hi! I'll help you discover your zodiac sign and numerology "
                "numbers — this is for fun and self-reflection, not a "
                "scientific forecast."
            ),
            "edit_intro": "Okay, let's update your profile.",
            "ask_name": "What's your name?",
            "empty_name": "Name can't be empty. Please try again.",
            "ask_birth_date": (
                "Enter your birth date (formats: DD.MM.YYYY, DD/MM/YYYY, "
                "or YYYY-MM-DD):"
            ),
            "invalid_date": (
                "Couldn't parse that date. Use one of these formats: "
                "DD.MM.YYYY, DD/MM/YYYY, YYYY-MM-DD."
            ),
            "date_in_future": "Birth date can't be in the future. Please try again.",
            "date_too_old": "That date doesn't look realistic. Please try again.",
            "profile_saved": (
                "All set, {name}! Birth date: {birth_date}. Zodiac sign: "
                "{sign}. Life Path Number: {life_path}."
            ),
        },
        "main_menu": {
            "title": "\nMain menu:",
            "items": [
                ("zodiac", "♈ Zodiac"),
                ("numerology", "🔢 Numerology"),
                ("change_language", "🌐 Change language"),
                ("edit_profile", "✏️ Edit profile"),
                ("exit", "🚪 Exit"),
            ],
        },
        "zodiac_menu": {
            "title": "\n♈ Zodiac menu:",
            "disclaimer": (
                "Astrological forecasts are for entertainment and "
                "self-reflection, not a scientifically proven way to "
                "predict the future."
            ),
            "items": [
                ("my_sign", "My zodiac sign"),
                ("today", "Forecast for today"),
                ("month", "Forecast for this month"),
                ("year", "Forecast for this year"),
                ("compatibility", "Compatibility"),
                ("ask_ai", "Ask AI a question"),
                ("back", "Back"),
            ],
        },
        "numerology_menu": {
            "title": "\n🔢 Numerology menu:",
            "disclaimer": (
                "Numerology is for entertainment and self-reflection, not a "
                "scientific method for predicting the future."
            ),
            "items": [
                ("life_path", "My Life Path Number"),
                ("today", "Today's numerology"),
                ("month", "This month's numerology"),
                ("year", "This year's numerology"),
                ("full_reading", "Full numerology reading"),
                ("compatibility", "Compatibility"),
                ("ask_ai", "Ask AI a question"),
                ("back", "Back"),
            ],
        },
        "zodiac": {
            "sign_names": {
                "aries": "Aries",
                "taurus": "Taurus",
                "gemini": "Gemini",
                "cancer": "Cancer",
                "leo": "Leo",
                "virgo": "Virgo",
                "libra": "Libra",
                "scorpio": "Scorpio",
                "sagittarius": "Sagittarius",
                "capricorn": "Capricorn",
                "aquarius": "Aquarius",
                "pisces": "Pisces",
            },
            "my_sign_result": "Your zodiac sign: {sign}",
            "my_sign_cta": "Get AI reading",
            "my_sign_reading_title": "AI reading: {sign}",
            "my_sign_preview_items": ["Character", "Strengths", "Growth points"],
            "my_sign_preview_label": "Your AI reading covers:",
            "instructions": (
                "You are a friendly Western astrology assistant. Always "
                "reply in English, no matter what language the user writes "
                "in. Use only the facts given to you (name, birth date, "
                "zodiac sign, today's date, period) — never recompute or "
                "change the zodiac sign yourself. Your answers are an "
                "entertaining interpretation for self-reflection, not a "
                "scientifically proven way to predict the future; avoid "
                "definitive promises."
            ),
            "ask_ai_prompt": "What would you like to ask about your zodiac sign?",
            "requests": {
                "my_sign": (
                    "Give a brief characteristic of this zodiac sign: key "
                    "traits, strengths, and possible challenges. Structure "
                    "your answer with clear headings."
                ),
                "today": "Give a personal horoscope for today.",
                "month": "Give a personal horoscope for this month.",
                "year": "Give a personal horoscope for this year.",
                "compatibility": (
                    "Describe the astrological compatibility of these two "
                    "zodiac signs in a friendly, entertaining tone."
                ),
            },
        },
        "numerology": {
            "instructions": (
                "You are a friendly numerology assistant. Always reply in "
                "English, no matter what language the user writes in. All "
                "numbers have already been calculated precisely by the "
                "program and given to you as facts — never recompute or "
                "invent them, only interpret them. Your answers are an "
                "entertaining self-reflection tool, not a scientific method "
                "for predicting the future; avoid definitive promises."
            ),
            "life_path_result": "Your Life Path Number: {number}",
            "today_result": "Today's Personal Day Number: {number}",
            "month_result": "This month's Personal Month Number: {number}",
            "year_result": "This year's Personal Year Number: {number}",
            "ask_ai_prompt": "What would you like to ask about your numerology?",
            "requests": {
                "life_path": (
                    "Give a brief interpretation of the Life Path Number: "
                    "its core meaning, strengths, and possible challenges. "
                    "Structure your answer with clear headings."
                ),
                "today": "Give a personal interpretation of today's number.",
                "month": "Give a personal interpretation of this month's number.",
                "year": "Give a personal interpretation of this year's number.",
                "full_reading": (
                    "Give a full numerology reading based on all the "
                    "numbers provided: cover the Life Path Number, "
                    "strengths, possible challenges, and a few "
                    "self-development tips. Structure your answer with "
                    "clear headings."
                ),
                "compatibility": (
                    "Describe the numerology compatibility of these two "
                    "people based on their Life Path Numbers, in a "
                    "friendly, entertaining tone."
                ),
            },
        },
        "compatibility": {
            "ask_companion_name": "What is the second person's name?",
            "ask_companion_birth_date": (
                "Enter the second person's birth date (formats: DD.MM.YYYY, "
                "DD/MM/YYYY, YYYY-MM-DD):"
            ),
        },
        "gui": {
            "app_title": "✨ Zodiac & Numerology",
            "app_subtitle": "Character, cycles, and relationships — through astrology, numerology, and AI",
            "hero_value_prop": "Your personal map: character, current cycles, and relationships — through astrology, numerology, and AI.",
            "onboarding_hint": "Takes less than a minute",
            "onboarding_title": "Discover your cosmic blueprint",
            "onboarding_points": [
                "Precise sign & number calculations",
                "Personal AI readings",
                "3 languages, private and fast",
            ],
            "language_label": "Language",
            "profile_section_title": "Your profile",
            "consent_label": "I consent to send my name and birth date to the AI for personalized readings.",
            "save_button": "Save profile",
            "profile_card_title": "Your profile",
            "profile_labels": {
                "name": "Name",
                "birth_date": "Birth date",
                "zodiac_sign": "Zodiac sign",
                "life_path": "Life Path Number",
            },
            "companion_section_title": "The second person",
            "get_interpretation_button": "Get your personal reading",
            "get_forecast_button": "Get forecast",
            "get_full_reading_button": "Get full reading",
            "get_compatibility_button": "Check compatibility",
            "ask_button": "Ask",
            "cached_note": "Showing a previously fetched result.",
            "hero_greeting": "Hi, {name}",
            "zodiac_card_descriptions": {
                "my_sign": "Traits, strengths, challenges",
                "today": "Today's energy, just for you",
                "month": "This month's mood and themes",
                "year": "This year's key themes",
                "compatibility": "Compare two zodiac signs",
                "ask_ai": "Ask anything about your sign",
            },
            "numerology_card_descriptions": {
                "life_path": "The core number of your path",
                "today": "Today's number and its meaning",
                "month": "This month's number and meaning",
                "year": "This year's number and meaning",
                "full_reading": "A full reading of every number",
                "compatibility": "Compare two people's numbers",
                "ask_ai": "Ask anything about your numerology",
            },
        },
        "errors": {
            "api_key_missing": "Error: OPENAI_API_KEY not found in the .env file.",
            "consent_required": "Consent is required before calling the AI.",
            "api_error": "An error occurred while contacting the AI: {error}",
            "empty_ai_response": "The AI returned an empty response. Please try again.",
        },
    },
    "vi": {
        "language_name": "Tiếng Việt",
        "common": {
            "exit_word": "exit",
            "empty_input": "Vui lòng nhập nội dung.",
            "invalid_menu_choice": "Không hiểu lựa chọn. Vui lòng nhập số của mục trong menu.",
            "keyboard_interrupt": "\n\nĐã bị người dùng dừng lại. Tạm biệt!",
            "ai_thinking": "AI đang suy nghĩ...",
            "ai_translating": "Đang dịch kết quả đã có...",
            "goodbye": "Hẹn gặp lại!",
        },
        "onboarding": {
            "intro": (
                "Xin chào! Mình sẽ giúp bạn khám phá cung hoàng đạo và các "
                "con số thần số học — đây là hoạt động giải trí và để tự "
                "chiêm nghiệm, không phải dự đoán khoa học."
            ),
            "edit_intro": "Được rồi, hãy cập nhật hồ sơ.",
            "ask_name": "Bạn tên là gì?",
            "empty_name": "Tên không được để trống. Vui lòng thử lại.",
            "ask_birth_date": (
                "Nhập ngày sinh (định dạng: DD.MM.YYYY, DD/MM/YYYY hoặc "
                "YYYY-MM-DD):"
            ),
            "invalid_date": (
                "Không nhận dạng được ngày. Hãy dùng một trong các định "
                "dạng: DD.MM.YYYY, DD/MM/YYYY, YYYY-MM-DD."
            ),
            "date_in_future": "Ngày sinh không thể ở tương lai. Vui lòng thử lại.",
            "date_too_old": "Ngày này có vẻ không hợp lý. Vui lòng thử lại.",
            "profile_saved": (
                "Xong rồi, {name}! Ngày sinh: {birth_date}. Cung hoàng đạo: "
                "{sign}. Số chủ đạo (Life Path): {life_path}."
            ),
        },
        "main_menu": {
            "title": "\nMenu chính:",
            "items": [
                ("zodiac", "♈ Cung hoàng đạo"),
                ("numerology", "🔢 Thần số học"),
                ("change_language", "🌐 Đổi ngôn ngữ"),
                ("edit_profile", "✏️ Sửa hồ sơ"),
                ("exit", "🚪 Thoát"),
            ],
        },
        "zodiac_menu": {
            "title": "\n♈ Menu Cung hoàng đạo:",
            "disclaimer": (
                "Vận trình chiêm tinh chỉ mang tính giải trí và tự chiêm "
                "nghiệm, không phải phương pháp dự đoán tương lai đã được "
                "khoa học chứng minh."
            ),
            "items": [
                ("my_sign", "Cung hoàng đạo của tôi"),
                ("today", "Vận trình hôm nay"),
                ("month", "Vận trình tháng này"),
                ("year", "Vận trình năm nay"),
                ("compatibility", "Sự hợp nhau"),
                ("ask_ai", "Hỏi AI"),
                ("back", "Quay lại"),
            ],
        },
        "numerology_menu": {
            "title": "\n🔢 Menu Thần số học:",
            "disclaimer": (
                "Thần số học chỉ mang tính giải trí và là công cụ tự chiêm "
                "nghiệm, không phải phương pháp khoa học để dự đoán tương lai."
            ),
            "items": [
                ("life_path", "Số chủ đạo của tôi (Life Path)"),
                ("today", "Thần số học hôm nay"),
                ("month", "Thần số học tháng này"),
                ("year", "Thần số học năm nay"),
                ("full_reading", "Phân tích thần số học đầy đủ"),
                ("compatibility", "Sự hợp nhau"),
                ("ask_ai", "Hỏi AI"),
                ("back", "Quay lại"),
            ],
        },
        "zodiac": {
            "sign_names": {
                "aries": "Bạch Dương",
                "taurus": "Kim Ngưu",
                "gemini": "Song Tử",
                "cancer": "Cự Giải",
                "leo": "Sư Tử",
                "virgo": "Xử Nữ",
                "libra": "Thiên Bình",
                "scorpio": "Bọ Cạp",
                "sagittarius": "Nhân Mã",
                "capricorn": "Ma Kết",
                "aquarius": "Bảo Bình",
                "pisces": "Song Ngư",
            },
            "my_sign_result": "Cung hoàng đạo của bạn: {sign}",
            "my_sign_cta": "Xem luận giải AI",
            "my_sign_reading_title": "Luận giải AI: {sign}",
            "my_sign_preview_items": ["Tính cách", "Điểm mạnh", "Điểm cần phát triển"],
            "my_sign_preview_label": "Luận giải AI bao gồm:",
            "instructions": (
                "Bạn là trợ lý thân thiện về chiêm tinh phương Tây. Luôn trả "
                "lời bằng tiếng Việt, bất kể người dùng hỏi bằng ngôn ngữ "
                "nào. Chỉ sử dụng các dữ kiện được cung cấp (tên, ngày sinh, "
                "cung hoàng đạo, ngày hôm nay, giai đoạn) — không tự tính "
                "lại hay thay đổi cung hoàng đạo. Câu trả lời của bạn chỉ "
                "mang tính giải trí và tự chiêm nghiệm, không phải phương "
                "pháp dự đoán tương lai đã được khoa học chứng minh; không "
                "đưa ra lời hứa chắc chắn."
            ),
            "ask_ai_prompt": "Bạn muốn hỏi gì về cung hoàng đạo của mình?",
            "requests": {
                "my_sign": (
                    "Hãy đưa ra đặc điểm ngắn gọn của cung hoàng đạo này: "
                    "những nét tính cách chính, điểm mạnh và những thử "
                    "thách có thể gặp. Trình bày câu trả lời theo các mục "
                    "rõ ràng."
                ),
                "today": "Hãy đưa ra vận trình cá nhân cho hôm nay.",
                "month": "Hãy đưa ra vận trình cá nhân cho tháng này.",
                "year": "Hãy đưa ra vận trình cá nhân cho năm nay.",
                "compatibility": (
                    "Hãy mô tả sự hợp nhau về chiêm tinh giữa hai cung hoàng "
                    "đạo này theo giọng điệu thân thiện, giải trí."
                ),
            },
        },
        "numerology": {
            "instructions": (
                "Bạn là trợ lý thân thiện về thần số học. Luôn trả lời bằng "
                "tiếng Việt, bất kể người dùng hỏi bằng ngôn ngữ nào. Tất cả "
                "các con số đã được chương trình tính toán chính xác và "
                "cung cấp cho bạn dưới dạng dữ kiện — không tự tính lại hay "
                "bịa ra số mới, chỉ diễn giải chúng. Câu trả lời của bạn chỉ "
                "mang tính giải trí và tự chiêm nghiệm, không phải phương "
                "pháp khoa học để dự đoán tương lai; không đưa ra lời hứa "
                "chắc chắn."
            ),
            "life_path_result": "Số chủ đạo (Life Path) của bạn: {number}",
            "today_result": "Số ngày cá nhân (Personal Day) hôm nay: {number}",
            "month_result": "Số tháng cá nhân (Personal Month) tháng này: {number}",
            "year_result": "Số năm cá nhân (Personal Year) năm nay: {number}",
            "ask_ai_prompt": "Bạn muốn hỏi gì về thần số học của mình?",
            "requests": {
                "life_path": (
                    "Hãy diễn giải ngắn gọn về Số chủ đạo (Life Path): ý "
                    "nghĩa cốt lõi, điểm mạnh và những thử thách có thể "
                    "gặp. Trình bày câu trả lời theo các mục rõ ràng."
                ),
                "today": "Hãy diễn giải cá nhân hóa cho số ngày hôm nay.",
                "month": "Hãy diễn giải cá nhân hóa cho số tháng này.",
                "year": "Hãy diễn giải cá nhân hóa cho số năm nay.",
                "full_reading": (
                    "Hãy đưa ra phân tích thần số học đầy đủ dựa trên tất cả "
                    "các con số đã cung cấp: bao gồm Số chủ đạo, điểm mạnh, "
                    "những thử thách có thể gặp và một vài lời khuyên để "
                    "phát triển bản thân. Trình bày câu trả lời theo các "
                    "mục rõ ràng."
                ),
                "compatibility": (
                    "Hãy mô tả sự hợp nhau về thần số học giữa hai người này "
                    "dựa trên số chủ đạo của họ, theo giọng điệu thân thiện, "
                    "giải trí."
                ),
            },
        },
        "compatibility": {
            "ask_companion_name": "Người thứ hai tên là gì?",
            "ask_companion_birth_date": (
                "Nhập ngày sinh của người thứ hai (định dạng: DD.MM.YYYY, "
                "DD/MM/YYYY, YYYY-MM-DD):"
            ),
        },
        "gui": {
            "app_title": "✨ Cung Hoàng Đạo & Thần Số Học",
            "app_subtitle": "Tính cách, chu kỳ và các mối quan hệ — qua chiêm tinh, thần số học và AI",
            "hero_value_prop": "Bản đồ cá nhân của bạn: tính cách, chu kỳ hiện tại và các mối quan hệ — qua chiêm tinh, thần số học và AI.",
            "onboarding_hint": "Chỉ mất chưa đến một phút",
            "onboarding_title": "Khám phá bản đồ vũ trụ của bạn",
            "onboarding_points": [
                "Tính toán chính xác cung và con số",
                "Luận giải AI cá nhân hóa",
                "3 ngôn ngữ, riêng tư và nhanh chóng",
            ],
            "language_label": "Ngôn ngữ",
            "profile_section_title": "Hồ sơ của bạn",
            "consent_label": "Tôi đồng ý gửi tên và ngày sinh của mình cho AI để nhận phân tích cá nhân hóa.",
            "save_button": "Lưu hồ sơ",
            "profile_card_title": "Hồ sơ của bạn",
            "profile_labels": {
                "name": "Tên",
                "birth_date": "Ngày sinh",
                "zodiac_sign": "Cung hoàng đạo",
                "life_path": "Số chủ đạo (Life Path)",
            },
            "companion_section_title": "Người thứ hai",
            "get_interpretation_button": "Xem phân tích cá nhân",
            "get_forecast_button": "Xem vận trình",
            "get_full_reading_button": "Xem phân tích đầy đủ",
            "get_compatibility_button": "Kiểm tra sự hợp nhau",
            "ask_button": "Hỏi",
            "cached_note": "Đang hiển thị kết quả đã lấy trước đó.",
            "hero_greeting": "Xin chào, {name}",
            "zodiac_card_descriptions": {
                "my_sign": "Tính cách, điểm mạnh, thử thách",
                "today": "Năng lượng hôm nay dành cho bạn",
                "month": "Tâm trạng và chủ đề tháng này",
                "year": "Những chủ đề chính của năm nay",
                "compatibility": "So sánh hai cung hoàng đạo",
                "ask_ai": "Hỏi bất cứ điều gì về cung của bạn",
            },
            "numerology_card_descriptions": {
                "life_path": "Con số cốt lõi của hành trình",
                "today": "Con số hôm nay và ý nghĩa",
                "month": "Con số tháng này và ý nghĩa",
                "year": "Con số năm nay và ý nghĩa",
                "full_reading": "Phân tích đầy đủ mọi con số",
                "compatibility": "So sánh con số của hai người",
                "ask_ai": "Hỏi bất cứ điều gì về thần số học",
            },
        },
        "errors": {
            "api_key_missing": "Lỗi: không tìm thấy OPENAI_API_KEY trong file .env.",
            "consent_required": "Cần có sự đồng ý trước khi gọi AI.",
            "api_error": "Đã xảy ra lỗi khi gọi AI: {error}",
            "empty_ai_response": "AI trả về phản hồi trống. Vui lòng thử lại.",
        },
    },
}

# Order of the language-selection menu: (menu number, language code in LOCALES).
LANGUAGE_CHOICES = [
    ("1", "ru"),
    ("2", "en"),
    ("3", "vi"),
]

_INVALID_LANGUAGE_CHOICE_TEXT = (
    "Неверный выбор, попробуйте снова / Invalid choice, try again / "
    "Lựa chọn không hợp lệ, vui lòng thử lại"
)


def language_menu_text():
    """Menu shown before a language is picked, so it stays multilingual by necessity."""
    lines = ["Выберите язык / Choose language / Chọn ngôn ngữ:"]
    for number, code in LANGUAGE_CHOICES:
        lines.append(f"{number} — {LOCALES[code]['language_name']}")
    return "\n".join(lines)


def invalid_choice_text():
    return _INVALID_LANGUAGE_CHOICE_TEXT


def resolve_language_choice(raw_choice):
    """Code language matching user input (menu number or language code), or None."""
    raw_choice = raw_choice.strip().lower()
    for number, code in LANGUAGE_CHOICES:
        if raw_choice == number or raw_choice == code:
            return code
    return None
