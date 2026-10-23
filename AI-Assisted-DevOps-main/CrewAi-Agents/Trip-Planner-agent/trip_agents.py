from crewai import Agent
from langchain_openai import ChatOpenAI
from tools.tools import TripTools 

# Use the recommended langchain_openai import
llm = ChatOpenAI(model='gpt-3.5-turbo')

class TripAgents():

  def city_selection_agent(self):
    return Agent(
        role='City Selection Expert',
        goal='Select the best city based on weather, season, and prices',
        backstory='An expert in analyzing travel data to pick ideal destinations',
        tools=[TripTools.search_internet], # Added search tool
        llm=llm,
        verbose=True)

  def local_expert(self):
    return Agent(
        role='Local Expert at this city',
        goal='Provide the BEST insights about the selected city',
        backstory="""A knowledgeable local guide with extensive information
        about the city, its attractions and customs""",
        tools=[TripTools.search_internet], # Added search tool
        llm=llm,
        verbose=True)

  def travel_concierge(self):
    return Agent(
        role='Amazing Travel Concierge',
        goal="""Create the most amazing travel itineraries with budget and 
        packing suggestions for the city""",
        backstory="""Specialist in travel planning and logistics with 
        decades of experience""",
        tools=[
            TripTools.search_internet, 
            TripTools.calculate # Concierge needs math for the budget!
        ], 
        llm=llm,
        verbose=True)