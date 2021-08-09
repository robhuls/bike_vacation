# Scrape the big site to obtain GPS coordinates
import requests


def scrape_bigs(big_numbers):
    bigs = {}

    # big_numbers.extend(range(101, 213))
    for big_number in big_numbers:  # After 866 we go to the special zone, 601..675=AT=zone 8, 676..825=IT=zone 9
        print('Retrieving', big_number)
        bigs[big_number] = {}
        page = requests.get('https://www.bigcycling.eu/en/big/index/index/big/{0:03}'.format(big_number))
        data = page.text

        lines = data.split('\n')
        for i, line in enumerate(lines):
            if 'GPS' in line:
                bigs[big_number]['lat'] = float(lines[i+1].split('/')[0].replace(',', '.'))
                bigs[big_number]['lon'] = float(lines[i+1].strip('<br />').split('/')[1].replace(',', '.'))
            elif 'title' in line:
                bigs[big_number]['name'] = line.split('<title>')[1].split('</title>')[0].split(' - ')[0]
            elif 'Rank Zone' in line:
                bigs[big_number]['zone'] = int(line.split('Zone')[1].split('(Claims)')[0])

    with open('bigs.txt', 'w', encoding='utf8') as fid:
        fid.write('num,name,lat,lon,zone\n')
        for num, data in bigs.items():
            print(data)
            fid.write('{0}, {1}, {2}, {3}, {4}\n'.format(num, data['name'], data['lat'], data['lon'], data['zone']))
