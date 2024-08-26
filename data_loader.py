import os
import sys

import numpy as np
import pandas as pd

# return
class DataLoader:
    def __init__(self, sampled_data, split):
        self.sampled_data = sampled_data
        self.split = split

    def load_data_paths(self):
        data_file_path_list = self.sampled_data[self.split]
        return data_file_path_list

    def copy_folders_from_list(self, data_file_path_list, output_path):
        for data_file_path in data_file_path_list:
            os.system(f"cp -r {data_file_path} {output_path}")