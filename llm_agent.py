
import os
import sys
import openai
from utils import get_openai_client
from process_observations import process_ob


# def llm(prompt, stop=["\n"], use_azure=True):
#     client = get_openai_client(use_azure)
    
#     if use_azure:
#         model = "gpt4o-mini" 
#     else:
#         model = "gpt-4-turbo"
    
#     response = client.chat.completions.create(
#         model=model,
#         messages=prompt,
#         temperature=0,
#         max_tokens=100,
#         top_p=1,
#         frequency_penalty=0.0,
#         presence_penalty=0.0,
#         stop=stop
#     )
#     content = response.choices[0].message.content
    
#     # Post-process to ensure we stop at the first occurrence of any stop sequence
#     for stop_seq in stop:
#         index = content.find(stop_seq)
#         if index != -1:
#             content = content[:index]
    
#     return content.strip()

def gpt_agent(prompt, stop=["\n"], use_azure=False):
    client = get_openai_client(use_azure)
    
    model = "gpt4o-mini" if use_azure else "gpt-4-turbo"
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=prompt,
            temperature=0,
            max_tokens=100,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stop=stop
        )
        
        if not response.choices:
            print("Warning: API returned an empty response.")
            return ""
        
        content = response.choices[0].message.content
        
        if content is None:
            print("Warning: API returned None as content.")
            return ""
        
        # Post-process to ensure we stop at the first occurrence of any stop sequence
        for stop_seq in stop:
            index = content.find(stop_seq)
            if index != -1:
                content = content[:index]
        
        return content.strip()
    
    except openai.OpenAIError as e:
        print(f"An error occurred while calling the OpenAI API: {str(e)}")
        return ""
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return ""

# def alfworld_run(env, prompt, to_print=True, ob=''):
#     init_prompt = prompt + ob + '\n>'
#     prompt = ''
#     if to_print:
#         print(ob)
#         sys.stdout.flush()
#     for i in range(1, 30):
#         message = [
#             {"role":"system", "content":init_prompt + prompt}
#         ]
#         action = llm(message, stop=['\n']).strip()
        
#         if action.startswith('speak:') or action.startswith('> speak:'):
#             # Remove the 'speak:' or '> speak:' prefix
#             question = action.split(':', 1)[1].strip()
#             print(f"Agent asks: {question}")
#             user_response = input("Your response: ")
#             observation = f"Human: {user_response}"
#         else:
#             observation, reward, done, info = env.step([action])
#             print(f"Agent action: {action}")
#             print(f"Observation: {observation}")
#             print(f"Reward: {reward}")
#             print(f"Done: {done}")
#             print(f"Info: {info}")
#             observation, reward, done = process_ob(observation[0]), info['won'][0], done[0]
#             if action.startswith('think:') or action.startswith('> think:'):
#                 observation = 'OK.'
        
#         if to_print:
#             print(f'Act {i}: {action}\nObs {i}: {observation}')
#             sys.stdout.flush()
#         prompt += f' {action}\n{observation}\n>'
#         if done:
#             return reward
#     return 0

# def alfworld_run(env, prompt, to_print=True, ob=''):
#     init_prompt = prompt + ob + '\n'
#     prompt = ''
#     if to_print:
#         print(ob)
#         sys.stdout.flush()
#     for i in range(1, 30):
#         message = [
#             {"role": "system", "content": init_prompt + prompt}
#         ]
#         action = llm(message, stop=['\n']).strip()
        
#         # Remove only the '>' prefix if present
#         action = action.lstrip('> ')
        
#         if action.startswith('think:'):
#             print(f"{action}")
#             observation = 'OK.'
#         elif action.startswith('speak:'):
#             question = action[6:].strip()
#             print(f"{action}")
#             user_response = input("Human: ")
#             observation = f"Human: {user_response}"
#         else:
#             observation, reward, done, info = env.step([action])
#             observation, reward, done = process_ob(observation[0]), info['won'][0], done[0]
        
#         if to_print:
#             print(f'{observation}')
#             sys.stdout.flush()
        
#         prompt += f'{action}\n{observation}\n'
        
#         if done:
#             return reward
#     return 0
    


