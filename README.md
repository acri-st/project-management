# Project Management

📌 [DESP-AAS Sandbox Parent Repository](https://github.com/acri-st/DESP-AAS-Sandbox)

## Table of Contents

- [Introduction](#Introduction)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Development](#development)
- [Contributing](#contributing)

## Introduction

### What is Project Management?

Project Management is a microservice that serves as the central hub for managing projects. It provides a comprehensive interface for creating, organizing, and overseeing sandbox project.

The Project Management UI enables users to:
- Create and configure new projects
- Manage project settings and configurations
- Monitor project status and resources
- Coordinate with other microservices (Auth, VM management, Storage)
- Access project development environments and tools

## Prerequisites

Before you begin, ensure you have the following installed:
- **Git** 
- **Docker** Docker is mainly used for the test suite, but can also be used to deploy the project via docker compose

## Installation

1. Clone the repository:
```bash
git clone https://github.com/acri-st/project-management.git
cd project-management
```

## Development

## Development Mode

### Standard local development

Setup environment
```bash
make setup
```

To clean the project and remove node_modules and other generated files, use:
```bash
make clean
```

## Contributing

Check out the **CONTRIBUTING.md** for more details on how to contribute.
