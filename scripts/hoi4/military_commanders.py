import hoi4
import re
import os
import hoi4


import pyradox



def compute_country_tag_and_name(filename):
    m = re.match('.*([A-Z]{3})\s*-\s*(.*)\.txt$', filename)
    return m.group(1), m.group(2)

def list_commander_traits(k, v):
    if 'traits' not in v: return ''
    result = ''
    for trait in v.find_all('traits'):
        if not isinstance(trait, str): continue
        result += '{{iconify|' + pyradox.yml.get_localisation(trait, game = 'HoI4') + '}}, '
    return result[:-2]

commander_type_keys = {
    'create_field_marshal' : 'Field Marshal',
    'create_corps_commander' : 'General',
    'create_navy_leader' : 'Admiral',
    }

columns = (
    ('Country', '{{flag|%(country)s}}', None),
    ('Name', '%(name)s', None),
    ('Type', lambda k, v: commander_type_keys[k], None),
    ('Skill', '%(skill)d', None),
    ('Traits', list_commander_traits, None),
    )

commanders = pyradox.Tree()

for filename, country in pyradox.txt.parse_dir(os.path.join(pyradox.get_game_directory('HoI4'), 'history', 'countries')):
    tag, _ = compute_country_tag_and_name(filename)
    ruling_party = country['set_politics']['ruling_party']
    country_name = pyradox.yml.get_localisation('%s_%s' % (tag, ruling_party), game = 'HoI4')
    for commander_type_key in commander_type_keys.keys():
        for leader in country.find_all(commander_type_key):
            leader['country'] = country_name
            commanders.append(commander_type_key, leader)

out = open("out/military_commanders.txt", "w", encoding="utf-8")
out.write(pyradox.table.make_table(commanders, 'wiki', columns, sort_function = lambda key, value: (value['country'], key, value['name'])))
out.close()
