import os,sys

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import resources.bot_functions as bot_functions
import controllers.leaguepedia as leaguepedia
team_players={
"G2":["BrokenBlade","Yike","Caps","Hans Sama","Mikyx"],
"KOI":["Szygenda","Malrang","Larssen","Comp","Trymbi"],
"SK":["Irrelevant","Markoon","Sertuss","Exakick","Doss"],
"MAD":["Chasy","Elyoya","Nisqy","Carzzy","Hylissang"]

}

dict_shorts_team = {
'Astralis':'AST',
'Excel Esports':'XL',
'Fnatic':'FNC',
'G2 Esports':'G2',
'KOI (Spanish Team)':'KOI',
'KOI':'KOI',
'MAD Lions':'MAD',
'SK Gaming':'SK',
'Team BDS':'BDS',
'Team Heretics':'TH',
'Team Vitality':'VIT',
'Misfits Gaming':"MSF", #do testow 2022
'Rogue (European Team)':'RGE', #do testow 2022
'TBD':'TBD'
}
dict_long_team = {
'Astralis':'Astralis',
'Excel Esports':'Excel',
'Fnatic':'Fnatic',
'G2 Esports':'G2 Esports',
'KOI (Spanish Team)':'KOI',
'KOI':'KOI',
'MAD Lions':'MAD Lions',
'SK Gaming':'SK Gaming',
'Team BDS':'BDS',
'Team Heretics':'Heretics',
'Team Vitality':'Vitality',
'Misfits Gaming':"Misfits", #do testow 2022
'Rogue (European Team)':'Rogue', #do testow 2022
'TBD':'TBD'
}

champions = leaguepedia.getChampions()
champions.append("none")
champions_lower = [i.lower().replace("'", "").replace("&amp;", "&").replace(" ", "") for i in champions]

basic_leaguepedia_link = "LEC/2023 Season/Spring Playoffs"

h=6
m=0
color_white = 0xE7E9E9
color_red = 0xDA1E37
color_basic = 0x5FD1BF
color_admin = 0x1F2425

red_square = "🟥"
blue_square = "🟦"
white_square = "⬜"
#---------------wiadomosci---------------
reset_embed_message = bot_functions.f_embed("You can vote again!","Your votes have been reset succesfully!",color_red)
already_voted_embed_message = bot_functions.f_embed("We have a problem 🤖","You have already voted for the team. Click Reset button to reset all your votes.",color_red)
already_voted_score_embed_message =bot_functions.f_embed("We have a problem 🤖","You need to vote for team at first or you have already voted for the score. Click Reset button to reset all your votes.",color_red)
