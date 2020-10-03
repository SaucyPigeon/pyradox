import _initpath
import os
import re
import collections


import pyradox

        
province_map = pyradox.worldmap.ProvinceMap(game = 'CK3')

colormap = {}
for water_province in province_map.water_provinces:
    colormap[water_province] = (51, 67, 85)
for impassable_province in province_map.impassable_provinces:
    colormap[impassable_province] = (36, 36, 36)

out = province_map.generate_image(colormap, default_land_color=(127, 127, 127))
pyradox.image.save_using_palette(out, 'out/blank_map.png')
