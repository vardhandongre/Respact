
# import os
# import sys

# from config import Config
# from data_loader import DataLoader
# from methods import get_method
# from environment import create_environment 

# class ExperimentRunner:
#     def __init__(self, exp_config, base_config):
#         self.exp_config = exp_config
#         self.base_config = base_config

#     def run_experiment(self, exp_name, experiment_config):
#         env = create_environment(self.base_config, split=experiment_config.get('split', 'train'))
#         method = get_method(
#             experiment_config['method'],
#             experiment_config['main_prompt_file'],
#             experiment_config['method_prompt_file'],
#             env,
#             experiment_config.get('oracle', False)
#         )
#         return method.run(exp_name = exp_name ,num_games=experiment_config.get('num_games', 134))

# # In your main.py or wherever you set up experiments
# if __name__ == "__main__":
#     base_config = Config.load_config('base_config.yaml')
#     exp_config = Config.load_config('experiment_configs.yaml')
#     runner = ExperimentRunner(exp_config, base_config)
    
#     for exp_name, exp_config in exp_config['experiments'].items():
#         print(f"Running experiment: {exp_name}")
#         # Check if exp_name folder exists in results, if not create it
#         if not os.path.exists(f"results/{exp_name}"):
#             os.makedirs(f"results/{exp_name}")
    
#         rs, cnts = runner.run_experiment(exp_name, exp_config)
#         # Process overall results...

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
        self.run_configs = exp_config.get('run_configs', {})

    def run_selected_experiments(self):
        selected_experiments = self.run_configs.get('selected_experiments', [])
        results = {}

        for exp_name in selected_experiments:
            if exp_name in self.exp_config['experiments']:
                print(f"Running experiment: {exp_name}")
                experiment_config = self.exp_config['experiments'][exp_name]
                
                # Check if exp_name folder exists in results, if not create it
                method = experiment_config['method']
                if not os.path.exists(f"results/{method}/{exp_name}"):
                    os.makedirs(f"results/{method}/{exp_name}")
                
                rs, cnts = self.run_experiment(exp_name, experiment_config)
                results[exp_name] = {'rs': rs, 'cnts': cnts}
            else:
                print(f"Warning: Experiment '{exp_name}' not found in config.")

        return results

    def run_experiment(self, exp_name, experiment_config):
        env = create_environment(self.base_config, split=experiment_config.get('split', 'train'))
        method = get_method(
            experiment_config['method'],
            experiment_config['agent'],
            experiment_config['main_prompt_file'],
            experiment_config['method_prompt_file'],
            env,
            experiment_config.get('oracle', False)
        )
        return method.run(exp_name=exp_name, num_games=experiment_config.get('num_games', 134))

# In your main.py or wherever you set up experiments
if __name__ == "__main__":
    base_config = Config.load_config('base_config.yaml')
    exp_config = Config.load_config('experiment_configs.yaml')
    runner = ExperimentRunner(exp_config, base_config)
    
    results = runner.run_selected_experiments()
    
    # Process overall results
    for exp_name, result in results.items():
        print(f"Results for {exp_name}:")
        print(f"Rewards: {result['rs']}")
        print(f"Counts: {result['cnts']}")
        print("-------------------------")