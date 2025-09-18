# Installere Neo4j Graph Data Science (GDS)

## Metode 1: Neo4j Desktop (enklest)
1. Åpne Neo4j Desktop
2. Gå til din database
3. Klikk på "Plugins" tab
4. Finn "Graph Data Science Library" 
5. Klikk "Install"
6. Restart databasen

## Metode 2: Manual download
1. Gå til https://neo4j.com/graph-data-science-software/
2. Last ned GDS plugin jar fil
3. Plasser den i `plugins/` mappen i Neo4j installasjonen
4. Restart Neo4j

## Metode 3: Docker
```bash
docker run \
    --name neo4j-gds \
    -p7474:7474 -p7687:7687 \
    -d \
    -v $HOME/neo4j/data:/data \
    -v $HOME/neo4j/logs:/logs \
    -v $HOME/neo4j/import:/var/lib/neo4j/import \
    -v $HOME/neo4j/plugins:/plugins \
    --env NEO4J_AUTH=neo4j/password \
    --env NEO4J_PLUGINS='["graph-data-science"]' \
    neo4j:latest
```

## Verifiser installasjon
Kjør i Neo4j Browser:
```cypher
CALL gds.version()
```
