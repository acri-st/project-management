# DESP-AAS Project Management


## Table of Contents

- [Introduction](#Introduction)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Development](#development)
- [Testing](#testing)
- [Contributing](#contributing)
- [Deployment](#deployment)
- [License](#license)
- [Support](#support)

## Introduction

###  What is the DESP-AAS Sandbox?

DESP-AAS Sandbox is a service that allows users to develop applications and models using cloud based services and to ease the deployment to the DESP-AAS collaborative platform.

The Microservices that make up the Sandbox project are the following: 
- **Auth** Authentication service to authenticate users.
- **Project management** Project management system. - *the current project*
- **VM management** manages the virtual machines for the projects. These virtual machines are where the user manages their project and develops.
- **Storage** Manages the project git files.


### What is Project Management?

Project Management is a microservice that serves as the central hub for managing projects within the DESP-AAS Sandbox ecosystem. It provides a comprehensive interface for creating, organizing, and overseeing sandbox project.

The Project Management UI enables users to:
- Create and configure new projects
- Manage project settings and configurations
- Monitor project status and resources
- Coordinate with other DESP-AAS sandbox microservices (Auth, VM management, Storage)
- Access project development environments and tools

## Prerequisites

Before you begin, ensure you have the following installed:
- **Git** 
- **Docker** Docker is mainly used for the test suite, but can also be used to deploy the project via docker compose

## Installation

1. Clone the repository:
```bash
git clone https://github.com/acri-st/DESPAAS-project-management.git
cd DESPAAS-project-management
```

## Development

## Development Mode

### Standard local development

Setup environment
```bash
make setup
```

Start the development server:
```bash
make start
```

To clean the project and remove node_modules and other generated files, use:
```bash
make clean
```

## Contributing

Check out the **CONTRIBUTING.md** for more details on how to contribute.