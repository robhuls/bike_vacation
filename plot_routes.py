import xml.etree.ElementTree as ElementTree
import os
import requests
import folium
from bs4 import BeautifulSoup
import pandas as pd
from fitparse import FitFile
from scrape_bigs import scrape_bigs
 
directory_to_process = '2023_Luxemburg'
big_numbers = list(range(24238, 24275))  # NATACHA Luxemburg
big_numbers = big_numbers + list(range(138, 151))
scrape_big_numbers = False  # Scrape big numbers
base_location = [50, 6.5]

os.chdir(directory_to_process)
if scrape_big_numbers:
    scrape_bigs(big_numbers)

colors = ['red', 'blue', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'lightblue', 'cadetblue', 'beige']

# Read the locations of the BIGS\
all_bigs = pd.read_csv('bigs.txt')

# Scrape the BIGS you claimed
print('Scraping the BIGs you claimed')
page = requests.get('https://www.bigcycling.eu/en/users/index/claims/user/4646/')
soup = BeautifulSoup(page.text, 'html.parser')
claimed_numbers = []
for link in soup.find_all('a'):
    if 'big/index/index/big' in link.get('href'):
        claimed_numbers.append(int(link.get('href').split('/')[-2]))

# Create a map
my_map = folium.Map(location=base_location, zoom_start=10)
folium.TileLayer('Stamen Toner').add_to(my_map)

# Add BIGS to the map
print('Adding BIG locations to the map')
for index, row in all_bigs.iterrows():
    tag = '{0}-{1}'.format(row['num'], row['name'])
    popup = folium.Popup(tag, parse_html=True)
    color = colors[row['zone']-1]
    if row['num'] in claimed_numbers:
        folium.Marker([row['lat'], row['lon']], popup=popup, icon=folium.Icon(color='green')).add_to(my_map)
    else:
        folium.Marker([row['lat'], row['lon']], popup=popup, icon=folium.Icon(color=color)).add_to(my_map)


def plot_gpx(gpx_filename, gpx_color):
    print('Adding', gpx_filename)
    tree = ElementTree.parse(gpx_filename)
    root = tree.getroot()
    lat_list = []
    lon_list = []
    for trkpt in root.iter('{http://www.topografix.com/GPX/1/0}trkpt'):  # From Tourenplaner
        lat_list.append(float(trkpt.attrib['lat']))
        lon_list.append(float(trkpt.attrib['lon']))
    for trkpt in root.iter('{http://www.topografix.com/GPX/1/1}trkpt'):  # From Strava
        lat_list.append(float(trkpt.attrib['lat']))
        lon_list.append(float(trkpt.attrib['lon']))
    gpx_path = [(gpx_lat, gpx_lon) for gpx_lat, gpx_lon in zip(lat_list, lon_list)]
    folium.PolyLine(gpx_path, color=gpx_color, weight=5).add_to(my_map)

# Added ridden gpx files
print(os.getcwd())
os.chdir('ridden')
for filename in os.listdir('.'):
    if 'gpx' in filename or 'GPX' in filename:
        plot_gpx(filename, 'blue')

# Add planned routes to map
os.chdir(os.path.join('..','planned'))
for filename in os.listdir('.'):
    if 'gpx' in filename or 'GPX' in filename:
        plot_gpx(filename, 'green')

# Add ridden files to map
os.chdir(os.path.join('..', 'ridden'))
for filename in os.listdir('.'):
    if 'fit' in filename:
        print('Adding ridden route', filename)
        fitfile = FitFile(filename)
        path = []
        for record in fitfile.get_messages('record'):
            lat = record.get_value('position_lat')  # semicircles, https://www.thisisant.com/forum/viewthread/6367/#6946
            lon = record.get_value('position_long')
            if lat is not None:  # I think this happens when the gps has no lock on the satellites
                # https://gis.stackexchange.com/questions/156887/conversion-between-semicircles-and-latitude-units
                lat_degrees = lat * (180 / 2 ** 31)
                lon_degrees = lon * (180 / 2 ** 31)
                path.append((lat_degrees, lon_degrees))
        folium.PolyLine(path, color='blue', weight=5).add_to(my_map)

# Read campsites and add them
os.chdir(os.path.join('..', 'autoroute'))
with open('campsites.txt') as fid:
    for line in fid.readlines():
        data = line.split(',')
        popup = folium.Popup(data[2], parse_html=True)
        folium.Marker([float(data[0]), float(data[1])], popup=popup, icon=folium.Icon(color='blue')).add_to(my_map)
        print('Adding', line.strip('\n'))
os.chdir('..')

# Read car routes and add them
os.chdir('autoroute')
for filename in os.listdir('.'):
    if 'gpx' in filename:
        plot_gpx(filename, 'red')
os.chdir('..')

print('Saving map')
folium.LayerControl().add_to(my_map)
my_map.save('vacation_planning.html')
