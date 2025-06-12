# darpa-demo
### Environment Setup
1. Create a virtual environment (same as ReSpAct):

```bash
conda create -n respact python=3.12 
conda activate respact
pip install -r requirements.txt 
```

> [!WARNING]
> If you use MacOS, Apple Clang 17.0 breaks one
of the dependencies. Install [Xcode 16.2](https://developer.apple.com/download/all/)
or earlier (comes with Apple Clang 16.0).
Verify using `g++ --version`.

2. Set up Alfworld as outlined in the [ReSpAct README](https://github.com/vardhandongre/Respact/blob/main/README.md)
   1. Download the Alfworld dataset
   2. Ensure the `ALFWORLD_DATA` directory is set in your environment variables
3. Configure user credentials for OpenAI or Azure OpenAI API
   1. Either export them in bash or set them in `demo.env` file

### Running the Demo
1. Run the script: `python demo3.py`. If you get an error like `ModuleNotFoundError: No module named 'oracle'` or any other
   local module, ensure you are in the git repository root directory, then export `PYTHONPATH=$(pwd)` in your terminal.
2. A tk window will open.
