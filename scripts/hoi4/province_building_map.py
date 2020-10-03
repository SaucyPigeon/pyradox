import hoi4
import os
import math
import re
import collections

import pyradox


from PIL import Image

building_type = 'naval_base'

scale = 2.0

# Load states.
states = pyradox.txt.parse_merge(os.path.join(pyradox.get_game_directory('HoI4'), 'history', 'states'), verbose=False)
province_map = pyradox.worldmap.ProvinceMap(game = 'HoI4')

colormap = {}
textmap = {}

for state in states.values():
    if 'buildings' not in state['history']:
        continue
    for province_id, buildings in state['history']['buildings'].items():
        if isinstance(province_id, int) and building_type in buildings:
            count = buildings[building_type]
            textmap[province_id] = '%d' % count
            colormap[province_id] = pyradox.image.colormap_red_green((count - 1) / 9)

# Create a blank map and scale it up 2x.
out = province_map.generate_image(colormap, default_land_color=(255, 255, 255), edge_color=(191, 191, 191))
# out = out.resize((out.size[0] * scale, out.size[1] * scale), Image.NEAREST)

# unfortunately lakes don't have unitstacks.txt
province_map.overlay_text(out, textmap, fontfile = "tahoma.ttf", fontsize = 9, antialias = False)
out.save('out/%s_map.png' % building_type)
#pyradox.image.save_using_palette(out, 'out/province__id_map.png')
