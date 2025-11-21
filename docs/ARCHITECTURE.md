---
title: Architecture
---

# System Components

The following components make up the system:

* `User`: The user interacting with the application.
* `Application`: The desktop application running on the user's computer.
* `Workspace`: A directory on the user's computer where the user can store their files and configurations.
* `Tools`: A collection of tools that the user can use to perform various tasks, such as creating new files, modifying existing ones, and running commands in the terminal.

# System Interfaces

The following interfaces define how these components interact with each other:

* `User Interface` (UI): The graphical user interface through which the user interacts with the application. It displays a list of available tools, as well as the current working directory and file system tree.
* `Terminal Interface` (TI): The terminal-based interface through which the user can run commands. It provides an interactive prompt for entering commands and displaying their output.
* `Tool Interface` (TO): The interface between the tool and the application, allowing it to communicate with the application and display its results.

# System Components

_The following components define all parts of the application_  
Example:

```md
# System Components
## Kontxt (class)
### Properties
* `id` (UUID)
* `plan` (List[PlanItem])
* `user` (str)
* `context` (List[str])
### Methods
* `curration_status(self)->bool`
  Returns the curration status of the current session
* `curration_status(self, stat: bool)`  
  Sets the curration status of the current session
* `is_complete(self) -> bool`  
  Returns True if the curration status is complete
```

# System Dependencies

_This section shows how components relate to each other_

Example:

```md
# System Dependencies
## ChatApp
### ChatApp->Kontxt:`curate(message:str)`
### ChatApp->Kontxt:`context_str`

```

# Features

_Assistant shall track current, future, and completed features under this section_

## Current Feature

_Allow only one feature here.  When User refers to `current feature` or `this feature` or `current work` they mean the feature listed in this section.  When completed move the feature to Features.Completed Features_  
Example:

```md
    ## Current Feature

    [>] Add a FooBar Widget to the UI
        Requirements: `docs/features/requirements/foobar_widget.md`
        Implementation: `doces/features/work/foobar_widget/md`
```

## Future Features

_Add all new features here.  When they are implemented, move them from this section to Features.Current Feature_  
Example:

```md
    ## Future Features
    [ ] Add a BarFooBar Widget to the UI
        Requirements: `docs/features/requirements/barfoobar_widget.md`
        Implementation: `doces/features/work/barfoobar_widget/md`
```

## Completed Features

_This is an archive of complete features for User and Assistant Reference. Move completed features here. Prepend the system date when completed/moved. Retain in order executed. Refer to this section to find indexes to Requirements and Implementations_  
Example:

```md
    ##  Completed Features
    [✔] (2025-11-20 10:15:00Z) Basic UI Window
        Requirements: `docs/features/requirements/basic_ui.md`
        Implementation: `doces/features/work/basic_ui/md`
```
