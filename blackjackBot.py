from discord.ext import commands
from blackjack import Game
import dbmanage as db
from decimal import *

bot = commands.Bot(description="blackjackbot", command_prefix="t.")


@bot.command(pass_context=True)
async def blackjack(ctx):

    server = ctx.message.server
    server_id = ctx.message.server.id
    player_id = ctx.message.author.id

    game = Game(server, server_id, player_id, bot)
    game.deal()
    await game.play(ctx)

    updated_money = Decimal(game.player.money).quantize(Decimal('.01'), rounding=ROUND_DOWN)
    db.update_money(server_id, player_id, updated_money)
    return

bot.run("NDU1MjE1NTY4MTYxODY1NzM5.Df4wtg.pMJ40Z6par_aNQd_yBreLelM3uU")

