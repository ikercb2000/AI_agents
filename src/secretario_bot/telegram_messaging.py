# project modules
from src.secretario_bot.enums import languages, llm_models
from src.secretario_bot.llm_message_generator import LLMMessageGenerator
from apis.asana import AsanaAPI

# packages
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


class SecretarioBot:
    def __init__(self, bot_token: str, llm_model: llm_models):
        """
        Initializes the SecretarioBot with the provided bot token.
        """
        self.llm = LLMMessageGenerator(model=llm_model)
        self.app = ApplicationBuilder().token(bot_token).build()
        self.lang_chosen = None

        # Asana state keys in user_data: 'asana_token', 'asana_project'

        # Command handlers
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help))
        self.app.add_handler(CommandHandler("daily", self.daily))
        self.app.add_handler(CommandHandler("recommend", self.recommend))
        self.app.add_handler(CommandHandler(
            "connect_asana", self.connect_asana))

        # Inline callback for language & commands
        self.app.add_handler(CallbackQueryHandler(self.callback_query))

        # Catch Asana PAT input *after* user sends it
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND,
                           self._catch_asana_inputs),
            group=1
        )

        # Greet on chat start
        self.app.add_handler(
            ChatMemberHandler(self.welcome, ChatMemberHandler.MY_CHAT_MEMBER),
            group=0
        )

    async def welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Fires when user first opens the chat with the bot.
        """
        status = update.my_chat_member.new_chat_member.status
        if status in ("member", "creator"):
            context.user_data["started"] = True
            await self.start(update, context)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Show inline buttons to pick a language.
        """
        keyboard = [
            [
                InlineKeyboardButton("ES – Español", callback_data="lang_es"),
                InlineKeyboardButton("GB – English", callback_data="lang_gb"),
            ]
        ]
        await update.message.reply_text(
            "Hello! I am your personal bot assistant.\n"
            "Please choose a language to continue:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    def _help_markup(self) -> InlineKeyboardMarkup:
        """
        Inline buttons for /help menu.
        """
        keyboard = [
            [
                InlineKeyboardButton("/daily", callback_data="cmd_daily"),
                InlineKeyboardButton(
                    "/recommend", callback_data="cmd_recommend"),
            ],
            [
                InlineKeyboardButton(
                    "/connect_asana", callback_data="cmd_connect_asana"),
                InlineKeyboardButton("/help", callback_data="cmd_help"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    def _help_text(self) -> str:
        if self.lang_chosen == languages.ES:
            return (
                "Usa uno de estos comandos:\n\n"
                "- /daily: Mostrar tus tareas pendientes\n"
                "- /recommend: Recomendaciones de organización\n"
                "- /connect_asana: Vincula tu cuenta Asana\n"
                "- /help: Ver este menú\n"
            )
        else:
            return (
                "Use one of these commands:\n\n"
                "- /daily: Show your pending tasks\n"
                "- /recommend: Organization tips\n"
                "- /connect_asana: Link your Asana account\n"
                "- /help: View this menu\n"
            )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Sends the help text with inline buttons.
        """
        await update.message.reply_text(
            self._help_text(),
            reply_markup=self._help_markup()
        )

    async def connect_asana(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Starts the Asana linking flow by requesting the PAT.
        """
        context.user_data["awaiting_asana_token"] = True
        await update.effective_message.reply_text(
            "Por favor pega tu *Asana Personal Access Token*:",
            parse_mode="Markdown"
        )

    async def _catch_asana_inputs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Catch Asana PAT input after /connect_asana.
        """
        if not context.user_data.get("awaiting_asana_token"):
            return  # ignore anything else
        # consume the PAT
        context.user_data.pop("awaiting_asana_token")
        token = update.message.text.strip()
        context.user_data["asana_token"] = token
        await update.message.reply_text(
            "✅ Token guardado. Ahora usa /help y pulsa /daily."
        )

    async def callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle inline button presses: language and commands.
        """
        query = update.callback_query
        await query.answer()
        data = query.data

        # language selection
        if data == "lang_es":
            self.lang_chosen = languages.ES
            await query.edit_message_text("Idioma configurado a Español.")
            return await query.message.reply_text(
                self._help_text(),
                reply_markup=self._help_markup()
            )
        if data == "lang_gb":
            self.lang_chosen = languages.GB
            await query.edit_message_text("Language set to English.")
            return await query.message.reply_text(
                self._help_text(),
                reply_markup=self._help_markup()
            )

        # re-trigger connect_asana flow
        if data == "cmd_connect_asana":
            return await self.connect_asana(update, context)
        # /daily → Asana logic
        if data == "cmd_daily":
            return await self._handle_daily_asana(update, context)
        if data == "cmd_recommend":
            return await self.recommend(update, context)
        if data == "cmd_help":
            return await query.message.reply_text(
                self._help_text(),
                reply_markup=self._help_markup()
            )

    async def _handle_daily_asana(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Ensure Asana logged in and project chosen, ask if needed, then show tasks.
        """
        token = context.user_data.get("asana_token")
        if not token:
            return await update.effective_message.reply_text(
                "Primero vincula Asana con /connect_asana"
            )

        proj = context.user_data.get("asana_project")
        client = AsanaAPI(token)

        if not proj:
            projs = client.get_projects()
            if not projs:
                return await update.effective_message.reply_text(
                    "No encontré proyectos en tu Asana."
                )
            kb = [
                [InlineKeyboardButton(
                    p["name"], callback_data=f"pick_proj:{p['gid']}")]
                for p in projs[:10]
            ]
            kb.append([InlineKeyboardButton(
                "Cancelar", callback_data="cancel_proj")])
            return await update.effective_message.reply_text(
                "Selecciona el proyecto para tus daily:",
                reply_markup=InlineKeyboardMarkup(kb)
            )

        tasks = client.get_tasks(proj)
        header = "📝 *Tus daily tasks:*" if self.lang_chosen == languages.ES else "📝 *Your daily tasks:*"
        lines = [header, ""]
        for t in tasks[:10]:
            lines.append(f"• {t['name']}")
        return await update.effective_message.reply_text(
            "\n".join(lines), parse_mode="Markdown"
        )

    async def daily(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await self._handle_daily_asana(update, context)

    async def recommend(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Por ahora nada bro. Aldo deja de pajearte."
        )

    def run(self):
        print("Bot running. Waiting for messages...")
        self.app.run_polling()
