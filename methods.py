import os
import sys
import json
import openai
from openai import OpenAI
from utils import get_openai_client, calculate_success_rate, visualize_results, update_results, load_txt, load_json, cprint
from process_observations import process_ob
from llm_agent import gpt4_agent, llama3_agent, mistral_agent, gpt4_structured_agent, mistralv3_7b_agent_together, llama31_8b_agent_together, llama31_70b_agent_together_user, llama31_405b_agent_together, mixtral_agent_together
from oracle import oracle_support

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from utils import calculate_success_rate, visualize_results, update_results, cprint

from user_sim import LLMUserAgent

######## Old Method class for React and ReSpAct to be used with main_prompt_file and method_prompt_file
        
class BaseMethod:
    def __init__(self, method_name, main_prompt_file, method_prompt_file, env, use_oracle=False):
        
        self.method_name = method_name
        if main_prompt_file == 'None':
            self.main_prompt = ''
        else:
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
        return load_txt(file_path)

    def load_json(self, file_path):
        return load_json(file_path)

    def alfworld_run(self, prompt, ob='', to_print=True):
        raise NotImplementedError("Subclasses must implement alfworld_run method")
    


    def run(self, exp_name, use_azure, num_games=134):
        rs = [0] * 6
        cnts = [0] * 6
        periodic_success_rates = []
        cumulative_rewards = []
        for run in range(num_games):
            ob, info = self.env.reset()
            ob = '\n'.join(ob[0].split('\n\n')[1:])
            name = '/'.join(info['extra.gamefile'][0].split('/')[-3:-1])
            print(name)

            # Add oracle support if specified in the config
            if self.use_oracle:
                game_file = info['extra.gamefile'][0] # Get the game file path
                oracle_info = oracle_support(game_file)

            for i, (k, v) in enumerate(self.prefixes.items()):
                if name.startswith(k):
                    full_prompt = (self.main_prompt + 
                                   'Interact with a household to solve a task. Here are 2 examples.\n' + 
                                   self.method_prompts[f'{self.method_prefix}_{v}_1'] + 
                                   self.method_prompts[f'{self.method_prefix}_{v}_2'] + 
                                   '\nHere is the task.\n')
                    print(k, v)
                    r = self.alfworld_run(exp_name, use_azure, name, full_prompt, ob=ob, to_print=True)
                    # r = self.alfworld_run(exp_name, use_azure, name, oracle_info, full_prompt, to_print=True, ob=ob) # exp_name, use_azure, name, oracle_info, prompt, to_print=True, ob=''
                    rs, cnts = update_results(rs, cnts, i, r)
                    break

            cumulative_rewards.append(sum(rs))
            current_success_rate = calculate_success_rate(rs, cnts)
            print(run+1, 'r', r, 'rs', rs, 'cnts', cnts, 'Current Success Rate:', f"{current_success_rate:.2%}")

            if (run + 1) % 10 == 0:  # Every 10 runs
                periodic_success_rates.append(current_success_rate)
                print(f"Run {run+1}: Success Rate = {current_success_rate:.2%}")
                
                # Visualize current results
                visualize_results(self.method_name, exp_name, name, rs, cnts, self.categories)
                
                # Visualize periodic success rates
                self.visualize_periodic_success_rates( exp_name, name, periodic_success_rates, run)
                
                # Visualize cumulative rewards
                self.visualize_cumulative_rewards(exp_name, name, cumulative_rewards)

            print('------------\n')

        # Final visualizations after all runs
        visualize_results(self.method_name, exp_name, name, rs, cnts, self.categories)
        # self.visualize_periodic_success_rates(periodic_success_rates, num_games, final=True)
        # self.visualize_cumulative_rewards(cumulative_rewards, final=True)

        return rs, cnts

    def visualize_periodic_success_rates(self, exp_name, name, rates, run, final=False):
        name = name.replace('/', '_')
        plt.figure(figsize=(12, 6))
        plt.plot(range(10, run + 2, 10), rates, marker='o')
        plt.title('Final Success Rate Every 10 Runs' if final else 'Success Rate Every 10 Runs')
        plt.xlabel('Number of Runs')
        plt.ylabel('Success Rate')
        plt.grid(True)
        # plt.show()
        # Save the plot
        plt.savefig(f'results/{self.method_name}/{self.agent}_{exp_name}_{name}_periodic_success_rate_plot.png')

    def visualize_cumulative_rewards(self, exp_name, name, cumulative_rewards, final=False):
        name = name.replace('/', '_')
        plt.figure(figsize=(10, 6))
        plt.plot(range(1, len(cumulative_rewards) + 1), cumulative_rewards)
        plt.title('Final Cumulative Rewards Over Time' if final else 'Cumulative Rewards Over Time')
        plt.xlabel('Number of Tasks')
        plt.ylabel('Cumulative Reward')
        plt.grid(True)
        # plt.show()
        plt.savefig(f'results/{self.method_name}/{self.agent}_{exp_name}_{name}_cum_success_rate_plot.png')



######## Method class for React and ReSpAct to be used with main_prompt_file and method_prompt_file (without symbols for acts)

class React(BaseMethod):
    def __init__(self, method_name, agent, main_prompt_file, method_prompt_file, env, use_oracle):
        super().__init__(method_name, main_prompt_file, method_prompt_file, env, use_oracle)
        self.method_prefix = 'react'
        self.agent = agent

    def alfworld_run(self, exp_name, use_azure, name, prompt, ob='', to_print=True):
        init_prompt = prompt + ob + '\n>'
        prompt = ''
        # Dictionary to store the action and observation pairs
        action_observation_pairs = {}
        # initialize the counter
        j = 0
        # save the initial observation
        action_observation_pairs[j] = ob
        if to_print:
            print(ob)
            sys.stdout.flush()

        for i in range(1, 50):
            # message = [{"role": "system", "content": init_prompt + prompt}]
            message = init_prompt + prompt
            action = eval(self.agent)(message, stop=['\n'], use_azure=use_azure).strip().lstrip('> ')
            cprint(action, 'cyan')
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
                # save the action and observation pair
                j += 1
                action_observation_pairs[j] = f'Act {i}: {action} \nObs {i}: {observation}'
                sys.stdout.flush()

            prompt += f' {action}\n{observation}\n>'

            if done:
                dir_path = f'results/{self.__class__.__name__}/{exp_name}/{self.agent}'
                os.makedirs(dir_path, exist_ok=True)
                sanitized_name = ''.join(c for c in name if c.isalnum() or c in ('-', '_'))
                file_path = f'{dir_path}/{sanitized_name}_action_observation_pairs.txt'
                
                try:
                    with open(file_path, 'w') as f:
                        for key, value in action_observation_pairs.items():
                            f.write(f'{key}: {value}\n')
                except IOError as e:
                    print(f"An error occurred while writing to file: {e}")
                return reward
        dir_path = f'results/{self.__class__.__name__}/{exp_name}/{self.agent}'
        os.makedirs(dir_path, exist_ok=True)
        sanitized_name = ''.join(c for c in name if c.isalnum() or c in ('-', '_'))
        file_path = f'{dir_path}/{sanitized_name}_action_observation_pairs_failed.txt'
        
        try:
            with open(file_path, 'w') as f:
                for key, value in action_observation_pairs.items():
                    f.write(f'{key}: {value}\n')
        except IOError as e:
            print(f"An error occurred while writing to file: {e}")
        return 0

class ReSpAct(BaseMethod):
    def __init__(self, method_name, agent, main_prompt_file, method_prompt_file, env, use_oracle):
        super().__init__(method_name, main_prompt_file, method_prompt_file, env, use_oracle)
        self.method_prefix = 'respact'
        self.agent = agent
        self.user_simulator = None  # Will be initialized in alfworld_run

    def alfworld_run(self, exp_name, use_azure, name, oracle_info, prompt, to_print=True, ob=''):
        # Initialize the user simulator
        # oracle_info = oracle_support(self.env.game_files[0]) if self.use_oracle else ""
        cprint(f"Oracle Information: {oracle_info}", 'red')
        
        user_simulator_prompt = 'prompts/user_sim.txt' # Load the user simulator prompt
        self.user_simulator = LLMUserAgent(oracle_info, self.agent, user_simulator_prompt)

        init_prompt = prompt + ob + '\n'
        prompt = ''
        # Dictionary to store the action and observation pairs
        action_observation_pairs = {}
        # initialize the counter
        j = 0
        # save the initial observation
        action_observation_pairs[j] = ob
        if to_print:
            print(ob)
            sys.stdout.flush()
        
        for i in range(1, 50):
            message = init_prompt + prompt
            action = eval(self.agent)(message, stop=['\n'], use_azure=use_azure).strip()
            # action = eval(self.agent)(message, stop=['\n'], use_azure=use_azure).strip().lstrip('> ')
            cprint(action, 'cyan')
            # Remove only the '>' prefix if present
            action = action.lstrip('> ')
            
            # Initialize done and reward
            done = False
            reward = 0
            
            if action.startswith('think:'):
                print(f"{action}")
                observation = 'OK.'
            elif action.startswith('speak:'):
                question = action[6:].strip() # Remove the 'speak:' prefix
                print(f"{action}")
                # user_response = input("Human: ")
                # observation = f"Human: {user_response}" #Human Evaluation
                user_response = self.user_simulator.user_response(question)
                observation = f"Human: {user_response}" #User Simulator
            elif action.startswith('act:'):
                action = action[4:].strip() # Remove the 'act:' prefix
                observation, reward, done, info = self.env.step([action])
                observation, reward, done = process_ob(observation[0]), info['won'][0], done[0]
            
            if to_print:
                print(f'Act {i}: {action}\nObs {i}: {observation}')
                j += 1
                action_observation_pairs[j] = f'Act {i}: {action} \nObs {i}: {observation}'
                sys.stdout.flush()
            
            prompt += f'{action}\n{observation}\n'

            # Update user simulator state
            self.user_simulator.update_state(action, observation)
            
            if done:
                self._save_action_observation_pairs(exp_name, name, action_observation_pairs)
                return reward
        
        self._save_action_observation_pairs(exp_name, name, action_observation_pairs, failed=True)
        return 0

    def _save_action_observation_pairs(self, exp_name, name, action_observation_pairs, failed=False):
        dir_path = f'results/{self.__class__.__name__}/{exp_name}/{self.agent}'
        os.makedirs(dir_path, exist_ok=True)
        sanitized_name = ''.join(c for c in name if c.isalnum() or c in ('-', '_'))
        status = '_failed' if failed else ''
        file_path = f'{dir_path}/{sanitized_name}_action_observation_pairs{status}.txt'
        
        try:
            with open(file_path, 'w') as f:
                for key, value in action_observation_pairs.items():
                    f.write(f'{key}: {value}\n')
        except IOError as e:
            print(f"An error occurred while writing to file: {e}")
    
def get_old_method(method_name, agent, main_prompt_file, method_prompt_file, env, use_oracle):
    print("Running original method")
    if method_name.lower() == 'react':
        return React(method_name, agent, main_prompt_file, method_prompt_file, env, use_oracle)
    elif method_name.lower() == 'respact':
        return ReSpAct(method_name, agent, main_prompt_file, method_prompt_file, env, use_oracle)
    else:
        raise ValueError(f"Unknown method: {method_name}")