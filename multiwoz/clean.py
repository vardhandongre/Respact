import json

file_name = "eval_result_online-40.json"
new_file_name = "eval_result_online-40-1.json"

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
