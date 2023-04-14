import os,sys,discord
from discord.ui import View
import models.models as models
import controllers.db as db
import resources.const as const

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

#createView tworzy buttony na dany mecz
def createView(today):
    view = View(timeout = None)
    todaysMatch = db.getTodaysMatches(today)
    
    view.add_item(models.TeamButton(f'team_1.1',0,todaysMatch.team_1_short, todaysMatch.match_id, today))
    view.add_item(models.VsButton(0))
    view.add_item(models.TeamButton(f'team_2.2',0,todaysMatch.team_2_short, todaysMatch.match_id, today))
    view.add_item(models.ScoreButton(f'30',1,'3:0',todaysMatch.match_id,today))
    view.add_item(models.ScoreButton(f'31',1,'3:1',todaysMatch.match_id,today))
    view.add_item(models.ScoreButton(f'32',1,'3:2',todaysMatch.match_id,today))
    view.add_item(models.ResetButton('reset',2,'Reset',today))
    return view

#createVotingMessage zwraca embed dolaczany do wiadomosci z glosowaniem
def createVotingMessage(server,is_bonus, week, day, role):
    title = f"\t\tWeek {week} Day {day}"
    description = ""
    roleToPing = None
    if is_bonus:    
        bonus = db.setServerBonus(server,week,day)
        description +=f"**Today bonus:** \n Name 3 champions that **{bonus}** will play\n"
    footer = "To vote just click the buttons below"
    if role != 'None': #jezeli jest rola do pingowania
        roleToPing = "Hi "
        if role == 'everyone':
            roleToPing += f"@{role}"
        else:
            roleToPing += f"<@&{role}>"
        roleToPing += " new voting has just dropped!"

    return f_embed(title, description, const.color_basic,footer),roleToPing

#createVotingResultEmbed tworzy i zwraca wiadomosc z wynikami glosowania
def  createVotingResultEmbed(server ,today):
    match_details = db.getMatchDetails(today) # [0] = week number, [1] = day number
    title = f"\t\tRound {match_details[0]}"
    description =  f"**Server votes (total votes: {countVotes(server,today)})"
    if countBonusVotes(server,today) ==0:
        description+="\n\n**"
    else:
        description+=f" | total votes for bonus: {countBonusVotes(server,today)}):\n\n**"
    results = {} # okresla glosy na dany team w danym meczu
    
    results = {"team_1_short":"","team_1_votes":0,"team_1_30":0,"team_1_31":0,"team_1_32":0, "team_2_short":"", "team_2_votes":0,"team_2_30":0,"team_2_31":0,"team_2_32":0}

    users_string_for_query = "" # okreslenie wszystkich userow servera jako string dla sql IN query
    for user in db.getUsersFromServer(server):
        users_string_for_query += f"{user}, "
    
    match = db.getTodaysMatches(today)
    team_1_votes = db.getAmountOfVotes(users_string_for_query,match.team_1_short, match.match_id)
    team_2_votes = db.getAmountOfVotes(users_string_for_query,match.team_2_short, match.match_id)

    results["team_1_short"] = match.team_1_short
    results["team_1_votes"] = team_1_votes[0]
    results["team_1_30"] = team_1_votes[1]
    results["team_1_31"] = team_1_votes[2]
    results["team_1_32"] = team_1_votes[3]

    results["team_2_short"] = match.team_2_short
    results["team_2_votes"] = team_2_votes[0]
    results["team_2_30"] = team_2_votes[1]
    results["team_2_31"] = team_2_votes[2]
    results["team_2_32"] = team_2_votes[3]

    
    if int(results["team_1_votes"]) + int(results["team_2_votes"]) == 0:
        description+= f"0% - {results['team_1_short']} {10*const.white_square} {results['team_2_short']} - 0%\n\n"
    else:
        #tworzenie pb (bloczki)
        team_1_percent_votes = results["team_1_votes"]/(results["team_1_votes"]+results["team_2_votes"])
        description += f"{round(team_1_percent_votes*100)}% - {results['team_1_short']} "
        description += f"{int(round(team_1_percent_votes*10)) * const.red_square}"
        description += f"{(10 - int(round(team_1_percent_votes*10))) * const.blue_square}"
        description += f" {results['team_2_short']} - {100 - round(team_1_percent_votes*100)}%\n\n"

        #torzenie procentowego dla kazdego wyniku
        total_score_votes = results["team_1_30"] +results["team_1_31"]+results["team_1_32"] +results["team_2_30"] +results["team_2_31"]+results["team_2_32"]
        description += f"**3:0** {results['team_1_short']} -> {int(round(results['team_1_30']/total_score_votes*100))} % | {results['team_2_short']} -> {int(round(results['team_2_30']/total_score_votes*100))} %\n"
        description += f"**3:1** {results['team_1_short']} -> {int(round(results['team_1_31']/total_score_votes*100))} % | {results['team_2_short']} -> {int(round(results['team_2_31']/total_score_votes*100))} %\n"
        description += f"**3:2** {results['team_1_short']} -> {int(round(results['team_1_32']/total_score_votes*100))} % | {results['team_2_short']} -> {int(round(results['team_2_32']/total_score_votes*100))} %\n\n"

    return f_embed(title, description, const.color_basic) # zwrocenie gotowego embeda

#countVotes dodajamy do votingMessageResultEmbed zwraca ilosc glosow danego dnia  
def countVotes(server,today):
    match_id = db.getTodaysMatches(today).match_id #do zapytania sql
    
    
    query = db.selectQuery(f"""
    SELECT Servers.server_name, COUNT(DISTINCT(Users_votes.user_id)) FROM Users_votes
    INNER JOIN Users ON Users_votes.user_id = Users.user_id 
    INNER JOIN Servers ON Users.discord_server_id = Servers.discord_server_id
    WHERE match_id = {match_id} AND Servers.discord_server_id = '{server.discord_server_id}'  GROUP BY Servers.server_name
    """)#query zwraca voty danego servera na dany dzien
    return query[0][1]

#createVoteEmbedMessage zwraca wiadomosc z glosami usera
def createVoteEmbedMessage(member:discord.member,today):
    users_votes = db.getUserVote(member,today) #[[team,score],[g2,2:1]]
    message = ""
    matches = db.getTodaysMatches(today)
    
    if matches.team_1_short == users_votes[0]:
        message+=f"**{matches.team_1_short}** {users_votes[1]} {matches.team_2_short}\n" #pogrubiamy mecz (**) na który user głosował
    else:
        message+=f"**{matches.team_2_short}** {users_votes[1]} {matches.team_1_short}\n"
    return f_embed("**Your votes:**",message,const.color_basic)

#createResultsEmbed zwraca embeda z resultami meczy
def createResultsEmbed(match):
    description = ""
    
    match.isWinner()
    if match.winner == match.team_1_short:
        description+=f"**{match.team_1_short}** {match.team_1_score} : {match.team_2_score} {match.team_2_short}\n"
    if match.winner == match.team_2_short:
        description+=f"**{match.team_2_short}** {match.team_2_score} : {match.team_1_score} {match.team_1_short}\n"
    
    return f_embed("TODAY'S  RESULTS:", description, const.color_admin) #zwrocenie gotowego embeda
 

#f_embed funckja zwraca embed
def f_embed(title, description, color,footer=None):
    embed=discord.Embed(title=title, description=description, color=color)
    embed.set_author(name="LEC_Bot", url="https://twitter.com/LEC_bot", icon_url="https://pbs.twimg.com/profile_images/1611378090298449920/FtZ5m_6N_400x400.jpg")
    embed.set_footer(text=footer)
    return embed

def countBonusVotes(server,today):
    week_day = db.getTodayWeekDay(today)
    users=""
    for i in db.getUsersFromServer(server):
        users+=f"{i}, "
    if users =="":
        return 0
    # server_users =  ", ".join(db.getUsersFromServer(server))

    query =db.selectQuery(f"SELECT COUNT(user_id) FROM Users_bonus_votes WHERE week={week_day[0]} AND day={week_day[1]} AND user_id IN ({users[:-2]})")
    if query == []:
        return 0
    return query[0][0]