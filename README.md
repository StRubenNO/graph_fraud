# Graph_Fraud - Neo4j Fraud Detection Demo

En demonstrasjon av Neo4j og Cypher for svindeldeteksjon med fokus på:
- **Cliques** (fullt forbundne subgrafer)
- **Web of Trust** (tillitsnettverk)
- **Betweenness Centrality** (sentralitetsanalyse)
- **Kommunikasjonsgrafer**

## Konsepter som demonstreres

### 1. Cliques (Fullt forbundne grafer)
- **Svindelring**: 5 personer (Alice, Bob, Charlie, David, Eve) som alle er forbundet med hverandre
- **Legitim forretningsring**: 4 personer (Frank, Grace, Henry, Iris) med normale forretningstransaksjoner

### 2. Web of Trust
- Tillitsrelasjoner mellom personer på tvers av gruppene
- Broer som forbinder svindelringen med legitime aktører

### 3. Betweenness Centrality
- Identifiserer "bro-noder" som ligger mellom forskjellige grupper
- Høy betweenness centrality = potensielle hvitvaskingskanaler

### 4. Kommunikasjonsgrafer
- Telefonsamtaler og meldinger mellom aktører
- Korrelasjon mellom kommunikasjon og transaksjoner

## Installasjon

```bash
cd ~/Documents/AWS/Graph_Fraud
pip install -r requirements.txt
```

## Bruk

### Metode 1: Python Script
```bash
python fraud_detection.py
```

### Metode 2: Cypher Queries (manuelt)
1. Åpne Neo4j Browser: http://localhost:7474
2. Kopier queries fra `cypher_queries.cypher`
3. Kjør en og en query

### Metode 3: Cypher Shell
```bash
cypher-shell < cypher_queries.cypher
```

## Nøkkelanalyser

### Clique Detection
Finner grupper hvor alle medlemmer er forbundet med hverandre:
```cypher
MATCH (p:Person)-[r:TRANSACTS_WITH]-(connected:Person)
WITH p, collect(DISTINCT connected) AS connections
WHERE size(connections) >= 3
RETURN p.name, size(connections) AS degree
ORDER BY degree DESC
```

### Betweenness Centrality
Identifiserer noder som ligger på mange korteste stier:
```cypher
MATCH (start:Person), (end:Person)
WHERE start <> end
MATCH path = shortestPath((start)-[*]-(end))
WITH nodes(path) AS pathNodes
UNWIND pathNodes AS node
RETURN node.name, count(*) AS centrality
ORDER BY centrality DESC
```

### Trust Analysis
Analyserer tillitsnettverk og kommunikasjonsmønstre:
```cypher
MATCH (p1:Person)-[t:TRUSTS]->(p2:Person)
RETURN p1.name, p2.name, t.strength
ORDER BY t.strength DESC
```

## Nettverksstruktur

```
Svindelring (Clique):     Broer:           Legitim ring (Clique):
Alice ←→ Bob              Jack             Frank ←→ Grace
  ↕   ×   ↕                ↕                 ↕   ×   ↕
Charlie ←→ David          Kate             Henry ←→ Iris
  ↕       ↕                ↕
  ←→ Eve ←→               Liam
```

## Resultater

Scriptet vil vise:
1. **Clique Detection**: Hvem som er mest forbundet
2. **Betweenness Centrality**: Hvem som fungerer som broer
3. **Trust Analysis**: Tillitsrelasjoner på tvers av grupper
4. **Suspicious Patterns**: Kombinert risikoanalyse

## Tekniske detaljer

- **Neo4j versjon**: 2025.08.0
- **Cypher Shell**: 2025.08.0
- **Python driver**: neo4j 5.28.2
- **Graph algoritmer**: Betweenness centrality, clique detection
# graph_fraud
