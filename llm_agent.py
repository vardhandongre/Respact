
import os
import sys
import openai
from utils import get_openai_client
from process_observations import process_ob
import transformers
import torch
import ollama
from pydantic import BaseModel
from openai import OpenAI
from typing import Literal

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

def gpt3_agent(prompt, stop=["\n"], use_azure=False):
    message = [{"role": "system", "content": prompt}]
    client = get_openai_client(use_azure)
    
    model = "gpt-3.5-turbo-1106" if use_azure else "gpt-3.5-turbo-1106"
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=message,
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

def gpt4_agent(prompt, stop=["\n"], use_azure=True):
    message = [{"role": "system", "content": prompt}]
    client = get_openai_client(use_azure)
    
    model = "gpt4o-mini" if use_azure else "gpt-4-turbo"
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=message,
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
    

# gptagent experiment with structured output (run seperately)
# Define the structure for our agent's response
class RespactAgentAction(BaseModel):
    action_type: Literal["thinking", "speaking", "acting"]
    content: str

class ReactAgentAction(BaseModel):
    action_type: Literal["thinking", "acting"]
    content: str

def gpt4_structured_agent(prompt, format, use_azure=False):
    client = get_openai_client(use_azure)
    
    model = "gpt-4o-2024-08-06" if use_azure else "gpt-4o-2024-08-06"
    
    try:
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
            ],
            response_format=eval(format),
            temperature=0,
            max_tokens=100,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )
        
        agent_action = completion.choices[0].message.parsed
        
        return agent_action.action_type, agent_action.content
    
    except openai.OpenAIError as e:
        print(f"An error occurred while calling the OpenAI API: {str(e)}")
        return "error", str(e)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return "error", str(e)

# 1. LLAMA 2
# 2. LLAMA 3
# 3. LLAMA 3.1

# OLLAMA
# def mistral_agent(prompt, stop=['\n'], model='mistral'):
#     return ollama.generate(prompt, model)['response'].strip()

# def llama3_agent(prompt, stop=['\n'], model='llama3'):
#     return ollama.generate(prompt, model)['response'].strip()
    
def mistral_agent(prompt, stop=['\n'], model='mistral'):
    try:
        response = ollama.generate(model=model, prompt=prompt)
        content = response['response']
        
        # Post-process to ensure we stop at the first occurrence of any stop sequence
        for stop_seq in stop:
            index = content.find(stop_seq)
            if index != -1:
                content = content[:index]
        
        return content.strip()
    except Exception as e:
        print(f"An error occurred while calling the Ollama API: {str(e)}")
        return ""
    
def llama3_agent(prompt, stop=['\n'], model='llama3'):
    try:
        response = ollama.generate(model=model, prompt=prompt)
        content = response['response']
        
        # Post-process to ensure we stop at the first occurrence of any stop sequence
        for stop_seq in stop:
            index = content.find(stop_seq)
            if index != -1:
                content = content[:index]
        
        return content.strip()
    except Exception as e:
        print(f"An error occurred while calling the Ollama API: {str(e)}")
        return ""
    
def llama31_agent(prompt, stop=['\n'], model='llama3.1'):
    try:
        response = ollama.generate(model=model, prompt=prompt)
        content = response['response']
        
        # Post-process to ensure we stop at the first occurrence of any stop sequence
        for stop_seq in stop:
            index = content.find(stop_seq)
            if index != -1:
                content = content[:index]
        
        return content.strip()
    except Exception as e:
        print(f"An error occurred while calling the Ollama API: {str(e)}")
        return ""
    

