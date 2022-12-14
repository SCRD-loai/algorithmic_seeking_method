#!/usr/bin/env python
# coding: utf-8
#To be run using the Batch Mode tool in Astos
import pandas as pd
import math
import pymap3d as pm
from decimal import Decimal, ROUND_UP
import numpy as np
src= r'astos_source_file\wind_land_opti' #Location of files
df = pd.read_csv(src+r"\tri_out.csv",sep='\t', lineterminator='\r').replace(r'\n',' ', regex=True).head(-1) #Open Astos output
df.to_csv(src+r"\file_name.csv", mode='a', sep='\t',index=False, header=False) #Append Astos output to csv file
df = pd.read_csv(src+r"\file_name.csv",sep='\t', lineterminator='\r', header=None).replace(r'\n',' ', regex=True).head(-1) #Open appended file
df.columns = ["Latitude", "Longitude", "Azimuth", "Incl"] #Add header to appended file
df = df.astype(float) #Convert to float for math operations

idx = len(df)-1

cntr_in=[175,84] #Azimuth and Incliantion of nominal landing point

#The local coordinate origin
lat0 =  df['Latitude'].iloc[-1] #Lat first row of astos output
lon0 =  df['Longitude'].iloc[-1] #Long first row of astos output
h0 = 0     #height in meters

theta = np.radians(cntr_in[0]) #to deal with sign convention for different azimuths

#The point of interest  
lat = 57.6215123 #Where I want to land Longitude %%%
lon = -93.7042073 #Where I want to land Latitude %%% 

#cntr_pt simulation is (0,0) in ENU coordinates
#ENU grid centered at cntr_pt of [Az,Incl] inputs, calculate distance from where I want to land
nom_pt = pm.geodetic2enu(lat, lon, h0, lat0, lon0, h0) 

cntr_angl = math.atan2((nom_pt[1]), (nom_pt[0])) + theta
if cntr_angl <=0:
    cntr_angl = cntr_angl+2*math.pi
    

x=7.5 #Azimuth first guess magnitude
y=0.625 #Inlicnation first guess magnitude

if len(df) >= 2:
    lat1 =  df['Latitude'].iloc[0]  # First simulation or center point latitude
    lon1 =  df['Longitude'].iloc[0] # First simulation or center point longitude
    #ENU grid centered at center point of [Az,Incl] inputs, calculate distance from first guess
    pt_dis  = pm.geodetic2enu(df['Latitude'].iloc[1], df['Longitude'].iloc[1], h0, lat1, lon1, h0)
    #ENU grid centered at last simulation and compares distance to where I want to land
    pt_nom1 =  pm.geodetic2enu(lat, lon, h0, lat0, lon0, h0) 

    #x Axis changes = Azimuth changes
    x=abs((df['Azimuth'].iloc[0]-df['Azimuth'].iloc[1])*(pt_nom1[0])/(pt_dis[0]))

    #y Axis changes = Inclination changes
    y=abs((df['Incl'].iloc[0]-df['Incl'].iloc[1])*(pt_nom1[1])/(pt_dis[1]))

    #Safety measures in case new inputs are 0
    if x == 0:
        x=float(Decimal((15/2**(idx))).quantize(Decimal('.1'), rounding=ROUND_UP))

    if y == 0:
        y=float(Decimal((1.25/2**(idx))).quantize(Decimal('.1'), rounding=ROUND_UP))

       
#After creating the ENU grid using the last simulation, move in the direction where you want to land
#Note that increasing/decreasing the inclination moves you further/closer from/to launch point 
quadrant = {
     0           <= cntr_angl <= math.pi/2   : [df['Azimuth'].iloc[-1]+x,df['Incl'].iloc[-1]-y], # Moving to quadrant 1 if theta is 0
     math.pi/2   <= cntr_angl <= math.pi     : [df['Azimuth'].iloc[-1]-x,df['Incl'].iloc[-1]-y], # Moving to quadrant 2 if theta is 0
     math.pi     <= cntr_angl <= 3*math.pi/2 : [df['Azimuth'].iloc[-1]-x,df['Incl'].iloc[-1]+y], # Moving to quadrant 3 if theta is 0
     3*math.pi/2 <= cntr_angl <= 2*math.pi   : [df['Azimuth'].iloc[-1]+x,df['Incl'].iloc[-1]+y]  # Moving to quadrant 4 if theta is 0
}

crnr_in = quadrant.get(True)

#Setting Azimuth and Inclination boundaries around possible inputs
if crnr_in[0] > cntr_in[0]+30:
    crnr_in[0] = cntr_in[0]+30
    
if crnr_in[0] < cntr_in[0]-30:
    crnr_in[0] = cntr_in[0]-30
    
if crnr_in[1] > 88:
    crnr_in[1] = 88
    
if crnr_in[1] < 83:
    crnr_in[1] = 83

#Save new inputs to csv file for Astos to read
astos_input = pd.DataFrame(crnr_in).T
astos_input.to_csv(src+r"\tri_input.txt", sep='\t',index=False, header=False) #append astos output to file

#To deal with empty line in csv file so Astos can correctly read it
with open(src+r"\tri_input.txt", 'r+') as f:
    f.seek(0,2)                    
    size=f.tell()               
    f.truncate(size-2)

