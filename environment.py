import alfworld
import alfworld.agents.environment

def create_environment(base_config, split="train"):
    env_type = base_config["env"]["type"]
    env_class = getattr(alfworld.agents.environment, env_type)
    env = env_class(base_config, train_eval=split)
    return env.init_env(batch_size=1)