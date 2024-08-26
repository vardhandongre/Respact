import alfworld
import alfworld.agents.environment

def create_environment(base_config, split="train"):
    '''
    Function to create the environment - ALFWorld TEXTWORLD environment
    Args:
        base_config (dict): Base configuration dictionary
        split (str): Split to be used for the environment - train or validation
    '''
    env_type = base_config["env"]["type"]
    env_class = getattr(alfworld.agents.environment, env_type)
    env = env_class(base_config, train_eval=split)
    return env.init_env(batch_size=1)