import random
import discord
import mysql.connector,os,sys
from mysql.connector import Error

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import models.models as models
import resources.const as const
import resources.secret_file as secret

def createDatabaseConnection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host=secret.db_host,
            user=secret.db_user,
            passwd=secret.db_passwd,
            database=secret.db_database
        )
       
    except Error as err:
        print(f"Error: '{err}'")
    return connection

def insertQuery(query):
    connection = createDatabaseConnection()
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
    except Error as err:
        print(f"Error: '{err}'")
        
def selectQuery(query):
    connection = createDatabaseConnection()
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        return cursor.fetchall()
    except Error as err:
        print(f"Error: '{err}'")

def existQuery(query):
    connection = createDatabaseConnection()
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        return cursor.fetchone()[0] == 1
    except Error as err:
        print(f"Error: '{err}'")

#createUser tworzy usera jezeli nie ma w tabeli/tabelach
def createUser(member:discord.Member):
    query = selectQuery(f"SELECT discord_user_id, discord_server_id FROM Users") #pobranie usera z tabeli Users
    
    for tuple_number in range(len(query)): #zmiana typow id z stringow na inty
        query[tuple_number] = list(map(int,list(query[tuple_number])))
    
    if [member.id,member.guild.id] in query: #jezli jest jest user to konczymy funckcje
        return True
     
    query = selectQuery(f"SELECT discord_user_id FROM Discord_users")#jezeli nie ma w tabeli Users to sprawdzamy czy glosowal na innym serwerze czyli
                                                                     #czyli czy jest w tabeli Discord_users
    
     #query = [(/tuple\),(/tuple\)] # tak wyglada struktura query
    for tuple_number in range(len(query)): #zmiana typow id z stringow na inty
        query[tuple_number] = list(map(int,list(query[tuple_number])))

    if [member.id] in query: #jezeli user jest w Discord_users do dodajemy go do tabeli Users i konczymy funckje 
        insertQuery(f"INSERT INTO Users (discord_user_id, discord_server_id) VALUES ('{member.id}', '{member.guild.id}')")
        insertQuery(f"INSERT INTO Users_points(user_id, points, answer_amount) VALUES ({getUserIdFromUsers(member.guild.id, member.id)} , 0, 0)")
        return True
 
    #jezeli nie ma w zadnej z tabel to dodajemy do obu
    insertQuery(f"INSERT INTO Discord_users (discord_user_id, user_name, user_discord_tag) VALUES ('{member.id}', '{member.name}', {member.discriminator})")
    insertQuery(f"INSERT INTO Users (discord_server_id, discord_user_id) VALUES ('{member.guild.id}', '{member.id}')")
    insertQuery(f"INSERT INTO Users_points(user_id, points, answer_amount) VALUES ({getUserIdFromUsers(member.guild.id, member.id)} , 0, 0)")
    return True

#getUserIdFromUsers zwraca id z tabeli user na podstawie discord i user id
def getUserIdFromUsers(discord_guild_id,discord_user_id):
    query =  selectQuery(f"SELECT user_id FROM Users WHERE discord_server_id ='{discord_guild_id}' AND discord_user_id = '{discord_user_id}'")
    if query==[]:
        return False
    return int(query[0][0])

#insertTeamVote dodaje glosc uzytkownika(team) do db
def insertTeamVote(member, match_id,team):
    if existQuery(f"SELECT EXISTS (SELECT team_vote FROM Users_votes WHERE match_id = {match_id} AND user_id = {getUserIdFromUsers(member.guild.id, member.id)})"):
        return True #jezeli user juz glosowal to zwracamy true
    insertQuery(f"INSERT INTO Users_votes(user_id, match_id, team_vote) VALUES ({getUserIdFromUsers(member.guild.id, member.id)}, {match_id}, '{team}')")#jezeli nie to dodajemy

#insertScoreVote dodaje glosc uzytkownika(score) do db
def insertScoreVote(member, match_id, score):
    if existQuery(f"SELECT EXISTS (SELECT team_vote FROM Users_votes WHERE match_id = {match_id} AND user_id = {getUserIdFromUsers(member.guild.id, member.id)})"):
        if existQuery(f"SELECT EXISTS (SELECT score_vote FROM Users_votes WHERE match_id = {match_id} AND user_id = {getUserIdFromUsers(member.guild.id, member.id)} AND score_vote IS NOT NULL)"):
            return True #jezeli user juz glosowal to zwracamy true
        insertQuery(f"UPDATE Users_votes SET score_vote = '{score}' WHERE user_id = {getUserIdFromUsers(member.guild.id, member.id)} AND match_id = {match_id}")
    else:
        return True  

def isVoteForAll(member, today):
    matches = getTodaysMatches(today)
    if len(selectQuery(f"""SELECT team_vote,score_vote FROM Users_votes 
    WHERE user_id = {getUserIdFromUsers(member.guild.id,member.id)} 
    AND match_id ={matches.match_id}
    AND score_vote IS NOT NULL"""))==1:
        return True

#deleteVote usuwa voty usera na dany mecz
def deleteVote(member:discord.Member,today):
    matches = getTodaysMatches(today)
    insertQuery(f"DELETE FROM Users_votes WHERE user_id = '{getUserIdFromUsers(member.guild.id, member.id)}' AND match_id ={matches.match_id}")

#getDates zwraca wszystkie dni jakie graja
def getDates():
    query = "SELECT DISTINCT date FROM Matches ORDER BY date" #pobieranie z db dat bez powtorzen (powtorzen i tak nie ma bo jest godzina (jednak chyba nie ma))
    dates = []
    for i in selectQuery(query): #dodanie dat juz bez godziny do tabeli
        dates.append(i[0])
    dates = list(dict.fromkeys(dates)) # usuniecie powtorzen w tabeli
    return dates

#getTodaysMatches zwraca model dzisiejszego meczu
def getTodaysMatches(today):
    query = f"SELECT match_id, team_1, team_2, winner, team_1_score, team_2_score, match_day, match_week, date FROM Matches WHERE date = '{today}'" #pobieranie skrotowych nazw teamow danego dnia
    query = selectQuery(query)
    return models.Match(query[0][0],query[0][1],query[0][2],query[0][3],query[0][4],query[0][5],query[0][6],query[0][7],None,today)

#getMatchDetails zwraca match_week i match_day zaleznia od podanego today.
def getMatchDetails(today):
    query = f"SELECT match_week, match_day FROM Matches WHERE date = '{today}' LIMIT 1"
    return selectQuery(query)[0][0], selectQuery(query)[0][1]

#getServers zwraca wszystkie serwery
def getServers(): #tworzenie listy obiekot klasy server
    query = "SELECT discord_server_id, server_name, channel, role_id, is_bonus, voting_message_id FROM Servers" #pobieranie z server_id z bazy danych
    servers = []
    for i in selectQuery(query): #dodanie serverow do listy
        servers.append(models.Server(i[0],i[1],i[2],i[3],i[4],i[5]))
    return servers

#getAmountOfVotes zwraca ilosc glosow na dany team / mecz uzytkownikow z danego servera
def getAmountOfVotes(users,team_short, match_id):
    if users == "":
        return 0
    team_votes = selectQuery(f"SELECT COUNT(team_vote) FROM Users_votes WHERE team_vote = '{team_short}' AND user_id IN ({users[:-2]}) AND match_id = {match_id}")[0][0]
    score_vote_30 = selectQuery(f"SELECT COUNT(score_vote) FROM Users_votes WHERE team_vote = '{team_short}' AND score_vote = '3:0' AND user_id IN ({users[:-2]}) AND match_id = {match_id}")[0][0]
    score_vote_31 = selectQuery(f"SELECT COUNT(score_vote) FROM Users_votes WHERE team_vote = '{team_short}' AND score_vote = '3:1' AND user_id IN ({users[:-2]}) AND match_id = {match_id}")[0][0]
    score_vote_32 = selectQuery(f"SELECT COUNT(score_vote) FROM Users_votes WHERE team_vote = '{team_short}' AND score_vote = '3:2' AND user_id IN ({users[:-2]}) AND match_id = {match_id}")[0][0]
    return team_votes, score_vote_30, score_vote_31, score_vote_32

#getUserVote zwraca glosy usera jako lista
def getUserVote(member:discord.member,today):
    matches = getTodaysMatches(today)
    team = selectQuery(f"SELECT team_vote,score_vote FROM Users_votes WHERE user_id = '{getUserIdFromUsers(member.guild.id, member.id)}' AND match_id  = {matches.match_id}")
    users_votes= [team[0][0],team[0][1]]
    return users_votes #[[team,score],[g2,2:1]]

#getUsersFromServer zwraca wszystkich userow z danego serwera
def getUsersFromServer(server):
    users = []
    for user in selectQuery(f"SELECT user_id FROM Users WHERE discord_server_id = '{server.discord_server_id}'"):  #selectQuery zwraca: [(user_id,)(user_id,))]
        users.append(user[0])
    return users

#updateMatchWinner uzywamy głownie w modelsach, zmienia winnera meczu
def updateMatchWinner(match):
    insertQuery(f"UPDATE Matches SET winner = '{match.winner}', team_1_score = '{match.team_1_score}', team_2_score = '{match.team_2_score}' WHERE match_id = {match.match_id}")

  
#updatePoints updatuje pointsy (wywolywane jest po zamknieciu glosowania)
def updatePoints(match,server): 
    users_array = getUsersFromServer(server) # uzytkownicy z servera
    users_points_dict= getUsersPointsAndAnswersAmount(server)[0] #pointsy uzytkowanikow z servera
    users_answers_amount_dict= getUsersPointsAndAnswersAmount(server)[1] # answer_amount uzytkownikow z servera
    users="" # do sql IN query

    for user in users_array:
        users+=f"{user}, " # do sql IN query

    if users == "":
        return
        

    if int(match.team_1_score) > int(match.team_2_score):
        score = match.team_1_score + ":" + match.team_2_score
    else:
        score = match.team_2_score + ":" + match.team_1_score
    for user in selectQuery(f"SELECT user_id FROM Users_votes WHERE team_vote = '{match.winner}' AND user_id IN ({users[:-2]}) AND match_id = {match.match_id}"):
        if score == selectQuery(f"SELECT score_vote FROM Users_votes WHERE user_id = {user[0]} AND match_id = {match.match_id}")[0][0]:
            users_points_dict[user[0]] += 3
        else:
            users_points_dict[user[0]] += 1
        
    for user in users_array: # to samo co wyzej tylko dla anser_amount
        users_answers_amount_dict[user] += getUserAnswersAmountToday(match, user)
    
    for user in users_points_dict: # update pointsow i answer_amount w db
        insertQuery(f"UPDATE Users_points SET points = {users_points_dict[user]}, answer_amount = {users_answers_amount_dict[user]} WHERE user_id = {user}")

#getUsersPointsAndAnswersAmount zwraca słowniki z aktualnymi punktami i liczba odpowidzi usera
def getUsersPointsAndAnswersAmount(server):
    users_array = getUsersFromServer(server) #sciaganie glosujacych uzytkownikow servera
    users_points_dict={} #dict do pointsow
    users_answers_amount_dict = {} #dict do liczby odpowiedzi
    users=""
    for user in users_array:
        users +=f"{user}, " #zmiana array na stringa do query

    if users == "": #jezli nie ma userow do puste dicty
        return users_points_dict, users_answers_amount_dict

    #selectQuery zwraca [(user_id,points),(user_id,points)] / [(user_id,liczba_odpowiedzi),(user_id,liczba_odpowiedzi)]
    for user in selectQuery(f"SELECT user_id, points FROM Users_points WHERE user_id IN({users[:-2]})"): #tworzenie slownika z kazdym uzytkownikiem i pointsami
        users_points_dict[user[0]] = user[1]
        
    for user in selectQuery(f"SELECT user_id, answer_amount FROM Users_points WHERE user_id IN({users[:-2]})"): #tworzenie slownika z kazdym uzytkownikiem i liczba głosów
        users_answers_amount_dict[user[0]] = user[1]
    
    return users_points_dict, users_answers_amount_dict

#getUserAnswersAmountToday sprawdz czy user odpowiedzial zwraca 1 jezeli tak w przeciwnym wypadku 0 
def getUserAnswersAmountToday(match, user):
    return selectQuery(f"SELECT COUNT(user_id) FROM Users_votes WHERE user_id = {user} AND match_id ={match.match_id}")[0][0]

#updateServerBonusStatus zmienia czy bonusma byc wlaczony czy wylaczony na serwerze
def updateServerBonusStatus(server_id,state):
    insertQuery(f"UPDATE Servers SET is_bonus = {state} WHERE discord_server_id = {server_id}")

#setServerBonus ustaiwa bonus dla danego serwera
def setServerBonus(server, week, day):
    if selectQuery(f"SELECT discord_server_id FROM Server_bonuses WHERE discord_server_id = '{server.discord_server_id}' AND week = '{week}' AND day = '{day}'") != []:#sprawdzamy czy na ten dzien juz nie ma(np jak byl reset bota zeby nie wywalilo)
        return selectQuery(f"SELECT bonus FROM Server_bonuses WHERE discord_server_id = '{server.discord_server_id}' AND week = '{week}' AND day = '{day}'")[0][0]
    todays_teams = selectQuery(f"SELECT team_1_short,team_2_short FROM Matches where match_week = {week} AND match_day = {day}")
    todays_players = const.team_players[todays_teams[0][0]]+const.team_players[todays_teams[0][1]]
    todays_bonus = random.choice(todays_players)
    insertQuery(f"INSERT INTO Server_bonuses (discord_server_id, bonus, week, day) VALUES ('{server.discord_server_id}','{todays_bonus}','{week}','{day}')")
    return todays_bonus

#insertBonusVote dodaje glos usera do db jezli nie ma
def insertBonusVote(votes, week, day, user_id):
    if selectQuery(f"SELECT user_id FROM Users_bonus_votes WHERE week = '{week}' AND day = '{day}' AND user_id ={user_id}") == []:#dodajemy jezeli nie glosowal
        vote = str(votes).replace("'","\"")
        insertQuery(f"INSERT INTO Users_bonus_votes (user_id,vote, week, day) VALUES ({user_id}, '{vote}', '{week}', '{day}')")
        return True
    return False

#getTodayWeekDay zwraca dzisejszy match_week i match_day
def getTodayWeekDay(today):
    return selectQuery(f"SELECT match_week, match_day FROM Matches WHERE date = '{today}'")[0]

#getServerById zwraca model Server na podstawie discord'owego id
def getServerById(discord_server_id): 
    query =  selectQuery(f"SELECT * FROM Servers WHERE discord_server_id = '{discord_server_id}'")
    return models.Server(query[0][0],query[0][2],query[0][4],query[0][1],query[0][3],query[0][5])

#deleteBonus usuwa glos usera na bonus (reset_bonus)
def deleteBonus(user_id, week, day):
    insertQuery(f"DELETE FROM Users_bonus_votes WHERE user_id = {user_id} AND week = '{week}' AND day = '{day}'")

def getDiscordUserIdFromUsers(user_id):
    return selectQuery(f"SELECT discord_user_id FROM Users WHERE user_id = {user_id}")[0][0]

#updatePointsBonus zlicza pointsy dla bonusu, answers to odpowiedzi danego przez admina jako poprawne
def updatePointsBonus(server, answers, week, day):
    try:
        answers = [i.lower() for i in answers]#zamieniamy wszytko na male litery
        for answer in answers:
            if answer not in const.champions_lower:
                return False

        users_array = getUsersFromServer(server)#sciaganie wszystkich userow z servera
        #users=", ".join(users_array)
        users=""
        for i in users_array:
            users+=f"{i}, "
        if users =="":
            return #jezeli nie ma userow to przerywamy
            
        users_vote_dict ={}
        users_points_dict = getUsersPointsAndAnswersAmount(server)[0]#sciagamy aktualne punkty kazdego usera
        
        for user in selectQuery(f"SELECT user_id, points FROM Users_points WHERE user_id IN ({users[:-2]})"): #tworzenie slownika z kazdym uzytkownikiem i pointsami
            users_points_dict[user[0]] = user[1]#??? to robimy wyzej
        
        for user_vote in selectQuery(f"SELECT user_id, vote FROM Users_bonus_votes WHERE user_id IN ({users[:-2]}) AND week = '{week}' AND day = '{day}'"):
            users_vote_dict[user_vote[0]] = str(user_vote[1])[2:-2].replace(" ","").replace("\"","").split(",") # user_vote[1] inaczej wyglada na pi(od 2) winda(od 4)
        #na pi [2:-2]
        #na win []

        for user_id in users_vote_dict:#przechodzimy po wszystkich userach
            temp =[False for _ in range(len(answers))]#tworzymy tablice z Falsami dla kazdego usera
            for vote in users_vote_dict[user_id]:#dla kazdego vota usera sprawdzamy czy zgadza sie z jakas odpowiedzia
                print("users_vote_dict[user_id] ",users_vote_dict[user_id])
                for i in range(len(answers)):
                    if vote == answers[i] and not temp[i]: #jezeli sie zgadza z odpowiedzia:
                        temp[i] = True #zmieniami na True jako iz ta odpowiedz juz sie policzyla
                        print("dodalem")
                        print("vote ", vote)
                        print("answers ",answers)
                        users_points_dict[user_id]+=1 #dodajemy punkt
                        break

        for user_id in users_points_dict:#update pointsow w bazie
            insertQuery(f"UPDATE Users_points SET points = {users_points_dict[user_id]} WHERE user_id = {user_id}")
    except Exception as e:
        print("bonus update points error: ",e)

#updateServerRole updatuje role do pingowania na serwerze
def updateServerRole(discord_server_id,role_id):    
	return f"UPDATE Servers SET role_id = '{role_id}' WHERE discord_server_id = '{discord_server_id}'"

