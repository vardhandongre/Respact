import json
import random
from collections import defaultdict
import argparse 

def sample_data(input_file, output_file, n, shuffle=True):
    # Ensure equal number of games are selected from each task type
    assert n % 6 == 0, "n must be divisible by 6"

    # Load file path data
    with open(input_file, 'r') as f:
        data = json.load(f)

    sampled_data = {}

    for split, tasks in data.items():
        samples_per_task = n // 6
        if split in ['valid_seen', 'valid_train', 'valid_unseen']:
            samples_per_task = 2
        print(f"Sampling {samples_per_task} games from {split} split")
        split_samples = []
        for task, games in tasks.items():
            # sampled_data[split][task] = random.sample(games, samples_per_task)
            print(f" Total games in {task} task: {len(games)}")
            if len(games) < samples_per_task:
                print(f"Warning: {task} task has less than {samples_per_task} games")
                print(f"Sampling {len(games)} games from {task} task")
                task_samples = games
            else:
                task_samples = random.sample(games, samples_per_task)
            split_samples.extend(task_samples)

        if shuffle:
            print(f"Shuffling {len(split_samples)} games")
            random.shuffle(split_samples)
        sampled_data[split] = split_samples

    with open(output_file, 'w') as f:
        json.dump(sampled_data, f, indent=4)

    print(f"Sampled data saved to {output_file}")


if __name__ == "__main__":
    # input_file = "data/file_path_per_task_per_split.json"
    # output_file = "data/sample.json"
    #argparse.ArgumentParser() 
    parser = argparse.ArgumentParser(description='Sample data from json file')
    parser.add_argument('--input_file', default="data/file_path_per_task_per_split.json", type=str, help='Input json file')
    parser.add_argument('--output_file', default="data/experiments/data_sample.json", type=str, help='Output json file')
    parser.add_argument('--n', default=60, type=int, help='Number of games to sample')
    parser.add_argument('--shuffle', action='store_true', help='Shuffle the data')
    args = parser.parse_args()

    sample_data(args.input_file, args.output_file, args.n, args.shuffle)

