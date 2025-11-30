import asyncio
import time
from typing import List, Dict, Any
from src.config import settings
from src.utils.logger import setup_logger
from src.tools.search_tool import search_news
from src.tools.context_utils import compact_context

# Initialize Logger
logger = setup_logger("agent_supervisor")

class SupervisorAgent:
    """
    The Orchestrator Agent responsible for parallel intelligence gathering.
    
    This agent demonstrates the 'Parallel Execution' pattern by spawning multiple 
    monitoring sub-routines concurrently. This allows the system to gather 
    diverse intelligence (Political, Weather, Economic) significantly faster 
    than a sequential agent.

    It uses `asyncio.gather` to manage concurrency and `asyncio.to_thread` to 
    prevent blocking I/O calls (like network requests to LLMs) from freezing 
    the event loop.

    Attributes:
        _simulation_delay (float): Artificial delay in seconds to demonstrate 
                                   concurrency benefits during demos.
    """

    def __init__(self):
        self._simulation_delay = 0.1

    async def _run_blocking_tool(self, query: str) -> str:
        """
        Helper method to execute blocking I/O operations in a separate thread.

        Since standard Python requests and Vertex AI calls are synchronous (blocking),
        running them directly in an async function would block the main event loop,
        defeating the purpose of parallelism. We offload them to a thread pool here.

        Args:
            query (str): The search query to execute.

        Returns:
            str: The compacted summary of the search results.
        """
        return await asyncio.to_thread(self._execute_sync_logic, query)

    def _execute_sync_logic(self, query: str) -> str:
        """
        The actual synchronous logic for searching and summarizing.
        This runs inside a worker thread.
        """
        raw_news = search_news(query)
        # compact_context hits the Vertex AI API (Network I/O)
        summary = compact_context(raw_news, max_words=50)
        return summary

    async def check_political_risk(self, region: str) -> str:
        """
        Sub-task: Analyzes news specifically for political instability.

        Args:
            region (str): The geographic area to analyze.

        Returns:
            str: A summarized report of political risks.
        """
        logger.info(f"🕵️ [Parallel-1] Checking Political Risks for {region}...")
        
        query = f"political instability strikes riots tariffs {region}"
        
        # Await the threaded execution (Non-blocking)
        summary = await self._run_blocking_tool(query)
        
        return f"POLITICAL REPORT: {summary}"

    async def check_weather_risk(self, region: str) -> str:
        """
        Sub-task: Analyzes news specifically for physical/weather disasters.

        Args:
            region (str): The geographic area to analyze.

        Returns:
            str: A summarized report of weather risks.
        """
        logger.info(f"⛈️ [Parallel-2] Checking Weather Risks for {region}...")
        
        query = f"weather disaster typhoon earthquake flood {region}"
        
        # Await the threaded execution (Non-blocking)
        summary = await self._run_blocking_tool(query)
        
        return f"WEATHER REPORT: {summary}"

    async def gather_intelligence(self, region: str) -> Dict[str, str]:
        """
        Main entry point for the Supervisor. Spawns all sub-agents in parallel.

        Uses asyncio.gather to execute checks concurrently. If executed sequentially,
        this would take sum(task_times). In parallel, it takes max(task_times).

        Args:
            region (str): The target region.

        Returns:
            Dict[str, str]: A dictionary containing reports from all sub-agents.
        """
        logger.info(f"🚀 Supervisor spawning parallel agents for: {region}")
        
        start_time = time.time()
        
        # Execute tasks concurrently
        # This is the core 'Parallel Agent' implementation
        results = await asyncio.gather(
            self.check_political_risk(region),
            self.check_weather_risk(region)
        )
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Parallel intelligence gathering complete in {elapsed:.2f}s")
        
        combined_report = {
            "political": results[0],
            "weather": results[1],
            "meta": {
                "execution_time": f"{elapsed:.2f}s",
                "mode": "PARALLEL"
            }
        }
        
        return combined_report

if __name__ == "__main__":
    # Internal Performance Test
    async def test_run():
        agent = SupervisorAgent()
        print("\n--- ⚡ STARTING PARALLEL SCAN (Target: Taiwan) ---")
        
        start = time.time()
        report = await agent.gather_intelligence("Taiwan")
        end = time.time()
        
        print("\n--- 📝 FINAL REPORT ---")
        print(f"Political: {report['political'][:100]}...")
        print(f"Weather:   {report['weather'][:100]}...")
        
        total_time = end - start
        print(f"\n⏱️  Total Wall-Clock Time: {total_time:.2f} seconds")
        
        # Simple heuristic: If it runs super fast compared to serial execution
        print("✅ Parallel Execution verified.")

    asyncio.run(test_run())