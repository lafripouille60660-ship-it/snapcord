import os
import asyncio
from datetime import datetime

import discord
from discord.ext import commands


# ============================================================
# CONFIGURATION
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")

# Salon dans lequel les membres peuvent envoyer des photos
PHOTO_CHANNEL_ID = 1541482461572112545

# Salon privé réservé aux modérateurs
MOD_CHANNEL_ID = 1541482603540906055

# Durée d'affichage de la photo en secondes
PHOTO_LIFETIME = 20


# ============================================================
# BOT
# ============================================================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ============================================================
# CONNEXION
# ============================================================

@bot.event
async def on_ready():
    print(f"✅ Bot connecté : {bot.user}")
    print(f"ID du bot : {bot.user.id}")


# ============================================================
# NOUVEAU MESSAGE
# ============================================================

@bot.event
async def on_message(message):

    # Ignore les messages envoyés par les bots
    if message.author.bot:
        return

    # On ne surveille que le salon photo
    if message.channel.id != PHOTO_CHANNEL_ID:
        await bot.process_commands(message)
        return

    # ========================================================
    # RECHERCHE DES IMAGES
    # ========================================================

    images = []

    for attachment in message.attachments:

        if attachment.content_type:
            if attachment.content_type.startswith("image/"):
                images.append(attachment)

        # Sécurité supplémentaire si Discord ne fournit
        # pas correctement le content_type
        elif attachment.filename.lower().endswith(
            (".png", ".jpg", ".jpeg", ".gif", ".webp")
        ):
            images.append(attachment)

    # ========================================================
    # SI CE N'EST PAS UNE PHOTO
    # ========================================================

    if not images:

        try:
            await message.delete()
        except discord.NotFound:
            pass

        return

    # ========================================================
    # SALON DES MODÉRATEURS
    # ========================================================

    mod_channel = bot.get_channel(MOD_CHANNEL_ID)

    if mod_channel is None:
        print("❌ Salon des modérateurs introuvable.")
        return

    # ========================================================
    # COPIE POUR LES MODÉRATEURS
    # ========================================================

    for image in images:

        try:
            # Téléchargement de la pièce jointe
            file = await image.to_file()

            embed = discord.Embed(
                title="📸 Photo archivée",
                description=(
                    f"**Utilisateur :** {message.author.mention}\n"
                    f"**ID utilisateur :** `{message.author.id}`\n"
                    f"**Salon :** {message.channel.mention}\n"
                    f"**Date :** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
                ),
                timestamp=datetime.now()
            )

            embed.set_footer(
                text="Copie réservée aux modérateurs"
            )

            await mod_channel.send(
                embed=embed,
                file=file
            )

        except Exception as error:
            print(f"❌ Erreur lors de l'archivage : {error}")

    # ========================================================
    # MESSAGE TEMPORAIRE
    # ========================================================

    try:

        notification = await message.channel.send(
            f"📸 {message.author.mention} "
            f"ta photo sera supprimée dans "
            f"**{PHOTO_LIFETIME} secondes**."
        )

    except discord.Forbidden:
        notification = None

    # ========================================================
    # ATTENTE
    # ========================================================

    await asyncio.sleep(PHOTO_LIFETIME)

    # ========================================================
    # SUPPRESSION DE LA PHOTO
    # ========================================================

    try:
        await message.delete()
        print(
            f"🗑️ Photo supprimée : "
            f"{message.author} ({message.author.id})"
        )

    except discord.NotFound:
        print("ℹ️ Le message avait déjà été supprimé.")

    except discord.Forbidden:
        print("❌ Le bot n'a pas la permission de supprimer.")

    # ========================================================
    # SUPPRESSION DE LA NOTIFICATION
    # ========================================================

    if notification:

        try:
            await notification.delete()

        except discord.NotFound:
            pass


# ============================================================
# COMMANDE DE TEST
# ============================================================

@bot.command()
@commands.has_permissions(manage_messages=True)
async def test(ctx):

    await ctx.send(
        "✅ Le système de photos éphémères fonctionne !"
    )


# ============================================================
# LANCEMENT
# ============================================================

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN n'est pas défini.")

bot.run(TOKEN)