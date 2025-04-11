import os
import logging
import openai
import yfinance as yf
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
openai.api_key = OPENAI_API_KEY

user_histories = {}

async def ask_gpt(user_id: int, message: str) -> str:
    history = user_histories.get(user_id, [])
    if not history:
        history.append({
            "role": "system",
            "content": "너는 투자 분석, 뉴스 해석, 시장 동향 설명에 특화 GPT-4 투자 비서야. "
        })

    history.append({"role": "user", "content": message})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=history
        )
        reply = response.choices[0].message['content'].strip()
        history.append({"role": "assistant", "content": reply})
        user_histories[user_id] = history[-10:]  # 최근 대화 10개 유지
        return reply
    except Exception as e:
        logging.error(f"GPT 응답 실패: {e}")
        return "GPT 응답 중 오류가 발생했습니다."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📈 GPT 투자 비서에 오신 것을 환영합니다!

/briefing : 아침 요약
/price TSLA : 실시간 주가 확인
자연어로 질문도 가능합니다!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text
    logging.info(f"📩 사용자({user_id}) 입력: {message}")
    if message.startswith("/price"):
        parts = message.split(" ")
        if len(parts) == 2:
            ticker = parts[1].upper()
            try:
                stock = yf.Ticker(ticker)
                price = stock.history(period="1d")["Close"].iloc[-1]
                await update.message.reply_text(f"{ticker} 현재 주가: ${price:.2f}")
            except Exception as e:
                await update.message.reply_text(f"{ticker} 주가 정보를 가져오는 데 실패했습니다.")
        else:
            await update.message.reply_text("사용법: /price TSLA")
    elif message.startswith("/briefing"):
        await update.message.reply_text("📊 아침 뉴스 요약을 준비 중입니다. (GPT 연결 필요)")
    else:
        reply = await ask_gpt(user_id, message)
        await update.message.reply_text(reply)

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()