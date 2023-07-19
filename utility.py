from random import randint

phonetic_alphabet = [  # TODO: Sci-fi names for the phonetic alphabet
    "Alpha",
    "Bravo",
    "Charlie",
    "Delta",
    "Echo",
    "Foxtrot",
    "Golf",
    "Hotel",
    "India",
    "Juliet",
    "Kilo",
    "Lima",
    "Mike",
    "November",
    "Oscar",
    "Papa",
    "Quebec",
    "Romeo",
    "Sierra",
    "Tango",
    "Uniform",
    "Victor",
    "Whiskey",
    "X-Ray",
    "Yankee",
    "Zulu"
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
