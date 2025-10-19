# ...existing code...
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os
import asyncio

# Intentar importar google.generativeai y detectar si falta
try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Leer tokens desde variables de entorno (NO dejar credenciales en el código)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

HAVE_GEMINI = False
if genai and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        HAVE_GEMINI = True
    except Exception as e:
        print(f"AVISO: no se pudo configurar Gemini: {e}")
else:
    if not genai:
        print("ERROR: falta el paquete 'google.generativeai'.")
    if not GEMINI_API_KEY:
        print("ADVERTENCIA: no se ha encontrado GEMINI_API_KEY en las variables de entorno.")

# Función de inicio
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hola! Soy el Asistente Turístico de Cali. ¿En qué puedo ayudarte hoy?")

# Función para generar respuesta (bloqueante) — se ejecutará en un hilo separado
def _generate_response_sync(user_message: str) -> str:
    if not HAVE_GEMINI:
        return ("No está configurado Gemini. Respuesta de fallback:\n\n"
                f"> {user_message}\n\n"
                "Instala y configura GEMINI_API_KEY para obtener respuestas generadas.")
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(f"Responde en tono amable y turístico. Pregunta: {user_message}")
        return getattr(response, "text", str(response))
    except Exception as e:
        return f"(Error al usar Gemini: {e})"

# Función para responder mensajes (async)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.text is None:
        return  # nada que procesar

    user_message = update.message.text.strip()

    try:
        # Ejecutar la llamada bloqueante en un hilo para no bloquear el loop async
        reply_text = await asyncio.to_thread(_generate_response_sync, user_message)
    except Exception as e:
        await update.message.reply_text(f"Ocurrió un error al generar la respuesta: {e}")
        return

    await update.message.reply_text(reply_text)

# Configuración del bot
if not TELEGRAM_TOKEN:
    print("ERROR: no se ha encontrado TELEGRAM_TOKEN en las variables de entorno. Define TELEGRAM_TOKEN antes de ejecutar.")
else:
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot ejecutándose...")
    try:
        app.run_polling()
    except KeyboardInterrupt:
        print("Detenido por el usuario.")
# ...existing code...ffffjjjg