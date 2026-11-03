import os
import time
import psutil
import GPUtil
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8443256748:AAH013KTg8ymkCPHRxKMaWJmV5GBhXO-16A"
OWNER_ID = 5629423524

was_running = False

def allowed(update):
    return update.effective_user.id == OWNER_ID

def find_process():
    for p in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmd = " ".join(p.info['cmdline']) if p.info['cmdline'] else ""
            if "process.py" in cmd:
                return p
        except:
            pass
    return None

async def send_owner(app, msg):
    await app.bot.send_message(chat_id=OWNER_ID, text=msg)

def monitor_loop(app):
    global was_running

    while True:
        try:
            proc = find_process()
            running = proc is not None

            if was_running and not running:
                app.create_task(send_owner(app, "⚠ process.py crashed or stopped!"))

            was_running = running

            # RAM Alert
            ram = psutil.virtual_memory().percent
            if ram > 92:
                app.create_task(send_owner(app, f"⚠ High RAM usage: {ram}%"))

            # GPU Temp Alert
            try:
                g = GPUtil.getGPUs()[0]
                if g.temperature > 88:
                    app.create_task(send_owner(app, f"⚠ GPU temp high: {g.temperature}C"))
            except:
                pass

        except:
            pass

        time.sleep(60)

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update): return
    await update.message.reply_text("Laptop online.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update): return

    proc = find_process()
    running = "Yes" if proc else "No"

    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent

    gpu = "Not found"
    try:
        g = GPUtil.getGPUs()[0]
        gpu = f"{g.name} | {g.load*100:.0f}% load | {g.temperature}C"
    except:
        pass

    txt = f"""process.py Running: {running}
CPU: {cpu}%
RAM: {ram}%
GPU: {gpu}
"""
    await update.message.reply_text(txt)

async def temp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update): return
    try:
        g = GPUtil.getGPUs()[0]
        await update.message.reply_text(f"GPU Temp: {g.temperature}C")
    except:
        await update.message.reply_text("Temp unavailable")

async def disk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update): return
    d = psutil.disk_usage("C:\\")
    await update.message.reply_text(f"Disk Used: {d.percent}%\nFree: {d.free//(1024**3)} GB")

async def uptime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update): return
    sec = time.time() - psutil.boot_time()
    hrs = int(sec // 3600)
    await update.message.reply_text(f"Uptime: {hrs} hours")

async def battery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update): return
    b = psutil.sensors_battery()
    if b:
        await update.message.reply_text(f"Battery: {b.percent}% Charging: {b.power_plugged}")
    else:
        await update.message.reply_text("Battery not found")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update): return
    proc = find_process()
    if proc:
        proc.terminate()
        await update.message.reply_text("Stopped process.py")
    else:
        await update.message.reply_text("Not running")

async def shutdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update): return
    await update.message.reply_text("Shutting down...")
    os.system("shutdown /s /t 5")

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update): return
    await update.message.reply_text("Restarting...")
    os.system("shutdown /r /t 5")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("ping", ping))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("temp", temp))
app.add_handler(CommandHandler("disk", disk))
app.add_handler(CommandHandler("uptime", uptime))
app.add_handler(CommandHandler("battery", battery))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(CommandHandler("shutdown", shutdown))
app.add_handler(CommandHandler("restart", restart))

threading.Thread(target=monitor_loop, args=(app,), daemon=True).start()

print("Bot started...")
app.run_polling()