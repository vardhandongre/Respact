import json
import random
import re
import string

import rstr
from fuzzywuzzy import fuzz

from mapping import DOMAIN_FINITE_KEYS, FUZZY_KEYS, PRIMARY_KEYS

database = dict()
with open("MultiWOZ2.4/data/mwz24/MULTIWOZ2.4/restaurant_db.json", "r") as f:
    database["restaurant"] = json.load(f)
with open("MultiWOZ2.4/data/mwz24/MULTIWOZ2.4/hotel_db.json", "r") as f:
    database["hotel"] = json.load(f)
with open("MultiWOZ2.4/data/mwz24/MULTIWOZ2.4/attraction_db.json", "r") as f:
    database["attraction"] = json.load(f)
with open("MultiWOZ2.4/data/mwz24/MULTIWOZ2.4/train_db.json", "r") as f:
    database["train"] = json.load(f)
with open("MultiWOZ2.4/data/mwz24/MULTIWOZ2.4/taxi_db.json", "r") as f:
    db_str = f.read()
    db_str = db_str.replace("]\n ", "],\n ").replace("\'", "\"").replace(" :", ":").replace("[\n ", "{\n ")[:-2]+"}"
    database["taxi"] = json.loads(db_str)

def query_basic(q, domain, max_retrieval=10, fuzzy_ratio=80):
    try:
        json_re = re.compile("({.*})", flags=re.DOTALL)
        json_str = json_re.search(q).groups()[0]
        query = json.loads(json_str)
    except:
        return json.dumps({"result": None, "message": "Failure! Cannot parse the API inputs. Check your API input format!"})
    query = {slot: value for slot, value in query.items() if value.lower() != "any"}
    valid_items = []
    for database_item in database[domain]:
        valid = True
        for query_key, query_value in query.items():
            database_value = database_item.get(query_key, None)
            if database_value and query_value:
                database_value = normalize_state_slot_value(query_key, database_value)
                query_value = normalize_state_slot_value(query_key, query_value)
                if (domain not in DOMAIN_FINITE_KEYS) or (query_key not in DOMAIN_FINITE_KEYS[domain]) or (query_value in DOMAIN_FINITE_KEYS[domain][query_key]):
                    if query_key in FUZZY_KEYS[domain] and fuzz.partial_ratio(database_value, query_value) < fuzzy_ratio:
                        valid = False
                    if query_key == "arriveBy" and time_str_to_minutes(database_value) > time_str_to_minutes(query_value):
                        valid = False
                    if query_key == "leaveAt" and time_str_to_minutes(database_value) < time_str_to_minutes(query_value):
                        valid = False
                    if query_key not in FUZZY_KEYS[domain] and query_key not in ["arriveBy", "leaveAt"] and database_value != query_value:
                        valid = False
            if not valid:
                break
        if valid:
            if len(valid_items) == max_retrieval:
                return json.dumps({"result": valid_items, "message": "Too many retrieved results! Please query more accurately!"})
            valid_items.append(database_item)
    return json.dumps({"result": valid_items})

def book_basic(q, domain, fuzzy_ratio=80):
    primary_key = PRIMARY_KEYS[domain]["primary_key"]
    other_keys = PRIMARY_KEYS[domain]["other_keys"]
    try:
        json_re = re.compile("({.*})", flags=re.DOTALL)
        json_str = json_re.search(q).groups()[0]
        query = json.loads(json_str)
    except:
        return json.dumps({"result": None, "message": "Failure! Cannot parse the API inputs. Check your API input format!"})
    query = {slot: value for slot, value in query.items() if value.lower() != "any"}
    found = False
    if primary_key is None:
        found = True
    elif primary_key in query.keys() and (other_keys is None or set(other_keys).issubset(set(query.keys()))):
        for database_item in database[domain]:
            database_value = normalize_state_slot_value(primary_key, database_item.get(primary_key, None))
            query_value = normalize_state_slot_value(primary_key, query[primary_key])
            if primary_key in FUZZY_KEYS[domain] and fuzz.partial_ratio(database_value, query_value) >= fuzzy_ratio:
                found = True
            if primary_key not in FUZZY_KEYS[domain] and database_value == query_value:
                found = True
    if found:
        return json.dumps({"result": {"reference": generate_reference_number(8)}, "message": "Success! Reference number is returned!"})
    elif other_keys is not None and not set(other_keys).issubset(set(query.keys())):
        return json.dumps({"result": None, "message": "Failure! API keys are incomplete!"})
    else:
        return json.dumps({"result": None, "message": "Failure! No matched entity in database!"})

def query_restaurants(q):               
    return query_basic(q, "restaurant")

def book_restaurant(q):
    return book_basic(q, "restaurant")

def query_hotels(q):
    return query_basic(q, "hotel")

def book_hotel(q):
    return book_basic(q, "hotel")

def query_attractions(q):
    return query_basic(q, "attraction")

def query_trains(q):
    return query_basic(q, "train")

def buy_train_tickets(q):
    return book_basic(q, "train")

def book_taxi(q):
    ret = json.loads(book_basic(q, "taxi"))
    taxi_color = random.choice(database["taxi"]["taxi_colors"])
    taxi_type = random.choice(database["taxi"]["taxi_types"])
    taxi_phone = rstr.xeger(database["taxi"]["taxi_phone"][0])
    ret["result"]["type"] = f"{taxi_color} {taxi_type}"
    ret["result"]["phone"] = str(taxi_phone)
    del ret["result"]["reference"]
    return json.dumps(ret)

def unknown_action(q):
    return json.dumps({"result": None, "message": "Failure! Unknown API name!"})

def generate_reference_number(length=10):
    characters = string.ascii_uppercase + string.digits
    reference_number = ''.join(random.choice(characters) for _ in range(length))
    return reference_number


def normalize_state_slot_value(slot_name, value):
    """ Normalize slot value:
        1) replace too distant venue names with canonical values
        2) replace too distant food types with canonical values
        3) parse time strings to the HH:MM format
        4) resolve inconsistency between the database entries and parking and internet slots
    """
    
    def type_to_canonical(type_string): 
        if type_string == "swimming pool":
            return "swimmingpool" 
        elif type_string == "mutliple sports":
            return "multiple sports"
        elif type_string == "night club":
            return "nightclub"
        elif type_string == "guest house":
            return "guesthouse"
        return type_string

    def name_to_canonical(name, domain=None):
        """ Converts name to another form which is closer to the canonical form used in database. """

        name = name.strip().lower()
        name = name.replace(" & ", " and ")
        name = name.replace("&", " and ")
        name = name.replace(" '", "'")
        
        name = name.replace("bed and breakfast","b and b")
        
        if domain is None or domain == "restaurant":
            if name == "hotel du vin bistro":
                return "hotel du vin and bistro"
            elif name == "the river bar and grill":
                return "the river bar steakhouse and grill"
            elif name == "nando's":
                return "nandos"
            elif name == "city center b and b":
                return "city center north b and b"
            elif name == "acorn house":
                return "acorn guest house"
            elif name == "caffee uno":
                return "caffe uno"
            elif name == "cafe uno":
                return "caffe uno"
            elif name == "rosa's":
                return "rosas bed and breakfast"
            elif name == "restaurant called two two":
                return "restaurant two two"
            elif name == "restaurant 2 two":
                return "restaurant two two"
            elif name == "restaurant two 2":
                return "restaurant two two"
            elif name == "restaurant 2 2":
                return "restaurant two two"
            elif name == "restaurant 1 7" or name == "restaurant 17":
                return "restaurant one seven"

        if domain is None or domain == "hotel":
            if name == "lime house":
                return "limehouse"
            elif name == "cityrooms":
                return "cityroomz"
            elif name == "whale of time":
                return "whale of a time"
            elif name == "huntingdon hotel":
                return "huntingdon marriott hotel"
            elif name == "holiday inn exlpress, cambridge":
                return "express by holiday inn cambridge"
            elif name == "university hotel":
                return "university arms hotel"
            elif name == "arbury guesthouse and lodge":
                return "arbury lodge guesthouse"
            elif name == "bridge house":
                return "bridge guest house"
            elif name == "arbury guesthouse":
                return "arbury lodge guesthouse"
            elif name == "nandos in the city centre":
                return "nandos city centre"
            elif name == "a and b guest house":
                return "a and b guesthouse"
            elif name == "acorn guesthouse":
                return "acorn guest house"

        if domain is None or domain == "attraction":
            if name == "broughton gallery":
                return "broughton house gallery"
            elif name == "scudamores punt co":
                return "scudamores punting co"
            elif name == "cambridge botanic gardens":
                return "cambridge university botanic gardens"
            elif name == "the junction":
                return "junction theatre"
            elif name == "trinity street college":
                return "trinity college"
            elif name in ['christ college', 'christs']:
                return "christ's college"
            elif name == "history of science museum":
                return "whipple museum of the history of science"
            elif name == "parkside pools":
                return "parkside swimming pool"
            elif name == "the botanical gardens at cambridge university":
                return "cambridge university botanic gardens"
            elif name == "cafe jello museum":
                return "cafe jello gallery"

        return name

    def time_to_canonical(time):
        """ Converts time to the only format supported by database, e.g. 07:15. """
        time = time.strip().lower()

        if time == "afternoon": return "13:00"
        if time == "lunch" or time == "noon" or time == "mid-day" or time == "around lunch time": return "12:00"
        if time == "morning": return "08:00"
        if time.startswith("one o'clock p.m"): return "13:00"
        if time.startswith("ten o'clock a.m"): return "10:00"
        if time == "seven o'clock tomorrow evening":  return "07:00"
        if time == "three forty five p.m":  return "15:45"
        if time == "one thirty p.m.":  return "13:30"
        if time == "six fourty five":  return "06:45"
        if time == "eight thirty":  return "08:30"

        if time.startswith("by"):
            time = time[3:]

        if time.startswith("after"):
            time = time[5:].strip()

        if time.startswith("afer"):
            time = time[4:].strip()    

        if time.endswith("am"):   time = time[:-2].strip()
        if time.endswith("a.m."): time = time[:-4].strip()

        if time.endswith("pm") or time.endswith("p.m."):
            if time.endswith("pm"):   time = time[:-2].strip()
            if time.endswith("p.m."): time = time[:-4].strip()
            tokens = time.split(':')
            if len(tokens) == 2:
                return str(int(tokens[0]) + 12) + ':' + tokens[1] 
            if len(tokens) == 1 and tokens[0].isdigit():
                return str(int(tokens[0]) + 12) + ':00'
        
        if len(time) == 0:
            return "00:00"
            
        if time[-1] == '.' or time[-1] == ',' or time[-1] == '?':
            time = time[:-1]
            
        if time.isdigit() and len(time) == 4:
            return time[:2] + ':' + time[2:]

        if time.isdigit(): return time.zfill(2) + ":00"
        
        if ':' in time:
            time = ''.join(time.split(' '))

        if len(time) == 4 and time[1] == ':':
            tokens = time.split(':')
            return tokens[0].zfill(2) + ':' + tokens[1]

        return time

    def food_to_canonical(food):
        """ Converts food name to caninical form used in database. """

        food = food.strip().lower()

        if food == "eriterean": return "mediterranean"
        if food == "brazilian": return "portuguese"
        if food == "sea food": return "seafood"
        if food == "portugese": return "portuguese"
        if food == "modern american": return "north american"
        if food == "americas": return "north american"
        if food == "intalian": return "italian"
        if food == "italain": return "italian"
        if food == "asian or oriental": return "asian"
        if food == "english": return "british"
        if food == "australasian": return "australian"
        if food == "gastropod": return "gastropub"
        if food == "brutish": return "british"
        if food == "bristish": return "british"
        if food == "europeon": return "european"

        return food

    if slot_name in ["name", "destination", "departure"]:
        return name_to_canonical(value)
    elif slot_name == "type":
        return type_to_canonical(value)
    elif slot_name == "food":
        return food_to_canonical(value)
    elif slot_name in ["arrive", "leave", "arriveBy", "leaveAt", "time"]:
        return time_to_canonical(value)
    elif slot_name in ["parking", "internet"]:
        return "yes" if value == "free" else value
    else:
        return value

def time_str_to_minutes(time_string):
    if not re.match(r"[0-9][0-9]:[0-9][0-9]", time_string):
        return 0
    return int(time_string.split(':')[0]) * 60 + int(time_string.split(':')[1])

class actions_base(dict):
    def __getitem__(self, key):
        return super().get(key, unknown_action)

known_actions_dict = {
    "query_restaurants": query_restaurants,
    "book_restaurant": book_restaurant,
    "query_hotels": query_hotels,
    "book_hotel": book_hotel,
    "query_attractions": query_attractions,
    "query_trains": query_trains,
    "buy_train_tickets": buy_train_tickets,
    "book_taxi": book_taxi,
}
known_actions = actions_base()
for known_action_name, known_action in known_actions_dict.items():
    known_actions[known_action_name] = known_action

if __name__ == "__main__":
    action_input = {
        "destination": "stevenage",
        "day": "wednesday",
        "arriveBy": "15:00",
        "departure": "cambridge"
    }
    action_input = json.dumps(action_input)
    action_output = known_actions["query_trains"](action_input)
    print(action_output)