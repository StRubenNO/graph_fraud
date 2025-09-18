# Installere GDS Plugin - Steg for steg

## Neo4j Desktop (Anbefalt)
1. Åpne Neo4j Desktop
2. Velg din database
3. Klikk på "Plugins" tab (til høyre)
4. Finn "Graph Data Science Library"
5. Klikk "Install"
6. Klikk "Start" for å starte databasen på nytt

## Verifiser installasjon
Åpne Neo4j Browser (http://localhost:7474) og kjør:
```cypher
CALL gds.version()
```

Hvis det fungerer, vil du se versjonsnummer.

## Hvis du bruker Docker
```bash
docker run \
    --name neo4j-gds \
    -p7474:7474 -p7687:7687 \
    -d \
    --env NEO4J_AUTH=neo4j/yourpassword \
    --env NEO4J_PLUGINS='["graph-data-science"]' \
    neo4j:latest
```
