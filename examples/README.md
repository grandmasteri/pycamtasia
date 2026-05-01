# pycamtasia Examples

Runnable end-to-end scripts demonstrating the pycamtasia API.

## Prerequisites

Install pycamtasia in development mode from the repository root:

```bash
pip install -e .
```

## Running

Each script is self-contained and can be run directly:

```bash
cd examples/
python 00_hello_world.py
python 01_inspect_project.py
python 02_add_clips.py
python 03_add_captions.py
python 04_template_workflow.py
```

## Scripts

| Script | Description |
|--------|-------------|
| `00_hello_world.py` | Create, save, and validate a new project |
| `01_inspect_project.py` | Load a fixture project and print summary statistics |
| `02_add_clips.py` | Create a project, add a track with a placeholder clip |
| `03_add_captions.py` | Add captions to a project and export as SRT |
| `04_template_workflow.py` | Save a project as a template, instantiate from it |

## Testing

The examples double as smoke tests via `conftest.py`:

```bash
cd ..
PYTHONPATH=src python -m pytest examples/ -q
```
