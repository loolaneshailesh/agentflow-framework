"""Web search tool for AgentFlow agents."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from agentflow.tools.base import BaseTool

logger = logging.getLogger(__name__)


@dataclass
class WebSearchTool(BaseTool):
    """Tool for performing web searches via DuckDuckGo or custom search API."""

    name: str = "web_search"
    description: str = "Search the web for current information on any topic."
    max_results: int = 5
    search_backend: str = "duckduckgo"
    api_key: Optional[str] = None

    async def arun(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Perform an async web search."""
        query = inputs.get("query") or inputs.get("input") or str(inputs)
        logger.info(f"WebSearchTool searching: {query!r}")
        try:
            if self.search_backend == "duckduckgo":
                return await self._duckduckgo_search(query)
            elif self.search_backend == "tavily":
                return await self._tavily_search(query)
            elif self.search_backend == "serper":
                return await self._serper_search(query)
            else:
                raise ValueError(f"Unknown search backend: {self.search_backend}")
        except Exception as e:
            logger.error(f"WebSearchTool error: {e}")
            return {"error": str(e), "query": query, "results": []}

    async def _duckduckgo_search(self, query: str) -> Dict[str, Any]:
        """Search using DuckDuckGo (no API key required)."""
        try:
            from duckduckgo_search import DDGS
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=self.max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    })
            return {"query": query, "results": results, "backend": "duckduckgo"}
        except ImportError:
            return {
                "query": query,
                "results": [],
                "error": "Install duckduckgo-search: pip install duckduckgo-search",
            }

    async def _tavily_search(self, query: str) -> Dict[str, Any]:
        """Search using Tavily API."""
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=self.api_key)
            response = client.search(query=query, max_results=self.max_results)
            results = [
                {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")}
                for r in response.get("results", [])
            ]
            return {"query": query, "results": results, "backend": "tavily"}
        except ImportError:
            return {"query": query, "results": [], "error": "Install tavily-python"}

    async def _serper_search(self, query: str) -> Dict[str, Any]:
        """Search using Serper API."""
        import aiohttp
        headers = {"X-API-KEY": self.api_key or "", "Content-Type": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://google.serper.dev/search",
                json={"q": query, "num": self.max_results},
                headers=headers,
            ) as resp:
                data = await resp.json()
        results = [
            {"title": r.get("title", ""), "url": r.get("link", ""), "snippet": r.get("snippet", "")}
            for r in data.get("organic", [])
        ]
        return {"query": query, "results": results, "backend": "serper"}

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous wrapper."""
        import asyncio
        return asyncio.run(self.arun(inputs))
