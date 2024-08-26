
import os
import sys

from config import Config
from data_loader import DataLoader
from methods import get_method
from environment import create_environment 

class ExperimentRunner:
    def __init__(self, exp_config, base_config):
        self.exp_config = exp_config
        self.base_config = base_config

    def run_experiment(self, experiment_config):
        env = create_environment(self.base_config, split=experiment_config.get('split', 'train'))
        method = get_method(
            experiment_config['method'],
            experiment_config['main_prompt_file'],
            experiment_config['method_prompt_file'],
            env,
            experiment_config.get('oracle', False)
        )
        return method.run(num_games=experiment_config.get('num_games', 134))

# set up experiments
if __name__ == "__main__":
    base_config = Config.load_config('base_config.yaml')
    exp_config = Config.load_config('experiment_configs.yaml')
    runner = ExperimentRunner(exp_config, base_config)
    
    for exp_name, exp_config in exp_config['experiments'].items():
        print(f"Running experiment: {exp_name}")
        rs, cnts = runner.run_experiment(exp_config)
        # Process overall results...