# Hints
When changes are made to this module, be sure to install in the demo framework's virtualenv.

- inspect module
 - find functions, inputs, outputs, etc
- ast_literal_eval
 - another 'little known library' relating to evaluating strings as python syntax
- eval
 - Evaluate a string as if it was python code

# TODO 
- Install into demo framework as a library (maybe clone/merge this as part of the build process)

# Notes

Pieces of a successful demo framework module

- Interface between module and web application
 - pass data between UI and backend
- UI element generation (if any) for web application

# Overview 

An example of setting up a module in the demo framework. Ideally, as little work
as possible should be done on the developers' side. A reasonable requirement 
is that hte demo should be packaged into a python module.

The workflow should be:

 1. create a repo in the demos repository
 2. put your module in its own folder in that repo
 3. create a main.py
  - import the functions to demo
  - decorate the functions
 4. done

Steps to accomplish this:
 -create a decorator in mlpux_demo module and add it to the main.py
 -use the inspect module to learn about argument types and return types
