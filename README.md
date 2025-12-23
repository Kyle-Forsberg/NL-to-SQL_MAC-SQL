# MAC-SQL: Multi-Agent Collaborative SQL

A local implementation of Multi-Agent Collaborative text-to-SQL using SQLCoder and DeepSeek R1 via Ollama.

## Architecture

**Three specialized agents:**
1. **Selector Agent**: Identifies relevant tables/columns from schema
2. **Decomposer Agent**: Breaks down natural language into SQL logic  
3. **Refiner Agent**: Fixes and optimizes generated SQL queries

## Setup

```bash
pip install -r requirements.txt
ollama pull codellama:13b
```

## Usage

```python
from backend.mac_sql import MACSQL

mac = MACSQL("path/to/database.db")

result = mac.query("Show me all customers who bought more than $1000 worth of products")
printMACResult(result)
```


## Hardware Requirements

- **Minimum**: 8GB VRAM 
