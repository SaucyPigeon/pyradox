import _initpath
import os
import re
import collections
import colorsys


import pyradox


# colour conversions

# hsv(0->1,0->1,0->1) >>> rgb(0->1,0->1,0->1)
def hsv_01_to_rgb_01(hsv_01):
    rgb_01 = colorsys.hsv_to_rgb(hsv_01[0], hsv_01[1], hsv_01[2])
    return rgb_01

# rgb(0->1,0->1,0->1) >>> rgb(0->255,0->255,0->255)
# rgb_255 is _INT_ only
def rgb_01_to_rgb_255(rgb_01):
    rgb_255 = (int(round(rgb_01[0]* 255)), int(round(rgb_01[1] * 255)), int(round(rgb_01[2] * 255)))
    return rgb_255

# hsv(0->360,0->1,0->1) >>> hsv(0->1,0->1,0->1)
def hsv_360_to_hsv_01(hsv_360):
    hsv_01 = (hsv_360[0] / 360, hsv_360[1], hsv_360[2])
    return hsv_01



# hsv(0->1,0->1,0->1) >>> rgb(0->255,0->255,0->255)
def hsv_01_to_rgb_255(hsv_01):
    rgb_01 = hsv_01_to_rgb_01(hsv_01)
    rgb_255 = rgb_01_to_rgb_255(rgb_01)
    return rgb_255

# hsv(0->360,0->1,0->1) >>> rgb(0->255,0->255,0->255)
def hsv_360_to_rgb_255(hsv_360):
    hsv_01 = hsv_360_to_hsv_01(hsv_360)
    rgb_255 = hsv_01_to_rgb_255(hsv_01)
    return rgb_255

def hsv_dec_to_rgb_int(h, s, v):
    rgb_dec = color_sys.hsv_to_rgb(h, s, v)
    rgb_int = (rgb_dec[0] * 255, rgb_dec[1] * 255, rgb_dec[2] * 255)
    return rgb_int
 
province_map = pyradox.worldmap.ProvinceMap(game = 'CK3')

# dict<province id, string>
terrain = {}
terrain_file = r"C:\Program Files (x86)\Steam\steamapps\common\Crusader Kings III\game\common\province_terrain\00_province_terrain.txt"
file = open(terrain_file)
lines = file.readlines()
counter = 0
for line in lines:
    if counter > 0:
        content = line
        content = content.split('#')[0]
        content = content.lstrip()
        content = content.rstrip()

        if len(content) == 0:
            continue
        key_value = content.split('=')
        key_string = key_value[0]
        province_id = int(key_string)
        terrain_type = key_value[1]

        terrain[province_id] = terrain_type

    counter = counter + 1


colormap = {}

plains_color = hsv_01_to_rgb_255((0.1, 0.5, 0.8))

for province in terrain:
    terrain_type = terrain[province]
    if terrain_type == "plains":
        colormap[province] = plains_color
    elif terrain_type == "farmlands":
        colormap[province] = hsv_01_to_rgb_255((0, 1, 1))
    elif terrain_type == "hills":
        colormap[province] = hsv_360_to_rgb_255((29, 0.867, 0.353))
    elif terrain_type == "mountains":
        colormap[province] = hsv_01_to_rgb_255((0, 0, 0.392))
    elif terrain_type == "desert":
        colormap[province] = hsv_01_to_rgb_255((0.15, 1, 1))
    elif terrain_type == "desert_mountains":
        colormap[province] = hsv_01_to_rgb_255((0.7, 0.5, 0.15))
    elif terrain_type == "oasis":
        colormap[province] = hsv_01_to_rgb_255((0.7, 0.3, 0.8))
    elif terrain_type == "jungle":
        colormap[province] = (10, 60, 35)
    elif terrain_type == "forest":
        colormap[province] = hsv_01_to_rgb_255((0.3, 0.75, 0.7))
    elif terrain_type == "taiga":
        colormap[province] = hsv_01_to_rgb_255((0.4, 0.7, 0.6))
    elif terrain_type == "wetlands":        
        colormap[province] = hsv_01_to_rgb_255((0.5, 0.5, 0.6))
    elif terrain_type == "steppe":
        colormap[province] = (200, 100, 25)
    elif terrain_type == "floodplains":
        colormap[province] = hsv_01_to_rgb_255((0.7, 0.8, 0.6))
    elif terrain_type == "drylands":
        colormap[province] = (220, 45, 120)
    else:
        print("Unexpected terrain type " + terrain_type)
        raise Exception()

for water_province in province_map.water_provinces:
    #colormap[water_province] = (51, 67, 85)
    #rivers = (142, 232, 255)
    #lakes = 51, 67, 85
    #normal sea = (68, 107, 163)
    colormap[water_province] = (68, 107, 163)
for water_province in province_map.lake_provinces:
    # not a fan of this colour but it is good enough
    colormap[water_province] = (51, 67, 85)
for water_province in province_map.river_provinces:
    colormap[water_province] = (142, 232, 255)
for water_province in province_map.impassable_sea_provinces:
    colormap[water_province] = (51, 67, 85)
for impassable_province in province_map.impassable_provinces:
    colormap[impassable_province] = (36, 36, 36)



out = province_map.generate_image(colormap, default_land_color=plains_color)
out.save('out/terrain_map.png')
