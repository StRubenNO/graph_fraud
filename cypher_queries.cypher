// FRAUD DETECTION CYPHER QUERIES
// Run these in Neo4j Browser or cypher-shell

// 1. CLEAR DATABASE
MATCH (n) DETACH DELETE n;

// 2. CREATE FRAUD RING CLIQUE (fully connected)
CREATE 
  (alice:Person {name: 'Alice', type: 'suspect', risk_score: 85}),
  (bob:Person {name: 'Bob', type: 'suspect', risk_score: 78}),
  (charlie:Person {name: 'Charlie', type: 'suspect', risk_score: 92}),
  (david:Person {name: 'David', type: 'suspect', risk_score: 81}),
  (eve:Person {name: 'Eve', type: 'suspect', risk_score: 88});

// Create all connections in fraud ring (clique)
MATCH (p1:Person {type: 'suspect'}), (p2:Person {type: 'suspect'})
WHERE p1.name < p2.name
CREATE (p1)-[:TRANSACTS_WITH {amount: 5000, frequency: 15}]->(p2),
       (p2)-[:TRANSACTS_WITH {amount: 4800, frequency: 12}]->(p1);

// 3. CREATE LEGITIMATE BUSINESS CLIQUE
CREATE 
  (frank:Person {name: 'Frank', type: 'legitimate', risk_score: 15}),
  (grace:Person {name: 'Grace', type: 'legitimate', risk_score: 22}),
  (henry:Person {name: 'Henry', type: 'legitimate', risk_score: 18}),
  (iris:Person {name: 'Iris', type: 'legitimate', risk_score: 25});

// Create business connections (clique)
MATCH (p1:Person {type: 'legitimate'}), (p2:Person {type: 'legitimate'})
WHERE p1.name < p2.name
CREATE (p1)-[:TRANSACTS_WITH {amount: 800, frequency: 3}]->(p2),
       (p2)-[:TRANSACTS_WITH {amount: 750, frequency: 2}]->(p1);

// 4. CREATE BRIDGE NODES (high betweenness centrality)
CREATE 
  (jack:Person {name: 'Jack', type: 'bridge', risk_score: 45}),
  (kate:Person {name: 'Kate', type: 'bridge', risk_score: 52}),
  (liam:Person {name: 'Liam', type: 'bridge', risk_score: 48});

// 5. CREATE WEB OF TRUST (bridges between cliques)
MATCH (alice:Person {name: 'Alice'}), (jack:Person {name: 'Jack'})
CREATE (alice)-[:TRUSTS {strength: 0.8}]->(jack),
       (jack)-[:TRUSTS {strength: 0.7}]->(alice);

MATCH (jack:Person {name: 'Jack'}), (frank:Person {name: 'Frank'})
CREATE (jack)-[:TRUSTS {strength: 0.9}]->(frank),
       (frank)-[:TRUSTS {strength: 0.8}]->(jack);

MATCH (eve:Person {name: 'Eve'}), (kate:Person {name: 'Kate'})
CREATE (eve)-[:TRANSACTS_WITH {amount: 5000, frequency: 3}]->(kate),
       (kate)-[:TRUSTS {strength: 0.6}]->(eve);

MATCH (kate:Person {name: 'Kate'}), (grace:Person {name: 'Grace'})
CREATE (kate)-[:TRUSTS {strength: 0.85}]->(grace),
       (grace)-[:TRUSTS {strength: 0.9}]->(kate);

// 6. ADD COMMUNICATION PATTERNS
MATCH (p1:Person), (p2:Person)
WHERE p1.type = 'suspect' AND p2.type = 'suspect' AND p1 <> p2
CREATE (p1)-[:COMMUNICATES {calls: 50, messages: 150}]->(p2);

// 7. ANALYZE CLIQUES - Find highly connected nodes
MATCH (p:Person)-[r:TRANSACTS_WITH]-(connected:Person)
WITH p, collect(DISTINCT connected) AS connections
WHERE size(connections) >= 3
RETURN p.name AS center, p.type AS type, p.risk_score AS risk,
       [conn IN connections | conn.name] AS connected_to,
       size(connections) AS degree
ORDER BY degree DESC, risk DESC;

// 8. BETWEENNESS CENTRALITY (manual calculation)
// Find nodes that appear in many shortest paths
MATCH (start:Person), (end:Person)
WHERE start <> end
MATCH path = shortestPath((start)-[*]-(end))
WITH nodes(path) AS pathNodes
UNWIND pathNodes AS node
WITH node, count(*) AS pathCount
WHERE pathCount > 1
RETURN node.name AS person, node.type AS type, 
       pathCount AS betweenness_indicator
ORDER BY pathCount DESC;

// 9. TRUST NETWORK ANALYSIS
MATCH (p1:Person)-[t:TRUSTS]->(p2:Person)
OPTIONAL MATCH (p1)-[c:COMMUNICATES]->(p2)
RETURN p1.name AS from_person, p1.type AS from_type,
       p2.name AS to_person, p2.type AS to_type,
       t.strength AS trust_strength,
       c.calls AS calls, c.messages AS messages
ORDER BY trust_strength DESC;

// 10. SUSPICIOUS PATTERN DETECTION
MATCH (p:Person)
OPTIONAL MATCH (p)-[t:TRANSACTS_WITH]-(other)
WITH p, count(t) AS transaction_count, 
     avg(t.amount) AS avg_amount,
     sum(t.frequency) AS total_frequency
OPTIONAL MATCH (p)-[tr:TRUSTS]-(trusted)
WITH p, transaction_count, avg_amount, total_frequency,
     count(tr) AS trust_connections,
     avg(tr.strength) AS avg_trust
RETURN p.name AS person, p.type AS type, p.risk_score AS risk,
       transaction_count, avg_amount, total_frequency,
       trust_connections, avg_trust,
       (p.risk_score + transaction_count * 2 + 
        CASE WHEN avg_amount > 5000 THEN 20 ELSE 0 END) AS suspicion_score
ORDER BY suspicion_score DESC;

// 11. FIND BRIDGES BETWEEN COMMUNITIES
MATCH (fraud:Person {type: 'suspect'})-[r]-(bridge:Person)-[r2]-(legit:Person {type: 'legitimate'})
RETURN DISTINCT bridge.name AS bridge_person, 
       bridge.risk_score AS risk,
       count(DISTINCT fraud) AS fraud_connections,
       count(DISTINCT legit) AS legit_connections
ORDER BY risk DESC;

// 12. VISUALIZE NETWORK STRUCTURE
MATCH (n:Person)
OPTIONAL MATCH (n)-[r]-(connected)
RETURN n, r, connected;
