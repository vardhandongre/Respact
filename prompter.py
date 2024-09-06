import os
import sys
import json

class PromptGenerator():
    def __init__(self, data_path, output_path):
        self.data_path = data_path
        self.output_path = output_path
        self.data = {}
        self.load_data()
        
    def load_data(self):
        for file in os.listdir(self.data_path):
            if file.endswith('.txt'):
                with open(os.path.join(self.data_path, file), 'r') as f:
                    self.data[file] = f.read()
                    
    def save_json(self):
        with open(self.output_path, 'w') as f:
            json.dump(self.data, f, indent=4) # indent=4 for pretty print
        
    def load_json(self):
        with open(self.output_path, 'r') as f:
            return json.load(f)
        
    def pretty_print(self, data, in_format='json'):
        # to do
        pass