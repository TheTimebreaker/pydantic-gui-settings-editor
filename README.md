# Pydantic GUI settings editor
A PySide6 / Qt based GUI editor for Pydantic(v2) settings models.

## Overview

Have you worked on a python project and wanted to add user settings and/or customizability?

Everyone LOVES being able to tinker an app to ones own liking. But just dumping a config file somewhere is also not ideal. Documentation on the settings may be hard to find and not all users even want to tinker directly with the config files. And then theres no guarantee of the user inputs actually working as intended.

This project aims to give developers the tools needed to

- (A) create settings that are verifiably valid, using `Pydantic` models
- (B) create a graphical way for users to securely interact with settings
- (C) without having to create the GUI manually, which is difficult to change later

## Features

- Edit `Pydantic` models through a automatically generated GUI based on said model
- Nest your settings however deep your heart desires
- Settings will always be validated through pydantic
- A beautiful interface made with `PySide6 / Qt`
- Light and Dark modes out of the box
- Add descriptions and titles in your `Pydantic` model, which will automatically appear in the GUI to document your settings right where the user needs them

## Currently supported field types

A `Pydantic` field should be defined as:
```python
    setting: <typehint> = Field(
        default=<default value>,
        title=<Optional: title>,
        description=<Optional: description>
    )
```
The `title` and `description` field are strongly recommended, to get the most out of the documentation.

The following setting types are currently supported:

- `bool`
- `int` and `float`
- `str` and `set[str]`
- `Enum` and `set[Enum]`
- `pathlib.Path` and `set[pathlib.Path]`
    - a special typehint for `FilePath`s and `DirectoryPath`s has been added to `pydantic_gui_settings_editor.types`, which you can import to specify a path to a file or a file to a path, while just type hinting a field as `Path` will allow any path.
- more (nested) `Pydantic` models

If there is a data type missing for your usecase, don't be afraid to create an issue on GitHub!

## Installation

Currently, this project is unpublished on `PyPi`. Therefore, you have to install it directly from the releases tab.