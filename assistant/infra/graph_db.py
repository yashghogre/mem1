from neo4j import AsyncGraphDatabase

from config import CONFIG

class _GraphDB:
    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            CONFIG.GRAPHDB_URL,
            auth=(CONFIG.GRAPHDB_USER, CONFIG.GRAPHDB_PASS)
        )


    async def close(self):
        await self.driver.close()


    def get_client(self):
        if not self.driver:
            raise ValueError("GraphDB client not initiated. Please initiate the client first.")
        return self.driver


GraphDB = _GraphDB()
