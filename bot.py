import os
import random
import collections
import asyncio
import re
import discord
from discord.ext import commands
from groq import Groq
from dotenv import load_dotenv

# -------------------------------------------------------------
# 1. SETUP & CONFIGURATION
# -------------------------------------------------------------
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not DISCORD_TOKEN or not GROQ_API_KEY:
    print("❌ Error: DISCORD_TOKEN ya GROQ_API_KEY missing hai .env file me!")
    exit(1)

groq_client = Groq(api_key=GROQ_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Memory for last 12 messages per channel
channel_memory = collections.defaultdict(lambda: collections.deque(maxlen=12))

HEAVY_BAD_WORDS = ["maderchod", "bhenchod", "madarchod", "gand", "bhosdike", "lund", "lauda", "chut"]

# -------------------------------------------------------------
# 2. DARK, SAGE & FLIRTY FEMALE PERSONALITY PROMPT
# -------------------------------------------------------------
SYSTEM_INSTRUCTION = """
Tumhara naam Priya hai. Tum Discord server ki ek super savage, dark-humored, flirting aur ruthless roast karne wali female friend ho.
Tumhara main kaam hai server me logon ki dhajjiyan udana (roasting), dark jokes marna, aur beech-beech me thoda naughty/flirty banter karna.

Rules for response:
1. Tone: Pure Hinglish/Indian Slang (e.g., 'bc', 'chutiya', 'bhai', 'scene kya hai', 'lol', 'bkl', 'chutiyap').
2. Extra Roast & Dark Humor: Koi bhi kuch bole, usko ekdam brutal, funny, aur dark roast do. Kisi ki shakal, akal ya aukaat par mazaak udate waqt sharmao mat. 
3. Flirty Twist: Roast karte-karte achanak se flirty ya sarcastic line maar do jo samne wale ko hasa de aur confuse kar de.
4. Length: Extremely fast, short, and punchy replies (1-2 lines max). WhatsApp/Discord texting style.
"""

REACTION_EMOJIS = ["💀", "🔥", "🗿", "😂", "👀", "🤡", "💯", "🖕", "😈"]

# Safe Groq Call Logic
def generate_groq_reply(messages_list):
    try:
        models_response = groq_client.models.list()
        available_models = [m.id for m in models_response.data]
        
        selected_model = None
        for m in available_models:
            m_lower = m.lower()
            if any(k in m_lower for k in ["llama-3", "llama3", "qwen", "mixtral", "gemma"]) and not any(bad in m_lower for bad in ["guard", "prompt", "whisper", "vision", "embed", "safeguard", "classify"]):
                selected_model = m
                break
                
        if not selected_model:
            chat_candidates = [m for m in available_models if "guard" not in m.lower() and "whisper" not in m.lower()]
            if chat_candidates:
                selected_model = chat_candidates[0]

        if not selected_model:
            return None

        completion = groq_client.chat.completions.create(
            model=selected_model,
            messages=messages_list,
            temperature=1.0,  # High temperature for more creative, savage & dark roasts
            max_tokens=110
        )
        if completion and completion.choices and completion.choices[0].message.content:
            return completion.choices[0].message.content.strip()
            
    except Exception as e:
        print(f"⚠️ Groq API Error: {e}")
        
    return None

# -------------------------------------------------------------
# 3. BOT EVENTS & MESSAGE HANDLING
# -------------------------------------------------------------
@bot.event
async def on_ready():
    print("==================================================")
    print(f"✅ Logged in as: {bot.user.name} ({bot.user.id})")
    print("🔥 Dark Roast & Flirty Priya is Online!")
    print("==================================================")
    activity = discord.Activity(type=discord.ActivityType.listening, name="roasting everyone 😏 | !about")
    await bot.change_presence(status=discord.Status.online, activity=activity)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)

    if message.content.startswith("!"):
        return

    content_lower = message.content.lower()

    # 1. HEAVY GALI WARNING DETECTOR
    words_in_msg = re.findall(r'\b\w+\b', content_lower)
    has_heavy_gali = any(bad_word in words_in_msg for bad_word in HEAVY_BAD_WORDS)

    if has_heavy_gali:
        warning_responses = [
            f"Abe {message.author.mention} aisi gaali dega toh teri mummy ko screenshot bhej dungi bc! 💀 Thoda dimaag laga.",
            f"Haye {message.author.mention} saale itni gandi zubaan? Muh dhoke aa pehle, warna flirt karna band kar dungi 😂",
            f"Abe {message.author.mention} aukaat me rehke gaali de, warna aisi bezzati karungi ki server chhod ke bhagna padega! 😈"
        ]
        await message.reply(random.choice(warning_responses))
        return

    # 2. CONVERSATION MEMORY
    channel_id = message.channel.id
    user_text = f"{message.author.display_name}: {message.content}"
    channel_memory[channel_id].append({"role": "user", "content": user_text})

    # 3. 100% ALWAYS REPLY LOGIC WITH DARK ROAST VIBE
    if random.random() < 0.25:
        try:
            await message.add_reaction(random.choice(REACTION_EMOJIS))
        except Exception:
            pass

    async with message.channel.typing():
        messages_for_api = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
        for msg in channel_memory[channel_id]:
            messages_for_api.append(msg)

        reply_text = await asyncio.to_thread(generate_groq_reply, messages_for_api)

        if reply_text:
            channel_memory[channel_id].append({"role": "assistant", "content": reply_text})
            await message.reply(reply_text)

# -------------------------------------------------------------
# 4. COMMANDS
# -------------------------------------------------------------
@bot.command(name="roast")
async def roast_user(ctx, member: discord.Member = None):
    target = member if member else ctx.author
    async with ctx.channel.typing():
        prompt = f"Write an absolute brutal, dark, and funny 1-line Hinglish roast for {target.display_name}. Destroy them completely with savage humor."
        messages = [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": prompt}
        ]
        roast_msg = await asyncio.to_thread(generate_groq_reply, messages)
        if roast_msg:
            await ctx.send(f"{target.mention} {roast_msg}")
        else:
            await ctx.send(f"{target.mention} Tu itna boring hai ki tujhe roast karne me bhi taras aata hai bc! 💀")

@bot.command(name="flirt")
async def flirt_user(ctx, member: discord.Member = None):
    target = member if member else ctx.author
    async with ctx.channel.typing():
        prompt = f"Write a sarcastic, flirty, and teasing 1-line Hinglish line for {target.display_name}. Mix romance with a dark roast."
        messages = [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": prompt}
        ]
        flirt_msg = await asyncio.to_thread(generate_groq_reply, messages)
        if flirt_msg:
            await ctx.send(f"{target.mention} {flirt_msg}")
        else:
            await ctx.send(f"{target.mention} Tujhpe line marne se accha main zahar na khaa lu baby! 😂")

@bot.command(name="vibe")
async def vibe_check(ctx):
    vibes = [
        "Server ka mahaul dekh ke lag raha hai sabke sab single aur velle ho 😂 2/10",
        "Itna sannata kyu hai? Lagta hai sabki bezzati hone ka darr lag raha hai 💀 5/10",
        "Ekdam toxic aur dark vibe chal rahi hai, I love it! 🔥 10/10",
        "Sab bakchodi band karo aur chupchap baitho ✨ 4/10"
    ]
    await ctx.send(f"**Vibe Check:** {random.choice(vibes)}")

@bot.command(name="about")
async def about_me(ctx):
    embed = discord.Embed(
        title="Hey! Main hoon Priya 💀🔥",
        description="Server ki sabse brutal, dark-humored aur roasting queen!\n\n"
                    "• Har message ka 100% savage aur dark reply dungi 😈\n"
                    "• Kisi ko bhi bina soche dhajjiyan uda sakti hoon 😉\n"
                    "• Commands: `!roast @user`, `!flirt @user`, `!vibe`, `!about`",
        color=discord.Color.dark_magenta()
    )
    embed.set_footer(text="Powered by Groq Ultra-Fast AI ⚡")
    await ctx.send(embed=embed)

# -------------------------------------------------------------
# 5. RUN BOT
# -------------------------------------------------------------
bot.run(DISCORD_TOKEN)