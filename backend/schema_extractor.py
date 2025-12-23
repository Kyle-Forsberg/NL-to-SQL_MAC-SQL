import sqlite3
from typing import List, Dict, Any


class SchemaExtractor:
    def __init__(self, database_path: str):
        self.database_path = database_path
    
    def get_tables(self) -> List[str]:
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            return [row[0] for row in cursor.fetchall()]
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    "name": row[1],
                    "type": row[2],
                    "not_null": bool(row[3]),
                    "primary_key": bool(row[5])
                })
            
            cursor = conn.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys = []
            for row in cursor.fetchall():
                foreign_keys.append({
                    "column": row[3],
                    "references_table": row[2],
                    "references_column": row[4]
                })
            
            return {
                "table_name": table_name,
                "columns": columns,
                "foreign_keys": foreign_keys
            }
    
    def get_schema_text(self) -> str:
        tables = self.get_tables()
        schema_parts = []
        
        for table_name in tables:
            table_schema = self.get_table_schema(table_name)
            
            table_part = f"Table: {table_name}\n"
            table_part += "Columns:\n"
            
            for col in table_schema["columns"]:
                col_desc = f"  - {col['name']} ({col['type']}"
                if col['primary_key']:
                    col_desc += ", PRIMARY KEY"
                if col['not_null']:
                    col_desc += ", NOT NULL"
                col_desc += ")\n"
                table_part += col_desc
            
            if table_schema["foreign_keys"]:
                table_part += "Foreign Keys:\n"
                for fk in table_schema["foreign_keys"]:
                    table_part += f"  - {fk['column']} -> {fk['references_table']}.{fk['references_column']}\n"
            
            schema_parts.append(table_part)
        
        return "\n".join(schema_parts)
    
    def get_column_list(self) -> str:
        tables = self.get_tables()
        column_list = []
        
        for table_name in tables:
            table_schema = self.get_table_schema(table_name)
            for col in table_schema["columns"]:
                column_list.append(f"{table_name}.{col['name']}")
        
        return "\n".join(sorted(column_list))
    
    def get_sample_data(self, table_name: str, limit: int = 3) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.database_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            return [dict(row) for row in cursor.fetchall()]
