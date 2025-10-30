from neo4j import AsyncGraphDatabase
from typing import Any, Dict

from config import CONFIG


class GraphDBException(Exception):
    ...


class GraphDB:
    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            CONFIG.GRAPHDB_URL,
            auth=(CONFIG.GRAPHDB_USER, CONFIG.GRAPHDB_PASS)
        )

    async def close(self):
        await self.driver.close()


    async def _execute_query(self, query, parameters: Dict[str, Any]=None):
        try:
            async with self.driver.session() as session:
                result = await session.run(query, parameters)
                return [record.data() for record in await result.list()]

        except Exception as e:
            raise GraphDBException(f"Error while executing query for GraphDB")


    def _normalize_dict(self, dct: Dict[str, Any]) -> Dict[str, Any]:
        new_dct = {}
        has_name = False
        for key, value in dct.items():
            if key.lower() == 'name':
                has_name = True
            new_dct[key.lower()] = value
        if not has_name:
            # Not sure whether to raise the error or to silently suspend the entire memory operation.
            raise GraphDBException(f"Error while normalizing dict: No 'name' key found in Node.")
        return new_dct


    # NOTE: We are storing every node with label `:Entity` for now for the simplicity of the code.
    # Might change it later.
    async def add_node(self, parameters: Dict[str, Any]):
        try:
            # TIP: The node must have a parameter called 'name',
            # remember this while crafting node making prompt.
            parameters = self._normalize_dict(parameters)
            params_for_query = f"{{{", ".join(f"{key}: ${key}" for key, _ in parameters.items())}}}"
            query = f"CREATE (e:Entity {params_for_query}) RETURN e"

            await self._execute_query(query=query, parameters=parameters)

        except Exception as e:
            raise GraphDBException(f"Error while adding new node in GraphDB")


    async def add_relationship(self, node_1_name: str, node_2_name: str, relationship: str):
        try:
            relationship = relationship.upper()
            query = f"""
            MATCH (e1:Entity {{name: $node_1_name}})
            MATCH (e2:Entity {{name: $node_2_name}})
            MERGE (e1)-[:{relationship}]->(e2)
            """
            parameters = {"node_1_name": node_1_name, "node_2_name": node_2_name}
            await self._execute_query(query=query, parameters=parameters)

        except Exception as e:
            raise GraphDBException(f"Error while adding relationship between Node: {node_1_name} and Node: {node_2_name}")


    async def find_node_by_name(self, name: str):
        try:
            name = name.lower()
            query="MATCH (e:Entity {name: $name}) RETURN e"
            parameters={"name": name}
            return await self._execute_query(query=query, parameters=parameters)

        except Exception as e:
            raise GraphDBException(f"Error while finding Node {name}")


    async def find_node_by_relationship(self, name: str, relationship: str):
        try:
            name = name.lower()
            relationship = relationship.upper()
            query = f"""
            MATCH (e:Entity {{name: $name}})-[:{relationship}]->(rel_node:Entity)
            RETURN friend
            """
            parameters = {"name": name}
            return await self._execute_query(query=query, parameters=parameters)

        except Exception as e:
            raise GraphDBException(f"Error while finding nodes for Node {name} with relationship {relationship}")


    async def delete_node(self, name: str):
        try:
            query = "MATCH (e:Entity {name: $name}) DETACH DELETE e"
            parameters = {"name": name.lower()}
            return await self._execute_query(query=query, parameters=parameters)

        except Exception as e:
            raise GraphDBException(f"Error while deleting Node {name}")
