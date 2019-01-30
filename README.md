# French public transport visualization

Course unit : OUAP-4112  

Developers : Vincent Barbosa Vaz ; Cécile Pov

Teacher : Daniel Courivaud

## Case study on public transport in France

This project is based on public transport data in France.  
https://opendata.stif.info/explore/?sort=modified  

## Data

Datasets are in .csv format, from 300Ko to 40Mo.
We focused on Paris and its periphery.

- https://opendata.stif.info/explore/dataset/validations-sur-le-reseau-ferre-nombre-de-validations-par-jour-1er-sem/information/

- https://opendata.stif.info/explore/dataset/validations-sur-le-reseau-ferre-profils-horaires-par-jour-type-1er-sem/information/

- https://opendata.stif.info/explore/dataset/emplacement-des-gares-idf/information/

## Data pre-processing

Pre-processing is done launching the app.

## Packages installation

Project uses external packages.
Run init.py to install all the packages needed.

## Run

Please define proxy for ESIEE computers: http://147.215.1.189:3128

Run init.py firstly ! Attention, it can be long since it downloads all the data from web

In terminal :

```bash
python main.py
```

Then copy the URL into the navigator.
