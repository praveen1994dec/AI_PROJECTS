from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from langchain_openai import ChatOpenAI 
import os

from tools.k8s_tools import (
    get_pod_logs, 
    get_pod_events, 
    get_pod_status, 
    get_pod_yaml
)

@CrewBase
class K8sRcaCrew():
    """Kubernetes Root Cause Analysis Crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        self.llm = ChatOpenAI(
            model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-4o"),
            temperature=0.0 
        )

    @agent
    def data_gatherer(self) -> Agent:
        return Agent(
            config=self.agents_config['data_gatherer'],
            tools=[get_pod_logs, get_pod_events, get_pod_status, get_pod_yaml],
            llm=self.llm,
            verbose=True
        )

    @agent
    def rca_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['rca_analyst'],
            llm=self.llm,
            verbose=True
        )

    @agent
    def devops_reporter(self) -> Agent:
        return Agent(
            config=self.agents_config['devops_reporter'],
            llm=self.llm, 
            verbose=True
        )

    @task
    def gather_data_task(self) -> Task:
        return Task(
            config=self.tasks_config['gather_data_task'],
        )

    @task
    def analyze_data_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_data_task'],
            context=[self.gather_data_task()]
        )

    @task
    def generate_report_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_report_task'],
            context=[self.analyze_data_task()]
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )