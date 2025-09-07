import discord
from discord.ext import commands
import datetime
from collections import defaultdict

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True  # serve per on_message_delete
        intents.members = True   # serve per recuperare i nomi dei membri
        super().__init__(command_prefix="!", intents=intents)
    
    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()

# Dizionario: { user_id: { channel_id: set(message_ids) } }
comandi_usati = defaultdict(lambda: defaultdict(set))

# Evento: ogni volta che un utente usa un comando slash
@bot.event
async def on_app_command_completion(interaction: discord.Interaction, command: discord.app_commands.Command):
    comandi_usati[interaction.user.id][interaction.channel.id].add(interaction.id)

# Evento: se un messaggio viene eliminato
@bot.event
async def on_message_delete(message: discord.Message):
    if message.interaction and message.interaction.user:  
        user_id = message.interaction.user.id
        channel_id = message.channel.id
        if message.interaction.id in comandi_usati[user_id][channel_id]:
            comandi_usati[user_id][channel_id].remove(message.interaction.id)

# COMANDO PING   
@bot.tree.command(name="ping", description="Mostra il ping del bot in millisecondi")
async def pingtest(interaction: discord.Interaction):
    ping_ms = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! Il mio ping è di **{ping_ms}ms**.")

# COMANDO CARICHI CIBO
@bot.tree.command(name="caricocibo", description="Registra un nuovo carico di cibo.")
async def caricocibo(interaction: discord.Interaction, quantita: str, luogo: str, prezzo: str):
    embed = discord.Embed(
        title="🛒 Carico Effettuato",
        description="Un nuovo carico di cibo è stato registrato.",
        color=discord.Color.orange(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="📦 Quantità:", value=f"**{quantita}**", inline=False)
    embed.add_field(name="📍 Luogo:", value=f"**{luogo}**", inline=False)
    embed.add_field(name="💵 Prezzo:", value=f"**{prezzo}**", inline=False)
    embed.set_footer(text=f"📌 Registrato da {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

# COMANDO CARICO KIT
@bot.tree.command(name="caricokit", description="Registra un nuovo carico di kit riparazione e pulizia.")
async def caricokit(interaction: discord.Interaction, quantita: str, prezzo: str):
    embed = discord.Embed(
        title="🛒 Carico Effettuato",
        description="Un nuovo carico di kit riparazione e pulizia è stato registrato.",
        color=discord.Color.orange(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="📦 Quantità:", value=f"**{quantita}**", inline=False)
    embed.add_field(name="💵 Prezzo:", value=f"**{prezzo}**", inline=False)
    embed.set_footer(text=f"📌 Registrato da {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

# COMANDO VEICOLO
@bot.tree.command(
    name="veicolo", 
    description="Registra l'acquisto di un veicolo con nome, cognome, targa, foto veicolo e foto patente."
)
async def veicolo(
    interaction: discord.Interaction, 
    nome: str, 
    cognome: str, 
    targa: str, 
    foto_veicolo: discord.Attachment, 
    foto_patente: discord.Attachment
):
    embed = discord.Embed(
        title="🚗 Certificato di Acquisto Veicolo",
        color=discord.Color.green(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="🏷 Nome e Cognome:", value=f"**{nome} {cognome}**", inline=False)
    embed.add_field(name="🔖 Targa:", value=f"**{targa.upper()}**", inline=False)
    embed.add_field(name="📅 Data di Acquisto:", value=datetime.datetime.utcnow().strftime('`%d-%m-%Y`'), inline=False)
    embed.set_thumbnail(url=foto_patente.url)
    embed.set_image(url=foto_veicolo.url)
    embed.set_footer(text=f"📌 Registrato da {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

# COMANDO CONTA COMANDI
@bot.tree.command(name="contacomandi", description="Conta quante volte un utente ha usato i comandi del bot.")
async def conta_comandi(interaction: discord.Interaction, membro: discord.Member, canale: discord.TextChannel = None):
    if canale is None:
        totale = sum(len(ids) for ids in comandi_usati[membro.id].values())
        await interaction.response.send_message(
            f"⚡ L'utente **{membro.display_name}** ha usato i comandi del bot **{totale} volte** in totale."
        )
    else:
        count = len(comandi_usati[membro.id][canale.id])
        await interaction.response.send_message(
            f"⚡ L'utente **{membro.display_name}** ha usato i comandi del bot **{count} volte** nel canale {canale.mention}."
        )

# NUOVO COMANDO TOP (con canale opzionale)
@bot.tree.command(name="top", description="Mostra la classifica degli utenti che hanno usato più comandi.")
async def top(interaction: discord.Interaction, canale: discord.TextChannel = None):
    ranking = []

    if canale is None:
        # conteggio totale
        for user_id, channels in comandi_usati.items():
            total = sum(len(ids) for ids in channels.values())
            if total > 0:
                ranking.append((user_id, total))
    else:
        # conteggio solo per il canale selezionato
        for user_id, channels in comandi_usati.items():
            total = len(channels[canale.id])
            if total > 0:
                ranking.append((user_id, total))

    if not ranking:
        await interaction.response.send_message("📊 Nessun comando usato finora.")
        return

    # Ordiniamo dal più alto al più basso
    ranking.sort(key=lambda x: x[1], reverse=True)

    # Creiamo l'embed con la classifica
    embed = discord.Embed(
        title="🏆 Classifica Comandi Usati",
        color=discord.Color.gold(),
        timestamp=datetime.datetime.utcnow()
    )

    description = ""
    for position, (user_id, total) in enumerate(ranking, start=1):
        member = interaction.guild.get_member(user_id)
        name = member.display_name if member else f"Utente {user_id}"
        description += f"**{position}. {name}** — {total} comandi\n"

    embed.description = description
    await interaction.response.send_message(embed=embed)

# Avvia il bot 
bot.run("MTM3NTQ2MTI5ODE1Mzk4NDA0Mw.G_HPN1.R-I5L2qk-HStdsWhD1Zq5FsR0cd3ORoYYuojNc")

