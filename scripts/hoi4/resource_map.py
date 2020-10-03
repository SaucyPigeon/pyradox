import hoi4
import os
import math
import re
import collections

import pyradox


from PIL import Image

game = 'HoI4'

scale = 2.0

colormap_power = 1.0

# Load states.
states = pyradox.txt.parse_merge(os.path.join(pyradox.get_game_directory(game), 'history', 'states'), verbose=False)
province_map = pyradox.worldmap.ProvinceMap(game = game)

# provinces -> state id
groups = {}
colormap = {}

for state in states.values():
    if 'resources' in state:
        resources = sum(state['resources'].values())

        k = []
        for province_id in state.find_all('provinces'):
            if not province_map.is_water_province(province_id):
                k.append(province_id)
                x = (resources / 150.0) ** colormap_power
                colormap[province_id] = pyradox.image.colormap_red_green(x)
        k = tuple(x for x in k)
        groups[k] = '%d' % resources

# Create a blank map and scale it up 2x.
out = province_map.generate_image(colormap, default_land_color=(255, 255, 255), edge_color=(191, 191, 191), edge_groups = groups.keys())
# out = out.resize((out.size[0] * scale, out.size[1] * scale), Image.NEAREST)

province_map.overlay_text(out, groups, fontfile = "tahoma.ttf", fontsize = 9, antialias = False)
out.save('out/resource_map.png')
#pyradox.image.save_using_palette(out, 'out/province__id_map.png')
