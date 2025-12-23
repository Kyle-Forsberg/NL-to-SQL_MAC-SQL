import sqlite3
import sqlparse
from typing import Dict, Any, List


class QueryValidator:
    def __init__(self, database_path: str):
        self.database_path = database_path
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        try:
            #make there is a query
            parsed = sqlparse.parse(query)
            if not parsed:
                return {
                    "is_valid": False,
                    "error": "Empty or invalid SQL query"
                }
            q_upper = query.upper().strip()
            
            #make sure the LLM doesnt nuke the DB for fun
            dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
            
            for keyword in dangerous_keywords:
                if keyword in q_upper:
                    return {
                        "is_valid": False,
                        "error": f"LLM tried to use {keyword} "
                    }
           #try executing the query 
            try:
                with sqlite3.connect(self.database_path) as conn:
                    conn.execute(f"EXPLAIN QUERY PLAN {query}")
                                    #this is amazing sqlite 
                return {
                    "is_valid": True,
                    "error": None,
                    "parsed_query": str(parsed[0])
                }
                
            except sqlite3.Error as e:
                return {
                    "is_valid": False,
                    "error": f"SQL error: {str(e)}"
                }
                
        except Exception as e:
            return {
                "is_valid": False,
                "error": f"Query validation failed: {str(e)}"
            }
    
    def execute_query(self, query: str, limit: int = 100) -> Dict[str, Any]:
        check = self.validate_query(query)
        if not check["is_valid"]:
            return {"success": False, "error": check["error"], "results": []}
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row
                final_q = self._add_limit_if_needed(query, limit)
                
                cursor = conn.execute(final_q)
                rows = cursor.fetchall()
                
                results = [dict(row) for row in rows]
                
                column_names = [description[0] for description in cursor.description] if cursor.description else []
                
                return {
                    "success": True,
                    "results": results,
                    "column_names": column_names,
                    "row_count": len(results),
                    "query_executed": final_q
                }
                
        except sqlite3.Error as e:
            print(f"Query execution failed: {e}")
            return {
                "success": False,
                "error": f"Execution error: {str(e)}",
                "results": []
            }
    
    def _add_limit_if_needed(self, sql_query: str, limit: int) -> str:
        sql_upper = sql_query.upper().strip()
       #so we dont nuke the terminal with a bad result 
        if sql_upper.startswith("SELECT") and "LIMIT" not in sql_upper:
            return f"{sql_query.rstrip(';')} LIMIT {limit}"
        
        return sql_query
    
