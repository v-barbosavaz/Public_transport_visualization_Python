import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html

import plotly.plotly as py
import plotly.graph_objs as go

import json
import pandas as pd
import numpy as np
import time
import math
import ast

# =====================================================================================

"""
    DATASETS CLEANING
"""

#------------------------------------------------------
# DATASET EMPLACEMENT DES GARES

stations = pd.read_csv("data/external/emplacement-des-gares-idf.csv", delimiter = ";")

stations = stations.loc[:,["Geo Point", "NOM_GARE","NOMLONG","GARES_ID", "RES_COM", "RESEAU", "INDICE_LIG"]] # usefull columns
stations["LATITUDE"], stations["LONGITUDE"] = stations["Geo Point"].str.split(',', 1).str # add 2 columns : latitude/longitude
stations = stations[['GARES_ID','LATITUDE', 'LONGITUDE',"NOM_GARE", 'NOMLONG',"RES_COM", "RESEAU", "INDICE_LIG"]] # reorder + delete some columns

stations["LATITUDE"] = stations["LATITUDE"].astype('float32')
stations["LONGITUDE"] = stations["LONGITUDE"].astype('float32')
stations["RES_COM"]= stations["RES_COM"].astype('category')


stations = stations.sort_values(by = "NOMLONG") #, ascending = [True, True]) # order values
stations = stations.set_index("NOMLONG") # set index
stations.index = stations.index.map(str)


#------------------------------------------------------
#DATASET COULEURS DES GARES

colors = pd.read_csv("data/colors.csv", delimiter = ";")
colors = colors.set_index("RES_COM")
colors = colors.fillna("#000000") # fill with black
#colors = colors[colors["COLOR_HEX"].isnull() == False]

#------------------------------------------------------
#DATASET VALIDATIONS PAR JOUR

valid = pd.read_csv('data/external/validations-sur-le-reseau-ferre-nombre-de-validations-par-jour-1er-sem.csv', sep =';', parse_dates=['JOUR'], dayfirst=True, na_values=['n/d'], encoding='utf8')

valid = valid.loc[:,['JOUR','LIBELLE_ARRET','NB_VALD', "CODE_STIF_ARRET", "CATEGORIE_TITRE"]]# if we want to work with a copy / better solution according to doc

#valid = valid.sort_values(by = "LIBELLE_ARRET")
#valid.index = valid.index.map(str)

def conv(x):
    try:
        return int(x)
    except:
        return np.nan
        
# delete the rows 'moins de 5'/NaN
valid['NB_VALD'] = valid['NB_VALD'].apply(conv)
valid = valid.dropna()
valid['NB_VALD'] = valid['NB_VALD'].astype('int32')

valid = valid.sort_values(by =["JOUR","LIBELLE_ARRET"])

#delete non-relevant values
valid = valid[valid["LIBELLE_ARRET"] != "Inconnu"]
valid = valid[(valid["CATEGORIE_TITRE"] != "NON DEFINI") & (valid["CATEGORIE_TITRE"] != "?")]

valid["WEEKDAY"] = valid['JOUR'].apply(lambda row : pd.Timestamp(row).weekday())  # add a column weekday


#------------------------------------------------------
#CREATE DATASET VALID_SUM : get total validation per station per day

valid_sum = valid.groupby(['JOUR','LIBELLE_ARRET'])['NB_VALD'].sum()
valid_sum = valid_sum.to_frame()
valid_sum = valid_sum.reset_index() #remove multi indexing

# in case
#valid_sum = valid_sum.sort_values(by = "LIBELLE_ARRET")
valid_sum = valid_sum.set_index("LIBELLE_ARRET")
valid_sum.index = valid_sum.index.map(str)



validyear = valid.groupby(['LIBELLE_ARRET'])['NB_VALD'].mean()
validyear = validyear.to_frame()
validyear = validyear.reset_index() #remove multi indexing

validyear['NB_VALD'] = np.ceil(validyear['NB_VALD'])
validyear["NB_VALD"] = validyear["NB_VALD"].astype('int32')
validyear = validyear.set_index("LIBELLE_ARRET")
    

    
validday2 = valid.groupby(['LIBELLE_ARRET', 'WEEKDAY'])['NB_VALD'].mean()
validday2 = validday2.to_frame()
validday2 = validday2.reset_index() #remove multi indexing
#validday2['NB_VALD'] = valid['NB_VALD'].apply(lambda row : math.ceil(row))
validday2['NB_VALD'] = np.ceil(validday2['NB_VALD'])
validday2["NB_VALD"] = validday2["NB_VALD"].astype('int32')



#------------------------------------------------------
#DATASET VALIDATION PAR JOUR TYPE

valid_type = pd.read_csv("data/external/validations-sur-le-reseau-ferre-profils-horaires-par-jour-type-1er-sem.csv", delimiter = ";" , low_memory=False)

valid_type["DEBUT_HORR"], valid_type["FIN_HORR"] = valid_type["TRNC_HORR_60"].str.split('H-', 1).str # ajout colonnes latitude/longitude
valid_type["FIN_HORR"] = valid_type["FIN_HORR"].str.replace("H","")
valid_type=valid_type.rename(columns = {'pourc_validations':'PCT_VALID'})
valid_type = valid_type[['LIBELLE_ARRET','CAT_JOUR', 'DEBUT_HORR', 'PCT_VALID',"TRNC_HORR_60"]]

valid_type = valid_type.drop(valid_type[valid_type["DEBUT_HORR"] == "ND"].index)
valid_type["LIBELLE_ARRET"] = valid_type["LIBELLE_ARRET"].astype('category')
valid_type["CAT_JOUR"] = valid_type["CAT_JOUR"].astype('category')
valid_type["DEBUT_HORR"]= valid_type["DEBUT_HORR"].astype('int32')

valid_type = valid_type.sort_values(by = ["LIBELLE_ARRET","CAT_JOUR","DEBUT_HORR"])


valid_type = valid_type.groupby(['LIBELLE_ARRET','CAT_JOUR','TRNC_HORR_60', "DEBUT_HORR"])['PCT_VALID'].mean()
valid_type = valid_type.reset_index() 
valid_type = valid_type.sort_values(["LIBELLE_ARRET","CAT_JOUR","DEBUT_HORR"])



# =====================================================================================

"""
    VARIABLES
"""
dates = valid["JOUR"].unique()

# valid_sum_year = valid_sum.groupby(['LIBELLE_ARRET'])['NB_VALD'].sum().to_frame()
# valid_sum_year.sort_values(by = "NB_VALD", ascending = False)

weekday_str = {0:"Monday",1:"Tuesday", 2:"Wednesday", 3:"Thursday", 4:"Friday", 5:"Saturday", 6:"Sunday"}

#day_categories = valid_type["CAT_JOUR"].unique().tolist()
day_categories = [elt for elt in valid_type["CAT_JOUR"].unique()]
horaires = valid_type["TRNC_HORR_60"].unique().tolist()


# =====================================================================================

"""
    FUNCTIONS
"""

def get_marks_size_year(line, size_factor) : 

    gares_ligne = stations.loc[stations["RES_COM"] == line] #retourne les stations de la ligne
    gares_ligne_ind = gares_ligne.index.tolist()

    result = validyear.reindex(gares_ligne_ind) #operation de selection 
    result = result.loc[:,["NB_VALD"]]
    result = result.fillna(5)
    result_list = result["NB_VALD"].tolist()
    return_result = [i*size_factor for i in result_list]
    return return_result
    
    
    
def get_marks_size(line, date_selected, size_factor) : 

    gares_ligne = stations.loc[stations["RES_COM"] == line] #retourne les stations de la ligne
    vsd = valid_sum.loc[(valid_sum["JOUR"] == date_selected)] # retourne les données du jour concerné
    gares_ligne_ind = gares_ligne.index.tolist()

    result = vsd.reindex(gares_ligne_ind) #operation de selection 
    result = result.loc[:,["NB_VALD"]]
    result = result.fillna(5)
    result_list = result["NB_VALD"].tolist()
    return_result = [i*size_factor for i in result_list]
    
    return return_result
    
    
    
# for now, dash does not support datatime type
def get_str_date(str_date):
    str_date = str_date.replace("T00:00:00.000000000","")
    return str_date

    
def get_hover_point(hoverData):
    selected_point = ast.literal_eval(json.dumps(hoverData, indent=2))
    #selected_point = ast.parse(json.dumps(hoverData, indent=2))
    elt1 = selected_point.get("points")
    text = elt1[0].get("text")
    #stations[stations["NOM_GARE"] == text]
    return text


# =====================================================================================
"""
    DASH APP
"""



app = dash.Dash(__name__)
# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

#app.css.config.serve_locally = True
#app.scripts.config.serve_locally = True

#------------------------------------------------------

app.layout = html.Div(className="row", children=[
    
    html.Div(className="col-lg-10", style={'margin-right': 'auto', 'margin-left': 'auto'}, 
    children=[
        html.Br(),
        html.H1('Dashboard on public transport in France',
            style={'textAlign': 'center'}
        ),
        html.Br(),
        html.Div(style={'background-color': 'rgb(245, 245, 245)'}, children=[
        html.P(children=[html.Span("This dashboard has been created by "),
            html.Span("Vincent Barbosa Vaz and Cécile Pov", style={'color': 'blue'}),
            html.Br(),
            html.Span("This unit has been coordonated by "),
            html.Span("Daniel Courivaud", style={'color': 'blue'}),
            html.Br(),
            html.Span("Code unit : "),
            html.Span("OUAP-4112", style={'color': 'blue'})

            ])

        ]),

        html.P("This is a case study on public transport in France."),

        html.P("\
        After mastering the basics of Python in class, we were asked to produce a dashboard \
        including data analysis and vizualisations. This dashboard uses pandas \
        library."),

        html.Br(),

        html.P("\
        The first dataset contains the number of validations for each stop, for each category \
        of transport ticket during the first semester of 2018. It is a interesting dataset because \
        ticket transport can reveal the category of people which takes transport at this station.\
        For example, a big amounts validations for the « IMAGINE R » ticket can shows that a lot a \
        students takes this station, and the « Amethyste » ticket shows that the line is attended by \
        elder people. First, before focusing on categories of individuals, we would like to quantify \
        those data in a more general way : how many people had attended this station on the date XX/XX/XXXX ?\
        In order to identify high traffic areas, lets represent this in a map."),




        ### THE INTERACTIVE MAP ----------------------------------------------------
        html.Br(),
        html.H3('Interactive map',
            style={'textAlign': 'center'}
        ),
        html.Div(style={'width': '100%','margin-right': 'auto', 'margin-left': 'auto'}, children=[
        dcc.Graph(
                id='map_date',
                animate=True
        )]),
         
        html.Div(
            id = "date_div",
            children='''Date''',
             style={
                'textAlign': 'center',
                #'color': colors['text']
            }
        ),

        html.Br(),
        
        html.Li(
            id = "dropdown instructions",
            children='''Select a transportation system : ''',
             style={
                'textAlign': 'left'
            }
        ),
        
        dcc.Dropdown(
            id = "dropdown_element",
            options = [{"label":reseau, "value":reseau} for reseau in stations["RESEAU"].unique()],#.append({"label":"ALL", "value":'default'}),
            placeholder = "Select a transportation system",
            value='METRO'
        ),
        
        
        dcc.Dropdown(
            id = "dropdown_element2",
            value='default',
            multi = True 
        ),
        
        html.Br(),

        html.Li(
            id = "slider_instructions",
            children='''Select a date from 01/01/2018 to 30/06/2018 : ''',
             style={
                'textAlign': 'left'
            }
        ),
        
        html.Div(style={'overflow': 'hidden'}, children =[
        dcc.Slider(
            id = 'slider_element',
            min=0,
            max= len(valid["JOUR"].unique()),
            step= 1,
            value=100,
            #marks={ i:valid_sum["JOUR"][i] for i in range (0,len(valid["JOUR"].unique()), 50)}
            marks={ i:str(valid["JOUR"].unique()[i]) for i in range (0,len(valid["JOUR"].unique()), 30)},
            included = True
        )]),
        
        html.Br(),

        html.Div(
            id = "notes_below_slider",
            children='''Note : hovering on a station on the previous map will automatically update the data on figures below. ''',
             style={
                'textAlign': 'left'
            }
        ),
        
        html.Br(),
        html.Br(),

        html.H3("MAPPING : TRANSPORT USERS TRAFFIC"),

        html.P("The dataset « emplacement-des-gares-idf.csv» contains several useful informations :"),

        html.Ul([
        html.Li("The location (latitude, longitude) of each stop"),
        html.Li("The different lines which the stop belongs to")
        ]),

        html.P("\
        To achieve this, we use mapbox, an open source mapping platform for custom designed maps. \
        We divide this step into 2 sub-steps : \
        "),

        html.Ul([
        html.Li("Plotting a map in which stations that belongs to the same line are marked with the same color ;"),
        html.Li("Adding a time and a quantity scale to the map : the size of the marker depends on the traffic at \
        day D. Bigger the marker is, higher was the traffic.")
        ]),

        html.P("\
        How did we got the total of validations per day per station ?\
        We used the first dataset : knowing the number of validations for each transport ticket category, \
        we group them by station and date and sum them together.\
        The time slider allows us to change the date studied.  It covers all the days of the first \
        semester of 2018. When the date on the slider changes, it triggers a callback that update the map. \
        The date and the weekday are printed at the bottom of the map.\
        We can also choose which type of transportation we want to show. To hide a particular station, \
        we can click on the legend on the right. \
        We observe that 5 stations has a particular high traffic, independently from the day : \
        "),

        html.Ul([
        html.Li("La Défense"),
        html.Li("Gare du Nord"),
        html.Li("Gare de Lyon"),
        html.Li("Montparnasse"),
        html.Li("Saint-Lazare"),
        html.Li("Châtelet-les-Halles"),
        ]),

        html.P("\
        As a consequence, we can say that Paris proper, and particularly the center of the city is a high \
        traffic area. La Défense, which is known as a worker place, is also one.\
        For the weekend days, we can see that the general traffic is far less high (non-working days).\
        To be more precise, we would like to compare the traffic for each weekday for each station."),

        html.Br(),
        
        
        
        html.Div(
            id='map_year'
            # figure = {
                # 'data': [ 
                # go.Scattermapbox(
                    # lat= stations.loc[stations["RES_COM"] == ligne,"LATITUDE"].astype(str).tolist(), 
                    # lon= stations.loc[stations["RES_COM"] == ligne,"LONGITUDE"].astype(str).tolist(), 
                    # mode = 'markers',
                    # #marker = dict(size = get_marks_size(ligne,date_slider,0.001), opacity=0.7, color = colors.loc[ligne,"COLOR_HEX"]),
                    # marker = dict(size = 10, opacity=0.7, color = colors.loc[ligne,"COLOR_HEX"]),
                    # text = (stations.loc[stations["RES_COM"] == ligne,"NOM_GARE"].astype(str)),
                    # name = ligne
                # ) for ligne in list(stations["RES_COM"].unique())
                # ],
                
                # 'layout': {
                    # 'mapbox': {
                        # 'accesstoken': ("pk.eyJ1IjoieWlmZW4iLCJhIjoiY2pudWdpYTh0MHc0eTNrczU0Z25ra2Z5aSJ9.20-X0Cqm_r3r3wWAi4o_Rg"),
                        # 'center' : dict(lat=48.866667,lon=2.333333),
                        # 'zoom': 11
                    # },
                    # 'margin': {
                        # 'l': 0, 'r': 0, 'b': 0, 't': 0
                    # },
                    # 'autosize':False,
                    # 'width':1300,
                    # 'height':500
                # }
            # },
            
            # hoverData= True
        ),
        
        
        # html.Div(
            # id = "title_bargraph",
            # children='''Influence de la météo''',
             # style={
                # 'textAlign': 'center',
                # #'color': colors['text']
            # }
        # ),
        
        
        dcc.Graph(
            id='bargraph',
            figure={
                'data': [
                    {'x': validday2.loc[validday2["LIBELLE_ARRET"] == "ABBESSES","WEEKDAY"].tolist(), 'y': validday2.loc[validday2["LIBELLE_ARRET"] == "ABBESSES","NB_VALD"].tolist(), 'type': 'bar', 'name': 'SF'},
                ],
                'layout': {
                    'title': 'Dash Data Visualization'
                }
            }
        ),
        html.H3("BARGRAPH : NUMBER OF VALIDATIONS PER WEEKDAY FOR EACH STATION"),

        html.P("\
        How did we got traffic for each weekday for each station?\
        To do this, we grouped the data by station and by weekday on the whole semester, and did the average."),

        html.P("\
        Let’s represent this information with a bargraph. On the x axis, we have the weekdays on on the y axis, \
        we have the mean of the number of validations on the semester for the specific weekday.\
        Note : hovering the mouse on the previous map will update the bargraph with the data of the hovered station.\
        A big difference between the working days and the non-working days traffic show that places around this stations \
        are mostly work or schools places. We can observe this for 2 stations :"),

        html.Ul([
        html.Li("La Défense, which divides its attendance nearly by 4 (Wedneday : 9331 people , Sunday : 2293) -> working place"),
        html.Li("Noisy-Champs, which also divide its attendance nearly by 4 (Friday : 3032 people , Sunday : 821) -> student campus")
        ]),

        html.P("\
        On the contrary, a small difference between the working days and the non-working days traffic show that places around \
        this stations are attended not only for work, by also for entertainment and leisure.\
        For example Châtelet-les-Halles only divide its high traffic by 2 : in fact, this station is located in the center \
        of Paris, it is a crossing point and a touristic place. However, the Chessy-Marne-la-Vallée may be the most relevant \
        and interesting and obvious case :  the attendance mostly remain the same the whole week. The small decline during the \
        non-working days is compensated by people who come for the Walt Disney Park. This phenomenon should be highlighted by \
        studying the different category of transport ticket during working days and weekends : it would show that majority of \
        transport tickets during business days are annual/longer fees (Navigo, Imagine R), while most of the tickets during \
        the weekend are more occasionnal tickets. \
        However, the dataset in which we are working on doesn’t take into account magnetic tickets, \
        and that would distort our results. If we take them into account in our bargraph, the attendances for the weekend \
        may be higher than for the rest of the week."),
        
        html.P("\
        However, this bargraph , on its own, is not a good reference of the attendance if we want to predict, \
        for example, the traffic at La Défense for next Thursday. \
        Indeed, what if next Thursday is a holiday ?"),
        
        html.P("\
        Moreover, with the bargraph, we don’t have any information about the hour (the traffic would be completely \
        different between 1AM and 6PM for example)"),

        html.Br([]),
        
        dcc.Graph(
            id='heatmap'
        ),

        html.H3("HEATMAP : NUMBER OF VALIDATIONS PER WEEKDAY FOR EACH STATION"),

        html.P("\
        If Thursday is a holiday, then the traffic at La Defense would not be as heavy as  «normal » Thursday.\
        In order to be more close to the reality, we have to categorize  each day by a day-type. Depending on if it \
        is a school break or a holiday, i twill belong to a certain category.\
        We started on working on this using different librairies and a calendar.csv, however, \
        it is a very long process.\
        The RATP provides a second dataset : « validations-sur-le-reseau-ferre-profils-horaires-par-jour-type-1er-sem.csv »,\
        which contains the percentage of validations per time slot per day-type, for each station. In the following, we will \
        work with this dataset. The percentage is relative to the total attendance on whole time slots of the day-type.\
        The dataset distinguish 5 day-types : \
        "),

        html.Ul([
        html.Li("JOHV : Jour Ouvré Hors Vacances Scolaires"),
        html.Li("SAHV : Samedi Hors Vacances Scolaires."),
        html.Li("JOVS : Jour Ouvré en période de Vacances Scolaires."),
        html.Li("SAVS : Samedi en période de Vacances Scolaires. "),
        html.Li("DIJFP : Dimanche et Jour Férié et les ponts .")
        ]),

        html.P("\
        Let’s represent this information with a bargraph. On the x axis, we have the time slots, and on the y axis, \
        we have the day-types for the specific hour. We can plot this heatmap for each station."),
            
        html.P("\
        Note : hovering the mouse on the previous map will update the heatmap with the data of the hovered station."),
        
        html.P("\
        This heatmap allows us to know if there is more people at a time-slot A or a time-slot B for a particular day-type,\
        but we don’t have any quantity notion. In fact, the pourcentage may has been calculated on a huge number or a small \
        number (1\% of 10 << 1\% of 1000). We must quantify the attendance in order to have a more relevant heatmap.\
        Moreover, in this heatmap, we can’t compare the day-type between them, that is to say read it « vertically » \
        : a percentage is proper to a row (a day-type). In fact, if for the time-slot T, the heatmap is red for a day-type1 \
        and blue for a day-type2, it doesn’t mean and we cannot say that the traffic is higher for the day-type1."),
            
        html.Br([])

        ]
    )
])


# # =====================================================================================

"""
    CALLBACKS
"""


    
@app.callback(
    dash.dependencies.Output('heatmap','figure'),
    [dash.dependencies.Input('map_date', 'hoverData')]
)
def set_map(hoverData):
    
    text = get_hover_point(hoverData)
    a = stations[stations["NOM_GARE"] == text]
    liste = a.index.values.tolist()
    liste0 = str(liste[0])
    
    
    z= []
    for category in day_categories :
        l_cat = valid_type.loc[(valid_type["CAT_JOUR"] == category) & (valid_type["LIBELLE_ARRET"] == liste0),"PCT_VALID"].tolist()
        z.append(l_cat)
    

    return  {
        'data': [
                    {'x': horaires, 
                     'y': day_categories, 
                     'z': z,
                     'type': 'heatmap', 'name': liste0
                    },
                ],
                
                'layout': {
                    'title': liste0
                }
    }

    
    


@app.callback(
    dash.dependencies.Output('date_div','children'),
    [dash.dependencies.Input('slider_element', 'value')]
)
def set_date_div(num_slider):
    date = get_str_date(str(valid["JOUR"].unique()[num_slider]))
    weekday = weekday_str.get(pd.Timestamp(valid["JOUR"].unique()[num_slider]).weekday())
    print(dates[-1])
    return str(weekday) + " - " + str(date)
    

    
    
    
# @app.callback(
    # dash.dependencies.Output('title_bargraph','children'),
    # [dash.dependencies.Input('map_year', 'hoverData')]
# )
# def set_title_bargraph(hoverData):
    # a = get_hover_point(hoverData)
    # return a
    

    
@app.callback(
    dash.dependencies.Output('bargraph','figure'),
    [dash.dependencies.Input('map_date', 'hoverData')]
)
def set_map(hoverData):
    text = get_hover_point(hoverData)
    a = stations[stations["NOM_GARE"] == text]
    liste = a.index.values.tolist()
    liste0 = str(liste[0])
    weekday_list = validday2.loc[validday2["LIBELLE_ARRET"] == liste0,"WEEKDAY"].tolist()
    return  {
                'data': [
                    {'x': [weekday_str.get(wd) for wd in weekday_list], 
                     'y': validday2.loc[validday2["LIBELLE_ARRET"] == liste0,"NB_VALD"].tolist(), 
                     'type': 'bar', 'name': liste0},
                ],
                
                'layout': {
                    'title': liste0
                }
            }

    
    

@app.callback(
    dash.dependencies.Output('map_date','figure'),
    [dash.dependencies.Input('dropdown_element', 'value'),
     dash.dependencies.Input('slider_element', 'value'),
     dash.dependencies.Input('dropdown_element2', 'value')]
)
def set_map(selected_data, num_slider, lines_list):
    
    if selected_data == "default":
        selected_data = stations
    else :
        selected_data = stations[stations["RESEAU"] == selected_data]

    date_slider = dates[num_slider]
    
    #print("date_slider : ", date_slider)
    #for line in list(selected_data["RES_COM"].unique()):
    
    #selected_data = stations.reindex(lines_list)
    # print(lines_list.keys())
    # print(type(lines_list))
    # print("-------------------------")
    
    return {
        'data': [ 
        go.Scattermapbox(
            lat= selected_data.loc[selected_data["RES_COM"] == ligne,"LATITUDE"].astype(str).tolist(), 
            lon= selected_data.loc[selected_data["RES_COM"] == ligne,"LONGITUDE"].astype(str).tolist(), 
            mode = 'markers',
            marker = dict(size = get_marks_size(ligne,date_slider,0.00075), opacity=0.55, color = colors.loc[ligne,"COLOR_HEX"]),
            text = (selected_data.loc[selected_data["RES_COM"] == ligne,"NOM_GARE"].astype(str)),
            name = ligne
        ) for ligne in list(selected_data["RES_COM"].unique())
        ],
        
        'layout': {
            'mapbox': {
                'accesstoken': ("pk.eyJ1IjoieWlmZW4iLCJhIjoiY2pudWdpYTh0MHc0eTNrczU0Z25ra2Z5aSJ9.20-X0Cqm_r3r3wWAi4o_Rg"),
                'center' : dict(lat=48.866667,lon=2.333333),
                'zoom': 11
            },
            'margin': {
                'l': 0, 'r': 0, 'b': 0, 't': 0
            },
            'autosize':True
            #'width':1300,
            #'height':500
        }
    }
    
    
    
@app.callback(
    dash.dependencies.Output('dropdown_element2','options'),
    [dash.dependencies.Input('dropdown_element', 'value')]
)
def set_stations_options(selected_data):
    
    if selected_data == "default":
        selected_data = stations
    else :
        selected_data = stations[stations["RESEAU"] == selected_data]
        
    return [{"label":line, "value":line} for line in list(selected_data["RES_COM"].unique())]

  
# @app.callback(
    # dash.dependencies.Output('dropdown_element2','value'),
    # [dash.dependencies.Input('dropdown_element', 'value')]
# )
# def set_stations_options(selected_data):
    
    # if selected_data == "default":
        # selected_data = stations
    # else :
        # selected_data = stations[stations["RESEAU"] == selected_data]
        
    # return [{"label":line, "value":line} for line in list(selected_data["RES_COM"].unique())]
    

if __name__ == '__main__':
    app.run_server(debug=True)