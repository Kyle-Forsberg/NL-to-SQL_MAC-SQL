

import sys
import os

from backend.mac_sql import MACSQL
from create_sample_db import create_sample_database


def main():
    print("Creating sample database...")
    db_path = create_sample_database("example.db")
    
    #init MAC-SQL
    print("Initializing MAC-SQL...")
    mac = MACSQL(database_path=db_path, model_name="codellama:13b") #can change model here if pleased
    
    status = mac.test_connection()
    print(f"Connection status: {status}")
    
    if status["llm_status"] != "connected":
        print("LLM model not available, make sure Ollama is running and codellama:13b is pulled.")
        return
    
    #interactive query loop
    print("\n" + "="*60)
    print("MAC-SQL Interactive Demo")
    print("Ask questions about the e-commerce database!")
    print("Type 'quit' to exit, 'schema' to see database structure")
    print("="*60)
    
    while True:
        question = input("\nYour question: ").strip()
        
        if question.lower() == 'quit':
            break
        elif question.lower() == 'schema':
            schema = mac.schema_extractor.get_schema_text()
            print(f"\nDatabase Schema:\n{schema}")
            continue
        elif not question:
            continue
        
        print(f"\nProcessing: {question}")
        print("-" * 40)
        
        try:
            result = mac.query(question)
            
            if result["success"]:
                print(f"Generated SQL:")
                print(f"  {result['final_sql']}")
                print(f"Debug - Selector output: {result['selector_output']['selected_schema'][:100]}...")
                print(f"Debug - Tries: {result['tries']}")
                
                if result["execution_result"] and result["execution_result"]["success"]:
                    results = result["execution_result"]["results"]
                    row_count = result["execution_result"]["row_count"]
                    
                    print(f"\nResults ({row_count} rows):")
                    
                    if results:
                        # Show column headers
                        headers = list(results[0].keys())
                        print("  " + " | ".join(headers))
                        print("  " + "-" * (len(" | ".join(headers))))
                        
                        # Show first few rows
                        for row in results[:10]:  # Limit to 10 rows
                            values = [str(row[h]) for h in headers]
                            print("  " + " | ".join(values))
                        
                        if len(results) > 10:
                            print(f"  ... and {len(results) - 10} more rows")
                    else:
                        print("No results found")
                        
                else:
                    print("Query execution failed")
                    if result["execution_result"]:
                        print(f"Error: {result['execution_result']['error']}")
                        
            else:
                print(f"Failed to generate SQL: {result.get('error', 'Unknown error')}")
                
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
