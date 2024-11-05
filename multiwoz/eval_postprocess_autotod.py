import json
from utils.nlp import normalize
from mapping import ACTION_DOMAINS
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--file_name", type=str, default="eval_result_online-41-1.json")
parser.add_argument("--new_file_name", type=str, default="eval_result_online-41-1-ready.json")
args = parser.parse_args()

file_name = args.file_name
new_file_name = args.new_file_name

with open(file_name, "r") as f:
    result = json.load(f)
with open("MultiWOZ2.4-main/data/mwz24/data.json", "r") as f:
    old_data = json.load(f)

processed_result = dict()

for sample_id, sample_content in result.items():
    cost = 0.0
    dialog_pred = list()
    for turn_idx, turn_response in enumerate(sample_content["responses"]):
        turn_question = sample_content["questions"][turn_idx]
        dialog_pred.append({"turn_idx": turn_idx+1, "user": turn_question, "agent": turn_response})
    goals = dict()
    for domain, domain_content in sample_content["goal_info"].items():
        if len(domain_content) != 0 and domain in ACTION_DOMAINS:
             goals[domain] = domain_content
    goal_messages = sample_content["goal_info"]["message"]
    dialog_refer = list()
    for turn_idx in range(0, len(old_data[sample_id]["log"]), 2):
        dialog_refer.append({"turn_idx": turn_idx//2+1, "user": old_data[sample_id]["log"][turn_idx]["text"], "agent": old_data[sample_id]["log"][turn_idx+1]["text"]})
    finish_status = sample_content["finish_status"] if "finish_status" in sample_content else "dialogue ends"
    processed_result[sample_id] = {"cost": cost, "dialog_pred": dialog_pred, "goals": goals, "goal_messages": goal_messages, "dialog_refer": dialog_refer, "finish_status": finish_status}

with open(new_file_name, "w") as f:
    json.dump(processed_result, f, indent=4)