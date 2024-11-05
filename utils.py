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

def color_text(text, color):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"  # Resets the color to default
    }
    return colors[color] + text + colors["reset"]

# colored print
def cprint(text, color):
    print(color_text(text, color))

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

# emrecan
# export OPENAI_API_KEY="sk-hzgbLMGMBwMSggpzVXh5dVw9XWs82wAL4XrvdhvbNWT3BlbkFJoRn63AvdnQBtk7w1hJRqZ9Ldf7xPRcqtn-x3MWSv8A"
# conv-ai
# export AZURE_OPENAI_KEY="2907ee0316c7484784e43e81092087eb"

# Openai tools
def get_openai_client(use_azure=False):
    if use_azure:
        client = AzureOpenAI(
            azure_endpoint="https://uiuc-convai.openai.azure.com/",
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2024-02-15-preview"
        )
    else:
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
    return client
    

def calculate_success_rate(rs, cnts):
    return sum(rs) / sum(cnts) if sum(cnts) > 0 else 0

def visualize_results(method, exp_name, name, rs, cnts, categories):
    # to do: pass experiment name as argument to save results to a folder with the experiment name
    name = name.replace('/', '_')
    success_rate = calculate_success_rate(rs, cnts)
    
    # 1. Bar plot of rewards by category
    plt.figure(figsize=(12, 6))
    sns.barplot(x=categories, y=rs)
    plt.title('Rewards by Category')
    plt.xlabel('Category')
    plt.ylabel('Total Reward')
    plt.xticks(rotation=45)
    plt.tight_layout()
    # plt.show()
    plt.savefig(f'results/{method}/{exp_name}_{name}_rewards_by_category.png')

    # 2. Pie chart of task distribution
    plt.figure(figsize=(10, 10))
    plt.pie(cnts, labels=categories, autopct='%1.1f%%', startangle=90)
    plt.title('Distribution of Tasks Across Categories')
    plt.axis('equal')
    # plt.show()
    plt.savefig(f'results/{method}/{exp_name}_{name}_task_distribution.png')

    # 3. Heatmap of success rate by category
    success_rates = [r/c if c > 0 else 0 for r, c in zip(rs, cnts)]
    plt.figure(figsize=(12, 6))
    sns.heatmap([success_rates], annot=True, xticklabels=categories, yticklabels=['Success Rate'], cmap='YlGnBu')
    plt.title('Success Rate by Category')
    plt.tight_layout()
    # plt.show()
    # Save the success rates to a JSON file
    # save_json(dict(zip(categories, success_rates)), f'results/{exp_name}_{name}_success_rates.json')
    # Save plots to files
    plt.savefig(f'results/{method}/{exp_name}_{name}_success_rate_by_category.png')


    # Print overall success rate
    cprint(f"Overall Success Rate: {success_rate:.2%}", 'red')

def update_results(rs, cnts, category_index, reward):
    rs[category_index] += reward
    cnts[category_index] += 1
    return rs, cnts


# function to analyze data - number of games files in each split, number of game files for each task type, number of trials per task

def analyze_data(data_path):
    splits = os.listdir(data_path) 
    task_categories = ['pick_and_place_simple', 'pick_clean_then_place_in_recep', 'pick_heat_then_place_in_recep', 'pick_cool_then_place_in_recep', 'look_at_obj_in_light', 'pick_two_obj_and_place']
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


## Webshop Tools            
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np

class MetricsTracker:
    def __init__(self):
        self.episode_rewards = []
        self.success_rate = []
        self.failure_rate = []
        self.cumulative_avg_reward = []

    def update(self, reward, success, failure):
        self.episode_rewards.append(reward)
        self.success_rate.append(int(success))
        self.failure_rate.append(int(failure))
        self.cumulative_avg_reward.append(np.mean(self.episode_rewards))

    def plot_metrics(self):
        episodes = range(1, len(self.episode_rewards) + 1)

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 15))

        # Plot episode rewards
        ax1.plot(episodes, self.episode_rewards, label='Episode Reward')
        ax1.plot(episodes, self.cumulative_avg_reward, label='Cumulative Average Reward')
        ax1.set_xlabel('Episode')
        ax1.set_ylabel('Reward')
        ax1.set_title('Episode Rewards and Cumulative Average')
        ax1.legend()

        # Plot success rate
        ax2.plot(episodes, np.cumsum(self.success_rate) / episodes, label='Success Rate')
        ax2.set_xlabel('Episode')
        ax2.set_ylabel('Success Rate')
        ax2.set_title('Cumulative Success Rate')
        ax2.legend()

        # Plot failure rate
        ax3.plot(episodes, np.cumsum(self.failure_rate) / episodes, label='Failure Rate')
        ax3.set_xlabel('Episode')
        ax3.set_ylabel('Failure Rate')
        ax3.set_title('Cumulative Failure Rate')
        ax3.legend()

        plt.tight_layout()
        plt.show()