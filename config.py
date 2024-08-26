import yaml
import json

class Config:
    '''
    Config class to load the config file
    config file is a yaml file
    '''
    @staticmethod
    def load_config(config_path='config.yaml'):
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)

        # # load sampled data
        # with open(config['sampled_data_file'], 'r') as f:
        #     config['sampled_data'] = json.load(f)

        return config