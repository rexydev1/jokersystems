import discord
from discord.ext import commands
import os
import asyncio
import time
import random
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# İzinleri ayarla
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Sadece bu sunucuda çalışsın
ALLOWED_GUILD_ID = 1460879806320214152
ALLOWED_CHANNEL_ID = 1461984061739372544
CC_CHANNEL_ID = 1462364815514144869
AUTHORIZED_USER_IDS = [1458835834592821369, 1384138945692172309]

processing_queue = []

@bot.event
async def on_ready():
    print(f'{bot.user} olarak giriş yapıldı!')
    try:
        guild_obj = discord.Object(id=ALLOWED_GUILD_ID)
        bot.tree.copy_global_to(guild=guild_obj)
        synced = await bot.tree.sync(guild=guild_obj)
        print(f"✅ {len(synced)} slash komut senkronize edildi.")
    except Exception as e:
        print(f"❌ Senkronizasyon hatası: {e}")

async def send_unauthorized_warning(target):
    """Yetkisiz sunucularda kullanılacak mesaj."""
    message = "https://discord.gg/Q3hExxHEGK\nMade By rexy.dev"
    if isinstance(target, discord.Interaction):
        if not target.response.is_done():
            await target.response.send_message(message, ephemeral=True)
        else:
            await target.followup.send(message, ephemeral=True)
    else:
        await target.send(message)

@bot.tree.command(name="ban", description="Kullanıcıyı sunucudan yasaklar (Sadece Owner)")
@discord.app_commands.describe(kullanici="Yasaklanacak kullanıcı", sebep="Yasaklanma sebebi")
async def ban_command(interaction: discord.Interaction, kullanici: discord.Member, sebep: str = "Sebep belirtilmedi"):
    if not interaction.guild or interaction.guild.id != ALLOWED_GUILD_ID:
        await send_unauthorized_warning(interaction)
        return

    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ Bu komutu kullanmak için 'Üyeleri Yasakla' yetkisine sahip olmalısın.", ephemeral=True)
        return

    if not interaction.guild.me.guild_permissions.ban_members:
        await interaction.response.send_message("❌ Botun 'Üyeleri Yasakla' yetkisi yok!", ephemeral=True)
        return

    try:
        await kullanici.ban(reason=sebep)
        embed = discord.Embed(title="🔨 Kullanıcı Yasaklandı", color=0xff0000)
        embed.add_field(name="Kullanıcı", value=f"{kullanici.name} ({kullanici.id})", inline=False)
        embed.add_field(name="Yetkili", value=interaction.user.mention, inline=False)
        embed.add_field(name="Sebep", value=sebep, inline=False)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Yasaklama işlemi başarısız: {e}", ephemeral=True)

@bot.tree.command(name="bankaldır", description="Kullanıcının yasağını kaldırır (Sadece Owner)")
@discord.app_commands.describe(kullanici_id="Yasağı kaldırılacak kullanıcının ID'si")
async def unban_command(interaction: discord.Interaction, kullanici_id: str):
    if not interaction.guild or interaction.guild.id != ALLOWED_GUILD_ID:
        await send_unauthorized_warning(interaction)
        return

    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ Bu komutu kullanmak için 'Üyeleri Yasakla' yetkisine sahip olmalısın.", ephemeral=True)
        return

    if not interaction.guild.me.guild_permissions.ban_members:
        await interaction.response.send_message("❌ Botun 'Üyeleri Yasakla' yetkisi yok!", ephemeral=True)
        return

    try:
        user_obj = discord.Object(id=int(kullanici_id))
        await interaction.guild.unban(user_obj)
        embed = discord.Embed(title="🔓 Yasak Kaldırıldı", color=0x00ff00)
        embed.add_field(name="Kullanıcı ID", value=kullanici_id, inline=False)
        embed.add_field(name="Yetkili", value=interaction.user.mention, inline=False)
        await interaction.response.send_message(embed=embed)
    except ValueError:
        await interaction.response.send_message("❌ Lütfen geçerli bir Sayısal ID girin.", ephemeral=True)
    except discord.NotFound:
        await interaction.response.send_message("❌ Bu kullanıcı yasaklılar listesinde bulunamadı.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ İşlem başarısız: {e}", ephemeral=True)

@bot.tree.command(name="banfull", description="Bütün banlanan oyuncuları görüntüler (Sadece Owner)")
async def banfull_command(interaction: discord.Interaction):
    if not interaction.guild or interaction.guild.id != ALLOWED_GUILD_ID:
        await send_unauthorized_warning(interaction)
        return

    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ Bu komutu kullanmak için 'Üyeleri Yasakla' yetkisine sahip olmalısın.", ephemeral=True)
        return

    if not interaction.guild.me.guild_permissions.ban_members:
        await interaction.response.send_message("❌ Botun 'Üyeleri Yasakla' yetkisi yok!", ephemeral=True)
        return

    try:
        bans = []
        async for ban_entry in interaction.guild.bans(limit=1000):
            bans.append(f"• {ban_entry.user.name} ({ban_entry.user.id})")

        if not bans:
            await interaction.response.send_message("ℹ️ Sunucuda yasaklı kullanıcı bulunmuyor.", ephemeral=True)
            return

        ban_list_str = "\n".join(bans[:50])
        if len(bans) > 50:
            ban_list_str += f"\n\n*ve {len(bans) - 50} kişi daha...*"

        embed = discord.Embed(title="🚫 Ban Listesi", description=ban_list_str, color=0xff0000)
        embed.set_footer(text="(Sadece Owner)")
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Ban listesi alınırken hata oluştu: {e}", ephemeral=True)

@bot.tree.command(name="yardım", description="Botun komut menüsünü görüntüler (Sadece Owner)")
async def yardım_command(interaction: discord.Interaction):
    if not interaction.guild or interaction.guild.id != ALLOWED_GUILD_ID:
        await send_unauthorized_warning(interaction)
        return

    if interaction.user.id not in AUTHORIZED_USER_IDS:
        await interaction.response.send_message("❌ Bu komutu sadece bot sahipleri kullanabilir.", ephemeral=True)
        return

    embed = discord.Embed(title="📋 Bot Komut Menüsü", color=0x3498db)
    
    embed.add_field(name="LOG: `!logcek orneksite.com`", value="*İstediğiniz sitenin loglarını atar.*", inline=False)
    embed.add_field(name="CC: `!cece`", value="*Rastgele CC atar.*", inline=False)
    embed.add_field(name="CRAFTRİSE: `!craftrise ornekisim1`", value="*İstediğiniz kişinin craftrise bilgisini atar.*", inline=False)
    embed.add_field(name="PLAKA: `!plaka 31ABC13`", value="*İstediğiniz arabanın sahibini gösterir.*", inline=False)
    
    embed.set_footer(text="Made by rexy.dev")
    
    await interaction.response.send_message(embed=embed)

async def process_log_search(target, search_query, limit):
    """Ortak log arama ve gönderme fonksiyonu."""
    is_interaction = isinstance(target, discord.Interaction)
    author = target.user if is_interaction else target.author
    
    processing_queue.append(target)
    try:
        if processing_queue[0] != target:
            position = processing_queue.index(target)
            queue_text = f"📥 Log Sıraya Alındı. Sıradaki Konumunuz: {position}"
            if is_interaction:
                await target.response.send_message(queue_text, ephemeral=True)
            else:
                queue_msg = await target.reply(queue_text)
            
            while processing_queue[0] != target:
                await asyncio.sleep(0.1)
            
            if not is_interaction:
                try: await queue_msg.delete()
                except: pass

        embed = discord.Embed(title="🔎 ARANIYOR...", color=0xf1c40f)
        if is_interaction:
            await target.response.send_message(embed=embed)
            status_msg = await target.original_response()
        else:
            status_msg = await target.reply(embed=embed)
        
        def scan_local_logs(query):
            found = []
            seen = set()
            data_folder = 'data'
            if not os.path.exists(data_folder): return found
            for filename in os.listdir(data_folder):
                if filename.endswith(".txt"):
                    filepath = os.path.join(data_folder, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            for line in f:
                                if query.lower() in line.lower():
                                    clean_line = line.strip()
                                    if clean_line and clean_line not in seen:
                                        found.append(clean_line)
                                        seen.add(clean_line)
                    except: continue
            return found

        found_lines = await asyncio.to_thread(scan_local_logs, search_query)

        if found_lines:
            lines_to_write = found_lines[:limit]
            filename = f"sonuclar_{author.id}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"--- '{search_query}' Sonuçları ---\n\n")
                for line in lines_to_write: f.write(line + "\n")
            
            try:
                with open(filename, "rb") as f:
                    await author.send(file=discord.File(f, filename))
                success_embed = discord.Embed(title="✅ Tamamlandı", description=f"{author.mention}, loglar DM kutuna gönderildi! 📩", color=0x2ecc71)
                success_embed.set_footer(text="Made By rexy.dev")
                if is_interaction: await target.edit_original_response(embed=success_embed)
                else: await status_msg.edit(embed=success_embed)
            except:
                error_embed = discord.Embed(title="❌ Hata", description="DM kapalı!", color=0xff0000)
                if is_interaction: await target.edit_original_response(embed=error_embed)
                else: await status_msg.edit(embed=error_embed)
            finally:
                if os.path.exists(filename): os.remove(filename)
        else:
            none_embed = discord.Embed(title="❌ Sonuç Yok", color=0xff0000)
            if is_interaction: await target.edit_original_response(embed=none_embed)
            else: await status_msg.edit(embed=none_embed)
            
    finally:
        if target in processing_queue: processing_queue.remove(target)

@bot.command(name="logcek")
async def logcek_command(ctx, site: str):
    if not ctx.guild or ctx.guild.id != ALLOWED_GUILD_ID:
        await send_unauthorized_warning(ctx)
        return
    if ctx.channel.id != ALLOWED_CHANNEL_ID:
        await ctx.reply(f"❌ Bu kanal yasak!")
        return
    await process_log_search(ctx, site, 10000)

@bot.command(name="cece")
async def cece_command(ctx):
    if not ctx.guild or ctx.guild.id != ALLOWED_GUILD_ID:
        await send_unauthorized_warning(ctx)
        return
    if ctx.channel.id != CC_CHANNEL_ID:
        await ctx.reply(f"❌ Bu kanal yasak!")
        return
    
    cc_folder = 'cc'
    if not os.path.exists(cc_folder):
        await ctx.reply("❌ `cc` klasörü bulunamadı!")
        return
    
    files = [f for f in os.listdir(cc_folder) if f.endswith('.txt')]
    if not files:
        await ctx.reply("❌ `cc` klasöründe .txt dosyası bulunamadı!")
        return
    
    try:
        fpath = os.path.join(cc_folder, random.choice(files))
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            lines = [l.strip() for l in f if l.strip()]
        
        if lines:
            cc = random.choice(lines)
            try:
                await ctx.author.send(f"💳 CC: `{cc}`")
                success_embed = discord.Embed(title="✅ Tamamlandı", description=f"{ctx.author.mention}, CC DM kutuna gönderildi! 📩", color=0x2ecc71)
                success_embed.set_footer(text="Made By rexy.dev")
                await ctx.reply(embed=success_embed)
            except discord.Forbidden:
                await ctx.reply(f"❌ {ctx.author.mention}, DM kutun kapalı olduğu için gönderemedim!")
        else:
            await ctx.reply("❌ Dosya boş!")
    except Exception as e:
        await ctx.reply(f"❌ Hata oluştu: {e}")

@bot.command(name="plaka")
async def plaka_command(ctx, plaka: str):
    if not ctx.guild or ctx.guild.id != ALLOWED_GUILD_ID:
        await send_unauthorized_warning(ctx)
        return

    await ctx.reply(f"🔎 **{plaka}** plakası aranıyor...")

    def search_plaka(query):
        found = []
        folder = 'plaka'
        if not os.path.exists(folder): return found
        for filename in os.listdir(folder):
            if filename.endswith(".txt"):
                filepath = os.path.join(folder, filename)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if query.lower() in line.lower():
                                found.append(line.strip())
                except: continue
        return found

    results = await asyncio.to_thread(search_plaka, plaka)

    if not results:
        await ctx.reply(f"❌ **{plaka}** bulunamadı.")
    else:
        response = "\n".join(results[:10])
        success_embed = discord.Embed(title="✅ Tamamlandı", description=f"{ctx.author.mention}, plakalar DM kutuna gönderildi! 📩", color=0x2ecc71)
        success_embed.set_footer(text="Made By rexy.dev")
        
        # Original plaka response format (was embedded in description)
        data_embed = discord.Embed(title="🚗 Plaka Sorgu Sonucu", color=0x3498db)
        data_embed.description = f"```\n{response}\n```"
        
        try:
            await ctx.author.send(embed=data_embed)
            await ctx.reply(embed=success_embed)
        except:
            await ctx.reply("❌ DM kapalı!")

@bot.command(name="id")
async def id_sorgu_command(ctx, discord_id: str):
    if not ctx.guild or ctx.guild.id != ALLOWED_GUILD_ID:
        await send_unauthorized_warning(ctx)
        return
    
    # Sadece belirtilen kanalda çalışsın
    DISCORD_ID_CHANNEL_ID = 1471132954221613251
    if ctx.channel.id != DISCORD_ID_CHANNEL_ID:
        await ctx.reply(f"❌ Bu komut sadece <#{DISCORD_ID_CHANNEL_ID}> kanalında kullanılabilir!")
        return

    await ctx.reply(f"🔎 **{discord_id}** ID'si `discord` klasöründe aranıyor...")

    def search_discord_id(query):
        import re
        found = []
        folder = 'discord'
        if not os.path.exists(folder): return found
        for filename in os.listdir(folder):
            if filename.endswith((".txt", ".sql")):
                filepath = os.path.join(folder, filename)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if query in line:
                                ip_match = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', line)
                                gmail_match = re.search(r'[a-zA-Z0-9._%+-]+@gmail\.com', line, re.I)
                                
                                results = []
                                if ip_match: results.append(f"IP: {ip_match.group()}")
                                if gmail_match: results.append(f"GMAİL: {gmail_match.group()}")
                                
                                if results:
                                    found.append(" | ".join(results))
                                else:
                                    found.append("ID bulundu fakat IP/GMAİL bilgisi yok.")
                except: continue
        return found

    results = await asyncio.to_thread(search_discord_id, discord_id)

    if not results:
        await ctx.reply(f"❌ **{discord_id}** bulunamadı.")
    else:
        try:
            embed = discord.Embed(title="🆔 Discord ID Sorgu Sonucu", color=0x34495e)
            response_text = "\n".join(results[:10])
            embed.description = f"```\n{response_text}\n```"
            await ctx.author.send(embed=embed)
            
            success_embed = discord.Embed(title="✅ Tamamlandı", description=f"{ctx.author.mention}, sonuçlar DM kutuna gönderildi! 📩", color=0x2ecc71)
            success_embed.set_footer(text="Made By rexy.dev")
            await ctx.reply(embed=success_embed)
        except:
            await ctx.reply("❌ DM kapalı!")

@bot.command(name="craftrise")
async def craftrise_command(ctx, isim: str):
    if not ctx.guild or ctx.guild.id != ALLOWED_GUILD_ID:
        await send_unauthorized_warning(ctx)
        return

    await ctx.reply(f"🔎 **{isim}** aranıyor...")

    def search_craftrise(query):
        found = []
        folder = 'craftrise'
        if not os.path.exists(folder): return found
        for filename in os.listdir(folder):
            if filename.endswith(".txt"):
                filepath = os.path.join(folder, filename)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if query.lower() in line.lower():
                                found.append(line.strip())
                except: continue
        return found

    results = await asyncio.to_thread(search_craftrise, isim)

    if not results:
        await ctx.reply(f"❌ **{isim}** bulunamadı.")
    else:
        try:
            embed = discord.Embed(title="🎮 CraftRise Sorgu Sonucu", color=0x9b59b6)
            response_text = "\n".join(results[:15])
            embed.description = f"```\n{response_text}\n```"
            await ctx.author.send(embed=embed)
            
            success_embed = discord.Embed(title="✅ Tamamlandı", description=f"{ctx.author.mention}, craftrise verileri DM kutuna gönderildi! 📩", color=0x2ecc71)
            success_embed.set_footer(text="Made By rexy.dev")
            await ctx.reply(embed=success_embed)
        except:
            await ctx.reply("❌ DM kapalı!")

if __name__ == "__main__":
    if not TOKEN:
        print("Lütfen .env dosyanıza geçerli bir DISCORD_TOKEN girin.")
    else:
        bot.run(TOKEN)
