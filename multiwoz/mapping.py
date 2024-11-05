ACTION_DOMAINS = ["hotel", "restaurant", "attraction", "train", "taxi"]


# Useful when querying entities

FUZZY_KEYS = {
    "hotel" : {"name"},
    "attraction" : {"name", "type"},
    "restaurant" : {"name", "food"},
    "train" : {"departure", "destination"},
}

FINITE_KEYS = {
    "query_restaurants": {
        "area": ["centre", "north", "south", "east", "west"],
        "pricerange": ["cheap", "moderate", "expensive"],
    },
    "book_restaurant": {
        "day": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
    },
    "query_hotels": {
        "area": ["centre", "north", "south", "east", "west"],
        "internet": ["yes", "no"],
        "parking": ["yes", "no"],
        "pricerange": ["cheap", "moderate", "expensive"],
        "stars": ["0", "1", "2", "3", "4", "5"],
        "type": ["bed and breakfast", "guesthouse", "hotel"],
    },
    "book_hotel": {
        "day": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
    },
    "query_attractions": {
        "area": ["centre", "north", "south", "east", "west"],
    },
    "query_trains": {
        "day": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
    },
    "buy_train_tickets": {
        "day": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
    },
}

DOMAIN_FINITE_KEYS = {
    "restaurant": {
        "area": ["centre", "north", "south", "east", "west"],
        "pricerange": ["cheap", "moderate", "expensive"],
        "day": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
    },
    "hotel": {
        "area": ["centre", "north", "south", "east", "west"],
        "internet": ["yes", "no"],
        "parking": ["yes", "no"],
        "pricerange": ["cheap", "moderate", "expensive"],
        "stars": ["0", "1", "2", "3", "4", "5"],
        "type": ["bed and breakfast", "guesthouse", "hotel"],
        "day": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
    },
    "attraction": {
        "area": ["centre", "north", "south", "east", "west"],
    },
    "train": {
        "day": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
    },
}

# Useful when making reservations

PRIMARY_KEYS = {
    "hotel" : {"primary_key": "name", "other_keys": ["people", "day", "stay"]},
    "restaurant" : {"primary_key": "name", "other_keys": ["people", "day", "time"]},
    # "train" : {"primary_key": "trainID", "other_keys": ["people"]},
    "train" : {"primary_key": None, "other_keys": None},
    "taxi" : {"primary_key": None, "other_keys": None},
}


VALID_MAPPING = {
    "query_restaurants": {
        "area": ["centre", "north", "south", "east", "west"],
        "pricerange": ["cheap", "moderate", "expensive"],
        "food": None,
        "name": None,
    },
    "book_restaurant": {
        "name": None,
        "people": None,
        "day": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
        "time": None,
    },
    "query_hotels": {
        "area": ["centre", "north", "south", "east", "west"],
        "internet": ["yes", "no"],
        "name": None,
        "parking": ["yes", "no"],
        "pricerange": ["cheap", "moderate", "expensive"],
        "stars": ["0", "1", "2", "3", "4", "5"],
        "type": ["bed and breakfast", "guesthouse", "hotel"],
    },
    "book_hotel": {
        "name": None,
        "people": None,
        "day": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
        "stay": None,
    },
    "query_attractions": {
        "area": ["centre", "north", "south", "east", "west"],
        "name": None,
        "type": None,
    },
    "query_trains": {
        "arriveBy": None,
        "day": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
        "departure": None,
        "destination": None,
        "leaveAt": None,
        "trainID": None,
    },
    "buy_train_tickets": {
        "arriveBy": None,
        "day": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
        "departure": None,
        "destination": None,
        "leaveAt": None,
        "trainID": None,
        "people": None,
    },
    "book_taxi": {
        "arriveBy": None,
        "departure": None,
        "destination": None,
        "leaveAt": None,
    },
}

DOMAIN_VALID_MAPPING = {
    "restaurant": {
        "area": ["centre", "north", "south", "east", "west"],
        "pricerange": ["cheap", "moderate", "expensive"],
        "food": None,
        "name": None,
        "people": None,
        "day": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
        "time": None,
    },
    "hotel": {
        "area": ["centre", "north", "south", "east", "west"],
        "internet": ["yes", "no"],
        "name": None,
        "parking": ["yes", "no"],
        "pricerange": ["cheap", "moderate", "expensive"],
        "stars": ["0", "1", "2", "3", "4", "5"],
        "type": ["bed and breakfast", "guesthouse", "hotel"],
        "people": None,
        "day": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
        "stay": None,
    },
    "attraction": {
        "area": ["centre", "north", "south", "east", "west"],
        "name": None,
        "type": None,
    },
    "train": {
        "arriveBy": None,
        "day": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
        "departure": None,
        "destination": None,
        "leaveAt": None,
        "trainID": None,
        "people": None,
    },
    "taxi": {
        "arriveBy": None,
        "departure": None,
        "destination": None,
        "leaveAt": None,
    },
}

DESCRIPTION = {
    "restaurant": {
        "area": "the location of the restaurant (e.g. centre, north, south, east, west)",
        "pricerange": "the price range of the restaurant",
        "food": "the food type or cuisine of the restaurant",
        "name": "the name of the restaurant",
        "people": "the number of people of the booking",
        "day": "the day when the people go in a week",
        "time": "the time of the reservation",
    },
    "hotel": {
        "area": "the location of the hotel (e.g. centre, north, south, east, west)",
        "internet": "whether the hotel has internet connection",
        "name": "the name of the hotel",
        "parking": "whether the hotel has parking space",
        "pricerange": "the price range of the hotel",
        "stars": "the stars of the hotel",
        "type": "the type of the hotel (e.g. bed and breakfast, guesthouse, hotel)",
        "people": "the number of people of the booking",
        "day": "the day when the people go in a week",
        "stay": "the number of days of stay for the reservation",
    },
    "attraction": {
        "area": "the location of the attraction (e.g. centre, north, south, east, west)",
        "name": "the name of the attraction",
        "type": "the specific type of the attraction",
    },
    "train": {
        "arriveBy": "the arrival time of the train",
        "day": "the day when the people go in a week",
        "departure": "the departure station of the train",
        "destination": "the destination station of the train",
        "leaveAt": "the leaving time of the train",
        "trainID": "the ID of train to buy a ticket of",
        "people": "the number of people of the booking",
    },
    "taxi": {
        "arriveBy": "the arrival time of the taxi",
        "departure": "the departure address of the taxi",
        "destination": "the destination address of the taxi",
        "leaveAt": "the leaving time of the taxi",
    },
}