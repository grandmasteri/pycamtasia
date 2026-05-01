# Examples

Runnable end-to-end scripts. Each script is kept in sync with the tests; if an example breaks, CI fails.

## Example 0: Create, Save, and Validate a New Project

Create a new Camtasia project from the bundled template, save it, and run validation to confirm there are no errors.

```{literalinclude} ../../examples/00_hello_world.py
:language: python
:linenos:
```

## Example 1: Inspect a Project

Load a fixture project and print summary statistics along with a markdown report.

```{literalinclude} ../../examples/01_inspect_project.py
:language: python
:linenos:
```

## Example 2: Add Clips to a Project

Create a project, add a track with a placeholder clip, save, and verify the clip persists on reload.

```{literalinclude} ../../examples/02_add_clips.py
:language: python
:linenos:
```

## Example 3: Add Captions and Export SRT

Load a fixture, add captions, save the project, and export the captions as an SRT subtitle file.

```{literalinclude} ../../examples/03_add_captions.py
:language: python
:linenos:
```

## Example 4: Template Workflow

Save a project as a `.camtemplate`, instantiate a new project from it, and verify the result has tracks.

```{literalinclude} ../../examples/04_template_workflow.py
:language: python
:linenos:
```
