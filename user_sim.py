import random
import re
from utils import load_txt
from llm_agent import gpt4_agent, gpt3_agent, gpt4_structured_agent, llama3_agent

# Rules-based User Simulator
class RBUserSimulator:
    def __init__(self, oracle_knowledge, initial_state):
        self.oracle_knowledge = oracle_knowledge
        self.initial_state = initial_state
        self.current_state = initial_state.copy()
        self.agent_actions = []
        self.agent_observations = []
        self.task_progress = 0

    def update_state(self, action, observation):
        self.agent_actions.append(action)
        self.agent_observations.append(observation)
        
        # Update current_state based on the action and observation
        if "take" in action:
            item = action.split()[1]
            self.current_state[item] = "in_hand"
        elif "put" in action:
            item = action.split()[1]
            location = action.split()[-1]
            self.current_state[item] = location
        elif "clean" in action:
            item = action.split()[1]
            self.current_state[item] = "clean"
        
        # Update task progress
        self.update_task_progress()

    def update_task_progress(self):
        completed_steps = set(self.agent_actions) & set(self.oracle_knowledge)
        self.task_progress = len(completed_steps) / len(self.oracle_knowledge)

    def respond_to_agent(self, query):
        # Analyze the query
        query_lower = query.lower()
        
        # Check if the query is about object locations
        if "where" in query_lower:
            for item, location in self.current_state.items():
                if item in query_lower:
                    return f"The {item} is {location}."
            
            # If the item is not in the current state, provide information based on oracle knowledge
            for step in self.oracle_knowledge:
                if any(word in query_lower for word in step.split()):
                    return f"You might want to {step}."
            
            return "I'm not sure about that specific item. Can you be more specific or ask about something else?"

        # Check if the query is about task completion
        if "task" in query_lower and "complete" in query_lower:
            if self.task_progress == 1:
                return "Yes, the task is completed."
            else:
                return f"Not yet. You've completed about {self.task_progress:.0%} of the task."

        # Check if the query is about what to do next
        if "what" in query_lower and "next" in query_lower:
            for step in self.oracle_knowledge:
                if step not in self.agent_actions:
                    return f"You might want to try to {step}."
            return "You've completed all the necessary steps. Check if the task is fully done."

        # If the query doesn't match any specific category, provide a general hint
        if self.task_progress < 0.5:
            return "You're still in the early stages. Keep exploring and interacting with the environment."
        elif self.task_progress < 1:
            return "You're making good progress. Think about what steps might be left to complete the task."
        else:
            return "You've taken all the necessary actions. Is there anything specific you're unsure about?"

class RefinedRBUserSimulator:
    def __init__(self, oracle_knowledge, initial_state):
        self.oracle_knowledge = oracle_knowledge
        self.initial_state = initial_state
        self.current_state = initial_state.copy()
        self.agent_actions = []
        self.agent_observations = []
        self.task_progress = 0

    def update_state(self, action, observation):
        self.agent_actions.append(action)
        self.agent_observations.append(observation)
        
        # Update current_state based on the action and observation
        action_parts = action.split()
        if action_parts[0] == "take":
            item = ' '.join(action_parts[1:-2])
            self.current_state[item] = "in_hand"
        elif action_parts[0] == "put":
            item = ' '.join(action_parts[1:-2])
            location = action_parts[-1]
            self.current_state[item] = location
        elif action_parts[0] in ["clean", "heat", "cool"]:
            item = ' '.join(action_parts[1:-2])
            self.current_state[item] = f"{action_parts[0]}ed"
        elif action_parts[0] == "go":
            location = ' '.join(action_parts[2:])
            self.current_state["agent_location"] = location
        elif action_parts[0] == "open":
            item = ' '.join(action_parts[1:])
            self.current_state[item] = "open"
        
        # Update task progress
        self.update_task_progress()

    def update_task_progress(self):
        completed_steps = 0
        for step in self.oracle_knowledge:
            if any(action.lower() in step.lower() for action in self.agent_actions):
                completed_steps += 1
        self.task_progress = completed_steps / len(self.oracle_knowledge)

    def respond_to_agent(self, query):
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["where", "find", "look"]):
            return self._get_location_hint(query_lower)
        
        if "what" in query_lower and "next" in query_lower:
            return self._get_next_step()

        if "task" in query_lower and "complete" in query_lower:
            if self.task_progress == 1:
                return "Yes, the task is completed."
            else:
                return f"Not yet. You've completed about {self.task_progress:.0%} of the task."

        # If the query doesn't match any specific category, provide a general hint
        return self._get_general_hint()

    def _get_location_hint(self, query):
        for item, location in self.current_state.items():
            if item in query:
                return f"The {item} is {location}."
        
        for step in self.oracle_knowledge:
            if "go to" in step:
                location = step.split("go to")[-1].strip()
                return f"You might want to go to {location}."
            elif "take" in step:
                item = step.split("take")[-1].split("from")[0].strip()
                location = step.split("from")[-1].strip()
                return f"You might find {item} in/on {location}."
        
        return "I'm not sure about that specific item. Try exploring the environment or focusing on the task objectives."

    def _get_next_step(self):
        for step in self.oracle_knowledge:
            if not any(action.lower() in step.lower() for action in self.agent_actions):
                return f"You might want to try to {step}."
        return "You've completed all the necessary steps. Check if the task is fully done."

    def _get_general_hint(self):
        if self.task_progress < 0.25:
            return "You're still in the early stages. Start by exploring the environment and looking for the objects mentioned in the task."
        elif self.task_progress < 0.5:
            return "You're making progress. Continue following the steps and interacting with the relevant objects."
        elif self.task_progress < 1:
            return "You're in the later stages of the task. Focus on completing the final steps with the objects you've interacted with."
        else:
            return "You've taken all the necessary actions. Double-check if the task is fully completed or if there's anything you've missed."


class AdvancedStateAwareRBUserSimulator:
    def __init__(self, oracle_knowledge, initial_state, task_description):
        self.oracle_knowledge = oracle_knowledge
        self.initial_state = initial_state
        self.current_state = initial_state.copy()
        self.task_description = task_description
        self.agent_actions = []
        self.agent_observations = []
        self.completed_steps = set()
        self.task_progress = 0
        self.task_objects = self._parse_task_objects()

    def _parse_task_objects(self):
        # Extract object types and quantities from the task description
        objects = {}
        words = self.task_description.lower().split()
        for i, word in enumerate(words):
            if word.isdigit() and i + 1 < len(words):
                objects[words[i+1]] = int(word)
        return objects

    def update_state(self, action, observation):
        self.agent_actions.append(action)
        self.agent_observations.append(observation)
        
        # Update current_state based on the action and observation
        action_parts = action.split()
        if action_parts[0] == "take":
            item = ' '.join(action_parts[1:-2])
            self.current_state[item] = "in_hand"
        elif action_parts[0] == "put":
            item = ' '.join(action_parts[1:-2])
            location = action_parts[-1]
            self.current_state[item] = location
        elif action_parts[0] in ["clean", "heat", "cool", "use"]:
            item = ' '.join(action_parts[1:])
            self.current_state[item] = f"{action_parts[0]}d"
        elif action_parts[0] == "go":
            location = ' '.join(action_parts[2:])
            self.current_state["agent_location"] = location
        elif action_parts[0] == "open":
            item = ' '.join(action_parts[1:])
            self.current_state[item] = "open"
        
        # Update completed steps
        self._update_completed_steps(action)
        
        # Update task progress
        self._update_task_progress()

    def _update_completed_steps(self, action):
        for step in self.oracle_knowledge:
            if step not in self.completed_steps and all(word in action.lower() for word in step.lower().split()):
                self.completed_steps.add(step)
                break

    def _update_task_progress(self):
        total_objects = sum(self.task_objects.values())
        placed_objects = sum(1 for item, location in self.current_state.items() 
                             if any(obj_type in item for obj_type in self.task_objects) 
                             and location == self.task_objects.get("in", ""))
        self.task_progress = placed_objects / total_objects

    def respond_to_agent(self, query):
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["where", "find", "look"]):
            return self._get_location_hint(query_lower)
        
        if "what" in query_lower and "next" in query_lower:
            return self._get_next_step()

        if "task" in query_lower and "complete" in query_lower:
            if self.task_progress == 1:
                return "Yes, the task is completed."
            else:
                return f"Not yet. You've completed about {self.task_progress:.0%} of the task."

        if "which" in query_lower and any(obj_type in query_lower for obj_type in self.task_objects):
            return self._get_object_selection_hint(query_lower)

        # If the query doesn't match any specific category, provide a general hint
        return self._get_general_hint()

    def _get_location_hint(self, query):
        for item, location in self.current_state.items():
            if item in query:
                return f"The {item} is {location}."
        
        for step in self.oracle_knowledge:
            if step not in self.completed_steps:
                if "go to" in step:
                    location = step.split("go to")[-1].strip()
                    return f"You might want to go to {location}."
                elif "take" in step:
                    item = step.split("take")[-1].split("from")[0].strip()
                    location = step.split("from")[-1].strip()
                    return f"You might find {item} in/on {location}."
        
        return "I'm not sure about that specific item. Try exploring the environment or focusing on the task objectives."

    def _get_next_step(self):
        for step in self.oracle_knowledge:
            if step not in self.completed_steps:
                return f"You might want to try to {step}."
        return "You've completed all the necessary steps. Check if the task is fully done."

    def _get_object_selection_hint(self, query):
        obj_type = next((obj for obj in self.task_objects if obj in query), None)
        if obj_type:
            placed_objects = [item for item, location in self.current_state.items() 
                              if obj_type in item and location == self.task_objects.get("in", "")]
            remaining_count = self.task_objects[obj_type] - len(placed_objects)
            if remaining_count > 0:
                available_objects = [item for item, location in self.current_state.items() 
                                     if obj_type in item and location not in [self.task_objects.get("in", ""), "in_hand"]]
                if available_objects:
                    return f"Please put {' and '.join(available_objects[:remaining_count])} in the {self.task_objects.get('in', '')}."
            else:
                return f"You have already placed all required {obj_type}s."
        return "I'm not sure which objects you're asking about. Could you be more specific?"

    def _get_general_hint(self):
        if self.task_progress < 0.25:
            return "You're still in the early stages. Start by finding the required objects and the destination."
        elif self.task_progress < 0.5:
            return "You're making progress. Continue finding and placing the required objects."
        elif self.task_progress < 1:
            return f"You're in the later stages of the task. Focus on placing the remaining objects in the {self.task_objects.get('in', '')}."
        else:
            return "You've taken all the necessary actions. Double-check if the task is fully completed."



class EnvironmentAlignedRBUserSimulator:
    def __init__(self, oracle_knowledge, initial_state, task_description):
        self.oracle_knowledge = oracle_knowledge
        self.initial_state = initial_state
        self.current_state = initial_state.copy()
        self.task_description = task_description
        self.agent_actions = []
        self.agent_observations = []
        self.completed_steps = set()
        self.task_progress = 0
        self.task_object, self.task_destination = self._parse_task_description()

    def _parse_task_description(self):
        # Extract the task details from the description
        match = re.search(r'Your task is to: put (some|a) (\w+) (on|in) (\w+)', self.task_description)
        if match:
            quantity, obj, preposition, destination = match.groups()
            return obj, destination
        else:
            return None, None

    def update_state(self, action, observation):
        self.agent_actions.append(action)
        self.agent_observations.append(observation)
        
        # Update current_state based on the action and observation
        action_parts = action.split()
        if action_parts[0] == "take":
            item = ' '.join(action_parts[1:-2])
            self.current_state[item] = "in_hand"
        elif action_parts[0] == "put":
            item = ' '.join(action_parts[1:-2])
            location = action_parts[-1]
            self.current_state[item] = location
        elif action_parts[0] in ["clean", "heat", "cool", "use"]:
            item = ' '.join(action_parts[1:])
            self.current_state[item] = f"{action_parts[0]}d"
        elif action_parts[0] == "go":
            location = ' '.join(action_parts[2:])
            self.current_state["agent_location"] = location
        elif action_parts[0] == "open":
            item = ' '.join(action_parts[1:])
            self.current_state[item] = "open"
        
        # Update completed steps
        self._update_completed_steps(action)
        
        # Update task progress
        self._update_task_progress()

    def _update_completed_steps(self, action):
        for step in self.oracle_knowledge:
            if step not in self.completed_steps and all(word in action.lower() for word in step.lower().split()):
                self.completed_steps.add(step)
                break

    def _update_task_progress(self):
        if self.task_object and self.task_destination:
            for item, location in self.current_state.items():
                if self.task_object in item and location == self.task_destination:
                    self.task_progress = 1
                    return
        self.task_progress = len(self.completed_steps) / len(self.oracle_knowledge)

    def respond_to_agent(self, query):
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["where", "find", "look"]):
            return self._get_location_hint(query_lower)
        
        if "what" in query_lower and "next" in query_lower:
            return self._get_next_step()

        if "task" in query_lower and "complete" in query_lower:
            if self.task_progress == 1:
                return "Yes, the task is completed."
            else:
                return f"Not yet. You've completed about {self.task_progress:.0%} of the task."

        # If the query doesn't match any specific category, provide a general hint
        return self._get_general_hint()

    def _get_location_hint(self, query):
        if self.task_object and self.task_object in query:
            for step in self.oracle_knowledge:
                if "take" in step and self.task_object in step:
                    location = step.split("from")[-1].strip()
                    return f"You might find the {self.task_object} in/on {location}."
        
        if self.task_destination and self.task_destination in query:
            return f"The {self.task_destination} is in the room. You need to locate it."
        
        for item, location in self.current_state.items():
            if item in query:
                return f"The {item} is {location}."
        
        return "I'm not sure about that specific item. Try exploring the environment or focusing on the task objectives."

    def _get_next_step(self):
        for step in self.oracle_knowledge:
            if step not in self.completed_steps:
                return f"You might want to try to {step}."
        return "You've completed all the necessary steps. Check if the task is fully done."

    def _get_general_hint(self):
        if self.task_progress == 0:
            return f"You need to find a {self.task_object} and put it on the {self.task_destination}. Start by looking for the {self.task_object}."
        elif self.task_progress < 0.5:
            return f"You're making progress. Have you found the {self.task_object} yet? If so, now you need to locate the {self.task_destination}."
        elif self.task_progress < 1:
            return f"You're almost there. Make sure you've put the {self.task_object} on the {self.task_destination}."
        else:
            return "You've taken all the necessary actions. Double-check if the task is fully completed."


class OracleAwareRBUserSimulator:
    def __init__(self, oracle_knowledge, initial_state, task_description):
        self.oracle_knowledge = oracle_knowledge
        self.initial_state = initial_state
        self.current_state = initial_state.copy()
        self.task_description = task_description
        self.agent_actions = []
        self.agent_observations = []
        self.completed_steps = set()
        self.task_progress = 0
        self.task_object, self.task_action, self.task_destination = self._parse_task_description()

    def _parse_task_description(self):
        # Remove the prefix "Your task is to: "
        task = self.task_description.replace("Your task is to: ", "").strip().lower()
        
        # Define patterns for different task types
        patterns = [
            # put a clean spatula in drawer
            (r'put (a|an|some) (\w+) (\w+) (in|on) (\w+)', 
             lambda m: {'action': 'put', 'object': m.group(2), 'state': m.group(3), 'destination': m.group(5)}),
            
            # put some watch on safe
            (r'put (a|an|some) (\w+) (in|on) (\w+)', 
             lambda m: {'action': 'put', 'object': m.group(2), 'destination': m.group(4)}),
            
            # examine the alarmclock with the desklamp
            (r'examine the (\w+) with the (\w+)', 
             lambda m: {'action': 'examine', 'object': m.group(1), 'tool': m.group(2)}),
            
            # heat some potato and put it in garbagecan
            (r'(\w+) (some|a|an) (\w+) and put it (in|on) (\w+)', 
             lambda m: {'action': m.group(1), 'object': m.group(3), 'destination': m.group(5)}),
        ]
        
        # Try to match the task with one of the patterns
        for pattern, extract in patterns:
            match = re.match(pattern, task)
            if match:
                return extract(match)
        
        # If no pattern matches, return a default structure
        return {'action': 'unknown', 'description': task}

    def update_state(self, action, observation):
        self.agent_actions.append(action)
        self.agent_observations.append(observation)
        
        # Update current_state based on the action and observation
        action_parts = action.split()
        if action_parts[0] == "take":
            item = ' '.join(action_parts[1:-2])
            self.current_state[item] = "in_hand"
        elif action_parts[0] == "put":
            item = ' '.join(action_parts[1:-2])
            location = action_parts[-1]
            self.current_state[item] = location
        elif action_parts[0] in ["clean", "heat", "cool", "use"]:
            item = ' '.join(action_parts[1:])
            self.current_state[item] = f"{action_parts[0]}d"
        elif action_parts[0] == "go":
            location = ' '.join(action_parts[2:])
            self.current_state["agent_location"] = location
        
        # Update completed steps
        self._update_completed_steps(action)
        
        # Update task progress
        self._update_task_progress()

    def _update_completed_steps(self, action):
        for step in self.oracle_knowledge:
            if step not in self.completed_steps and all(word in action.lower() for word in step.lower().split()):
                self.completed_steps.add(step)
                break

    def _update_task_progress(self):
        self.task_progress = len(self.completed_steps) / len(self.oracle_knowledge)

    def respond_to_agent(self, query):
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["where", "find", "look"]):
            return self._get_location_hint(query_lower)
        
        if "what" in query_lower and "next" in query_lower:
            return self._get_next_step()

        if "task" in query_lower and "complete" in query_lower:
            if self.task_progress == 1:
                return "Yes, the task is completed."
            else:
                return f"Not yet. You've completed about {self.task_progress:.0%} of the task."

        # If the query doesn't match any specific category, provide a general hint
        return self._get_general_hint()

    def _get_location_hint(self, query):
        for step in self.oracle_knowledge:
            if step not in self.completed_steps:
                if "go to" in step:
                    location = step.split("go to")[-1].strip()
                    return f"You should go to {location}."
                elif "take" in step and self.task_object in step:
                    location = step.split("from")[-1].strip()
                    return f"You can find the {self.task_object} in/on {location}."
        
        return f"I'm not sure about the exact location. Try exploring the environment to find the {self.task_object}."

    def _get_next_step(self):
        for step in self.oracle_knowledge:
            if step not in self.completed_steps:
                return f"You should try to {step}."
        return "You've completed all the necessary steps. Check if the task is fully done."

    def _get_general_hint(self):
        if 'action' not in self.task_info or self.task_info['action'] == 'unknown':
            return f"Focus on the task: {self.task_info['description']}"
        
        if self.task_progress == 0:
            if self.task_info['action'] == 'put':
                state = self.task_info.get('state', '')
                return f"You need to find a {state} {self.task_info['object']} and put it in/on the {self.task_info['destination']}. Start by looking for the {self.task_info['object']}."
            elif self.task_info['action'] == 'examine':
                return f"You need to find the {self.task_info['object']} and the {self.task_info['tool']}, then examine the {self.task_info['object']} with the {self.task_info['tool']}."
            else:
                return f"You need to {self.task_info['action']} the {self.task_info['object']}. Start by finding it."
        
        elif self.task_progress < 0.5:
            if self.task_info['action'] == 'put':
                state = self.task_info.get('state', '')
                return f"You're making progress. Have you found and {state} the {self.task_info['object']} yet? If so, now you need to locate the {self.task_info['destination']}."
            elif self.task_info['action'] == 'examine':
                return f"You're making progress. Have you found both the {self.task_info['object']} and the {self.task_info['tool']} yet?"
            else:
                return f"You're making progress. Continue following the steps to {self.task_info['action']} the {self.task_info['object']}."
        
        elif self.task_progress < 1:
            if self.task_info['action'] == 'put':
                state = self.task_info.get('state', '')
                return f"You're almost there. Make sure you've put the {state} {self.task_info['object']} in/on the {self.task_info['destination']}."
            elif self.task_info['action'] == 'examine':
                return f"You're almost there. Make sure you've examined the {self.task_info['object']} with the {self.task_info['tool']}."
            else:
                return f"You're almost there. Make sure you've completed the {self.task_info['action']} action on the {self.task_info['object']}."
        
        else:
            return "You've taken all the necessary actions. Double-check if the task is fully completed."


# Agentic User Simulator
# class LLMUserAgent:
#     def __init__(self, oracle_knowledge, model_name, base_prompt):
#         self.oracle_knowledge = oracle_knowledge
#         self.model = model_name
#         self.base_prompt = load_txt(base_prompt)
    
#     def user_response(self, query):
#         prompt = self.base_prompt.format(oracle_text= self.oracle_knowledge, query=query)
#         response = gpt4_agent(prompt)
#         return response
    
class LLMUserAgent:
    def __init__(self, oracle_knowledge, model_name, base_prompt):
        self.oracle_knowledge = oracle_knowledge
        self.model = model_name
        self.base_prompt = load_txt(base_prompt)
        self.action_history = []
        self.observation_history = []

    def user_response(self, query):
        # Construct the history string
        history = self._construct_history()
        
        # Construct the full prompt
        prompt = self.base_prompt.format(
            oracle_text=self.oracle_knowledge,
            action_observation_history=history,
            query=query
        )
        
        # Get response from the language model
        response = gpt4_agent(prompt)
        return response

    def update_state(self, action, observation):
        self.action_history.append(action)
        self.observation_history.append(observation)

    def _construct_history(self):
        history = ""
        for i, (action, obs) in enumerate(zip(self.action_history, self.observation_history)):
            history += f"Action {i+1}: {action}\nObservation {i+1}: {obs}\n\n"
        return history