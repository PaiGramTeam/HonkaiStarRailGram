from telegram import Update, Chat, User
from telegram.ext import CallbackContext, ChatMemberHandler

from core.admin.services import BotAdminService
from core.plugin import Plugin, handler
from utils.chatmember import extract_status_change
from utils.decorators.error import error_callable
from utils.log import logger


class ChatMember(Plugin):
    def __init__(
        self,
        bot_admin_service: BotAdminService = None
    ):
        self.bot_admin_service = bot_admin_service

    @handler.chat_member(chat_member_types=ChatMemberHandler.MY_CHAT_MEMBER, block=False)
    @error_callable
    async def track_chats(self, update: Update, context: CallbackContext) -> None:
        result = extract_status_change(update.my_chat_member)
        if result is None:
            return
        was_member, is_member = result
        user = update.effective_user
        chat = update.effective_chat
        if chat.type == Chat.PRIVATE:
            if not was_member and is_member:
                logger.info("用户 %s[%s] 启用了机器人", user.full_name, user.id)
            elif was_member and not is_member:
                logger.info("用户 %s[%s] 屏蔽了机器人", user.full_name, user.id)
        elif chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
            if not was_member and is_member:
                logger.info("用户 %s[%s] 邀请BOT进入群 %s[%s]", user.full_name, user.id, chat.title, chat.id)
                await self.greet(user, chat, context)
            elif was_member and not is_member:
                logger.info("用户 %s[%s] 从 %s[%s] 群移除Bot", user.full_name, user.id, chat.title, chat.id)
        else:
            if not was_member and is_member:
                logger.info("用户 %s[%s] 邀请BOT进入频道 %s[%s]", user.full_name, user.id, chat.title, chat.id)
            elif was_member and not is_member:
                logger.info("用户 %s[%s] 从 %s[%s] 频道移除Bot", user.full_name, user.id, chat.title, chat.id)

    async def greet(self, user: User, chat: Chat, context: CallbackContext) -> None:
        quit_status = True
        try:
            admin_list = await self.bot_admin_service.get_admin_list()
            if user.id in admin_list:
                quit_status = False
            else:
                logger.warning("不是管理员邀请！退出群聊")
        except Exception as exc:  # pylint: disable=W0703
            logger.error("获取信息出现错误", exc_info=exc)
        if quit_status:
            await context.bot.send_message(chat.id, "不是管理员的邀请！")
            await context.bot.leave_chat(chat.id)
