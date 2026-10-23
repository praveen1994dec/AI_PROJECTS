import os
import json
import logging
from typing import Dict, List, Optional

from dotenv import load_dotenv
from github import Github, GithubException
from mcp.server.fastmcp import FastMCP

# ==========================================================
# Load Environment
# ==========================================================

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

# ==========================================================
# GitHub Authentication
# ==========================================================

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise Exception("GITHUB_TOKEN not found in .env")

github = Github(GITHUB_TOKEN)

# ==========================================================
# MCP Server
# ==========================================================

mcp = FastMCP(
    name="GitHub MCP Server",
    instructions="""
GitHub MCP Server.

Available Tools

- list_repositories
- get_repository
- create_repository
- delete_repository

Always return JSON.
"""
)

# ==========================================================
# Helper
# ==========================================================

def repo_object(repo_name: str):
    """
    repo_name format:
    owner/repository
    """

    try:
        return github.get_repo(repo_name)

    except GithubException as e:
        raise Exception(str(e))



@mcp.tool()
def list_repositories(username: str) -> List[Dict]:
    """
    List all public repositories of a GitHub user.

    """

    try:

        user = github.get_user(username)

        repos = []

        for repo in user.get_repos():

            repos.append({
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "private": repo.private,
                "language": repo.language,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "watchers": repo.watchers_count,
                "default_branch": repo.default_branch,
                "clone_url": repo.clone_url,
                "html_url": repo.html_url
            })

        return repos

    except GithubException as e:
        return [{"error": str(e)}]



@mcp.tool()
def get_repository(repo: str) -> Dict:
    """
    Get repository information.

    """

    try:

        repository = repo_object(repo)

        return {

            "name": repository.name,
            "full_name": repository.full_name,
            "owner": repository.owner.login,
            "description": repository.description,
            "visibility": repository.visibility,
            "default_branch": repository.default_branch,
            "stars": repository.stargazers_count,
            "forks": repository.forks_count,
            "open_issues": repository.open_issues_count,
            "language": repository.language,
            "size_kb": repository.size,
            "created_at": str(repository.created_at),
            "updated_at": str(repository.updated_at),
            "clone_url": repository.clone_url,
            "ssh_url": repository.ssh_url,
            "homepage": repository.homepage

        }

    except GithubException as e:
        return {"error": str(e)}

# ==========================================================
# Tool
# Create Repository
# ==========================================================

@mcp.tool()
def create_repository(
    name: str,
    description: str = "",
    private: bool = False,
) -> Dict:
    """
    Create a new GitHub repository.

    Parameters
    ----------
    name : Repository name

    description : Repository description

    private : True for private repository


    Example
    -------
    create_repository(
        name="my-demo",
        description="Created from MCP",
        private=False
    )
    """

    try:

        user = github.get_user()

        repo = user.create_repo(
            name=name,
            description=description,
            private=private,
        )

        return {

            "success": True,
            "message": "Repository created successfully.",

            "repository": {

                "name": repo.name,
                "full_name": repo.full_name,
                "private": repo.private,
                "html_url": repo.html_url,
                "clone_url": repo.clone_url,
                "ssh_url": repo.ssh_url,
                "default_branch": repo.default_branch

            }

        }

    except GithubException as e:

        return {

            "success": False,
            "error": str(e)

        }


@mcp.tool()
def delete_repository(
    repo: str,
) -> Dict:
    """
    Delete a GitHub repository.

    Parameters
    ----------
    repo

        owner/repository


    """
    try:

        repository = repo_object(repo)

        repository.delete()

        return {

            "success": True,
            "message": f"{repo} deleted successfully."

        }

    except GithubException as e:

        return {

            "success": False,
            "error": str(e)

        }

@mcp.resource("github://server/info")
def github_info() -> str:

    return json.dumps({

        "server": "GitHub MCP Server",
        "version": "1.0.0",
        "tools": 5

    }, indent=2)


@mcp.prompt()
def github_prompt() -> str:

    return """
You are an AI GitHub Assistant.

You have access to GitHub through MCP.

Use the available tools whenever repository information
is required.

Never guess repository details.

Always use the GitHub tools.
"""


if __name__ == "__main__":

    logger.info("Starting GitHub MCP Server...")

    mcp.run(transport="sse",port=9090)