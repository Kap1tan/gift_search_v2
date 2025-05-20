import logging
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Настройка логгера
logging.basicConfig(
    format='[%(levelname)s] %(message)s',
    level=logging.INFO
)
logger = logging.getLogger()

# Конфигурация (все данные хранятся в памяти)
CONFIG = {
    'TOKEN': '7064434574:AAG9TuO_wlzmyWg4m68uj_T4j8g3HkXPe-Q',
    'ORIGINAL_ADMINS': {804644988, 7403767874},  # Изначальные админы
    'ADMINS': {804644988, 7403767874},  # Копия изначальных админов
    'USERS': set()
}

# Предустановленные подарки с максимальными пределами
GIFTS = {
    "MadPumpkin": 22199,
    "LolPop": 468745,
    "LootBag": 14489,
    "LoveCandle": 30296,
    "LovePotion": 30412,
    "LunarSnake": 259346,
    "MagicPotion": 4871,
    "WitchHat": 88480,
    "WinterWreath": 100846,
    "VoodooDoll": 27620,
    "VintageCigar": 31024,
    "TrappedHeart": 26407,
    "ToyBear": 57724,
    "TopHat": 35099,
    "TamaGadget": 135097,
    "SwissWatch": 29323,
    "StarNotepad": 99082,
    "SpyAgaric": 89438,
    "SpicedWine": 146090,
    "SnowMittens": 49969,
    "SnowGlobe": 72788,
    "SleighBell": 28000,
    "SkullFlower": 24126,
    "SignetRing": 18499,
    "SharpTongue": 8546,
    "ScaredCat": 19289,
    "SantaHat": 89034,
    "SakuraFlower": 93115,
    "RecordPlayer": 46888,
    "PreciousPeach": 3160,
    "PlushPepe": 2813,
    "PerfumeBottle": 4848,
    "PartySparkler": 243771,
    "NekoHelmet": 16149,
    "EternalCandle": 46590,
    "GingerCookie": 188888,
    "AstralShard": 6196,
    "BDayCandle": 338745,
    "BerryBox": 66580,
    "BunnyMuffin": 66655,
    "CandyCane": 320622,
    "CookieHeart": 264486,
    "CrystalBall": 27732,
    "DeskCalendar": 374077,
    "DiamondRing": 32924,
    "DurovsCap": 4774,
    "EasterEgg": 173176,
    "EternalRose": 37640,
    "ElectricSkull": 9407,
    "EvilEye": 85204,
    "FlyingBroom": 25916,
    "GenieLamp": 7666,
    "HangingStar": 58118,
    "HexPot": 69837,
    "HomemadeCake": 199482,
    "HypnoLollipop": 116639,
    "IonGem": 4692,
    "JackInTheBox": 97345,
    "JellyBunny": 129350,
    "JesterHat": 190222,
    "JingleBells": 124593,
    "KissedFrog": 14278
}

ITEMS_PER_PAGE = 7  # Количество подарков на страницу


class GiftBot:
    def __init__(self):
        self.sessions = {}  # Хранение сессий пользователей

    async def _reply(self, update: Update, text: str, reply_markup=None):
        """Универсальный метод отправки сообщений"""
        try:
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=reply_markup,
                    disable_web_page_preview=False
                )
            else:
                await update.message.reply_text(
                    text=text,
                    reply_markup=reply_markup,
                    disable_web_page_preview=False
                )
        except Exception as e:
            logger.error(f"Ошибка отправки: {e}")

    # Основные команды
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in CONFIG['ADMINS'] and user_id not in CONFIG['USERS']:
            await self._reply(update, "⛔ Нет доступа")
            return

        await self._show_gift_catalog(update, page=0)

    async def _show_gift_catalog(self, update: Update, page=0):
        """Показать каталог подарков с пагинацией"""
        gift_names = list(GIFTS.keys())
        total_pages = (len(gift_names) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

        # Проверяем диапазон страниц
        if page < 0:
            page = total_pages - 1
        elif page >= total_pages:
            page = 0

        start_idx = page * ITEMS_PER_PAGE
        end_idx = min(start_idx + ITEMS_PER_PAGE, len(gift_names))
        current_gifts = gift_names[start_idx:end_idx]

        # Создаем кнопки для каждого подарка на странице
        keyboard = []
        for gift_name in current_gifts:
            keyboard.append([
                InlineKeyboardButton(
                    f"{gift_name}",
                    callback_data=f"gift_{gift_name}"
                )
            ])

        # Добавляем навигационные кнопки
        keyboard.append([
            InlineKeyboardButton("« Назад", callback_data=f"page_{page - 1}"),
            InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="info"),
            InlineKeyboardButton("Вперед »", callback_data=f"page_{page + 1}")
        ])

        await self._reply(
            update,
            f"🎁 Каталог подарков (Страница {page + 1}/{total_pages}):\nВыберите подарок из списка:",
            InlineKeyboardMarkup(keyboard)
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in CONFIG['ADMINS'] and user_id not in CONFIG['USERS']:
            await self._reply(update, "⛔ Нет доступа")
            return

        text = update.message.text

        # Проверяем, есть ли активная сессия для пользователя
        if user_id in self.sessions and 'gift_name' in self.sessions[user_id]:
            # У пользователя есть выбранный подарок, он должен ввести номер
            try:
                num = int(text)
                gift_name = self.sessions[user_id]['gift_name']

                # Проверяем, не превышает ли номер максимальный предел
                max_num = GIFTS[gift_name]
                if num <= 0:
                    await self._reply(update, "❌ Номер должен быть положительным числом!")
                elif num > max_num:
                    await self._reply(update,
                                      f"❌ Подарка {gift_name} с номером {num} не существует!\nМаксимальный номер: {max_num}")
                else:
                    await self._show_gift_with_number(update, gift_name, num)
            except ValueError:
                await self._reply(update, "❌ Пожалуйста, введите число!")
        else:
            # Проверяем, является ли текст числом (номер подарка в списке)
            try:
                gift_index = int(text) - 1  # Пользователи считают с 1, но индекс с 0
                gift_names = list(GIFTS.keys())
                if 0 <= gift_index < len(gift_names):
                    gift_name = gift_names[gift_index]
                    max_num = GIFTS[gift_name]
                    self.sessions[user_id] = {'gift_name': gift_name}
                    await self._reply(update,
                                      f"🔍 Вы выбрали подарок: {gift_name}\nТеперь введите номер (от 1 до {max_num}):")
                else:
                    await self._reply(update, f"❌ Введите число от 1 до {len(gift_names)}")
            except ValueError:
                # Если это не число, показываем каталог
                await self._show_gift_catalog(update, page=0)

    async def _show_gift_with_number(self, update: Update, name: str, num: int):
        """Показать подарок с заданным номером и навигационными кнопками"""
        link = f"https://t.me/nft/{name}-{num}"
        max_num = GIFTS[name]

        # Создаем клавиатуру для навигации
        keyboard = [
            [
                InlineKeyboardButton("« Предыдущий", callback_data=f"prev_{name}_{num}"),
                InlineKeyboardButton("Следующий »", callback_data=f"next_{name}_{num}")
            ],
            [InlineKeyboardButton("🔙 Назад к каталогу", callback_data="catalog")]
        ]

        await self._reply(
            update,
            f"🎁 Подарок: {name}\nНомер: {num} (макс. {max_num})\nСсылка: {link}",
            InlineKeyboardMarkup(keyboard)
        )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = update.effective_user.id

        try:
            await query.answer()  # Необходимо ответить на callback

            callback_data = query.data

            if callback_data == "catalog":
                # Очищаем сессию пользователя и показываем каталог
                if user_id in self.sessions:
                    self.sessions.pop(user_id, None)
                await self._show_gift_catalog(update, page=0)

            elif callback_data == "info":
                # Информационная кнопка, ничего не делаем
                pass

            elif callback_data.startswith("page_"):
                # Пагинация каталога
                page = int(callback_data.split("_")[1])
                await self._show_gift_catalog(update, page=page)

            elif callback_data.startswith("gift_"):
                # Выбор подарка из каталога
                _, gift_name = callback_data.split("_", 1)
                max_num = GIFTS[gift_name]
                self.sessions[user_id] = {'gift_name': gift_name}
                await self._reply(update,
                                  f"🔍 Вы выбрали подарок: {gift_name}\nТеперь введите номер (от 1 до {max_num}):")

            elif callback_data.startswith("next_"):
                # Следующий номер подарка
                _, gift_name, current_num = callback_data.split("_", 2)
                next_num = int(current_num) + 1
                max_num = GIFTS[gift_name]

                if next_num > max_num:
                    await self._reply(update, f"❌ Достигнут максимальный номер для {gift_name}: {max_num}")
                else:
                    await self._show_gift_with_number(update, gift_name, next_num)

            elif callback_data.startswith("prev_"):
                # Предыдущий номер подарка
                _, gift_name, current_num = callback_data.split("_", 2)
                prev_num = int(current_num) - 1
                if prev_num < 1:
                    await self._reply(update, "❌ Номер не может быть меньше 1")
                else:
                    await self._show_gift_with_number(update, gift_name, prev_num)

        except Exception as e:
            logger.error(f"Ошибка в callback: {e}")
            try:
                await self._reply(update, "⚠️ Ошибка, попробуйте снова")
            except Exception:
                # Если уже не можем ответить на callback
                pass

    # Команды администратора (старые)
    async def add_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in CONFIG['ADMINS']:
            return

        try:
            new_admin = int(context.args[0])
            CONFIG['ADMINS'].add(new_admin)
            await self._reply(update, f"✅ Админ {new_admin} добавлен")
        except:
            await self._reply(update, "Используйте: /add_admin <ID>")

    async def remove_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in CONFIG['ADMINS']:
            return

        try:
            admin_id = int(context.args[0])
            if admin_id == update.effective_user.id:
                await self._reply(update, "❌ Нельзя удалить самого себя")
            elif admin_id in CONFIG['ADMINS']:
                CONFIG['ADMINS'].remove(admin_id)
                await self._reply(update, f"✅ Админ {admin_id} удален")
            else:
                await self._reply(update, "❌ Админ не найден")
        except:
            await self._reply(update, "Используйте: /remove_admin <ID>")

    # Новые команды администратора (только для оригинальных админов)
    async def add_admin_special(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in CONFIG['ORIGINAL_ADMINS']:
            await self._reply(update, "⛔ Нет доступа")
            return

        try:
            new_admin = int(context.args[0])
            CONFIG['ADMINS'].add(new_admin)
            await self._reply(update, f"✅ Админ {new_admin} добавлен")
        except:
            await self._reply(update, "Используйте: /qwerty <ID>")

    async def remove_admin_special(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in CONFIG['ORIGINAL_ADMINS']:
            await self._reply(update, "⛔ Нет доступа")
            return

        try:
            admin_id = int(context.args[0])
            if admin_id in CONFIG['ORIGINAL_ADMINS']:
                await self._reply(update, "❌ Нельзя удалить оригинального админа")
            elif admin_id in CONFIG['ADMINS']:
                CONFIG['ADMINS'].remove(admin_id)
                await self._reply(update, f"✅ Админ {admin_id} удален")
            else:
                await self._reply(update, "❌ Админ не найден")
        except:
            await self._reply(update, "Используйте: /ytrewq <ID>")

    async def add_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in CONFIG['ADMINS']:
            return

        try:
            new_user = int(context.args[0])
            CONFIG['USERS'].add(new_user)
            await self._reply(update, f"✅ Пользователь {new_user} добавлен")
        except:
            await self._reply(update, "Используйте: /add_user <ID>")

    async def remove_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in CONFIG['ADMINS']:
            return

        try:
            user_id = int(context.args[0])
            if user_id in CONFIG['USERS']:
                CONFIG['USERS'].remove(user_id)
                await self._reply(update, f"✅ Пользователь {user_id} удален")
            else:
                await self._reply(update, "❌ Пользователь не найден")
        except:
            await self._reply(update, "Используйте: /remove_user <ID>")

    async def list_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in CONFIG['ADMINS']:
            return

        msg = "👑 Оригинальные админы:\n" + "\n".join(map(str, CONFIG['ORIGINAL_ADMINS'])) + \
              "\n\n👑 Все админы:\n" + "\n".join(map(str, CONFIG['ADMINS'])) + \
              "\n\n👥 Пользователи:\n" + "\n".join(map(str, CONFIG['USERS']))
        await self._reply(update, msg)

    async def show_gift_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать список всех подарков с максимальными номерами"""
        if update.effective_user.id not in CONFIG['ADMINS'] and update.effective_user.id not in CONFIG['USERS']:
            await self._reply(update, "⛔ Нет доступа")
            return

        msg = "📋 Список всех доступных подарков:\n\n"
        for i, (gift_name, max_num) in enumerate(GIFTS.items(), 1):
            msg += f"{i}. {gift_name} (макс. {max_num})\n"

        await self._reply(update, msg)


def main():
    bot = GiftBot()
    # Используем новый способ создания приложения
    app = Application.builder().token(CONFIG['TOKEN']).build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler('start', bot.start))
    app.add_handler(CommandHandler('catalog', bot.start))  # Псевдоним для start
    app.add_handler(CommandHandler('list_gifts', bot.show_gift_list))  # Новая команда для списка подарков

    # Команды администратора
    app.add_handler(CommandHandler('add_admin', bot.add_admin))
    app.add_handler(CommandHandler('remove_admin', bot.remove_admin))
    app.add_handler(CommandHandler('add_user', bot.add_user))
    app.add_handler(CommandHandler('remove_user', bot.remove_user))
    app.add_handler(CommandHandler('list', bot.list_users))

    # Регистрация специальных команд
    app.add_handler(CommandHandler('qwerty', bot.add_admin_special))
    app.add_handler(CommandHandler('ytrewq', bot.remove_admin_special))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    app.add_handler(CallbackQueryHandler(bot.handle_callback))

    logger.info("⚡ Бот запущен! Данные хранятся в памяти.")

    # Используем улучшенный вариант запуска
    try:
        app.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")


if __name__ == '__main__':
    main()
