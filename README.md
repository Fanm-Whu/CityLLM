# CityLLM

An AI-powered urban land use simulation system built with DeepSeek LLM agents and cellular automata algorithms.

## Overview

CityLLM is an intelligent urban simulation platform that leverages Large Language Models (LLM) to decompose complex urban planning tasks, analyze data requirements, and execute simulation algorithms. The system automatically breaks down high-level urban planning queries into executable subtasks through a chain of specialized agents.

## Architecture

The system uses a multi-agent pipeline architecture:

```
User Input → TaskDecomposerAgent → InterParserAgent → DataDemandAgent → AlgorithmExeAgent → Results
```

### Agent Chain

| Agent | Description |
|-------|-------------|
| [TaskDecomposerAgent](src/agents/TaskDecomposerAgent.py) | Decomposes complex user queries into simple, executable subtasks |
| [InterParserAgent](src/agents/InterParserAgent.py) | Interprets and parses user intent from natural language |
| [DataDemandAgent](src/agents/DataDemandAgent.py) | Analyzes data requirements for each subtask |
| [AlgorithmExeAgent](src/agents/AlgorithmExeAgent.py) | Executes the appropriate simulation algorithm |

### Core Algorithms

| Algorithm | Description |
|-----------|-------------|
| [ImprovedCA](src/algorithms/ImprovedCA.py) | Improved Cellular Automata model for land use simulation |
| [PopulationSimulator](src/algorithms/PopulationSimulator.py) | Population growth and distribution simulation |
| [GDPSimulator](src/algorithms/GDPSimulator.py) | GDP-related economic simulation |
| [LandSimulator](src/algorithms/LandSimulator.py) | Land use change simulation |
| [GeoProcessor](src/algorithms/GeoProcessor.py) | Geographic data processing utilities |
| [MutiElementsSimulator](src/algorithms/MutiElementsSimulator.py) | Multi-element urban simulation |
| [SimulateHelper](src/algorithms/SimulateHelper.py) | Simulation helper utilities |

## Project Structure

```
CityLLM/
├── README.md
├── main.py                    # Entry point
├── src/
│   ├── agents/               # Agent implementations
│   │   ├── BaseAgent.py
│   │   ├── ChainAgent.py
│   │   ├── TaskDecomposerAgent.py
│   │   ├── InterParserAgent.py
│   │   ├── DataDemandAgent.py
│   │   └── AlgorithmExeAgent.py
│   └── algorithms/           # Simulation algorithms
│       ├── ImprovedCA.py
│       ├── PopulationSimulator.py
│       ├── GDPSimulator.py
│       ├── LandSimulator.py
│       ├── GeoProcessor.py
│       ├── MutiElementsSimulator.py
│       └── SimulateHelper.py
└── tests/                   # Test suite
    ├── test_ChainAgent.py
    ├── test_ImprovedCA.py
    └── ...
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd CityLLM
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:
```bash
DEEPSEEK_API_KEY=your_api_key_here
```

## Usage

Initialize the ChainAgent and run urban simulation tasks:

```python
from src.agents import ChainAgent

# Initialize the agent chain
agent = ChainAgent()

# Run a simulation task
result = agent.run("Simulate population growth in Beijing over the next 20 years")

# Process results
for r in result:
    print(r.to_string())
```

### Running a Single Task

```python
from src.agents import ChainAgent

agent = ChainAgent()
single_result = agent.singleTaskRun("Calculate urban expansion for Shanghai")
print(single_result.to_string())
```

## Requirements

- Python 3.8+
- deepseek-chat (via langchain)
- langchain >= 0.1.0
- numpy
- GDAL
- scipy
- python-dotenv

## License

MIT License