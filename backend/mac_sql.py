import sqlite3
import json
from typing import Dict, Any, Optional, List

from .sql_agents import SelectorAgent, DecomposerAgent, RefinerAgent
from .llm_client import OllamaClient
from .schema_extractor import SchemaExtractor
from .query_validator import QueryValidator


class MACSQL:
    def __init__(self, 
                 database_path: str,
                 #model_name: str = "deepseek-r1:8b",  #smaller general model, did okay
                 model_name: str = "codellama:13b",  #Larger code-specialized model, did better
                 max_refinement_attempts: int = 3):  #can play with this, turn up temp on refiner if you want to crank this 
        
        self.database_path = database_path
        self.max_refinement_attempts = max_refinement_attempts
        
        self.llm_client = OllamaClient(model=model_name)
        
        self.selector = SelectorAgent(self.llm_client)
        self.decomposer = DecomposerAgent(self.llm_client)
        self.refiner = RefinerAgent(self.llm_client)
        
        if not database_path:
            raise ValueError("database_path is required")
        
        self.schema_extractor = SchemaExtractor(database_path)
        self.validator = QueryValidator(database_path)
        
        print(f"MAC-SQL initialized with model: {model_name}")
    
    def query(self, question: str) -> Dict[str, Any]:
        print(f"Processing question: {question}")
        
        try:
            if not self.schema_extractor:
                raise ValueError("No database configured")
            
            schema = self.schema_extractor.get_schema_text()
            cols = self.schema_extractor.get_column_list()
            
            #Selector Agent
            print("Running Selector...")
            sel_input = {"question": question, "schema": cols}
            sel_result = self.selector.process(sel_input)
            
            #Decomposer Agent
            print("Running Decomposer...")
            decomp_input = {
                "question": question,
                "selected_schema": sel_result["selected_schema"]
            }
            decomp_result = self.decomposer.process(decomp_input)
            
            #refiner agent 
            query = decomp_result["sql_query"]
            tries = 0
            
            while tries < self.max_refinement_attempts:
                print(f"Validation attempt {tries + 1}")
                
                #check query
                if self.validator:
                    check = self.validator.validate_query(query)
                    if check["is_valid"]:
                        print("Query valid")
                        break
                    else:
                        print(f"Query failed: {check['error']}")
                        err = check["error"]
                else:
                    err = "Check syntax"
                
                #refiner looping 
                print(f"Running Refiner (attempt {tries + 1})...")
                ref_input = {
                    "sql_query": query,
                    "error_message": err,
                    "schema": cols,  
                    "question": question
                }
                ref_result = self.refiner.process(ref_input)
                query = ref_result["refined_query"]
                tries += 1
            
            #send it home
            result = None
            if self.validator and check.get("is_valid", False):
                result = self.validator.execute_query(query)
            
            return {
                "question": question,
                "final_sql": query,
                "selector_output": sel_result,
                "decomposer_output": decomp_result,
                "tries": tries,
                "execution_result": result,
                "success": True
            }
            
        except Exception as e:
            print(f"MAC-SQL processing failed: {e}")
            return {
                "question": question,
                "error": str(e),
                "success": False
            }
    
    def test_connection(self) -> Dict[str, Any]:
        results = {}
        
        #ensure ollama is all good
        try:
            if self.llm_client.is_available():
                results["llm_status"] = "connected"
                print(f"LLM model {self.llm_client.model} is available")
            else:
                results["llm_status"] = "model_not_found"
                print(f"Model {self.llm_client.model} not found")
        except Exception as e:
            results["llm_status"] = f"error: {e}"
        
        #ensure db is in order
        if self.database_path:
            try:
                with sqlite3.connect(self.database_path) as conn:
                    conn.execute("SELECT 1")
                results["database_status"] = "connected"
                print(f"Database {self.database_path} is accessible")
            except Exception as e:
                results["database_status"] = f"error: {e}"
        else:
            results["database_status"] = "no_database_configured"
        
        return results
    




    def printMACSQLResult(self,result):
        print('Final SQL:')                                                                       
        print(result.get('final_sql', 'None'))                                                 
        print()                                                                                   
        print('Success:', result.get('success'))                                                  
        print('Tries:', result.get('tries', 0)) 
        print('Results from the Database: ')
        if result["success"]==False: 
            print("There was either no result, or a unseccessful result, run using smaller model if Ollama times out")
            print(result)
            return

        if result["execution_result"] and result["execution_result"]["success"]:
            results = result["execution_result"]["results"]
            row_count = result["execution_result"]["row_count"]
                    
            print(f"\nResults ({row_count} rows):")
                    
            if results:
                headers = list(results[0].keys())
                print("  " + " | ".join(headers))
                print("  " + "-" * (len(" | ".join(headers))))
                            
                for row in results[:10]:
                    values = [str(row[h]) for h in headers]
                    print("  " + " | ".join(values))
                        
                    if len(results) > 10:
                        print(f"... and {len(results) - 10} more rows")
                        
            else:
                print("Query execution failed")
                if result["execution_result"]:
                    print(f"Error: {result['execution_result']['error']}")
