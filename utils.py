import os
import json
import yaml 
from openai import OpenAI, AzureOpenAI
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def load_yaml(file):
    with open(file) as f:
        return yaml.safe_load(f)

def load_json(file):
    with open(file, 'r') as f:
        return json.load(f)
    
def load_txt(file):
    with open(file, 'r') as f:
        return f.read()


def pretty_print(data, in_format='json'):
    if in_format == 'json':
        print(json.dumps(data, indent=4))

    elif in_format == 'yaml':
        print(yaml.dump(data))

    elif in_format == 'txt':
        print(data)
    # to do: add more formats as needed
    pass

def pretty_print_respact_prompt(data, prefixes):
    # random sample one prompt per task type - there are 3 prompts per task type
    for i, (k, v) in enumerate(prefixes.items()):
        n = np.random.randint(0,3)
        print(data[f'react_{v}_{n}'])
        print('\n')

def save_json(data, file):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4) # indent=4 for pretty print

def save_dict_to_json(data, file):
    with open(file , 'w') as f:
        json.dump(data, f, indent=4)

# create combined prompt json file from each txt file
        
def create_combined_prompt_json(data_path, output_path):
    data = {}
    for file in os.listdir(data_path):
        if file.endswith('.txt'):
            with open(os.path.join(data_path, file), 'r') as f:
                f_name = file.split('.')[0]
                data[f_name] = f.read()
    save_json(data, output_path)

# create_combined_prompt_json('data', 'data/prompts.json')
    
def load_combined_prompt_json(file):
    return load_json(file)


# Openai tools
def get_openai_client(use_azure=True):
    if use_azure:
        client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2024-05-01-preview"
        )
    else:
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
    return client
    

def calculate_success_rate(rs, cnts):
    return sum(rs) / sum(cnts) if sum(cnts) > 0 else 0

def visualize_results(rs, cnts, categories):
    success_rate = calculate_success_rate(rs, cnts)
    
    # 1. Bar plot of rewards by category
    plt.figure(figsize=(12, 6))
    sns.barplot(x=categories, y=rs)
    plt.title('Rewards by Category')
    plt.xlabel('Category')
    plt.ylabel('Total Reward')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    # 2. Pie chart of task distribution
    plt.figure(figsize=(10, 10))
    plt.pie(cnts, labels=categories, autopct='%1.1f%%', startangle=90)
    plt.title('Distribution of Tasks Across Categories')
    plt.axis('equal')
    plt.show()

    # 3. Heatmap of success rate by category
    success_rates = [r/c if c > 0 else 0 for r, c in zip(rs, cnts)]
    plt.figure(figsize=(12, 6))
    sns.heatmap([success_rates], annot=True, xticklabels=categories, yticklabels=['Success Rate'], cmap='YlGnBu')
    plt.title('Success Rate by Category')
    plt.tight_layout()
    plt.show()

    # Print overall success rate
    print(f"Overall Success Rate: {success_rate:.2%}")

def update_results(rs, cnts, category_index, reward):
    rs[category_index] += reward
    cnts[category_index] += 1
    return rs, cnts


# function to analyze data - number of games files in each split, number of game files for each task type, number of trials per task

def analyze_data(data_path):
    splits = os.listdir(data_path) 
    task_categories = ['pick_and_place_with_movable_recep', 'pick_clean_then_place_in_recep', 'pick_heat_then_place_in_recep', 'pick_cool_then_place_in_recep', 'look_at_obj_in_light', 'pick_two_obj_and_place']
    num_games = {}
    num_files_per_task_per_split = {}
    file_path_per_task_per_split = {}

    for split in splits:
        if split.startswith('.'):
            continue
        num_games[split] = len(os.listdir(os.path.join(data_path, split)))

        for game in os.listdir(os.path.join(data_path, split)):
            # print(game)
            if game.startswith('.'):
                continue
            task_type = game.split('-')[0]
            # print(task_type)
            if task_type in task_categories:
                num_files_per_task_per_split[split] = num_files_per_task_per_split.get(split, {})
                num_files_per_task_per_split[split][task_type] = num_files_per_task_per_split[split].get(task_type, 0) + 1
                file_path_per_task_per_split[split] = file_path_per_task_per_split.get(split, {})
                file_path_per_task_per_split[split][task_type] = file_path_per_task_per_split[split].get(task_type, []) + [os.path.join(data_path, split, game)]
                # num_files_per_task[task_type] = num_files_per_task.get(task_type, 0) + 1
                # file_path_per_task[task_type] = file_path_per_task.get(task_type, []) + [os.path.join(data_path, split, game)]
    # save files to json
    print("Number of games in each split: ")
    pretty_print(num_games)
    print("Number of game files for each task type: ")
    pretty_print(num_files_per_task_per_split)
    print("Saving file path per task to data/file_path_per_task.json")
    save_json(file_path_per_task_per_split, 'data/file_path_per_task_per_split.json')
    return num_games, num_files_per_task_per_split, file_path_per_task_per_split


            
