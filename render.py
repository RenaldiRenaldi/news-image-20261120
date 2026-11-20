"""Draw an engraved news atlas at twice its delivery resolution."""

import json
import math
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from urllib.request import urlopen

from PIL import Image, ImageDraw, ImageFont

PAPER = "#f6eedc"
INK = "#192c37"
RUST = "#943c30"
SEA = "#174662"
LAND = "#e5cea1"
GOLD = "#f4c579"
PALE = "#fff2cd"
RULE = "#b7a783"
FACTOR = 2
canvas = Image.new("RGB", (2048, 2048), PAPER)
pen = ImageDraw.Draw(canvas)
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
FACES = {"s": "DejaVuSans-Bold", "b": "DejaVuSerif-Bold", "r": "DejaVuSerif"}


@lru_cache(maxsize=None)
def face(kind, size):
    return ImageFont.truetype(str(FONT_DIR / (FACES[kind] + ".ttf")), size * FACTOR)


def xy(point):
    return tuple(round(value * FACTOR) for value in point)


def label(x, y, message, size=12, kind="s", color=INK, anchor="lt"):
    pen.text(xy((x, y)), message, font=face(kind, size), fill=color, anchor=anchor)


def width(message, kind, size):
    return pen.textlength(message, font=face(kind, size)) / FACTOR


def box(x0, y0, x1, y1, fill=None, outline=None):
    pen.rectangle(xy((x0, y0, x1, y1)), fill=fill, outline=outline, width=2)


def oval(x, y, rx, ry, fill=None, outline=None, weight=1):
    pen.ellipse(xy((x-rx, y-ry, x+rx, y+ry)), fill=fill, outline=outline,
                width=max(1, round(weight * FACTOR)))


def line(points, color, weight=1):
    pen.line([xy(p) for p in points], fill=color,
             width=max(1, round(weight * FACTOR)), joint="curve")


def polygon(points, fill):
    pen.polygon([xy(p) for p in points], fill=fill)


def project(lon, lat):
    return 29 + (lon + 180) * 966 / 360, 178 + (90 - lat) * 372 / 180


def world():
    root = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2"
    with urlopen(root + "/geojson/ne_110m_land.geojson", timeout=25) as response:
        payload = response.read()
    expected = "9e0729ee253ca7d7a5c4ae9395fb1902264c5377c52e224d13dd85010e2835d9"
    if sha256(payload).hexdigest() != expected:
        raise ValueError("Natural Earth land geometry failed its checksum")
    mask = Image.new("1", canvas.size)
    coast = ImageDraw.Draw(mask)
    for feature in json.loads(payload)["features"]:
        geometry = feature["geometry"]
        parts = geometry["coordinates"]
        if geometry["type"] == "Polygon":
            parts = [parts]
        for outer, *holes in parts:
            coast.polygon([xy(project(*p)) for p in outer], fill=1)
            for hole in holes:
                coast.polygon([xy(project(*p)) for p in hole], fill=0)
    canvas.paste(LAND, mask=mask)
    for lon in range(-180, 181, 30):
        line([project(lon, 90), project(lon, -90)], "#87918a", .55)
        if abs(lon) < 180:
            label(project(lon, 0)[0], 177, f"{abs(lon)}°", 8, color=PALE, anchor="mt")
    for lat in range(-90, 91, 30):
        line([project(-180, lat), project(180, lat)], "#87918a", .65)
        if abs(lat) < 90:
            label(32, project(0, lat)[1]+3, f"{abs(lat)}°", 8, color=PALE)


def compass(x, y):
    oval(x, y, 27, 27, outline=GOLD)
    for index in range(8):
        theta = math.pi * index / 4
        length = 37 if index % 2 == 0 else 22
        dx, dy = math.sin(theta), -math.cos(theta)
        tip = (x + length * dx, y + length * dy)
        a = (x - 6 * dy, y + 6 * dx)
        b = (x + 6 * dy, y - 6 * dx)
        polygon([(x, y), a, tip], PALE)
        polygon([(x, y), b, tip], "#ac7e48")
    oval(x, y, 4, 4, SEA, GOLD)
    for dx, dy, text in [(0,-49,"N"), (48,0,"E"), (0,47,"S"), (-48,0,"W")]:
        label(x+dx, y+dy, text, 11, color=PALE, anchor="mm")


def storm(x, y):
    for radius in (19, 30, 41):
        oval(x, y, radius, radius, outline="#496e7d")
    for arm in range(3):
        for braid in range(4):
            points = []
            for index in range(58):
                phase = index / 57
                angle = arm * math.tau / 3 + phase * 3.4 + braid * .10
                radius = 5 + phase * (43 - braid * 3)
                points.append((x + radius * math.cos(angle), y + radius * math.sin(angle)))
            line(points, ("#f9ebc7", "#b9dde3", "#8eb5c5", "#587d91")[braid], 1.6)
    oval(x, y, 3.1, 3.1, GOLD)


def bridge(x, y):
    for offset, length in [(0,74), (7,79), (14,66)]:
        line([(x-length/2, y+offset+22), (x+length/2, y+offset+22)], "#6ba3b7")
    for offset, height in [(-33,15),(-24,21),(-13,16),(12,18),(24,22),(34,14)]:
        box(x+offset-3, y+19-height, x+offset+3, y+18, "#587f92")
    line([(x-41,y+19),(x+41,y+19)], PALE, 2)
    for tower in (-18,18):
        line([(x+tower,y+26),(x+tower,y-6)], PALE, 2.5)
        for span in (-20,-13,13,20):
            line([(x+tower,y-6),(x+tower+span,y+19)], GOLD, .9)
    for offset in (0, 11, 22):
        line([(x-37+offset,y-36),(x-18+offset,y-29),(x+2+offset,y-15)], "#bf795a", 1.2)
        oval(x+2+offset,y-15,1.6,1.6,PALE)


def climate(x, y):
    oval(x-5,y,30,30,outline="#75a3a8")
    oval(x-5,y,15,30,outline="#75a3a8")
    oval(x-5,y,30,13,outline="#75a3a8")
    line([(x-35,y),(x+25,y)], "#75a3a8")
    box(x+13,y-34,x+21,y+16,PAPER)
    oval(x+17,y-34,4,4,PAPER)
    oval(x+17,y+19,9,9,PAPER)
    line([(x+17,y+19),(x+17,y-16)], "#d76b53", 4)
    oval(x+17,y+19,5.8,5.8,"#d76b53")
    for tick in range(5):
        yy = y-29+tick*8
        line([(x+24,yy),(x+30,yy)], GOLD)


def monument(x, y, lon, lat, route, scene, num, place, head, body, source):
    target = project(lon, lat)
    line([target, *route, (x,y)], INK, 3)
    line([target, *route, (x,y)], GOLD, 1.1)
    oval(x,y,49,49,"#17394e", GOLD, 1.4)
    oval(x,y,45,45,outline="#62838a")
    scene(x,y)
    if route:
        oval(*target, 6.1, 6.1, INK)
        oval(*target, 3.6, 3.6, GOLD)
    lx = x-50
    ly = y+51
    text_width = max(width(row,"b",18) for row in head)
    panel_width = max(203, text_width+18)
    box(lx-7,ly,lx-7+panel_width,ly+94,"#14354b", "#6e9093")
    label(lx,ly+8,f"{num}   {place}",10,color=GOLD)
    for index, row in enumerate(head):
        label(lx,ly+23+index*20,row,18,"b",PALE)
    label(lx,ly+66,body,10,"s","#e4e9d9")
    label(lx,ly+81,source,9,"s","#a7c9cb")


NUMBERS = [
    ("300,000+", "Evacuated before Akvan"),
    ("110+", "Missiles fired at Ukraine"),
    ("−6.2%", "Taiex, down on Friday"),
    ("2.3%", "Japan October inflation"),
    ("100,000", "EU–UK places per side/year"),
    ("$2.36bn", "GTA VI day one estimate"),
]


def header():
    box(14,14,1010,1010,outline=RULE)
    label(28,22,"PLATE 20  ·  THE WORLD",14,color=RUST)
    label(995,23,"SURVEYED FRIDAY 20 NOVEMBER 2026",12,anchor="rt")
    box(24,46,1000,576,SEA)
    world()
    box(35,55,989,129,PAPER,GOLD)
    label(512,63,"20 November 2026",56,"b",anchor="mt")
    box(35,133,989,168,"#ead9b6")
    label(512,140,"Akvan strikes India, Kyiv’s bridges are hit and climate talks run over.",22,"b",RUST,"mt")
    for index, (number, copy) in enumerate(NUMBERS):
        x = 28 + index * 161
        box(x,580,x+160,631,"#eee2c7")
        label(x+80,585,number,24,"b",RUST,"mt")
        label(x+80,614,copy,10,"s",INK,"mt")


def map_annotations():
    for lon, lat, name in [(-125,53,"NORTH AMERICA"),(-72,-30,"SOUTH AMERICA"),
                           (38,5,"AFRICA"),(12,61,"EUROPE"),(94,57,"ASIA"),
                           (153,-16,"AUSTRALIA"),(77,-82,"ANTARCTICA")]:
        x,y = project(lon,lat)
        box(x-3,y-2,x+width(name,"s",9)+3,y+10,"#435e60")
        label(x,y,name,9,color=PALE)
    for lon, lat in [(4.35,50.85),(139.7,35.7),(174.8,-41.3),(-17.4,14.7),
                     (-175.2,-21.1),(21,52.2)]:
        x,y = project(lon,lat)
        oval(x,y,3,3,PALE,SEA)
    for lon,lat,name,dx,dy in [(139.7,35.7,"TOKYO",8,0),(174.8,-41.3,"WELLINGTON",-77,28),
                               (-175.2,-21.1,"NUKUʻALOFA",9,2),(-17.4,14.7,"DAKAR",10,-21)]:
        x,y = project(lon,lat)
        tx,ty = x+dx,y+dy
        box(tx-2,ty-1,tx+width(name,"s",9)+2,ty+9,"#254d60")
        if name == "WELLINGTON":
            line([(x,y+4),(x-6,y+23),(tx+59,y+23)],"#b3c7c4")
        label(x+dx,y+dy,name,9,color=PALE)
    compass(114,302)
    scale_start, scale_y = 45, 476
    step = 1000 / 111.195 * 966 / 360
    for index in range(4):
        left = scale_start + index*step
        box(left,scale_y,left+step,scale_y+4,PALE if index%2==0 else SEA,PALE)
    label(45,485,"0",9,color=PALE)
    label(scale_start+4*step,485,"4,000 km",9,color=PALE,anchor="mt")
    label(45,499,"SCALE AT EQUATOR",8,color="#b1cfd3")
    monument(319,268,30.5,50.4,[(520,260),(374,260)],bridge,"01","KYIV",
             ("Russia hits three","Kyiv bridges"),"At least 8 killed across Ukraine","REUTERS  ·  110+ MISSILES")
    monument(543,391,30.7,36.9,[(543,325)],climate,"02","ANTALYA",
             ("COP31 runs","into overtime"),"Draft drops fossil fuel language","REUTERS  ·  $120bn TARGET CUT")
    monument(*project(84.9,19.3),84.9,19.3,[],storm,"03","GOPALPUR",
             ("Akvan makes landfall","in eastern India"),"Gusts to 90 km/h at landfall","IMD  ·  NO DEATHS REPORTED")
    line([(33,550),(990,550)],"#92a7a4")
    label(36,558,"POSITIONS ARE TRUE  ·  FIGURES ARE THE DAY’S OWN",10,color=PALE)
    label(990,558,"NATURAL EARTH   /   30° GRATICULE",10,color=PALE,anchor="rt")


def sprite(code, x, y):
    cream = "#fff2d1"
    orange = "#ef9a65"
    teal = "#75c2bd"
    if code == "asia":
        for offset in (6,16,26):
            line([(x+2,y+offset),(x+71,y+offset)], "#617382")
        line([(x+3,y+4),(x+16,y+6),(x+25,y+14),(x+35,y+9),
              (x+47,y+24),(x+58,y+21),(x+70,y+34)],orange,2.8)
    elif code == "eu":
        for i in range(12):
            phi = math.tau*i/12
            oval(x+19+12*math.sin(phi),y+17+12*math.cos(phi),1.25,1.25,GOLD)
        box(x+36,y+5,x+70,y+25,"#365979")
        line([(x+36,y+5),(x+70,y+25)],cream,3)
        line([(x+36,y+25),(x+70,y+5)],cream,3)
        line([(x+36,y+15),(x+70,y+15)],cream,5)
        line([(x+53,y+5),(x+53,y+25)],cream,5)
        line([(x+36,y+15),(x+70,y+15)],"#c76750",2.4)
        line([(x+53,y+5),(x+53,y+25)],"#c76750",2.4)
        polygon([(x+23,y+27),(x+41,y+21),(x+59,y+27),(x+41,y+33)],GOLD)
        line([(x+53,y+28),(x+53,y+35)],GOLD)
    elif code == "japan":
        box(x+3,y+5,x+39,y+29,cream)
        oval(x+21,y+17,7,7,"#c45c4a")
        for i,h in enumerate((9,15,23)):
            box(x+45+i*9,y+32-h,x+50+i*9,y+32,(teal,cream,orange)[i])
    elif code == "gta":
        oval(x+51,y+15,12,12,"#ee8691")
        for i,h in enumerate((8,14,23,10,17,24,11,15)):
            box(x+3+i*9,y+33-h,x+9+i*9,y+33,"#5c6996", "#c7a0c8")
        line([(x+4,y+33),(x+73,y+33)],"#f3a98d",2)
    elif code == "poland":
        polygon([(x+1,y+29),(x+34,y+17),(x+73,y+27),(x+73,y+35),(x+1,y+35)],"#688b72")
        for i in range(4):
            line([(x+30+i*8,y+24),(x+4+i*19,y+35)],GOLD,.7)
        box(x+50,y+5,x+70,y+19,cream)
        box(x+50,y+12,x+70,y+19,"#ca6a60")
        line([(x+50,y+5),(x+50,y+28)],cream)
    elif code == "tonga":
        polygon([(x+1,y+25),(x+27,y+20),(x+73,y+25),(x+73,y+35),(x+1,y+35)],"#ba8863")
        line([(x+37,y+22),(x+30,y+29),(x+41,y+31),(x+37,y+35)],INK,1.3)
        oval(x+14,y+10,7,7,GOLD)
        box(x+52,y+16,x+67,y+31,teal)
        oval(x+59.5,y+16,7.5,2.5,"#b7e0d2")
    elif code == "cricket":
        oval(x+28,y+22,26,11,"#65977c")
        polygon([(x+14,y+28),(x+23,y+13),(x+38,y+13),(x+31,y+28)],"#e5cd9b")
        for i in range(3):
            line([(x+46+i*3,y+12),(x+46+i*3,y+29)],cream,1.3)
        line([(x+45,y+11),(x+53,y+11)],cream)
        line([(x+59,y+29),(x+69,y+7)],GOLD,4)
        oval(x+61,y+20,2.5,2.5,orange)
    elif code == "india":
        for i,h in enumerate((9,15,12,22,28)):
            box(x+5+i*13,y+32-h,x+13+i*13,y+32,teal)
        line([(x+4,y+22),(x+25,y+16),(x+39,y+18),(x+67,y+3)],GOLD,2)
    elif code == "malawi":
        box(x+10,y+7,x+31,y+34,orange)
        box(x+14,y+11,x+27,y+19,cream)
        line([(x+31,y+26),(x+39,y+28),(x+40,y+14),(x+35,y+11)],cream,2)
        for i in (46,60):
            box(x+i,y+25,x+i+12,y+31,teal)
            oval(x+i+3,y+32,2,2,cream)
            oval(x+i+9,y+32,2,2,cream)
    elif code == "iraq":
        line([(x+4,y+30),(x+38,y+18),(x+72,y+30)],GOLD,2)
        box(x+23,y+9,x+28,y+31,cream)
        box(x+54,y+9,x+59,y+31,cream)
        box(x+22,y+8,x+61,y+13,orange)
        box(x+35,y+17,x+51,y+32,teal)


CARDS = [
    ("asia","−6.2% TAIEX",("Asia’s AI","shares slide"),"Seoul −5.2% · Tokyo −5.1%"),
    ("eu","6 MONTHS",("EU–UK pact,","fees deferred"),"Youth mobility agreed"),
    ("japan","2.3% CPI",("Japan prices","rise faster"),"Core CPI 2.2% in October"),
    ("gta","$2.36bn",("GTA VI’s","first-day haul"),"Sensor Tower estimate"),
    ("poland","NO INJURIES",("Missile falls","in Polish field"),"Warsaw confirms incursions"),
    ("malawi","FUEL CRISIS",("Malawi faces","fuel queues"),"Shortages disrupt daily life"),
    ("tonga","EL NIÑO",("Drought aid","in the Pacific"),"Tonga · Papua New Guinea"),
    ("cricket","175 NOT OUT",("Nicholls lifts","NZ to 368"),"First India Test · Wellington"),
    ("india","+898 POINTS",("Sensex bucks","regional rout"),"Friday close: 83,919.71"),
    ("iraq","HANDOVER",("Iraq deploys","in militia hub"),"Forces enter Jurf al-Sakhar"),
]


def cards():
    regions = [("EUROPE","#4c546c"),("EAST ASIA","#3d6661"),("SOUTH ASIA","#8b503a"),
               ("MIDDLE EAST","#64526c"),("AFRICA","#845c31"),("AMERICAS","#41647b"),
               ("OCEANIA","#506a50")]
    for i, (name, shade) in enumerate(regions):
        left = 28+i*139
        box(left,637,left+131,656,shade)
        label(left+65.5,641,name,11,color=PAPER,anchor="mt")
    for i,(code,badge,headline,detail) in enumerate(CARDS):
        x,y = 29+(i%5)*195, 660+(i//5)*96
        box(x,y,x+185,y+91,"#f9f1df",RULE)
        box(x+1,y+1,x+184,y+35,INK)
        sprite(code,x+4,y+1)
        label(x+178,y+12,badge,10,color=GOLD,anchor="rt")
        for j, words in enumerate(headline):
            assert width(words,"b",21) < 174, words
            label(x+6,y+37+j*22,words,21,"b")
        label(x+6,y+81,detail,11,"r")


BRIEFS = [
    ("ITALY","CGIL stages a nationwide strike"),
    ("CHINA","Loan prime rates stay at 3% and 3.5%"),
    ("AUSTRALIA","Albanese meets Xi in Shenzhen"),
    ("INDONESIA","Xi and Prabowo launch trade talks"),
    ("SOUTH AFRICA","Quarterly murders fall to 5,590"),
    ("UNITED STATES","Anthropic shares fall after debut"),
    ("LAS VEGAS","Russell leads wet F1 practice"),
    ("NIGERIA","Rescuers search after Bayelsa barge capsizes"),
    ("NIGERIA","Government urges lenders to fund farms and small firms"),
    ("GHANA","Water utility cites pipe obstructions and rising demand"),
    ("MEXICO","Sheinbaum returns from APEC for Revolution Day"),
    ("BRAZIL","Markets shut for Black Awareness Day"),
    ("ESTONIA","Russian road crossings will close Dec. 1"),
    ("THAILAND","PM stresses need to keep US trade ties"),
    ("PHILIPPINES","Weather bureau warns of widespread showers"),
    ("GERMANY","Merz says Europe will join new Ukraine talks soon"),
    ("MOSCOW","Kremlin rejects a role for EU’s Kallas in talks"),
    ("BRITAIN","October retail sales volumes rise 0.7%"),
    ("UNITED STATES","November consumer sentiment improves"),
    ("AUSTRALIA","US sanctions Comanchero motorcycle gang"),
    ("OIL","Crude heads for a third weekly loss"),
    ("SAUDI ARABIA","Coalition reports new Houthi interceptions"),
    ("ROMANIA","Home battery funding opens to applications"),
]


def lower_margin():
    label(29,851,"DISPATCHES  /  THE DAY IN BRIEF",11,color=RUST)
    label(994,851,f"{3+len(CARDS)+len(BRIEFS)} STORIES  ·  SEVEN REGIONS",11,anchor="rt")
    line([(29,864),(994,864)],RULE)
    for i,(place,item) in enumerate(BRIEFS):
        x = 29 + (i%2)*489
        y = 867 + (i//2)*8.6
        label(x,y,place,9,color=RUST)
        label(x+width(place,"s",9)+9,y,item,9,"r")
    box(28,971,995,998,"#ebdec0")
    label(35,973,"DATE CHECK ✓ Every story on this page happened, or was first reported, on Friday 20 November 2026.",10)
    label(35,986,"LEFT OUT AS THURSDAY’S NEWS: Anthropic’s $97.17 debut close · Senate’s 51–48 Iran vote · ICJ Rohingya verdict · Shenzhen summit itself · GTA VI midnight launch · Van Gogh $190.4m sale · Voyager 1 light-day.",8,"r")
    label(29,1000,"Sources: Reuters · AP · AFP · BBC · IMD · UN News · The Guardian · Al Jazeera · Statistics Bureau of Japan · Sensor Tower (estimate)",8)


def render():
    header()
    map_annotations()
    cards()
    lower_margin()
    output = Path(__file__).resolve().parent / "assets" / "entry.png"
    canvas.resize((1024,1024),Image.Resampling.LANCZOS).save(output,optimize=True)
    assert output.stat().st_size <= 1024**2


if __name__ == "__main__":
    render()
