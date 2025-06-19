# project modules

from src.secretario_bot.enums import languages, llm_models
from src.secretario_bot.llm_message_generator import LLMMessageGenerator

# packages


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)

# telegram functionalities


class SecretarioBot:
    def __init__(self, bot_token: str, llm_model: llm_models):
        """
        Initializes the SecretarioBot with the provided bot token.
        """

        # Instantiate the bot with the provided token

        self.llm = LLMMessageGenerator(model=llm_model)
        self.app = ApplicationBuilder().token(bot_token).build()
        self.lang_chosen = None

        # Handlers for different commands and messages

        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help))
        self.app.add_handler(CommandHandler("daily", self.daily))
        self.app.add_handler(CommandHandler("recommend", self.recommend))
        self.app.add_handler(CallbackQueryHandler(self.language_selected))
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, self.echo))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /start command, prompting the user to select a language.
        """
        # Create an inline keyboard with language options

        keyboard = [
            [
                InlineKeyboardButton(
                    "ES - Español", callback_data=languages.ES.name),
                InlineKeyboardButton(
                    "GB - English", callback_data=languages.GB.name)
            ]
        ]

        # Create the reply markup with the keyboard

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Hello! I am your personal bot assistant.\n"
            "Please choose a language to continue:",
            reply_markup=reply_markup
        )

    async def language_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the language selection from the inline keyboard.
        """

        # Get the callback query

        query = update.callback_query
        await query.answer()
        lang_code = query.data

        # Set the chosen language based on the callback data

        if lang_code == languages.ES.name:
            self.lang_chosen = languages.ES
            await query.edit_message_text("Idioma configurado a ES Español. Envía el comando /help para ver las opciones disponibles.")

        elif lang_code == languages.GB.name:
            self.lang_chosen = languages.GB
            await query.edit_message_text("Language set to GB English. Send the command /help to see available options.")

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /help command, providing information based on the chosen language.
        """

        if self.lang_chosen == languages.ES:
            await update.message.reply_text(
                "Puedo ayudarte con:\n"
                "- Mostrar tus tareas pendientes en forma de lista -> /daily\n"
                "- Obtener recomendaciones sobre cómo organizarte -> /recommend\n"
                "- Enviarte recordatorios\n\n"
            )
        elif self.lang_chosen == languages.GB:
            await update.message.reply_text(
                "I can help you with:\n"
                "- Show your pending tasks in a list format -> /daily\n"
                "- Get recommendations on how to organize yourself -> /recommend\n"
                "- Send you reminders\n\n"
            )
        else:
            await update.message.reply_text("Please choose a language first with /start.")

    async def daily(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Por ahora nada bro. Jinni es la mejor novia del mundo.")

    async def recommend(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Por ahora nada bro. Aldo deja de pajearte.")

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.text:
            llm_norm_reply = self.llm.generate_message(
                f"Reply to the following message in {'english' if self.lang_chosen == languages.GB else 'spanish'} \
                in a polite way without using very formal or technical terms: '{update.message.text}'"
            )

            llm_help_needed = self.llm.generate_message(
                f"Detect whether there is something in the following message: \
                      '{update.message.text}' that could be identified as a command or a request for the bot\
                        the functions we use are '/daily', which shows a list of pending tasks, and '/recommend', \
                        which provides recommendations on how to organize yourself. If yes, reply me with just a \
                            single word 'True' or 'False' if not."
            )

            llm_help_needed = True if llm_help_needed.lower() == "true" else False

            if llm_help_needed:
                llm_helpful_reply = self.llm.generate_message(
                    f"Given the following message '{update.message.text}', reply in {'english' if self.lang_chosen == languages.GB else 'spanish'} \
                    in a polite way without using very formal or technical terms that you can help the user with his tasks if it provides more information\
                        that is needed.")

                await update.message.reply_text(f"{llm_helpful_reply}")

            else:
                llm_normal_reply = self.llm.generate_message(
                    f"Reply to the following message in {'english' if self.lang_chosen == languages.GB else 'spanish'} \
                    in a polite way without using very formal or technical terms: '{update.message.text}'")

                await update.message.reply_text(f"{llm_normal_reply}")

    def run(self):
        print("Bot running. Waiting for messages...")
        self.app.run_polling()
