# ReSpAct

## Quickstart

Create a virtual environment (recommended)

    conda create -n respact python=3.12
    conda activate respact
    pip install -r requirements.txt

## Alfworld Setup

> [!WARNING]  
> If you are using MacOS with an arm-based system, it is recommended to use
> 
    CONDA_SUBDIR=osx-64 conda create -n alfworld python=3.12
    conda activate alfworld

Install with pip (python3.9+):

    pip install alfworld

Download PDDL & Game files and pre-trained MaskRCNN detector:
```bash
export ALFWORLD_DATA=<storage_path>
alfworld-download
```

Use `--extra` to download pre-trained checkpoints and seq2seq data.

## Run ReSpAct Experiments
```bash
export OPENAI_API_KEY=<key>
```
For Azure:
```bash
export AZURE_OPENAI_ENDPOINT=<endpoint>
export AZURE_OPENAI_KEY=<key>
```

The experiments are controlled via two yaml files, `base_config.yaml` to control the alfworld games and `experiment_configs.yaml` for the respact experimentation. 

    python main.py
