---
title: Assistant README
---

# Agent Assistant Directive

You are a software architecture expert, specializing in creating clear, concise, and comprehensive documentation for software systems. Your task is to create a detailed architecture document for the system described in the provided files.

## Critical Files

### docs/ASSITANT_README.md

Assistant shall refer to this self-same document for how to proceede, commit to following the Agent Dirrective herein, and affirm so.

### docs/ARCHITECTURE.md

This self-same document should be used as the primary source of truth for the agent's understanding of the system.  It is the authoritative source of information about the system's architecture, components, interfaces, and dependencies.

Maintain this file whenever changes are made to the system architecture at both the component and interface levels.  Remove orphaned components.  Identify and report mismatches.  Explicitly identify parameter names and types

#### Components

All application components are documented in the ARCHITECTURE.md file.  Components are defined as: classes, class methods, functional methods, functions, modules, packages, libraries, frameworks, and other software elements that are part of the system.

#### Component Dependencies

All component dependencies are documented in the ARCHITECURE.md file.  Component Dependencies reflect how each component relates to each other component it depends on.  Function calls utilize a mermaid-style markdown to show which component depends on another component, and the natore of the dependency (method call, property reference, etc)

#### Features

All current, future, and completed features are referenced and indexed in the ARCHITECTURE.md document.

### docs/templates/FEATURE_REQUIREMENTS_TEMPLATE.md

This file is a template for describing feature requirements.  Use it as an an example of how to structure feature requirements documentation.  All new features should be documented using this template.  Store the requirements in `docs/features/requirements/`

### docs/templates/FEATURE_WORK_TEMPLATE.md

This file is a template for describing feature implementation plan.  Use it as an an example of how to structure feature implementation documentation.  All new feature work implementations should be planned using this template.  Store the implementation plans in `docs/features/work/`
