from backend.mac_sql import MACSQL                                                             
                                                                                         
mac = MACSQL('example.db', model_name='codellama:13b')
result = mac.query('Show me the top 5 customers by total order value with their email addresses')                       
mac.printMACSQLResult(result)



print("#######")
#printResult(result)
