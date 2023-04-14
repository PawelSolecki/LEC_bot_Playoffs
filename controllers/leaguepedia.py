import mwclient
import json
import sys
import os

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import controllers.db as db
import models.models as models
import resources.const as const

site = mwclient.Site('lol.fandom.com', path='/')

#response od leaguepedia api
def leaguepediaResponse(tables,fields,limit='max',where=None,order_by=None,format='json'):
    try:
        response = site.api('cargoquery',
        limit = limit,
        tables = tables,
        fields = fields,
        where = where,
        order_by = order_by,  
        format = format
        )
        return json.loads(json.dumps(response)) #zwrocenie json zamiast orderedDict
    except Exception as err:
        return err

def constructMatches():
    decoded = leaguepediaResponse('MatchSchedule','Team1,Team2,Team1Score,Team2Score,Winner,MatchDay,Tab,IsReschedulable, DateTime_UTC ',where=f"OverviewPage = '{const.basic_leaguepedia_link}'",order_by='DateTime_UTC')
    last_match_id_query = "SELECT MAX(match_id) FROM Matches;" #query zwracajace id ostatniego wpisanego meczu
    last_match_id = db.selectQuery(last_match_id_query)[0][0] #zwraca tupla w liscie [(n,)] wiec [0][0] zeby dostac numer
    
    if last_match_id == None: #jezeli nie ma jeszcze nic w tabeli
        last_match_id=0

    #dodawanie meczy ktorych jeszcze nie ma
    for i in range(last_match_id,len(decoded['cargoquery'])): #przejscie po wszystkich meczach, len(decoded['cargoquery']) - ilosc meczy
        if decoded['cargoquery'][i]['title']['Tab'] == "Finals":
            week = 3
        else:
            week = decoded['cargoquery'][i]['title']['Tab'][6:]
        match = models.Match(
            i,
            decoded['cargoquery'][i]['title']['Team1'],
            decoded['cargoquery'][i]['title']['Team2'],
            decoded['cargoquery'][i]['title']['Team1Score'],
            decoded['cargoquery'][i]['title']['Team2Score'],
            decoded['cargoquery'][i]['title']['Winner'],
            decoded['cargoquery'][i]['title']['MatchDay'],
            week,
            decoded['cargoquery'][i]['title']['IsReschedulable'],
            decoded['cargoquery'][i]['title']['DateTime UTC']
        )
        if match.is_reschedulable != True and match.team_1 != 'TBD'and match.team_2 != 'TBD': #sprawdzamy czy kolejnosc sie moze zmienic i czy teamy juz sa wpisane
            db.insertQuery(match.toDbMatches()) #insert into nasza baza danych poprawnego meczu

#isMatchWinner sprawdza czy w danym meczy jest juz wygrany
def isMatchWinner(match):
    if match.match_week == 3:
        Tab = "Finals"
    else:
        Tab = f"Round {match.match_week}"
    decoded = leaguepediaResponse('MatchSchedule','Winner',where=f"OverviewPage = '{const.basic_leaguepedia_link}' AND MatchDay = '{match.match_day}' AND Tab = '{Tab}' AND Team1 = '{match.team_1}' AND Team2 = '{match.team_2}'",order_by='DateTime_UTC')
    #return True, "1"
    
    return decoded['cargoquery'][0]['title']['Winner'] != None, decoded['cargoquery'][0]['title']['Winner']

def getTeamScore(match):
    if match.match_week == 3:
        Tab = "Finals"
    else:
        Tab = f"Round {match.match_week}"
    decoded = leaguepediaResponse('MatchSchedule','Team1Score,Team2Score',where=f"OverviewPage = '{const.basic_leaguepedia_link}' AND MatchDay = '{match.match_day}' AND Tab = '{Tab}' AND Team1 = '{match.team_1}' AND Team2 = '{match.team_2}'",order_by='DateTime_UTC')
    #return "3","2"
    return decoded['cargoquery'][0]['title']['Team1Score'],decoded['cargoquery'][0]['title']['Team2Score']

#sciaganie championow z API
def getChampions():
    decoded = leaguepediaResponse('Champions','Name')
    champions=[]
    for champion in decoded['cargoquery']:
        champions.append(champion['title']['Name'])
    return champions

