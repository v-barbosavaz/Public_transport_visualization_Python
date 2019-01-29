datasets = ['emplacement-des-gares-idf.csv',
            'validations-sur-le-reseau-ferre-nombre-de-validations-par-jour-1er-sem.csv',
            'validations-sur-le-reseau-ferre-profils-horaires-par-jour-type-1er-sem.csv']
            
import urllib.request        
import os
#import pip._internal
#from pip import main
import importlib
import subprocess
import requests


url = "https://perso.esiee.fr/~barbosav/DRIO-4103C/DATA"

for file in datasets :
    dir = './data/external/'
    dirfile = dir + file
    if os.path.isfile(dirfile) == False :
        link = url + "/" + file
        response = requests.get(link)
        with open(os.path.join(dir, file), 'wb') as f:
            f.write(response.content)  
        
print("All files downloaded.")

packages = ["dash", 
            "dash.dependencies", 
            "dash_core_components",
            "dash_html_components",
            "plotly.plotly",
            "plotly.graph_objs",
            "json",
            "pandas",
            "numpy",
            "time",
            "math",
            "ast"]

            
            
# def install_and_import2(package):
    # try:
        # importlib.import_module(package)
    # except ImportError:
        # import pip
        # pip.main(['install', package])
    # # finally:
        # # globals()[package] = importlib.import_module(package)
        
        
def install_and_import2(package):
    try:
        importlib.import_module(package)
    except ImportError:
        #From pip._internal import main
        from pip import main as pip
        pip(['install', '--user', package])
        importlib.import_module(package)
        

def install_and_import(package):
    str = "pip install "+ package
    subprocess.call(str, shell=True)

        
for pkg in packages :
    install_and_import2(pkg)

print("All packages installed.")
    
# for file in datasets :
    # dir = './data/external/'
    # file = dir + file
    # if os.path.isfile(file) == False :
        # link = url + "/" + file
        # urllib.request.urlretrieve(url, file)  
        
# def install(package):
    # # if hasattr(pip, 'main'):
        # pip.main(['install', package])
    # # else:
        # # pip._internal.main(['install', package])
        
    

            
# import dash
# from dash.dependencies import Input, Output
# import dash_core_components as dcc
# import dash_html_components as html

# import plotly.plotly as py
# import plotly.graph_objs as go

# import json
# import pandas as pd
# import numpy as np
# import time
# import math
# import ast