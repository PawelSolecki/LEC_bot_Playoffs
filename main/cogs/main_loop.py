import os,sys
from discord.ext import commands, tasks
from datetime import datetime, date


current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import resources.bot_functions as bot_functions
import controllers.db as db
import resources.const as const

h = datetime.now().hour
m = datetime.now().minute
isDayEnded = False

#today = '2023-02-11'
class MainLoop(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("bot is raedy")
        synced = await self.bot.tree.sync()
        print(f"Synced {len(synced)} commands")	
        self.mainLoop.start()
        
    # @commands.command()#NA CZAS TESTOW
    # async def s(self,ctx):
    #     self.mainLoop.start()

    @tasks.loop(minutes=1.0)
    async def mainLoop(self):
        try:
            global isDayEnded
            print(f"main_loop: {datetime.now().hour} : {datetime.now().minute} : {datetime.now().second}")
            if str(date.today()) in db.getDates(): #czy dzis jest mecz (format daty YYYY-MM-DD)
            #if True:
                try:
                    if datetime.now().hour == h and datetime.now().minute == m:
                    #if datetime.now().hour == const.h and datetime.now().minute == const.m:
                        isDayEnded=False
                        
                        view = bot_functions.createView(date.today())
                        details = db.getMatchDetails(date.today()) # [0] = week number, [1] = day number
                        #view = bot_functions.createView('2023-02-25')                        
                        #details = db.getMatchDetails('2023-02-25') # [0] = week number, [1] = day number
                        for server in db.getServers():
                            
                            voting_message = bot_functions.createVotingMessage(server,server.is_bonus,details[0],details[1],server.role_id)
                            voting_message = await self.bot.get_channel(int(server.channel)).send(voting_message[1],embed=voting_message[0],view=view)
                            server.votingMessageIdToDb(voting_message_id = voting_message.id)
                    #if datetime.now().hour == h and datetime.now().minute == m+1:
                    if datetime.now().hour == 18 and datetime.now().minute == 0:
                        for server in db.getServers():
                            try:
                                #edytowanie wiadomosci 
                                channel = self.bot.get_channel(int(server.channel))
                                voting_message = await channel.fetch_message(int(server.voting_message_id))
                                
                                voting_result = bot_functions.createVotingResultEmbed(server,date.today())
                                #voting_result = bot_functions.createVotingResultEmbed(server,'2023-02-25')
                                await voting_message.edit(content=None,embed=voting_result,view=None)
                            except Exception as e:
                                print(e)
                    #if datetime.now().hour == h and datetime.now().minute == m+2:
                    if datetime.now().hour > 20 and datetime.now().hour <=23:
                    #if True:
                        #if mecze zakonczone
                        if not isDayEnded:
                            matches = db.getTodaysMatches(date.today())
                            #matches = db.getTodaysMatches('2023-02-20')
                            if matches.isWinner():
                                for server in db.getServers():
                                    await self.bot.get_channel(int(server.channel)).send(embed=bot_functions.createResultsEmbed(matches))
                                    db.updatePoints(matches,server)
                                isDayEnded = True
                except Exception as e:
                    print(e)
        except Exception as e:
                print(e)

    # @commands.hybrid_command(name="dziala",with_app_command=True,description = "dziala")
    # async def dziala(self,ctx):
    #    
    #   await ctx.reply("dzialaa",ephemeral=True)
    #     

async def setup(bot):
    await bot.add_cog(MainLoop(bot))
