import os
import sys
import json
import openai
from openai import OpenAI
from utils import get_openai_client, calculate_success_rate, visualize_results, update_results, load_txt, load_json, cprint
from process_observations import process_ob
from llm_agent import gpt4_agent, llama3_agent, mistral_agent, gpt4_structured_agent
# from llm_agent import llama3_agent as llm
from oracle import oracle_support

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from utils import calculate_success_rate, visualize_results, update_results, cprint


class BaseMethod:
    def __init__(self, method_name, main_prompt_file, method_prompt_file, env, use_oracle=False):
        self.method_name = method_name
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
        
    def parse_agent_response(self, response):
        thinking = ""
        speaking = ""
        action = ""
        
        lines = response.split('\n')
        for line in lines:
            if line.startswith('🤔 Thinking:'):
                thinking = line[len('🤔 Thinking:'):].strip()
            elif line.startswith('💬 Speaking:'):
                speaking = line[len('💬 Speaking:'):].strip()
            elif line.startswith('🔄 Acting:'):
                action = line[len('🔄 Acting:'):].strip()
        
        return thinking, speaking, action

    def alfworld_run(self, prompt, ob='', to_print=True):
        raise NotImplementedError("Subclasses must implement alfworld_run method")

    def run(self, exp_name, num_games=132):
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
                    # print few shot examples
                    # print("Examples: \n")
                    # print(self.method_prompts[f'{self.method_prefix}_{v}_0'])
                    # print(self.method_prompts[f'{self.method_prefix}_{v}_1'])
                    r = self.alfworld_run(exp_name, name, full_prompt, ob=ob) # name for saving the action_observation_pairs
                    rs[i] += r
                    cnts[i] += 1
                    break

            cumulative_rewards.append(sum(rs))
            current_success_rate = calculate_success_rate(rs, cnts)
            print(run+1, 'r', r, 'rs', rs, 'cnts', cnts, 'Current Success Rate:', f"{current_success_rate:.2%}")

            if (run + 1) % 30 == 0:  # Every 30 runs
                periodic_success_rates.append(current_success_rate)
                print(f"Run {run+1}: Success Rate = {current_success_rate:.2%}")
                
                # Visualize current results
                visualize_results(self.method_name, exp_name, name, rs, cnts, self.categories)
                
                # Visualize periodic success rates
                self.visualize_periodic_success_rates(self.method_name, exp_name, name, periodic_success_rates, run)
                
                # Visualize cumulative rewards
                self.visualize_cumulative_rewards(self.method_name, exp_name, name, cumulative_rewards)

            print('------------\n')

        # Final visualizations after all runs
        visualize_results(exp_name, name, rs, cnts, self.categories)
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
        plt.savefig(f'results/{self.method_name}/{exp_name}_{name}_periodic_success_rate_plot.png')

    def visualize_cumulative_rewards(self, exp_name, name, cumulative_rewards, final=False):
        name = name.replace('/', '_')
        plt.figure(figsize=(10, 6))
        plt.plot(range(1, len(cumulative_rewards) + 1), cumulative_rewards)
        plt.title('Final Cumulative Rewards Over Time' if final else 'Cumulative Rewards Over Time')
        plt.xlabel('Number of Tasks')
        plt.ylabel('Cumulative Reward')
        plt.grid(True)
        # plt.show()
        plt.savefig(f'results/{self.method_name}/{exp_name}_{name}_cum_success_rate_plot.png')


######## Old Method class for React and ReSpAct to be used with main_prompt_file and method_prompt_file
        
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



######### Method class for React and ReSpAct to be used with main_prompt_file and method_prompt_file (without symbols for acts)

# class React(BaseMethod):
#     def __init__(self, agent, main_prompt_file, method_prompt_file, env, use_oracle):
#         super().__init__(main_prompt_file, method_prompt_file, env, use_oracle)
#         self.method_prefix = 'react'
#         self.agent = agent

#     def alfworld_run(self, exp_name, name, prompt, ob='', to_print=True):
#         init_prompt = prompt + ob + '\n>'
#         prompt = ''
#         # Dictionary to store the action and observation pairs
#         action_observation_pairs = {}
#         # initialize the counter
#         j = 0
#         # save the initial observation
#         action_observation_pairs[j] = ob
#         if to_print:
#             print(ob)
#             sys.stdout.flush()

#         for i in range(1, 30):
#             # message = [{"role": "system", "content": init_prompt + prompt}]
#             message = init_prompt + prompt
#             action = eval(self.agent)(message, stop=['\n']).strip().lstrip('> ')
#             # Initialize done and reward
#             done = False
#             reward = 0
#             if action.startswith('think:'):
#                 observation = 'OK.'
#             else:
#                 observation, reward, done, info = self.env.step([action])
#                 observation, reward, done = process_ob(observation[0]), info['won'][0], done[0]

#             if to_print:
#                 print(f'Act {i}: {action}\nObs {i}: {observation}')
#                 # save the action and observation pair
#                 j += 1
#                 action_observation_pairs[j] = f'Act {i}: {action} \nObs {i}: {observation}'
#                 sys.stdout.flush()

#             prompt += f' {action}\n{observation}\n>'

#             if done:
#                 # Save the action and observation pairs to a file
#                 with open(f'results/React/{exp_name}/{name}_action_observation_pairs.txt', 'w') as f:
#                     for key, value in action_observation_pairs.items():
#                         f.write(f'{key}: {value}\n')
#                 return reward

#         return 0

# class ReSpAct(BaseMethod):
#     def __init__(self, agent, main_prompt_file, method_prompt_file, env, use_oracle):
#         super().__init__(main_prompt_file, method_prompt_file, env, use_oracle)
#         self.method_prefix = 'respact'
#         self.agent = agent

#     def alfworld_run(self, exp_name, name, prompt, to_print=True, ob=''):
#         init_prompt = prompt + ob + '\n'
#         prompt = ''
#         # Dictionary to store the action and observation pairs
#         action_observation_pairs = {}
#         # initialize the counter
#         j = 0
#         # save the initial observation
#         action_observation_pairs[j] = ob
#         if to_print:
#             print(ob)
#             sys.stdout.flush()
        
#         for i in range(1, 30):
#             message = [
#                 {"role": "system", "content": init_prompt + prompt}
#             ]
#             action = eval(self.agent)(message, stop=['\n']).strip()
            
#             # Remove only the '>' prefix if present
#             action = action.lstrip('> ')
            
#             # Initialize done and reward
#             done = False
#             reward = 0
            
#             if action.startswith('think:'):
#                 print(f"{action}")
#                 observation = 'OK.'
#             elif action.startswith('speak:'):
#                 question = action[6:].strip() # Remove the 'speak:' prefix
#                 print(f"{action}")
#                 user_response = input("Human: ")
#                 observation = f"Human: {user_response}"
#             else:
#                 observation, reward, done, info = self.env.step([action])
#                 observation, reward, done = process_ob(observation[0]), info['won'][0], done[0]
            
#             if to_print:
#                 print(f'Act {i}: {action}\nObs {i}: {observation}')
#                 j += 1
#                 action_observation_pairs[j] = f'Act {i}: {action} \nObs {i}: {observation}'
#                 sys.stdout.flush()
            
#             prompt += f'{action}\n{observation}\n'
            
#             if done:
#                 # Save the action and observation pairs to a file
#                 with open(f'results/Respact/{exp_name}/{name}_action_observation_pairs.txt', 'w') as f:
#                     for key, value in action_observation_pairs.items():
#                         f.write(f'{key}: {value}\n')
#                 return reward
#         return 0
        

######### Method class for React and ReSpAct to be used with main_prompt_opt and method_prompt(with symbols for acts)
    
class React(BaseMethod):
    def __init__(self, method_name, agent, main_prompt_file, method_prompt_file, env, use_oracle):
        super().__init__(method_name, main_prompt_file, method_prompt_file, env, use_oracle)
        self.method_prefix = 'react'
        self.agent = agent

    # def alfworld_run(self, exp_name, name, prompt, ob='', to_print=True):
    #     init_prompt = prompt + ob + '\n'
    #     context = ''
    #     action_observation_pairs = {}
    #     j = 0
    #     action_observation_pairs[j] = ob
    #     if to_print:
    #         print(ob)
    #         sys.stdout.flush()

    #     for i in range(1, 30):
    #         message = init_prompt + context
    #         action_type, content = gpt4_structured_agent(message, format='ReactAgentAction')  # This should return an AgentAction object
            
    #         # Initialize done and reward
    #         done = False
    #         reward = 0
            
    #         if action_type == "thinking":
    #             observation = 'OK.'
    #             if to_print:
    #                 cprint(f'🤔 Thinking: {content}', 'green')
    #         elif action_type == "acting":
    #             observation, reward, done, info = self.env.step([content])
    #             observation, reward, done = process_ob(observation[0]), info['won'][0], done[0]
    #             if to_print:
    #                 cprint(f'🔄 Acting: {content}', 'blue')
    #         else:
    #             observation = "Invalid response format. Please use the correct action type."

    #         if to_print:
    #             cprint(f'Obs {i}: {observation}', 'red')
    #             j += 1
    #             action_observation_pairs[j] = f'Step {i}:\n{action_type.capitalize()}: {content}\nObs {i}: {observation}'
    #             sys.stdout.flush()

    #         context += f'{action_type.capitalize()}: {content}\n{observation}\n'

    #         if done:
    #             dir_path = f'results/{self.__class__.__name__}/{exp_name}'
    #             os.makedirs(dir_path, exist_ok=True)
    #             sanitized_name = ''.join(c for c in name if c.isalnum() or c in ('-', '_'))
    #             file_path = f'{dir_path}/{sanitized_name}_action_observation_pairs.txt'
                
    #             try:
    #                 with open(file_path, 'w') as f:
    #                     for key, value in action_observation_pairs.items():
    #                         f.write(f'{key}: {value}\n')
    #             except IOError as e:
    #                 print(f"An error occurred while writing to file: {e}")
                
    #             return reward
    #     dir_path = f'results/{self.__class__.__name__}/{exp_name}'
    #     os.makedirs(dir_path, exist_ok=True)
    #     sanitized_name = ''.join(c for c in name if c.isalnum() or c in ('-', '_'))
    #     file_path = f'{dir_path}/{sanitized_name}_action_observation_pairs_failed.txt'
        
    #     try:
    #         with open(file_path, 'w') as f:
    #             for key, value in action_observation_pairs.items():
    #                 f.write(f'{key}: {value}\n')
    #     except IOError as e:
    #         print(f"An error occurred while writing to file: {e}")
    #     return 0
    
    ###### Not expecting structured response from the agent
    def alfworld_run(self, exp_name, name, prompt, ob='', to_print=True):
        init_prompt = prompt + ob + '\n'
        prompt = ''
        action_observation_pairs = {}
        j = 0
        action_observation_pairs[j] = ob
        if to_print:
            print(ob)
            sys.stdout.flush()

        for i in range(1, 30):
            message = init_prompt + prompt
            response = eval(self.agent)(message, stop=['\n\n']).strip()
            cprint(f'Response: {response}', 'yellow')
            thinking, speaking, action = self.parse_agent_response(response)
            
            # Initialize done and reward
            done = False
            reward = 0
            
            if thinking:
                observation = 'OK.'
            elif speaking:
                # Handle speaking action if needed
                observation = 'OK.'
            elif action:
                observation, reward, done, info = self.env.step([action])
                observation, reward, done = process_ob(observation[0]), info['won'][0], done[0]
            else:
                observation = "Invalid response format. Please use the correct prefix."

            if to_print:
                print(f'Step {i}:')
                if thinking: cprint(f'🤔 Thinking: {thinking}', 'green')
                # if speaking: print(f'💬 Speaking: {speaking}')
                if action: cprint(f'🔄 Acting: {action}', 'blue')
                cprint(f'Obs {i}: {observation}', 'red')
                j += 1
                action_observation_pairs[j] = f'Step {i}:\n{response}\nObs {i}: {observation}'
                sys.stdout.flush()

            prompt += f'{response}\n{observation}\n'

            if done:
                dir_path = f'results/{self.__class__.__name__}/{exp_name}'
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
        dir_path = f'results/{self.__class__.__name__}/{exp_name}'
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

    # def alfworld_run(self, exp_name, name, prompt, to_print=True, ob=''):
    #     init_prompt = prompt + ob + '\n'
    #     context = ''
    #     action_observation_pairs = {}
    #     j = 0
    #     action_observation_pairs[j] = ob
    #     if to_print:
    #         print(ob)
    #         sys.stdout.flush()
        
    #     for i in range(1, 30):
    #         message = init_prompt + context
    #         action_type, content = eval(self.agent)(message, format = 'RespactAgentAction')  # Assuming self.agent is now gpt4_structured_agent
    #         cprint(f'Response: {content}', 'yellow')
            
    #         # Initialize done and reward
    #         done = False
    #         reward = 0
            
    #         if action_type == "thinking":
    #             observation = 'OK.'
    #             cprint(f'🤔 Thinking: {content}', 'green')
    #         elif action_type == "speaking":
    #             cprint(f"💬 Speaking: {content}", 'cyan')
    #             user_response = input("Human: ")
    #             observation = f"Human: {user_response}"
    #         elif action_type == "acting":
    #             cprint(f'🔄 Acting: {content}', 'blue')
    #             # print(f'Act {i}: {content}')
    #             observation, reward, done, info = self.env.step([content])
    #             observation, reward, done = process_ob(observation[0]), info['won'][0], done[0]
    #         else:
    #             observation = "Invalid response format. Please use the correct action type."
            
    #         if to_print:
    #             cprint(f'Obs {i}: {observation}', 'red')
    #             j += 1
    #             action_observation_pairs[j] = f'Step {i}:\n{action_type.capitalize()}: {content}\nObs {i}: {observation}'
    #             sys.stdout.flush()
            
    #         context += f'{action_type.capitalize()}: {content}\n{observation}\n'
            
    #         if done:
    #             # Create the directory path
    #             dir_path = f'results/{self.__class__.__name__}/{exp_name}'
    #             os.makedirs(dir_path, exist_ok=True)

    #             # Sanitize the filename
    #             sanitized_name = ''.join(c for c in name if c.isalnum() or c in ('-', '_'))
    #             file_path = f'{dir_path}/{sanitized_name}_action_observation_pairs.txt'

    #             try:
    #                 with open(file_path, 'w') as f:
    #                     for key, value in action_observation_pairs.items():
    #                         f.write(f'{key}: {value}\n')
    #             except IOError as e:
    #                 print(f"An error occurred while writing to file: {e}")

    #             return reward
    #     # Create the directory path
    #     dir_path = f'results/{self.__class__.__name__}/{exp_name}'
    #     os.makedirs(dir_path, exist_ok=True)

    #     # Sanitize the filename
    #     sanitized_name = ''.join(c for c in name if c.isalnum() or c in ('-', '_'))
    #     file_path = f'{dir_path}/{sanitized_name}_action_observation_pairs_failed.txt'

    #     try:
    #         with open(file_path, 'w') as f:
    #             for key, value in action_observation_pairs.items():
    #                 f.write(f'{key}: {value}\n')
    #     except IOError as e:
    #         print(f"An error occurred while writing to file: {e}")
    #     return 0

    ###### Not expecting structured response from the agent

    def alfworld_run(self, exp_name, name, prompt, to_print=True, ob=''):
        init_prompt = prompt + ob + '\n'
        prompt = ''
        action_observation_pairs = {}
        j = 0
        action_observation_pairs[j] = ob
        if to_print:
            print(ob)
            sys.stdout.flush()
        
        for i in range(1, 30):
            # message = [
            #     {"role": "system", "content": init_prompt + prompt}
            # ]
            message = init_prompt + prompt
            response = eval(self.agent)(message, stop=['\n\n']).strip()
            cprint(f'Response: {response}', 'yellow')
            thinking, speaking, acting = self.parse_agent_response(response)
            cprint(f'Thinking: {thinking}', 'green')
            cprint(f'Speaking: {speaking}', 'cyan')
            cprint(f'Acting: {acting}', 'blue')
            # Initialize done and reward
            done = False
            reward = 0
            
            if thinking:
                observation = 'OK.'
            elif speaking:
                cprint(f"💬 Speaking: {speaking}", 'cyan')
                user_response = input("Human: ")
                observation = f"Human: {user_response}"
            elif acting:
                observation, reward, done, info = self.env.step([acting])
                observation, reward, done = process_ob(observation[0]), info['won'][0], done[0]
            else:
                observation = "Invalid response format. Please use the correct prefix."
            
            if to_print:
                # print(f'Step {i}:')
                if thinking: cprint(f'🤔 Thinking: {thinking}', 'green')
                if speaking: cprint(f'💬 Speaking: {speaking}', 'cyan')
                if acting: cprint(f'🔄 Acting: {acting}', 'blue')
                cprint(f'Obs {i}: {observation}', 'red')
                j += 1
                action_observation_pairs[j] = f'Step {i}:\n{response}\nObs {i}: {observation}'
                sys.stdout.flush()
            
            prompt += f'{response}\n{observation}\n'
            
            if done:
                with open(f'results/Respact/{exp_name}/{name}_action_observation_pairs.txt', 'w') as f:
                    for key, value in action_observation_pairs.items():
                        f.write(f'{key}: {value}\n')
                return reward
        return 0
    


def get_method(method_name, agent, main_prompt_file, method_prompt_file, env, use_oracle):
    if method_name.lower() == 'react':
        return React(method_name, agent, main_prompt_file, method_prompt_file, env, use_oracle)
    elif method_name.lower() == 'respact':
        return ReSpAct(method_name, agent, main_prompt_file, method_prompt_file, env, use_oracle)
    else:
        raise ValueError(f"Unknown method: {method_name}")
    