from neo4j import AsyncDriver
from typing import Any, Dict, List, Optional


class GraphDBException(Exception):
    ...


class GraphDBUtils:
    def __init__(self, driver: AsyncDriver):
        self.driver = driver


    async def _execute_query(self, query, parameters: Optional[Dict[str, Any]]=None):
        try:
            async with self.driver.session() as session:
                result = await session.run(query, parameters)
                return [record.data() async for record in result]

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
            raise GraphDBException(f"Error while normalizing dict: No 'name' key found in Node.")
        return new_dct


    async def add_node(self, parameters: Dict[str, Any], entity: Optional[str] = "Entity"):
        try:
            # NOTE: Each node must have `Entity` type. And the entity parameters should have name,
            # embedding vector and other metadata like timestamp, etc. (Keeping this here for future reference.)
            # parameters = {"name" : "name-of-node", "vector_embedding": <embedding>, "timestamp": <timestamp>}

            parameters = self._normalize_dict(parameters)
            node_name = parameters.pop("name")
            entity_safe = entity.replace("`", "")
            # params_for_query = f"{{{", ".join(f"{key}: ${key}" for key, _ in parameters.items())}}}"
            # query = f"CREATE (e:{entity} {params_for_query}) RETURN e"

            query = f"""
            MERGE (e:`{entity}` {{name: $name}})
            SET e += $props
            RETURN e
            """

            await self._execute_query(query=query, parameters={"name": node_name, "props": parameters})

        except Exception as e:
            raise GraphDBException(f"Error while adding new node in GraphDB")


    async def add_relationship(
        self,
        node_1_name: str,
        node_2_name: str,
        relationship: str,
        node_1_entity: Optional[str] = "Entity",
        node_2_entity: Optional[str] = "Entity"
    ):
        try:
            relationship_safe = relationship.upper().replace("`", "")
            node_1_entity_safe = node_1_entity.replace("`", "")
            node_2_entity_safe = node_2_entity.replace("`", "")

            query = f"""
            MATCH (e1:`{node_1_entity_safe}` {{name: $node_1_name}})
            MATCH (e2:`{node_2_entity_safe}` {{name: $node_2_name}})
            MERGE (e1)-[:`{relationship_safe}`]->(e2)
            """
            parameters = {"node_1_name": node_1_name, "node_2_name": node_2_name}
            await self._execute_query(query=query, parameters=parameters)

        except Exception as e:
            raise GraphDBException(f"Error while adding relationship between Node: {node_1_name} and Node: {node_2_name}")


    # async def find_node_by_name(self, name: str):
    #     try:
    #         name = name.lower()
    #         query="MATCH (e:Entity {name: $name}) RETURN e"
    #         parameters={"name": name}
    #         return await self._execute_query(query=query, parameters=parameters)

    #     except Exception as e:
    #         raise GraphDBException(f"Error while finding Node {name}")


    async def find_node_by_relationship(self, name: str, relationship: str):
        try:
            name = name.lower()
            relationship = relationship.upper()
            query = f"""
            MATCH (e:Entity {{name: $name}})-[:{relationship}]->(rel_node:Entity)
            RETURN rel_node
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


    async def get_1_hop_neighborhood(self, name: str):
        try:
            query = """
            MATCH (center)
            WHERE toLower(center.name) = toLower($name)
            MATCH (center)-[r]-(neighbor)
            RETURN center.name, type(r) as relationship, neighbor.name, labels(neighbor) as types
            """
            parameters = {"name": name}
            return await self._execute_query(query, parameters)

        except Exception as e:
            raise GraphDBException(f"Error retrieving neighborhood for {name}")


    async def delete_relationship(self, node_1_name: str, node_2_name: str, relationship: str):
        try:
            relationship = relationship.upper().replace(" ", "_")
            query = f"""
            MATCH (e1 {{name: $n1}})-[r:{relationship}]->(e2 {{name: $n2}})
            DELETE r
            """
            await self._execute_query(query, {"n1": node_1_name, "n2": node_2_name})
        except Exception as e:
            raise GraphDBException(f"Error deleting relationship: {e}")


    async def search_similar_nodes(self, name: str, limit: int = 5) -> List[Dict]:
        try:
            query = """
            MATCH (n)
            WHERE toLower(n.name) CONTAINS toLower($name)
            RETURN n.name as name, labels(n) as labels
            LIMIT $limit
            """
            return await self._execute_query(query, {"name": name, "limit": limit})
        except Exception as e:
            return []


    async def get_2_hop_neighborhood(self, name: str, limit: int = 15):
        try:
            query = """
            MATCH (center) WHERE toLower(center.name) = toLower($name)
            MATCH (center)-[r1]-(n1)
            OPTIONAL MATCH (n1)-[r2]-(n2)
            WHERE n2 <> center 
            RETURN 
                center.name as source, 
                type(r1) as rel1, 
                n1.name as intermediate, 
                type(r2) as rel2, 
                n2.name as target
            LIMIT $limit
            """
            return await self._execute_query(query, {"name": name, "limit": limit})
        except Exception as e:
            return []


    async def find_node_by_name(self, name: str):
        try:
            query = "MATCH (e {name: $name}) RETURN e"
            return await self._execute_query(query, {"name": name})
        except Exception as e:
            return []
