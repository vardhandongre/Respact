# darpa-demo
This repository is meant to be used as a submodule of the [ReSpAct](https://github.com/vardhandongre/Respact)
using the `respact-demo` branch.
### Environment Setup
1. Create a virtual environment (recommended):

```bash
conda create -n darpa-demo python=3.12 
conda activate darpa-demo
pip install -r requirements.txt 
```

> [!WARNING]
> If you use MacOS, Apple Clang 17.0 breaks one
of the dependencies. Install [Xcode 16.2](https://developer.apple.com/download/all/)
or earlier (comes with Apple Clang 16.0).
Verify using `g++ --version`.

2. Set up Alfworld as outlined in the [ReSpAct README](https://github.com/vardhandongre/Respact/blob/main/README.md)