import copy
import itertools
import json
import re

from tqdm import tqdm

from actions import known_actions
from chatbot import ChatBot_for_eval, ChatBot_for_eval_without_dst, ChatBot_for_usersim
from mapping import DESCRIPTION
from prompt import eval_prompt as prompt
from prompt import user_prompt


class evaluator:
    def __init__(self, data, old_data, sample_ids, prompt=prompt, user_prompt=user_prompt, client_config=dict(), user_client_config=dict(), known_actions=known_actions, online=False, max_online_turns=20):
        self.data = data
        self.old_data = old_data
        self.sample_ids = sample_ids
        self.prompt = prompt
        self.user_prompt = user_prompt
        self.client_config = client_config
        self.user_client_config = self.client_config if len(user_client_config) == 0 and len(client_config) != 0 else user_client_config
        self.known_actions = known_actions
        self.online = online
        self.max_online_turns = max_online_turns
        self.grounding_utterances = self._prepare_grounding_utterances()
        self.eval_result = None
        self.domain_list = ["attraction", "hotel", "restaurant", "taxi", "train"]

    def _prepare_grounding_utterances(self):
        total_grounding_utterances = dict()
        for sample in self.sample_ids:
            grounding_utterances = list()
            composed_utterance = ""
            for i, utterance_turn in enumerate(self.data[sample]["dialogue"]):
                assistant_utterance = utterance_turn["system_transcript"].strip()
                user_utterance = utterance_turn["transcript"].strip()
                if assistant_utterance:
                    composed_utterance += f"{assistant_utterance}\n"
                composed_utterance += f"[User]\n{user_utterance}\n[Assistant]\n"
                grounding_utterances.append(composed_utterance)
            total_grounding_utterances[sample] = grounding_utterances
        return total_grounding_utterances

    def evaluate(self, debug=False):
        if self.online:
            self.eval_result = self._online_evaluate(debug)
        else:
            self.eval_result = self._offline_evaluate(debug)

    def _online_evaluate(self, structured_goal=False, offline_style=False, debug=False):
        eval_result = dict()
        for sample in tqdm(self.sample_ids):
            grounding_utterances = self.grounding_utterances[sample]
            goal_info = self.old_data.get(sample, {"goal":None})["goal"]
            if not structured_goal:
                assert goal_info is not None
                goal_message = goal_info["message"]
            questions = list()
            answers = list()
            action_inputs = list()
            action_outputs = list()
            responses = list()
            states = list()
            current_state = dict()
            finish_status = None
            try:
                assert goal_info is not None
                if structured_goal:
                    clean_goal_info = dict()
                    for domain, domain_content in goal_info.items():
                        if domain_content and domain in self.domain_list:
                            clean_goal_info[domain] = {"info":domain_content.get("info",None), "book":domain_content.get("book",None), "reqt":domain_content.get("reqt",None)}
                    user = ChatBot_for_usersim(system=self.user_prompt.format(user_goals = json.dumps(clean_goal_info)), client_config=self.user_client_config)
                else:
                    clean_goal_message = list()
                    CLEANR = re.compile('<.*?>') 
                    for message in goal_message:
                        clean_message = re.sub(CLEANR, '', message)
                        clean_goal_message.append(clean_message)
                    user = ChatBot_for_usersim(system=self.user_prompt.format(user_goals = "\n".join(clean_goal_message)), client_config=self.user_client_config)
                finish_status = "dialogue ends"
                if offline_style:
                    dialogue_history = ""
                    for i in tqdm(range(self.max_online_turns), leave=False):
                        bot = ChatBot_for_eval(system=self.prompt, known_actions=self.known_actions, client_config=self.client_config)
                        if i == 0:
                            user_utterance = self.data[sample]["dialogue"][0]["transcript"].strip()
                        else:
                            if response:
                                user_utterance = user.sim_session(response)
                            else:
                                user_utterance = user.sim_session(assistant_utterance)
                            if user_utterance[-5:] == "Exit.":
                                break
                        dialogue_history += f"[User]\n{user_utterance}\n[Assistant]\n"
                        assistant_utterance, new_action_inputs, new_action_outputs, response = bot.eval_session(dialogue_history, debug=debug)
                        dialogue_history += f"{response}"
                        for api_inputs in new_action_inputs:
                            state = self._api2state(api_inputs)
                            for slot, value in state.items():
                                current_state[slot] = value
                        questions.append(user_utterance)
                        answers.append(assistant_utterance)
                        action_inputs.append(new_action_inputs)
                        action_outputs.append(new_action_outputs)
                        responses.append(response)
                        states.append(current_state.copy())
                        if i == self.max_online_turns-1:
                            finish_status = None
                else:
                    bot = ChatBot_for_eval(system=self.prompt, known_actions=self.known_actions, client_config=self.client_config)
                    for i in tqdm(range(self.max_online_turns), leave=False):
                        if i == 0:
                            user_utterance = self.data[sample]["dialogue"][0]["transcript"].strip()
                        else:
                            if response:
                                user_utterance = user.sim_session(response)
                            else:
                                user_utterance = user.sim_session(assistant_utterance)
                            if user_utterance[-5:] == "Exit.":
                                break
                        assistant_utterance, new_action_inputs, new_action_outputs, response = bot.eval_session(user_utterance, debug=debug)
                        for api_inputs in new_action_inputs:
                            state = self._api2state(api_inputs)
                            for slot, value in state.items():
                                current_state[slot] = value
                        questions.append(user_utterance)
                        answers.append(assistant_utterance)
                        action_inputs.append(new_action_inputs)
                        action_outputs.append(new_action_outputs)
                        responses.append(response)
                        states.append(current_state.copy())
                        if i == self.max_online_turns-1:
                            finish_status = None
                eval_result[sample] = {"grounding_utterances": grounding_utterances, "goal_info": goal_info, "questions": questions, "answers": answers, "action_inputs": action_inputs, "action_outputs": action_outputs, "responses": responses, "states": states, "finish_status": finish_status}
            except Exception as e:
                eval_result[sample] = {"grounding_utterances": grounding_utterances, "goal_info": goal_info, "questions": questions, "answers": answers, "action_inputs": action_inputs, "action_outputs": action_outputs, "responses": responses, "states": states, "finish_status": finish_status, "error": str(e)}
        return eval_result

    def _offline_evaluate(self, debug=False):
        eval_result = dict()
        for sample in tqdm(self.sample_ids):
            grounding_utterances = self.grounding_utterances[sample]
            goal_info = self.old_data.get(sample, {"goal":None})["goal"]
            answers = list()
            action_inputs = list()
            action_outputs = list()
            responses = list()
            states = list()
            current_state = dict()
            try:
                for grounding_utterance in tqdm(grounding_utterances, leave=False):
                    bot = ChatBot_for_eval(system=self.prompt, known_actions=self.known_actions, client_config=self.client_config)
                    answer, new_action_inputs, new_action_outputs, response = bot.eval_session(grounding_utterance, debug=debug)
                    for api_inputs in new_action_inputs:
                        state = self._api2state(api_inputs)
                        for slot, value in state.items():
                            current_state[slot] = value
                    answers.append(answer)
                    action_inputs.append(new_action_inputs)
                    action_outputs.append(new_action_outputs)
                    responses.append(response)
                    states.append(current_state.copy())
                eval_result[sample] = {"grounding_utterances": grounding_utterances, "goal_info": goal_info, "answers": answers, "action_inputs": action_inputs, "action_outputs": action_outputs, "responses": responses, "states": states}
            except Exception as e:
                eval_result[sample] = {"grounding_utterances": grounding_utterances, "goal_info": goal_info, "answers": answers, "action_inputs": action_inputs, "action_outputs": action_outputs, "responses": responses, "states": states, "error": str(e)}
        return eval_result

    def _api2state(self, api_inputs):
        attraction_slots = ["attraction-name", "attraction-type", "attraction-area"]
        hotel_slots = ["hotel-name", "hotel-type", "hotel-parking", "hotel-area", "hotel-bookday", "hotel-bookstay", "hotel-internet", "hotel-bookpeople", "hotel-stars", "hotel-pricerange"]
        restaurant_slots = ["restaurant-name", "restaurant-food", "restaurant-area", "restaurant-bookday", "restaurant-booktime", "restaurant-bookpeople", "restaurant-pricerange"]
        taxi_slots = ["taxi-arriveby", "taxi-departure", "taxi-leaveat", "taxi-destination"]
        train_slots = ["train-arriveby", "train-day", "train-leaveat", "train-destination", "train-departure", "train-bookpeople"]
        total_slots = list(itertools.chain.from_iterable([attraction_slots, hotel_slots, restaurant_slots, taxi_slots, train_slots]))
        domain_list = ["attraction", "hotel", "restaurant", "taxi", "train"]
        query_only_domain_list = ["taxi"]
        book_indicator_list = ["book", "buy"]
        prim_key_indicator_list = ["name", "ID"]
        
        current_domain = None
        for domain in domain_list:
            if domain in api_inputs["action"]:
                current_domain = domain
        assert current_domain is not None
    
        is_book = None
        for domain in query_only_domain_list:
            if current_domain  == domain:
                is_book = False
        if is_book is None:
            for book_indicator in book_indicator_list:
                if book_indicator in api_inputs["action"]:
                    is_book = True
        if is_book is None:
            is_book = False
        book = "book" if is_book else ""
    
        state = {}
        for api, api_input in api_inputs.items():
            neglect_book = False
            for prim_key_indicator in prim_key_indicator_list:
                if prim_key_indicator in api and is_book:
                    neglect_book = True
            if api != "action":
                if not neglect_book:
                    state_key = f"{current_domain}-{book}{api}".lower()
                else:
                    state_key = f"{current_domain}-{api}".lower()
                if state_key in total_slots:
                    state[state_key] = api_input
    
        return state

    def save_result(self, dir):
        if self.eval_result:
            with open(dir, "w") as f:
                json.dump(self.eval_result, f, indent=4)
        else:
            print("No evaluation results now! Please evaluate first!")

class evaluator_without_dst(evaluator):
    def __init__(self, data, old_data, sample_ids, prompt=prompt, user_prompt=user_prompt, client_config=dict(), user_client_config=dict(), known_actions=known_actions, online=False, max_online_turns=20, log_file=None):
        super().__init__(data, old_data, sample_ids, prompt, user_prompt, client_config=client_config, user_client_config=user_client_config, known_actions=known_actions, online=online, max_online_turns=max_online_turns)
        self.log_file = log_file

    def _offline_evaluate(self, debug=False):
        eval_result = dict()
        for sample in tqdm(self.sample_ids):
            grounding_utterances = self.grounding_utterances[sample]
            goal_info = self.old_data.get(sample, {"goal":None})["goal"]
            dst = self.log_file.get(sample, None)
            answers = list()
            action_inputs = list()
            action_outputs = list()
            responses = list()
            states = list()
            current_state = dict()
            try:
                for turn_idx, grounding_utterance in enumerate(tqdm(grounding_utterances, leave=False)):
                    bot = ChatBot_for_eval_without_dst(system=self.prompt, known_actions=self.known_actions, client_config=self.client_config)
                    if dst:
                        parsed_dst = self._parse_dst(dst["turns"][turn_idx]["pr_original"])
                    else:
                        parsed_dst = None
                    answer, new_action_inputs, new_action_outputs, response = bot.eval_session(grounding_utterance, debug=debug, dst=parsed_dst)
                    for api_inputs in new_action_inputs:
                        state = self._api2state(api_inputs)
                        for slot, value in state.items():
                            current_state[slot] = value
                    answers.append(answer)
                    action_inputs.append(new_action_inputs)
                    action_outputs.append(new_action_outputs)
                    responses.append(response)
                    states.append(current_state.copy())
                eval_result[sample] = {"grounding_utterances": grounding_utterances, "goal_info": goal_info, "answers": answers, "action_inputs": action_inputs, "action_outputs": action_outputs, "responses": responses, "states": states}
            except Exception as e:
                eval_result[sample] = {"grounding_utterances": grounding_utterances, "goal_info": goal_info, "answers": answers, "action_inputs": action_inputs, "action_outputs": action_outputs, "responses": responses, "states": states, "error": str(e)}
        return eval_result
    
    def _parse_dst(self, dst):
        action_inputs = dict()
        for slot_name, slot_value in dst.items():
            domain, slot_name = slot_name.split("-")[0], slot_name.split("-")[1]
            slot_name = slot_name.replace("book", "")
            if domain not in action_inputs:
                action_inputs[domain] = dict()
            action_inputs[domain][slot_name] = slot_value
        return action_inputs
    
class evaluator_without_dst_with_correction(evaluator_without_dst):
    def __init__(self, data, old_data, sample_ids, prompt=prompt, user_prompt=user_prompt, client_config=dict(), user_client_config=dict(), known_actions=known_actions, online=False, max_online_turns=20, log_file=None):
        super().__init__(data, old_data, sample_ids, prompt, user_prompt, client_config, user_client_config, known_actions, online, max_online_turns, log_file)

    def _offline_evaluate(self, debug=False):
        eval_result = dict()
        for sample in tqdm(self.sample_ids):
            grounding_utterances = self.grounding_utterances[sample]
            goal_info = self.old_data.get(sample, {"goal":None})["goal"]
            dst = self.log_file.get(sample, None)
            frictions = list()
            answers = list()
            action_inputs = list()
            action_outputs = list()
            responses = list()
            states = list()
            current_state = dict()
            try:
                for turn_idx, grounding_utterance in enumerate(tqdm(grounding_utterances, leave=False)):
                    bot = ChatBot_for_eval_without_dst(system=self.prompt, known_actions=self.known_actions, client_config=self.client_config)
                    if dst:
                        parsed_dst = self._parse_dst(dst["turns"][turn_idx]["pr_corrected"])
                    else:
                        parsed_dst = None
                    
                    answer, new_action_inputs, new_action_outputs, response = bot.eval_session(grounding_utterance, debug=debug, dst=parsed_dst)
                    for api_inputs in new_action_inputs:
                        state = self._api2state(api_inputs)
                        for slot, value in state.items():
                            current_state[slot] = value
                    answers.append(answer)
                    action_inputs.append(new_action_inputs)
                    action_outputs.append(new_action_outputs)
                    responses.append(response)
                    states.append(current_state.copy())
                eval_result[sample] = {"grounding_utterances": grounding_utterances, "frictions": frictions, "goal_info": goal_info, "answers": answers, "action_inputs": action_inputs, "action_outputs": action_outputs, "responses": responses, "states": states}
            except Exception as e:
                eval_result[sample] = {"grounding_utterances": grounding_utterances, "frictions": frictions, "goal_info": goal_info, "answers": answers, "action_inputs": action_inputs, "action_outputs": action_outputs, "responses": responses, "states": states, "error": str(e)}
        return eval_result
    
    def _online_evaluate(self, structured_goal=False, debug=False):
        eval_result = dict()
        for sample in tqdm(self.sample_ids):
            grounding_utterances = self.grounding_utterances[sample]
            goal_info = self.old_data.get(sample, {"goal":None})["goal"]
            if not structured_goal:
                assert goal_info is not None
                goal_message = goal_info["message"]
            dst = self.log_file.get(sample, None)
            frictions = list()
            answers = list()
            action_inputs = list()
            action_outputs = list()
            responses = list()
            states = list()
            current_state = dict()
            try:
                assert goal_info is not None
                if structured_goal:
                    clean_goal_info = dict()
                    for domain, domain_content in goal_info.items():
                        if domain_content and domain in self.domain_list:
                            clean_goal_info[domain] = {"info":domain_content.get("info",None), "book":domain_content.get("book",None), "reqt":domain_content.get("reqt",None)}
                    user_goals = json.dumps(clean_goal_info)
                else:
                    clean_goal_message = list()
                    CLEANR = re.compile('<.*?>') 
                    for message in goal_message:
                        clean_message = re.sub(CLEANR, '', message)
                        clean_goal_message.append(clean_message)
                    user_goals = "\n".join(clean_goal_message)
                for turn_idx, grounding_utterance in enumerate(tqdm(grounding_utterances, leave=False)):
                    bot = ChatBot_for_eval_without_dst(system=self.prompt, known_actions=self.known_actions, client_config=self.client_config)
                    if dst:
                        parsed_dst = self._parse_dst(dst["turns"][turn_idx]["pr_original"])
                        parsed_fp = self._parse_dst(dst["turns"][turn_idx]["possible_fp"])
                        parsed_fn = self._parse_dst(dst["turns"][turn_idx]["possible_fn"])
                        friction = self._online_correct(parsed_dst, parsed_fp, parsed_fn, user_goals, grounding_utterance)
                        friction_utterance = "".join([f"{assistant_utterance}\n[[User]\n{user_utterance}\n[Assistant]\n" for assistant_utterance, user_utterance in friction])
                        answer, new_action_inputs, new_action_outputs, response = bot.eval_session(grounding_utterance+friction_utterance, debug=debug, dst=None)
                    else:
                        parsed_dst = None
                        friction = list()
                        answer, new_action_inputs, new_action_outputs, response = bot.eval_session(grounding_utterance, debug=debug, dst=parsed_dst)

                    for api_inputs in new_action_inputs:
                        state = self._api2state(api_inputs)
                        for slot, value in state.items():
                            current_state[slot] = value
                    frictions.append(friction)
                    answers.append(answer)
                    action_inputs.append(new_action_inputs)
                    action_outputs.append(new_action_outputs)
                    responses.append(response)
                    states.append(current_state.copy())
                eval_result[sample] = {"grounding_utterances": grounding_utterances, "frictions": frictions, "goal_info": goal_info, "answers": answers, "action_inputs": action_inputs, "action_outputs": action_outputs, "responses": responses, "states": states}
            except Exception as e:
                eval_result[sample] = {"grounding_utterances": grounding_utterances, "frictions": frictions, "goal_info": goal_info, "answers": answers, "action_inputs": action_inputs, "action_outputs": action_outputs, "responses": responses, "states": states, "error": str(e)}
        return eval_result
    
    def _online_correct(self, pr_original, possible_fp, possible_fn, user_goals, dialogue_history):
        # Process fp slots
        for domain, domain_slots in possible_fp.items():
            for fp_slot in domain_slots.keys():
                del pr_original[domain][fp_slot]
        # Process fn slots
        user = ChatBot_for_usersim(system=self.user_prompt.format(user_goals = user_goals, dialogue_history = dialogue_history), client_config=self.user_client_config)
        firction_question = ""
        for domain, domain_slots in possible_fn.items():
            firction_question += f"As for {domain}, could you please again tell me"
            for idx, fn_slot in enumerate(domain_slots.keys()):
                description = DESCRIPTION[domain][fn_slot]
                if idx == 0:
                    firction_question += f" {description}"
                elif idx == len(domain_slots) - 1:
                    firction_question += f", {description}?\n"
                else:
                    firction_question += f", {description}"
        if firction_question:
            user_utterance = user.sim_session(firction_question)
            return [(firction_question, user_utterance)]
        else:
            return []