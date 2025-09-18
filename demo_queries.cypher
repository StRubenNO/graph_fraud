// DEMO: Fraud Detection with Cliques and Centrality

// 1. Clear database
MATCH (n) DETACH DELETE n;

// 2. Create Fraud Ring Clique (fully connected)
CREATE 
  (alice:Person {name: 'Alice', type: 'suspect', risk: 85}),
  (bob:Person {name: 'Bob', type: 'suspect', risk: 78}),
  (charlie:Person {name: 'Charlie', type: 'suspect', risk: 92});

// Connect fraud ring (clique)
MATCH (p1:Person {type: 'suspect'}), (p2:Person {type: 'suspect'})
WHERE p1.name < p2.name
CREATE (p1)-[:TRANSACTS {amount: 5000}]->(p2),
       (p2)-[:TRANSACTS {amount: 4800}]->(p1);

// 3. Create Business Clique
CREATE 
  (frank:Person {name: 'Frank', type: 'business', risk: 15}),
  (grace:Person {name: 'Grace', type: 'business', risk: 22});

MATCH (frank:Person {name: 'Frank'}), (grace:Person {name: 'Grace'})
CREATE (frank)-[:TRANSACTS {amount: 800}]->(grace),
       (grace)-[:TRANSACTS {amount: 750}]->(frank);

// 4. Create Bridge (high betweenness centrality)
CREATE (jack:Person {name: 'Jack', type: 'bridge', risk: 45});

// Connect bridge between cliques
MATCH (alice:Person {name: 'Alice'}), (jack:Person {name: 'Jack'})
CREATE (alice)-[:TRUSTS {strength: 0.8}]->(jack);

MATCH (jack:Person {name: 'Jack'}), (frank:Person {name: 'Frank'})
CREATE (jack)-[:TRUSTS {strength: 0.9}]->(frank);

// 5. ANALYZE: Show all nodes and relationships
MATCH (n)-[r]-(m) 
RETURN n.name AS person1, type(r) AS relationship, m.name AS person2, n.type AS type1;

// 6. CLIQUE ANALYSIS: Find highly connected nodes
MATCH (p:Person)-[r]-(connected:Person)
WITH p, count(r) AS connections
RETURN p.name AS person, p.type AS type, p.risk AS risk_score, connections
ORDER BY connections DESC, risk_score DESC;

// 7. CENTRALITY: Find bridge nodes
MATCH (start:Person), (end:Person)
WHERE start.type = 'suspect' AND end.type = 'business'
MATCH path = shortestPath((start)-[*]-(end))
WITH nodes(path) AS pathNodes
UNWIND pathNodes[1..-1] AS bridgeNode
WHERE bridgeNode.type = 'bridge'
RETURN bridgeNode.name AS bridge, count(*) AS centrality_score
ORDER BY centrality_score DESC;
