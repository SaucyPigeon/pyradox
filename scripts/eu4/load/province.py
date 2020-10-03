import os
import math

import pyradox

parse_provinces, get_provinces = pyradox.load.load_functions('EU4', 'provinces', ('history', 'provinces'))

def get_province_name(province_id):
    """
    Gets the name a country by its tag according to localisation.
    """
    key = 'PROV%d' % province_id
    return pyradox.yml.get_localisation(key)

def province_cost(province):
    cost = 0
    if 'base_tax' in province:
        cost += province['base_tax'] * 0.5
            
    if 'base_production' in province:
        cost += province['base_production'] * 0.5
        if 'trade_goods' in province and province['trade_goods'] == 'gold':
            cost += province['base_production'] * 3.0
        
    if 'base_manpower' in province:
        cost += province['base_manpower'] * 0.5

    if 'extra_cost' in province:
        cost += province['extra_cost']

    # TODO: terrain mult

    if cost > 0:
        return math.floor(cost)
    else:
        return None
