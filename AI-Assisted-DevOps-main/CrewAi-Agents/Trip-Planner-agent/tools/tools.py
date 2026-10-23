import os
import json
import requests
from langchain.tools import tool

class TripTools:

    @tool("Search the internet")
    def search_internet(query: str) -> str:
        """
        Useful to search the internet about a given topic and return relevant results.
        Use this to find current weather, flights, hotels, restaurants, and events.
        """
        top_result_to_return = 4
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query})
        headers = {
            'X-API-KEY': os.environ.get('SERPER_API_KEY', ''),
            'content-type': 'application/json'
        }
        
        try:
            response = requests.request("POST", url, headers=headers, data=payload)
            response.raise_for_status() # Raise an exception for bad status codes
            results = response.json().get('organic', [])
            
            string_results = []
            for result in results[:top_result_to_return]:
                string_results.append(f"Title: {result.get('title')}\nLink: {result.get('link')}\nSnippet: {result.get('snippet')}\n---")
                
            return '\n'.join(string_results)
        except Exception as e:
            return f"An error occurred while searching the internet: {e}"

    @tool("Calculate budget and math")
    def calculate(operation: str) -> str:
        """
        Useful to perform any mathematical calculations, like sum, subtraction, multiplication, division, etc.
        The input to this tool should be a mathematical expression, a couple examples are `200*7` or `5000/2*10`.
        Use this to calculate total trip budgets.
        """
        try:
            # Using eval carefully here for basic math. In a hyper-strict production environment, 
            # you might use a safer math parser, but for LLM agents, this is standard.
            result = eval(operation)
            return f"The result of the calculation is: {result}"
        except SyntaxError:
            return "Error: Invalid syntax in mathematical expression. Please provide a valid math equation."
        except ZeroDivisionError:
            return "Error: Cannot divide by zero."
        except Exception as e:
            return f"An error occurred during calculation: {e}"