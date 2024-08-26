import os
import sys
import json
import openai
from openai import OpenAI
from utils import get_openai_client, calculate_success_rate, visualize_results, update_results, load_txt, load_json
from process_observations import process_ob
from llm_agent import gpt_agent as llm
from oracle import oracle_support

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from utils import calculate_success_rate, visualize_results, update_results


class BaseMethod:
    def __init__(self, main_prompt_file, method_prompt_file, env, use_oracle=False):
        self.main_prompt = self.load_txt(main_prompt_file)
        self.method_prompts = self.load_json(method_prompt_file)
        self.env = env
        self.use_oracle = use_oracle
        self.prefixes = {
            'pick_and_place': 'put',
            'pick_clean_then_place': 'clean',
            'pick_heat_then_place': 'heat',
            'pick_cool_then_place': 'cool',
            'look_at_obj': 'examine',
            'pick_two_obj': 'puttwo'
        }
        self.categories = list(self.prefixes.keys())

    def load_txt(self, file_path):
        with open(file_path, 'r') as file:
            return file.read().strip()

    def load_json(self, file_path):
        with open(file_path, 'r') as file:
            return json.load(file)

    def alfworld_run(self, prompt, ob='', to_print=True):
        raise NotImplementedError("Subclasses must implement alfworld_run method")

    def run(self, num_games=134):
        rs = [0] * 6
        cnts = [0] * 6
        periodic_success_rates = []
        cumulative_rewards = []

        for run in range(num_games):
            ob, info = self.env.reset()
            ob = '\n'.join(ob[0].split('\n\n')[1:])
            name = '/'.join(info['extra.gamefile'][0].split('/')[-3:-1])
            print("This is the gamefile and trial: \n")
            print(name)

            # Add oracle support if specified in the config
            if self.use_oracle:
                game_file = info['extra.gamefile'][0] # Get the game file path
                oracle_support(game_file)

            for i, (k, v) in enumerate(self.prefixes.items()):
                if name.startswith(k):
                    full_prompt = (self.main_prompt + 
                                   'Interact with a household to solve a task. Here are 2 examples.\n' + 
                                   self.method_prompts[f'{self.method_prefix}_{v}_0'] + 
                                   self.method_prompts[f'{self.method_prefix}_{v}_1'] + 
                                   '\nHere is the task.\n')
                    print(k, v)
                    r = self.alfworld_run(full_prompt, ob=ob)
                    rs[i] += r
                    cnts[i] += 1
                    break

            cumulative_rewards.append(sum(rs))
            current_success_rate = calculate_success_rate(rs, cnts)
            print(run+1, 'r', r, 'rs', rs, 'cnts', cnts, 'Current Success Rate:', f"{current_success_rate:.2%}")

            if (run + 1) % 10 == 0:  # Every 10 runs
                periodic_success_rates.append(current_success_rate)
                print(f"Run {run+1}: Success Rate = {current_success_rate:.2%}")
                
                # Visualize current results
                visualize_results(rs, cnts, self.categories)
                
                # Visualize periodic success rates
                self.visualize_periodic_success_rates(periodic_success_rates, run)
                
                # Visualize cumulative rewards
                self.visualize_cumulative_rewards(cumulative_rewards)

            print('------------\n')

        # Final visualizations after all runs
        visualize_results(rs, cnts, self.categories)
        self.visualize_periodic_success_rates(periodic_success_rates, num_games, final=True)
        self.visualize_cumulative_rewards(cumulative_rewards, final=True)

        return rs, cnts

    def visualize_periodic_success_rates(self, rates, run, final=False):
        plt.figure(figsize=(12, 6))
        plt.plot(range(10, run + 2, 10), rates, marker='o')
        plt.title('Final Success Rate Every 10 Runs' if final else 'Success Rate Every 10 Runs')
        plt.xlabel('Number of Runs')
        plt.ylabel('Success Rate')
        plt.grid(True)
        plt.show()

    def visualize_cumulative_rewards(self, cumulative_rewards, final=False):
        plt.figure(figsize=(10, 6))
        plt.plot(range(1, len(cumulative_rewards) + 1), cumulative_rewards)
        plt.title('Final Cumulative Rewards Over Time' if final else 'Cumulative Rewards Over Time')
        plt.xlabel('Number of Tasks')
        plt.ylabel('Cumulative Reward')
        plt.grid(True)
        plt.show()

# class BaseMethod:
#     def __init__(self, main_prompt_file, method_prompt_file, env):
#         self.main_prompt = self.load_txt(main_prompt_file)
#         self.method_prompts = self.load_json(method_prompt_file)
#         self.env = env
#         self.prefixes = {
#             'pick_and_place': 'put',
#             'pick_clean_then_place': 'clean',
#             'pick_heat_then_place': 'heat',
#             'pick_cool_then_place': 'cool',
#             'look_at_obj': 'examine',
#             'pick_two_obj': 'puttwo'
#         }
#         self.categories = list(self.prefixes.keys())

#     def load_txt(self, file_path):
#         return load_txt(file_path)

#     def load_json(self, file_path):
#         return load_json(file_path)

#     def alfworld_run(self, prompt, ob='', to_print=True):
#         raise NotImplementedError("Subclasses must implement alfworld_run method")

#     def run(self, num_games=134):
#         rs = [0] * 6
#         cnts = [0] * 6
#         periodic_success_rates = []

#         for run in range(num_games):
#             ob, info = self.env.reset()
#             ob = '\n'.join(ob[0].split('\n\n')[1:])
#             name = '/'.join(info['extra.gamefile'][0].split('/')[-3:-1])
#             print(name)

#             for i, (k, v) in enumerate(self.prefixes.items()):
#                 if name.startswith(k):
#                     full_prompt = (self.main_prompt + 
#                                    'Interact with a household to solve a task. Here are 2 examples.\n' + 
#                                    self.method_prompts[f'{self.method_prefix}_{v}_0'] + 
#                                    self.method_prompts[f'{self.method_prefix}_{v}_1'] + 
#                                    '\nHere is the task.\n')
#                     print(k, v)
#                     r = self.alfworld_run(full_prompt, ob=ob)
#                     rs, cnts = update_results(rs, cnts, i, r)
#                     break

#             current_success_rate = calculate_success_rate(rs, cnts)
#             print(run+1, 'r', r, 'rs', rs, 'cnts', cnts, 'Current Success Rate:', f"{current_success_rate:.2%}")

#             if (run + 1) % 10 == 0:
#                 periodic_success_rates.append(current_success_rate)
#                 print(f"Run {run+1}: Success Rate = {current_success_rate:.2%}")
#                 visualize_results(rs, cnts, self.categories)
#                 self.visualize_periodic_success_rates(periodic_success_rates, run)

#             print('------------\n')

#         visualize_results(rs, cnts, self.categories)
#         self.visualize_periodic_success_rates(periodic_success_rates, num_games, final=True)

#         return rs, cnts

#     def visualize_periodic_success_rates(self, rates, run, final=False):
#         plt.figure(figsize=(12, 6))
#         plt.plot(range(10, run + 2, 10), rates, marker='o')
#         plt.title('Final Success Rate Every 10 Runs' if final else 'Success Rate Every 10 Runs')
#         plt.xlabel('Number of Runs')
#         plt.ylabel('Success Rate')
#         plt.grid(True)
#         plt.show()

class React(BaseMethod):
    def __init__(self, main_prompt_file, method_prompt_file, env, use_oracle):
        super().__init__(main_prompt_file, method_prompt_file, env, use_oracle)
        self.method_prefix = 'react'

    def alfworld_run(self, prompt, ob='', to_print=True):
        init_prompt = prompt + ob + '\n>'
        prompt = ''
        if to_print:
            print(ob)
            sys.stdout.flush()

        for i in range(1, 30):
            message = [{"role": "system", "content": init_prompt + prompt}]
            action = llm(message, stop=['\n']).strip().lstrip('> ')
            # Initialize done and reward
            done = False
            reward = 0
            if action.startswith('think:'):
                observation = 'OK.'
            else:
                observation, reward, done, info = self.env.step([action])
                observation, reward, done = process_ob(observation[0]), info['won'][0], done[0]

            if to_print:
                print(f'Act {i}: {action}\nObs {i}: {observation}')
                sys.stdout.flush()

            prompt += f' {action}\n{observation}\n>'

            if done:
                return reward

        return 0

class ReSpAct(BaseMethod):
    def __init__(self, main_prompt_file, method_prompt_file, env, use_oracle):
        super().__init__(main_prompt_file, method_prompt_file, env, use_oracle)
        self.method_prefix = 'respact'

    def alfworld_run(self, prompt, to_print=True, ob=''):
        init_prompt = prompt + ob + '\n'
        prompt = ''
        if to_print:
            print(ob)
            sys.stdout.flush()
        
        for i in range(1, 30):
            message = [
                {"role": "system", "content": init_prompt + prompt}
            ]
            action = llm(message, stop=['\n']).strip()
            
            # Remove only the '>' prefix if present
            action = action.lstrip('> ')
            
            # Initialize done and reward
            done = False
            reward = 0
            
            if action.startswith('think:'):
                print(f"{action}")
                observation = 'OK.'
            elif action.startswith('speak:'):
                question = action[6:].strip()
                print(f"{action}")
                user_response = input("Human: ")
                observation = f"Human: {user_response}"
            else:
                observation, reward, done, info = self.env.step([action])
                observation, reward, done = process_ob(observation[0]), info['won'][0], done[0]
            
            if to_print:
                print(f'Act {i}: {action}\nObs {i}: {observation}')
                sys.stdout.flush()
            
            prompt += f'{action}\n{observation}\n'
            
            if done:
                return reward
        return 0

def get_method(method_name, main_prompt_file, method_prompt_file, env, use_oracle):
    if method_name.lower() == 'react':
        return React(main_prompt_file, method_prompt_file, env, use_oracle)
    elif method_name.lower() == 'respact':
        return ReSpAct(main_prompt_file, method_prompt_file, env, use_oracle)
    else:
        raise ValueError(f"Unknown method: {method_name}")
    