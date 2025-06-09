## Business Case Assistant
A tool for writing business case documents using AI agents.

## Overview
The Business Case Assistant uses advanced language models and LangGraph to interview the user about project requirements and create a business case document based on the user's responses.

## Prerequisites
- Python 3.11+
- Install uv: https://docs.astral.sh/uv/getting-started/installation/

## Setup
1. Set up your virtual environment:
    ```bash
    uv sync
    ```
2. Install beeai
    ```bash
    brew install i-am-bee/beeai/beeai
    ```

3. Configure your env: 
    ```bash
    beeai env setup
    ``` 
    

## Usage

1. Start the ACP server: 
    ```bash 
    uv run server
    ```
    
3.  Interact with the agent using the UI: 
    ```bash 
    beeai ui
    ```
