import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("--file_name", type=str, default="eval_result-46-1.json")
parser.add_argument("--new_file_name", type=str, default="eval_result-46-ready.json")
args = parser.parse_args()

file_name = parser.file_name
new_file_name = args.new_file_name

with open(file_name, "r") as f:
    result = json.load(f)

new_result = dict()
problem_list = list()

for dialogue_idx, dialogue_content in result.items():
    if "error" in dialogue_content:
        print(dialogue_idx)
        problem_list.append(dialogue_idx)
    else:
        new_result[dialogue_idx] = dialogue_content

print(len(new_result))

with open(new_file_name, "w") as f:
    json.dump(new_result, f, indent=4)
