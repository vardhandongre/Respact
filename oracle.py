import os
import json
import glob
import random
import argparse
from os.path import join as pjoin

import textworld
from textworld.agents import HumanAgent

import textworld.gym

from alfworld.info import ALFWORLD_DATA
from alfworld.agents.utils.misc import add_task_to_grammar
from alfworld.agents.environment.alfred_tw_env import AlfredExpert, AlfredDemangler, AlfredExpertType

def oracle_support(game_file, expert = AlfredExpertType.PLANNER):
    '''
    Function to display the expert plan for a given game file
    Args:
        game_file (str): Path to the game file
        expert (AlfredExpertType): Expert type to be used for the game
    
    '''
    expert = AlfredExpert(expert_type=expert)
    request_infos = textworld.EnvInfos(won=True, admissible_commands=True, score=True, max_score=True, intermediate_reward=True, extras=["expert_plan"])
    env_id = textworld.gym.register_game(game_file, request_infos,
                                         max_episode_steps=1000000,
                                         wrappers=[AlfredDemangler(), expert])
    oracle_env = textworld.gym.make(env_id)
    _, oracle_infos = oracle_env.reset()
    print(f"Oracle Information: {oracle_infos['extra.expert_plan']}")
