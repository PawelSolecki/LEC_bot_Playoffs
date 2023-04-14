from datetime import date
import discord,os,sys
from discord.ext import commands
from discord import app_commands

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import controllers.db as db
import resources.bot_functions as bot_functions
import resources.const as const
import models.models as models
import controllers.leaguepedia as leaguepedia

class Common(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
    #komenda points sluzy do sprawdziania glosow: swoich, kogos innego i wszystkich na serverze
    @commands.hybrid_command(name="points",with_app_command=True, description = "Use it to check server's points!")
    async def points(self, ctx, given_user_from_user : discord.Member = None):
        try:
            
            embeds_array = [] # tablica Pages dla MenuPages
            description = ""
            server = db.getServerById(ctx.guild.id) #okreslenie servera po guild.id wyciagnietym z wiadomosci
            
            if given_user_from_user == None: # w przypadku gdy sama points tzn. >points to given_user rowne jest authorowi wiadomosci
                given_user_from_user = ctx.author.id
            else:                   # inaczej jest rowny jest innemu memberowi servera
                given_user_from_user = given_user_from_user.id
            
            given_user = db.getUserIdFromUsers(ctx.guild.id, given_user_from_user) # znalezienie user_id podanego usera w db
            if given_user == False:
                db.createUser(ctx.author)
                given_user = db.getUserIdFromUsers(ctx.guild.id, given_user_from_user)

            users_points_dict = db.getUsersPointsAndAnswersAmount(server)[0] # pointsy userow dla tego servera
            users_points_dict = dict(sorted(users_points_dict.items(), key=lambda item: item[1],reverse=True)) #posortowanie pointsow na serverze po ilosci punktow malejaco
            given_user_place = list(users_points_dict.keys()).index(given_user) #miejsce podanego uzytkownika
            
            #przechodmimy po dict'cie (posortowanym malejąco) gdzie kluczem jest user_id(z tabeli Users) a kluczem jego punkty
            #i jest numerem iteracji pętli
            #user to klucz w users_points_dict
            for i, user in zip(range(len(users_points_dict)), users_points_dict):
                description += f"{placeSymbol(i)} <@{db.getDiscordUserIdFromUsers(user)}> : {users_points_dict[user]}\n" # dodajemy linijke z miejscem usera (i+1), z db wyciagamy jego discord id, i bierzemy pointsy z dict'a

                if (i+1)%10==0: #10 okresla ilosc linijek (userow) na jedenej stronie wiec jezeli jest 10 konczymy strone
                    description += f"\n{placeSymbol(given_user_place)} <@{db.getDiscordUserIdFromUsers(given_user)}> : {users_points_dict[given_user]}" #dodajemy numer nazwe i punkty usera podanego w komendzie
                    
                    embeds_array.append(bot_functions.f_embed(f"**Points**",description, const.color_basic, footer=f"Page {(i+1)//10} / {len(users_points_dict)//10+1}")) #aktualny numer strony na maksymalna ilosc (aktualny numer nie ma dzielenia // bo if zapewnia podzielnosc) maks strony + 1 bo // ucina jednosci
                    
                    description="" #zerujemy description dla kolejnej strony
            
            if (i+1)%10!=0: #jezeli i+1 po petli nie jest podzielne przez 10 to trzeba dodac ostatnia strone (gdzie bedzie mniej niz 10 linijek)
                description += f"\n{placeSymbol(given_user_place)} <@{db.getDiscordUserIdFromUsers(given_user)}> : {users_points_dict[given_user]}" #tak samo jak wyzej
                embeds_array.append(bot_functions.f_embed(f"**Points**",description, const.color_basic, footer=f"Page {len(users_points_dict)//10+1} / {len(users_points_dict)//10+1}")) #ten page jest ostani

            await models.MenuPages(embeds=embeds_array,user_id=ctx.author.id,givenUserPage=(given_user_place)//10).send(ctx) # wyslanie gotowych MenuPages, #given_user_plave -1 bo page 10 usera = 0
        
        except Exception as e:
            print(e)

    #komenda points2 sluzy do sprawdziania glosow: swoich, kogos innego i wszystkich na serverze
    @commands.hybrid_command(name="points2",with_app_command=True, description = "Use it to check server's points!")
    async def points2(self, ctx, given_user_from_user : discord.Member = None):
        try:
            embeds_array = [] # tablica Pages dla MenuPages
            description = ""
            server = db.getServerById(ctx.guild.id) #okreslenie servera po guild.id wyciagnietym z wiadomosci
            
            if given_user_from_user == None: # w przypadku gdy sama points tzn. >points to given_user rowne jest authorowi wiadomosci
                given_user_from_user = ctx.author.id
            else:                   # inaczej jest rowny jest innemu memberowi servera
                given_user_from_user = given_user_from_user.id
            
            given_user = db.getUserIdFromUsers(ctx.guild.id, given_user_from_user) # znalezienie user_id podanego usera w db
            if given_user == False:
                db.createUser(ctx.author)
                given_user = db.getUserIdFromUsers(ctx.guild.id, given_user_from_user)

            users_points_dict = db.getUsersPointsAndAnswersAmount(server)[0] # pointsy userow dla tego servera
            users_points_dict = dict(sorted(users_points_dict.items(), key=lambda item: item[1],reverse=True)) #posortowanie pointsow na serverze po ilosci punktow malejaco
            given_user_place = list(users_points_dict.keys()).index(given_user) #miejsce podanego uzytkownika
            
            #przechodmimy po dict'cie (posortowanym malejąco) gdzie kluczem jest user_id(z tabeli Users) a kluczem jego punkty
            #i jest numerem iteracji pętli
            #user to klucz w users_points_dict
            for i, user in zip(range(len(users_points_dict)), users_points_dict):
                description += f"{placeSymbol(i)} *{db.getUserDiscordName(user)}* : {users_points_dict[user]}\n" # dodajemy linijke z miejscem usera (i+1), z db wyciagamy jego discord id, i bierzemy pointsy z dict'a

                if (i+1)%10==0: #10 okresla ilosc linijek (userow) na jedenej stronie wiec jezeli jest 10 konczymy strone
                    description += f"\n{placeSymbol(given_user_place)} *{db.getUserDiscordName(given_user)}* : {users_points_dict[given_user]}" #dodajemy numer nazwe i punkty usera podanego w komendzie
                    
                    embeds_array.append(bot_functions.f_embed(f"**Points**",description, const.color_basic, footer=f"Page {(i+1)//10} / {len(users_points_dict)//10+1}")) #aktualny numer strony na maksymalna ilosc (aktualny numer nie ma dzielenia // bo if zapewnia podzielnosc) maks strony + 1 bo // ucina jednosci
                    
                    description="" #zerujemy description dla kolejnej strony
            
            if (i+1)%10!=0: #jezeli i+1 po petli nie jest podzielne przez 10 to trzeba dodac ostatnia strone (gdzie bedzie mniej niz 10 linijek)
                description += f"\n{placeSymbol(given_user_place)} *{db.getUserDiscordName(given_user)}* : {users_points_dict[given_user]}" #tak samo jak wyzej
                embeds_array.append(bot_functions.f_embed(f"**Points**",description, const.color_basic, footer=f"Page {len(users_points_dict)//10+1} / {len(users_points_dict)//10+1}")) #ten page jest ostani

            await models.MenuPages(embeds=embeds_array,user_id=ctx.author.id,givenUserPage=(given_user_place)//10).send(ctx) # wyslanie gotowych MenuPages, #given_user_plave -1 bo page 10 usera = 0
        
        except Exception as e:
            print(e)

    #feedback - komenda sluzaca do wysylania feedbacku
    @app_commands.command(name="feedback",description = "Use it to send to bot owners any problems, ideas or anything else")
    async def feedback(self,interaction:discord.Interaction):
        await interaction.response.send_modal(models.FeedbackModal(bot = self.bot)) 
    

    #my_vote - zwraca votsy zaleznie od day i week, z defoultu jest today
    @commands.hybrid_command(name = "my_votes",with_app_command=True,description="Shows your todays (or previous) votes")
    async def myVotes(self, ctx, week = None, day = None):
        try:#jak ktos nie week i day a dzis nie ma meczy
            if week == None and day == None:#jezeli nie dal dajemy dzisiejsze
                matches = db.getTodaysMatches(date.today())
                week = matches.match_week
                day = matches.match_day
            if (int(day) <= 0 or int(day) >= 2) and (int(week) <= 0 or int(week) >= 3):
                return
            user_id = db.getUserIdFromUsers(ctx.guild.id,ctx.author.id)
            #sciaganie votow usera z danego dnia i weeeka
            query = db.selectQuery(f"""
            SELECT team_vote, Matches.team_1_short,Matches.team_2_short,score_vote FROM Users_votes
            INNER JOIN Matches ON Users_votes.match_id = Matches.match_id
            WHERE user_id = {user_id} AND Matches.match_day = {day} AND Matches.match_week = {week}
            ORDER BY Matches.match_id
            """)
            
            description = ""
            for match in query: #odpowiednie dodanie teamow do wiadomosci
                if match[0]==match[1]:
                    description += f"**{match[0]}** {match[3]} {match[2]}\n"
                elif match[0]==match[2]:
                    description += f"**{match[0]}** {match[3]} {match[1]}\n"
                else:
                    description += f"{match[1]} vs {match[2]}\n"
            if db.getServerById(ctx.guild.id).is_bonus==1: #sciaganie bonusu usera z danego dnia i weeka
                query2 = db.selectQuery(f"""
                SELECT vote FROM Users_bonus_votes
                WHERE user_id = {user_id} AND day = '{day}' AND week = '{week}'
                """)
                if query2 !=[]: #dodanie sciagnietych bonusow do wiadomosci
                    bonus = str(query2[0][0])[4:-3].replace("\"","")
                    description+=f"\n**Your Bonus:**\n{bonus}"
            
            await ctx.reply(embed = bot_functions.f_embed(f"**Your votes week {week} day {day}**",description,const.color_basic),ephemeral=True)
        except Exception as e:
            print("my_votes: ",e)

#placeSymbol zwraca numer miejsca
def placeSymbol(place): 
    if place == 0: # jezeli pierwsze miejsce
        return "🥇" 
    elif place == 1: # jezeli drugie miejsce
        return "🥈"
    elif place == 2: # jezeli trzecie miejsce
        return "🥉"
    else:           # w przypadku pozostalych miejsc
        return f"**{place+1}.**" 
   
async def setup(bot):
    await bot.add_cog(Common(bot))
