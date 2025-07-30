## v0.3.1-beta.1 (2025-07-30)

## v0.3.0 (2025-07-28)

### BREAKING CHANGE

- extra validation function and save function now accepts two positional arguments: name and config.

### Feat

- feat: allow profiles to be disabled
- press enter to confirm editing profile
- hide json by default for password entries
- add controls for terminal output
- add icons
- feat: add support for profiles
- allow schema setting for UserConfig
- add support for adding schema order to xxxOf
- auto collapse menu on small screens
- add error handler for background programs

### Fix

- get_schema returns a deepcopy of the schema
- use the correct icon for invalid profile
- allow none type for some parameters
- escape the messages
- change display style of checklists
- add the missing "the" before "main program"
- anchor of array items not set
- change positions of checkboxes

### Refactor

- add a type annotation
- modify file structure and configurations
- use importlib to get version
- rearrange the code files
- change layout to 8:4
- change dropdown font style to normal
- adjust layout by changing ratio
- change some positional arguments
- change indentaion of json string to 4
- rewrite the logic of output capture
- change the messages when cleaning up
- restructure some parts of the html

## v0.2.1 (2024-10-25)

### Feat

- hijack output and display it in the editor

## v0.2.0 (2024-10-24)

### Feat

- upgrade bootstrap from version 4 to 5

### Fix

- adjust styles of certain button groups

## v0.1.1 (2024-10-24)

### Fix

- remove console output
- change front-end style when adding items

## v0.1.0 (2024-10-23)

### Feat

- no longer pass name arg into functions
- launch main program and termination
- suport config saving
- change styles of checkboxes automatically
- get config from back-end
- accept post requests
- add flash messages
- add web element
- build the frontend

### Fix

- no minified version of fontawesome
- static file link error
- ipv6 problem
- f-string and backslash problem

