import os
import dotenv
from typing import Final
from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes
)
import logging
import runpod
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate

dotenv.load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Antonella-Telegram-Bot")

TOKEN: Final = os.getenv("TELEGRAM_TOKEN", "")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME", "antonellaa_bot")
RUNPOD_API_KEY: Final =  os.getenv("RUNPOD_API_KEY", "")
ENDPOINT_ID: Final = os.getenv("ENDPOINT_ID", "")

runpod.api_key = RUNPOD_API_KEY
endpoint = runpod.Endpoint(ENDPOINT_ID)

conversation_history = ConversationBufferWindowMemory(k=20, ai_prefix="assistant", human_prefix="user")
template = """<s> [INST] The following is a friendly conversation between an user and a assistant. The AI is talkative and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it does not know. [/INST] </s> 
<s> [INST] current conversation: 
{history} 
user: {input}
assistant: [/INST]"""
CONVERSATION_CHAIN_PROMPT = PromptTemplate(template=template, input_variables=["history", "input"])

# Command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    """First message after the bot is activated
    """
    # pass here the text that you want the bot to say as soon as you tap on `start`
    # or type `/start`
    await update.message.reply_text("Hello! Thanks for chatting with me. I am Antonella")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    """Help to tell the user how the bot works when user uses `/help`
    """
    # pass here the text that you want the bot to say as soon as you type `/help`
    await update.message.reply_text("I am your girlfriend, please type someting so I can respond")

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    """First 
    """
    # pass here the text that you want the bot to say as soon as you type `/custom`
    await update.message.reply_text("This is just a custom command")

# Responses
def handle_response(text: str) -> str: 
    history = conversation_history.load_memory_variables({})
    prompt = CONVERSATION_CHAIN_PROMPT.format(input=text, history=history["history"])
    logger.info(f"PROMPT: {prompt}")

    run_request = endpoint.run({
            "prompt": prompt,
            "max_new_tokens": 500,
            "temperature": 0.9,
            "top_k": 50,
            "top_p": 0.7,
            "repetition_penalty": 1.2,
            "batch_size": 8,
            "stop": ["</s>"]
        })
    outputs = run_request.output()
    logger.info("\nOUTPUT:\n {outputs}")
    conversation_history.save_context({"input": text}, {"output": outputs})
    logger.info(f"Response: {outputs}")

    return outputs

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    # determine if current message is from group chat or private chat
    message_type: str = update.message.chat.type

    # user's message
    text: str = update.message.text

    # get the user's id who send the message in message type (group/private)
    logger.info(f"User ({update.message.chat.id}) in {message_type}: {text}")

    if message_type == "group": 
        # in a group, the bot would just reponds if it was mentioned
        if BOT_USERNAME in text: 
            # we dont want to process the bot name when mentioning the bot
            # jsut the acutal message. For example, "@antonella_bot Hi", we just 
            # take "Hi" to process
            new_text: str = text.replace(BOT_USERNAME, "")
            response: str = handle_response(new_text)
        else: 
            return 
    else: 
        response: str =  handle_response(text)
    
    # track bot's answer in developer's evironment (terminal)
    logger.info(f"BOT: {response}")

    # send the generated response to the telegram, to the user
    await update.message.reply_text(response)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """logging error"""
    logger.error(f"Update {update} caused error {context.error}")

if __name__ == "__main__": 
    logger.info("Starting bot...")
    app = Application.builder().token(TOKEN).build()

    # Command
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("custom", custom_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Error
    app.add_error_handler(error)

    # Polls the bot 
    logger.info("Polling...")
    app.run_polling(poll_interval=3)