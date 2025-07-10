import random
import string
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from playwright.async_api import async_playwright
import os

TOKEN = os.getenv("TOKEN")

def generate_email():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10)) + "@spiceupdownloader.xyz"

def generate_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

async def create_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = generate_email()
    password = generate_password()
    headers = {"Content-Type": "application/json"}
    payload = {
        "email": email,
        "password": password,
        "username": email.split('@')[0],
        "birthdate": "1999-01-01",
        "gender": "not_given"
    }
    try:
        response = requests.post("https://sso.crunchyroll.com/register", json=payload, headers=headers)
        if response.status_code in [200, 201]:
            login_link = f"https://www.crunchyroll.com/login?email={email}"
            msg = f"""𝗛𝗲𝗿𝗲 𝗶𝘀 𝗬𝗼𝘂𝗿 𝗖𝗿𝘂𝗻𝗰𝗵𝘆𝗥𝗼𝗹𝗹 𝗔𝗰𝗰𝗼𝘂𝗻𝘁

𝗘𝗺𝗮𝗶𝗹: {email}
𝗣𝗮𝘀𝘀: {password}

🔗 [Auto Login Link]({login_link})
"""
        else:
            msg = f"❌ Failed. Status code: {response.status_code}\n{response.text}"
    except Exception as e:
        msg = f"⚠️ Error: {e}"

    await update.message.reply_text(msg, parse_mode="Markdown")

async def crunchyroll_change_email(email, password):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        try:
            await page.goto("https://www.crunchyroll.com/login", timeout=15000)
            await page.fill('input[name="email"]', email)
            await page.click('button:has-text("Next")')
            await page.wait_for_selector('input[name="password"]', timeout=8000)
            await page.fill('input[name="password"]', password)
            await page.click('button:has-text("Log In")')
            await page.wait_for_load_state("networkidle", timeout=8000)

            if "login" in page.url.lower():
                return "❌ Login failed. Check credentials."

            await page.goto("https://www.crunchyroll.com/account/email", timeout=10000)
            content = (await page.content()).lower()
            if "verify your email" in content:
                await page.click("text=Send Verification Email")
                return "✅ Verification email sent. Please verify manually, then run /change again."
            else:
                await page.click("text=Send email change link")
                return "Email Change Link Sent 🤝"
        except Exception as e:
            return f"⚠️ Error occurred: {e}"
        finally:
            await context.close()
            await browser.close()

async def change_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or ':' not in context.args[0]:
        await update.message.reply_text("❌ Use `/change email:pass`")
        return
    email, password = context.args[0].split(':', 1)
    result = await crunchyroll_change_email(email, password)
    await update.message.reply_text(result)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("create", create_account))
app.add_handler(CommandHandler("change", change_command))
app.run_polling()
