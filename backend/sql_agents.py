from typing import List, Dict, Any, Optional
from .llm_client import OllamaClient


class SelectorAgent:
    def __init__(self, llm_client: OllamaClient):
        self.llm = llm_client
    
    def get_system_prompt(self) -> str:
        return """You are a database schema analyzer. Your job is to identify which tables and columns are relevant for answering a given question.

CRITICAL RULES:
1. ONLY return table and column names that exist in the provided schema
2. Use EXACT table.column format
3. Include foreign key relationships if joins are needed
4. Be conservative - don't include unnecessary tables
5. NEVER hallucinate columns that don't exist in the schema
6. Return as clean text listing: table.column format, one per line"""

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        question = input_data["question"]
        schema = input_data["schema"]


#in this section, some few-shot examples as to the layout of tables help this agent a lot
#some are left in a text file in this project and should be pasted here when testing
        prompt = f"""DATABASE SCHEMA (EXACT COLUMN NAMES):
{schema}


QUESTION: "{question}"

TASK: Identify ONLY the table.column combinations needed to answer this question.
Use EXACT names from the schema above. Do not invent column names.

ANALYSIS RULES:
- Look at the question keywords to identify relevant data
- For comparative questions (most/highest): Include the comparison column
- Always include JOIN keys when joining tables
- Use only column names that exist in the provided schema

FORMAT: Return each needed column as table.column on a separate line.

RESPOND WITH COLUMN LIST ONLY:"""

        response = self.llm.generate(
            prompt=prompt,
            system=self.get_system_prompt(),
            temperature=0.0
        )
        
        return {
            "selected_schema": response.strip(),
            "reasoning": f"Selected schema for: {question}"
        }


class DecomposerAgent:
    def __init__(self, llm_client: OllamaClient):
        self.llm = llm_client
    
    def get_system_prompt(self) -> str:
        return """You are an expert SQLite query generator. Convert natural language questions into valid SQLite queries.

CRITICAL RULES - FOLLOW EXACTLY:
1. GENERATE ONLY VALID SQL CODE - NO EXPLANATIONS, NO COMMENTS, NO MARKDOWN
2. Use ONLY the columns provided in the schema - DO NOT INVENT COLUMN NAMES
3. Use proper SQLite syntax (|| for concatenation, LIMIT not TOP)
4. Use appropriate JOINs when joining tables
5. For "highest/most/top/best" questions: MUST include ORDER BY ... DESC LIMIT 1
6. For "lowest/least/worst" questions: MUST include ORDER BY ... ASC LIMIT 1
7. For "top N" questions: ORDER BY ... DESC LIMIT N
8. Use exact string matches for state names (e.g., "Wisconsin" not "WI")
9. RESPOND WITH SQL QUERY ONLY - NO OTHER TEXT
10. ALWAYS add LIMIT 1 for superlative questions (most, highest, best, worst, etc.)"""

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        question = input_data["question"]
        selected_schema = input_data["selected_schema"]
        
        available_columns = [line.strip() for line in selected_schema.split('\n') if line.strip() and '.' in line.strip()]
        
        domain_knowledge = """
GENERAL SQL PATTERNS:
- "highest/most X" = ORDER BY X DESC LIMIT 1 (must include ORDER BY and LIMIT)
- "lowest/least X" = ORDER BY X ASC LIMIT 1
- "top N" = ORDER BY column DESC LIMIT N
- "average X" = SELECT AVG(X)
- "in [Location]" = WHERE location_column = '[Location]'

JOIN PATTERNS:
- To connect tables with shared keys, use ON table1.key = table2.key
- Only join tables that are actually needed for the question
- Use table aliases (T1, T2, T3) for clarity

FILTERING PATTERNS:
- If question mentions a specific location/category, add WHERE clause
- Use appropriate comparison operators (=, <, >, LIKE)

COMMON QUESTION PATTERNS:
- "Which X has most Y in Z" = SELECT X FROM ... WHERE location='Z' ORDER BY Y DESC LIMIT 1
- "What is average X in Y" = SELECT AVG(X) FROM ... WHERE location='Y'
- "Top N X by Y" = SELECT X FROM ... ORDER BY Y DESC LIMIT N
      



      """
        
        prompt = f"""AVAILABLE COLUMNS (USE ONLY THESE):
{chr(10).join(available_columns)}

{domain_knowledge}

LEARN FROM THESE EXAMPLES:
     EXAMPLE 1:
     Question: "Which customer has placed the most orders?"
     SQL: SELECT customer_id FROM orders GROUP BY customer_id ORDER BY COUNT(*) DESC 
   LIMIT 1;
     
     EXAMPLE 2:
     Question: "What is the most expensive product?"
     SQL: SELECT product_name FROM products ORDER BY price DESC LIMIT 1;
     
     EXAMPLE 3:
     Question: "How many customers are from California?"
     SQL: SELECT COUNT(*) FROM customers WHERE state = 'CA';
     
     EXAMPLE 4:
     Question: "What is the total revenue from completed orders?"
     SQL: SELECT SUM(total_amount) FROM orders WHERE status = 'completed';
     
     EXAMPLE 5:
     Question: "Which product category has the highest average price?"
     SQL: SELECT T2.category_name FROM products T1 JOIN categories T2 ON 
   T1.category_id = T2.category_id GROUP BY T1.category_id ORDER BY AVG(T1.price) DESC
    LIMIT 1;
     
     EXAMPLE 6:
     Question: "How many orders were placed in 2023?"
     SQL: SELECT COUNT(*) FROM orders WHERE order_date LIKE '2023%';
     
     EXAMPLE 7:
     Question: "Which city has the most customers?"
     SQL: SELECT city FROM customers GROUP BY city ORDER BY COUNT(*) DESC LIMIT 1;
     
     EXAMPLE 8:
     Question: "What is the average order value for pending orders?"
     SQL: SELECT AVG(total_amount) FROM orders WHERE status = 'pending';
     
     EXAMPLE 9:
     Question: "List the top 3 most ordered products by quantity"
     SQL: SELECT T2.product_name FROM order_items T1 JOIN products T2 ON T1.product_id
    = T2.product_id GROUP BY T1.product_id ORDER BY SUM(T1.quantity) DESC LIMIT 3;
     
     EXAMPLE 10:
     Question: "Which customer spent the most money total?"
     SQL: SELECT customer_id FROM orders GROUP BY customer_id ORDER BY 
   SUM(total_amount) DESC LIMIT 1;
     
     KEY PATTERNS FROM EXAMPLES:
     - Customer analysis: Use customers table with city, state columns
     - Product queries: Use products table with price, category_id columns
     - Order analysis: Use orders table with status, total_amount, order_date columns
     - Revenue calculations: SUM(total_amount) for financial totals
     - Time filtering: Use LIKE '2023%' for year-based date filtering
     - Most/highest questions: ORDER BY column DESC LIMIT 1
     - Counting patterns: COUNT(*) with GROUP BY for frequency analysis
     - Product-order relationships: JOIN order_items with products for detailed 
   analysis
     - Status filtering: WHERE status = 'completed'/'pending'/'shipped'



NOW SOLVE: "{question}"

CRITICAL REQUIREMENTS:
- Follow the exact patterns shown in the examples above
- Use EXACT column names from available columns
- For "highest/most/which X": ORDER BY X DESC LIMIT 1
- Use proper table aliases like in examples
- Respond with SQL query ONLY

SQL QUERY:"""

        response = self.llm.generate(
            prompt=prompt,
            system=self.get_system_prompt(),
            temperature=0.0
        )
        
        sql_query = self._extract_sql(response)
        
        return {
            "sql_query": sql_query,
            "confidence": 0.8
        }
    
    def _extract_sql(self, resp: str) -> str:
        import re
        # clean markdown
        sql_blocks = re.findall(r'```sql\s*(.*?)\s*```', resp, re.DOTALL | re.IGNORECASE)
        if sql_blocks:
            sql = sql_blocks[0].strip()
        else:
            code_blocks = re.findall(r'```\s*(.*?)\s*```', resp, re.DOTALL)
            if code_blocks:
                sql = code_blocks[0].strip()
            else:
                cleaned = resp.strip()
                prefixes_to_remove = [
                    "Here's the SQL query:",
                    "The SQL query is:",
                    "Query:",
                    "SQL:",
                    "SQL Query:",
                    "The query:",
                    "Here is the query:",
                    "Based on the schema,",
                ]
                
                for prefix in prefixes_to_remove:
                    if cleaned.lower().startswith(prefix.lower()):
                        cleaned = cleaned[len(prefix):].strip()
                
                lines = cleaned.split('\n')
                sql_lines = []
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    if line.lower().startswith(('this query', 'the query', 'explanation:', 'note:')):
                        break   #sometimes it likes to add these so well just toss those
                    #anyline without sql words is bad
                    if not any(keyword in line.upper() for keyword in ['SELECT', 'FROM', 'WHERE', 'JOIN', 'ORDER', 'GROUP', 'HAVING', 'UNION', 'INSERT', 'UPDATE', 'DELETE']):
                        if not line.endswith(';') and not line.endswith(',') and 'ON' not in line.upper():
                            continue
                    sql_lines.append(line)
                
                #fit them all back together
                sql = ' '.join(sql_lines)
                if ';' in sql:
                    sql = sql.split(';')[0] + ';'
        
        return sql.strip()


class RefinerAgent:
    def __init__(self, llm_client: OllamaClient):
        self.llm = llm_client
    
    def get_system_prompt(self) -> str:
        return """You are a SQLite debugging expert. Fix syntax errors and optimize queries for SQLite.

CRITICAL RULES - FOLLOW EXACTLY:
1. GENERATE ONLY VALID SQL CODE - NO EXPLANATIONS, NO COMMENTS, NO MARKDOWN
2. Fix the specific error mentioned in the error message
3. Use ONLY SQLite-compatible syntax (|| for concatenation, LIMIT not TOP)
4. Use ONLY columns that exist in the provided schema
5. Preserve the original query's intent
6. For missing columns, find the correct column name from schema
7. For ambiguous columns, add proper table aliases
8. RESPOND WITH CORRECTED SQL QUERY ONLY - NO OTHER TEXT"""

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        original_query = input_data["sql_query"]
        error_message = input_data.get("error_message", "")
        schema = input_data["schema"]
        question = input_data["question"]
        
        common_fixes = self._analyze_error(error_message, original_query, question)
        
        prompt = f"""ORIGINAL QUESTION: "{question}"

DATABASE SCHEMA:
{schema}

BROKEN SQL QUERY:
{original_query}

ERROR MESSAGE: {error_message}

TASK: Fix the SQL query to eliminate the error.

{common_fixes}

CRITICAL FIXES NEEDED:
- Use ONLY columns that exist in the schema above
- Fix JOIN conditions using proper table.column = table.column syntax
- Fix table aliases consistently (T1, T2, T3)
- Ensure WHERE clauses reference correct tables
- For comparative questions, ensure ORDER BY and LIMIT are included

FIXED SQL QUERY:"""

        response = self.llm.generate(
            prompt=prompt,
            system=self.get_system_prompt(),
            temperature=0.3 #kicking it up for some chance debugging
        )
        
        sql_query = self._extract_sql(response)
        
        return {
            "refined_query": sql_query,
            "fixes_applied": f"Fixed error: {error_message}"
        }
    
    def _analyze_error(self, error_message: str, query: str, question: str) -> str:
        fixes = []
        
        error_lower = error_message.lower()
        
        if "no such column" in error_lower:
            fixes.append("- ERROR: Column doesn't exist → Use correct column name from schema")
        
        if "ambiguous column" in error_lower:
            fixes.append("- ERROR: Ambiguous column → Add proper table aliases (T1.column, T2.column)")
        
        return "SPECIFIC FIXES NEEDED:\n" + "\n".join(fixes) if fixes else "COMMON FIXES:"
    
    def _extract_sql(self, response: str) -> str:
        import re
        
        sql_blocks = re.findall(r'```sql\s*(.*?)\s*```', response, re.DOTALL | re.IGNORECASE)
        if sql_blocks:
            return sql_blocks[0].strip()
        
        code_blocks = re.findall(r'```\s*(.*?)\s*```', response, re.DOTALL)
        if code_blocks:
            return code_blocks[0].strip()
        
        cleaned = response.strip()
        
        prefixes_to_remove = [
            "Here's the corrected SQL query:",
            "The corrected SQL query is:",
            "Here's the fixed SQL query:",
            "The fixed SQL query is:",
            "Here's the SQL query:",
            "The SQL query is:",
            "Query:",
            "SQL:",
            "SQL Query:",
            "Fixed query:",
            "Corrected query:",
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
        
        
        lines = cleaned.split('\n')
        sql_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.lower().startswith(('this query', 'the query', 'explanation:', 'note:', 'this fixes')):
                break
            if not any(keyword in line.upper() for keyword in ['SELECT', 'FROM', 'WHERE', 'JOIN', 'ORDER', 'GROUP', 'HAVING', 'UNION', 'INSERT', 'UPDATE', 'DELETE']):
                if not line.endswith(';') and not line.endswith(',') and 'ON' not in line.upper():
                    continue
            sql_lines.append(line)
        
        result = ' '.join(sql_lines)
        
        if ';' in result:
            result = result.split(';')[0] + ';'
        
        return result.strip()
