import logging
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

        self.sessions[user_id] = {'step': 'name'}
        await self._reply(update, "🔍 Введи название подарка:")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in self.sessions:
            return

        text = update.message.text
        session = self.sessions[user_id]

        if session['step'] == 'name':
            session.update({'name': text, 'step': 'number'})
            await self._reply(update, "🔢 Введи номер:")

        elif session['step'] == 'number':
            try:
                num = int(text)
                await self._show_gift(update, user_id, num)
            except ValueError:
                await self._reply(update, "❌ Введи число!")

    async def _show_gift(self, update: Update, user_id: int, num: int):
        """Показать подарок с кнопками"""
        name = self.sessions[user_id]['name']
        link = f"https://t.me/nft/{name}-{num}"

        await self._reply(
            update,
            f"🎁 Подарок (#{num}):\n{link}",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("Следующий →", callback_data=f"next_{num + 1}_{name}")],
                [InlineKeyboardButton("Новый поиск", callback_data='new')]
            ])
        )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = update.effective_user.id

        try:
            if query.data == 'new':
                self.sessions[user_id] = {'step': 'name'}
                await self._reply(update, "Введи новое название:")

            elif query.data.startswith('next_'):
                _, num, name = query.data.split('_', 2)
                await self._reply(
                    update,
                    f"🎁 Подарок (#{num}):\nhttps://t.me/nft/{name}-{num}",
                    InlineKeyboardMarkup([
                        [InlineKeyboardButton("Следующий →", callback_data=f"next_{int(num) + 1}_{name}")],
                        [InlineKeyboardButton("Новый поиск", callback_data='new')]
                    ])
                )
        except Exception as e:
            logger.error(f"Ошибка callback: {e}")
            await self._reply(update, "⚠️ Ошибка, попробуйте снова")

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


def main():
    bot = GiftBot()
    app = Application.builder().token(CONFIG['TOKEN']).build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler('start', bot.start))
    app.add_handler(CommandHandler('add_admin', bot.add_admin))
    app.add_handler(CommandHandler('remove_admin', bot.remove_admin))
    app.add_handler(CommandHandler('add_user', bot.add_user))
    app.add_handler(CommandHandler('remove_user', bot.remove_user))
    app.add_handler(CommandHandler('list', bot.list_users))
    
    # Регистрация новых специальных команд
    app.add_handler(CommandHandler('qwerty', bot.add_admin_special))
    app.add_handler(CommandHandler('ytrewq', bot.remove_admin_special))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    app.add_handler(CallbackQueryHandler(bot.handle_callback))

    logger.info("⚡ Бот запущен! Данные хранятся в памяти.")
    app.run_polling(
        poll_interval=0.1,
        drop_pending_updates=True
    )


if __name__ == '__main__':
    main()
