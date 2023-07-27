from random import randint

phonetic_alphabet = [  
    "Atlas",       
    "Binary",  
    "Calypso",
    "Deimos",
    "Eros",
    "Fusion",
    "Ganymede",
    "Hyperion", 
    "Io", 
    "Jupiter",
    "Kuiper",
    "Luna",
    "Mars",
    "Neptune",
    "Oberon", 
    "Pulsar",
    "Quasar",
    "Rhea",
    "Saturn",
    "Titan",
    "Uranus",
    "Venus", 
    "Warp",
    "Xena",
    "Ymir", 
    "Zodiac" 
]


# Takes an index (starting at 0) and returns the element of
# the phonetic alphabet corresponding to it. Repeats if 
# index is larger than the phonetic alphabet.
def phonetic_index(i):
    index = i
    repetitions = None
    if i < 0:
        index *= -1
    if i >= len(phonetic_alphabet):
        repetitions = i // len(phonetic_alphabet)
    name = phonetic_alphabet[i % len(phonetic_alphabet)]
    if repetitions is not None:
        name = "{} {}".format(name, repetitions + 1)
    return name


primary_system_names = [
    "Terra",
    "Gibby",
    "Omicron",
    "Reticuli",
    "Centauri",
    "Vega",
    "Altair",
    "Antares",
    "Markab",
    "Marklar",
    "Izar",
    "Arcturus",
    "Nunki",
    "Rigel",
    "Sirius",
    "Adhara",
    "Betelgeuse",
    "Procyon",
    "Pollux",
    "Aldebaran",
    "Castor",
    "Algol",
    "Mirpac",
    "Mirach",
    "Shedir",
    "Deneb",
    "Enif",
    "Nunki",
    "Polaris",
    "Ankaa",
    "Diphda",
    "Fomalhaut",
    "Achernar",
    "Hadar",
    "Canopus",
    "Spica",
    "Denebola",
    "Alphekka",
    "Dubhe",
    "Kochab",
    "Rasalhague",
    "Unukalhai",
    "Hamal",
    "Vindemiatrix",
    "Alcyone",
    "Acrux",
    "Alasia",
    "Alrakis",
    "Bubup",
    "Chara",
    "Cursa",
    "Dalim",
    "Danfeng",
    "Diadem",
    "Dziban",
    "Electra",
    "Eltanin",
    "Fafnir",
    "Fang",
    "Felis",
    "Gar",
    "Grumium",
    "Gumala",
    "Intan",
    "Itonda",
    "Jabbah",
    "Kang",
    "Karaka",
    "Kaveh",
    "Koeia",
    "Lich",
    "Mago",
    "Maia",
    "Maru",
    "Moriah",
    "Musica",
    "Naos",
    "Navi",
    "Nembus",
    "Nosaxa",
    "Ogma",
    "Orkaria",
    "Petra",
    "Rana",
    "Rastaban",
    "Sabik",
    "Sadr",
    "Sarin",
    "Tayi",
    "Tangra",
    "Tejat",
    "Thuban",
    "Uruk",
    "Wasat",
    "Wazn",
    "Xihe",
    "Alphabeetrium"
    # TODO: more
]

prefix_system_names = [
    "Nova",
    # TODO: more
]

secondary_system_names = [
    "Beta",
    "Alpha",
    "Omega",
    "Prime",
    "Secundus",
    # TODO: More
]

ai_empire_faction_post_labels = [
    "Union",
    "Republic",
    "Empire",
    "Federation",
    "Confederacy",
    "Polity",
    "Clique",
]

ai_empire_faction_pre_labels = [
    "Union of",
    "Empire of",
    "State of",
    "Kingdom of",
    "Duchy of",
    "Republic of",
]

# Takes a number and returns a string with Xst, Xnd, Xrd, Xth
def xthify(num): # oh, this is kinda tricky hehe
    stringified = "{}".format(num)
    listified = [i for i in stringified]
    listified.reverse()
    if len(listified) == 1:
        listified.append("2")
    last_digit = listified[0]
    if listified[1] == "1":
        return "{}th".format(num)
    elif last_digit == "1":
        return "{}st".format(num)
    elif last_digit == "2":
        return "{}nd".format(num)
    elif last_digit == "3":
        return "{}rd".format(num)
    return "{}th".format(num)

# Returns a click-and-drag rect based on two mouse positions
def click_and_drag_rect(start, end):
    x1 = start[0]
    x2 = end[0]
    y1 = start[1]
    y2 = end[1]
    if x1 == x2:
        rect = (min(x1, x2), y1, max(x1, x2) - min(x1, x2), 0)
    elif y1 == y2:
        rect = (x1, min(y1, y2), 0, max(y1, y2) - min(y1, y2))
    elif x1 > x2 and y1 > y2:
        rect = (x2, y2, x1 - x2, y1 - y2)
    elif x1 < x2 and y1 < y2:
        rect = (x1, y1, x2 - x1, y2 - y1)
    elif x1 > x2 and y1 < y2:
        rect = (x2, y1, x1 - x2, y2 - y1)
    elif x1 < x2 and y1 > y2:
        rect = (x1, y2, x2 - x1, y1 - y2)
    return rect # Uhh might need rect = None again let's find out

# returns a list with a number of d20 results
def d20(num_dice=1, bonus=0):
    results = [randint(1, 20) + bonus for _ in range(num_dice)]
    results.sort(reverse=True)
    return results

def coin_flip():
    return d20()[0] <= 5

# returns a list with a number of d100 results
def d100(num_dice=1, bonus=0):
    results = [randint(1, 100) + bonus for _ in range(num_dice)]
    results.sort(reverse=True)
    return results


# returns a list with a number of d1000 results
def d1000(num_dice=1, bonus=0):
    results = [randint(1, 1000) + bonus for _ in range(num_dice)]
    results.sort(reverse=True)
    return results

# returns a list with a number of d10000 results
def d10000(num_dice=1, bonus=0):
    results = [randint(1, 10000) + bonus for _ in range(num_dice)]
    results.sort(reverse=True)
    return results
