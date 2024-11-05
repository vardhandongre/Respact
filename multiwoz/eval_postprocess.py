import argparse
import itertools
import json
import re

from mapping import ACTION_DOMAINS, DOMAIN_FINITE_KEYS
from tqdm import tqdm

from utils import delexicalize
from utils.nlp import normalize

parser = argparse.ArgumentParser()
parser.add_argument("--file_name", type=str, default="eval_result-46-1.json")
parser.add_argument("--new_file_name", type=str, default="eval_result-46-ready.json")
args = parser.parse_args()

file_name = args.file_name
new_file_name = args.new_file_name

with open(file_name, "r") as f:
    result = json.load(f)

def api2state(api_inputs):
    attraction_slots = ["attraction-name", "attraction-type", "attraction-area"]
    hotel_slots = ["hotel-name", "hotel-type", "hotel-parking", "hotel-area", "hotel-bookday", "hotel-bookstay", "hotel-internet", "hotel-bookpeople", "hotel-stars", "hotel-pricerange"]
    restaurant_slots = ["restaurant-name", "restaurant-food", "restaurant-area", "restaurant-bookday", "restaurant-booktime", "restaurant-bookpeople", "restaurant-pricerange"]
    taxi_slots = ["taxi-arriveby", "taxi-departure", "taxi-leaveat", "taxi-destination"]
    train_slots = ["train-arriveby", "train-day", "train-leaveat", "train-destination", "train-departure", "train-bookpeople"]
    total_slots = list(itertools.chain.from_iterable([attraction_slots, hotel_slots, restaurant_slots, taxi_slots, train_slots]))
    domain_list = ["attraction", "hotel", "restaurant", "taxi", "train"]
    query_only_domain_list = ["taxi"]
    book_indicator_list = ["book", "buy"]
    prim_key_indicator_list = ["name", "ID"]
    
    current_domain = None
    for domain in domain_list:
        if domain in api_inputs["action"]:
            current_domain = domain
    assert current_domain is not None

    is_book = None
    for domain in query_only_domain_list:
        if current_domain  == domain:
            is_book = False
    if is_book is None:
        for book_indicator in book_indicator_list:
            if book_indicator in api_inputs["action"]:
                is_book = True
    if is_book is None:
        is_book = False
    book = "book" if is_book else ""

    state = {}
    for api, api_input in api_inputs.items():
        neglect_book = False
        for prim_key_indicator in prim_key_indicator_list:
            if prim_key_indicator in api and is_book:
                neglect_book = True
        if api != "action":
            if not neglect_book:
                state_key = f"{current_domain}-{book}{api}".lower()
            else:
                state_key = f"{current_domain}-{api}".lower()
            if state_key in total_slots:
                state[state_key] = api_input

    return state

processed_result = dict()

dic = delexicalize.prepareSlotValuesIndependent()
bar = tqdm(result.items())
for sample_id, sample_content in bar:
    bar.set_description(sample_id)
    processed_sample_content = list()
    for turn_idx, turn_response in enumerate(sample_content["responses"]):
        turn_input = sample_content["action_inputs"][turn_idx]
        turn_output = sample_content["action_outputs"][turn_idx]
        turn_state = sample_content["states"][turn_idx]
        processed_turn_state = dict()
        for slot, slot_value in turn_state.items():
            if slot_value.lower() != "any":
                domain, slot = slot.split("-")
                if domain not in DOMAIN_FINITE_KEYS or slot not in DOMAIN_FINITE_KEYS[domain] or slot_value in DOMAIN_FINITE_KEYS[domain][slot]:
                    if domain not in processed_turn_state.keys():
                        processed_turn_state[domain] = dict()
                    processed_turn_state[domain][slot] = slot_value
        processed_turn_domains = list()
        for api_input in turn_input:
            action = api_input["action"]
            for domain in ACTION_DOMAINS:
                if domain in action:
                    processed_turn_domains.append(domain)
        if turn_response:
            bar.set_description(f"{sample_id}:{len(turn_response)}")
        if turn_response and len(turn_response) < 5000:
            try:
                processed_turn_response = normalize(turn_response)
            except:
                processed_turn_response = ""
            words = processed_turn_response.split()
            processed_turn_response = delexicalize.delexicalise(' '.join(words), dic)
            processed_turn_response = delexicalize.delexicaliseReferenceNumber(processed_turn_response, turn_input, turn_output)
            digitpat = re.compile(r'\d+')
            processed_turn_response = re.sub(digitpat, '[value_count]', processed_turn_response)
            processed_turn_response = delexicalize.fixDelex(processed_turn_response, processed_turn_state)
        else:
            processed_turn_response = ""
        processed_sample_content.append({"response": processed_turn_response, "state": processed_turn_state})
        # processed_sample_content.append({"response": processed_turn_response, "state": processed_turn_state, "active_domains": processed_turn_domains})
    processed_result[sample_id.replace(".json", "").lower()] = processed_sample_content

with open(new_file_name, "w") as f:
    json.dump(processed_result, f, indent=4)