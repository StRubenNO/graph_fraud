from neo4j import GraphDatabase
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FraudDetection:
    def __init__(self, uri=None, user=None, password=None, 
                 N=15, p_comm=0.3, p_trust=0.2, p_noise=0.1, cluster_strength=0.7):
        uri = uri or os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        user = user or os.getenv('NEO4J_USER', 'neo4j')
        password = password or os.getenv('NEO4J_PASSWORD')
        
        if password is None:
            password = input("Enter Neo4j password: ")
            
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.N = N
        self.p_comm = p_comm
        self.p_trust = p_trust
        self.p_noise = p_noise
        self.cluster_strength = cluster_strength
    
    def close(self):
        self.driver.close()
    
    def clear_database(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("Database cleared")
    
    def create_fraud_network(self):
        """Create a fraud detection network with configurable parameters"""
        with self.driver.session() as session:
            # Create N persons with cluster assignment
            cluster_size = int(self.N * self.cluster_strength)
            
            # Fraud cluster
            fraud_cluster = [f"Person_{i}" for i in range(cluster_size)]
            for person in fraud_cluster:
                session.run(
                    "CREATE (p:Person {name: $name, type: 'suspect', risk_score: $risk, cluster: 'fraud'})",
                    name=person, risk=np.random.randint(70, 95)
                )
            
            # Legitimate cluster
            legit_cluster = [f"Person_{i}" for i in range(cluster_size, self.N)]
            for person in legit_cluster:
                session.run(
                    "CREATE (p:Person {name: $name, type: 'legitimate', risk_score: $risk, cluster: 'legit'})",
                    name=person, risk=np.random.randint(10, 30)
                )
            
            all_persons = fraud_cluster + legit_cluster
            
            # Create transaction edges within clusters (high probability)
            for cluster in [fraud_cluster, legit_cluster]:
                for i, p1 in enumerate(cluster):
                    for p2 in cluster[i+1:]:
                        if np.random.random() < self.cluster_strength:
                            amount = np.random.randint(1000, 10000) if cluster == fraud_cluster else np.random.randint(100, 2000)
                            session.run("""
                                MATCH (p1:Person {name: $name1}), (p2:Person {name: $name2})
                                CREATE (p1)-[:TRANSACTS_WITH {amount: $amount, frequency: $freq}]->(p2)
                            """, name1=p1, name2=p2, amount=amount, freq=np.random.randint(1, 10))
            
            # Add noise edges (random connections)
            max_edges = self.N * (self.N - 1) // 2
            noise_edges = int(max_edges * self.p_noise)
            
            for _ in range(noise_edges):
                p1, p2 = np.random.choice(all_persons, 2, replace=False)
                session.run("""
                    MATCH (p1:Person {name: $name1}), (p2:Person {name: $name2})
                    WHERE NOT (p1)-[:TRANSACTS_WITH]-(p2)
                    CREATE (p1)-[:TRANSACTS_WITH {amount: $amount, frequency: 1, type: 'noise'}]->(p2)
                """, name1=p1, name2=p2, amount=np.random.randint(50, 500))
            
            # Add communication edges
            for i, p1 in enumerate(all_persons):
                for p2 in all_persons[i+1:]:
                    if np.random.random() < self.p_comm:
                        session.run("""
                            MATCH (p1:Person {name: $name1}), (p2:Person {name: $name2})
                            CREATE (p1)-[:COMMUNICATES {calls: $calls, messages: $msgs}]->(p2)
                        """, name1=p1, name2=p2, calls=np.random.randint(1, 50), msgs=np.random.randint(10, 200))
            
            # Add trust edges
            for i, p1 in enumerate(all_persons):
                for p2 in all_persons[i+1:]:
                    if np.random.random() < self.p_trust:
                        session.run("""
                            MATCH (p1:Person {name: $name1}), (p2:Person {name: $name2})
                            CREATE (p1)-[:TRUSTS {strength: $strength}]->(p2)
                        """, name1=p1, name2=p2, strength=np.random.uniform(0.3, 1.0))
            
            print(f"Network created: N={self.N}, p_comm={self.p_comm}, p_trust={self.p_trust}, p_noise={self.p_noise}, cluster_strength={self.cluster_strength}")
    
    def analyze_betweenness_centrality_fast(self):
        """Fast betweenness centrality approximation"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Person)
                OPTIONAL MATCH (p)-[r]-(other:Person)
                WITH p, count(r) AS total_degree,
                     count(CASE WHEN p.cluster <> other.cluster THEN 1 END) AS cross_cluster_degree
                RETURN p.name AS name, p.type AS type, p.risk_score AS risk_score,
                       total_degree, cross_cluster_degree,
                       (total_degree + cross_cluster_degree * 3) AS centrality_score
                ORDER BY centrality_score DESC, risk_score DESC
            """)
            
            print("\n=== BETWEENNESS CENTRALITY ANALYSIS (FAST) ===")
            print("High centrality = potential money laundering bridges")
            print("-" * 60)
            
            for record in result:
                print(f"{record['name']:10} | Type: {record['type']:10} | "
                      f"Risk: {record['risk_score']:2} | Centrality: {record['centrality_score']} "
                      f"(Cross-cluster: {record['cross_cluster_degree']})")

    def analyze_betweenness_centrality_exact(self):
        """Calculate exact betweenness centrality with progress tracking"""
        with self.driver.session() as session:
            print("\n=== BETWEENNESS CENTRALITY ANALYSIS (EXACT) ===")
            print("Calculating true betweenness centrality...")
            
            # Get all persons first
            persons_result = session.run("MATCH (p:Person) RETURN p.name AS name ORDER BY name")
            persons = [record['name'] for record in persons_result]
            total_persons = len(persons)
            
            print(f"Processing {total_persons} nodes...")
            
            centrality_scores = {}
            
            # Calculate for each person
            for i, person in enumerate(persons):
                print(f"Progress: {i+1}/{total_persons} ({person}) - {((i+1)/total_persons*100):.1f}%", end='\r')
                
                # Count shortest paths through this person
                result = session.run("""
                    MATCH (start:Person), (end:Person)
                    WHERE start.name <> end.name AND start.name <> $person AND end.name <> $person
                    MATCH path = shortestPath((start)-[*]-(end))
                    WHERE $person IN [n IN nodes(path) | n.name]
                    RETURN count(*) AS paths_through
                """, person=person)
                
                paths_through = result.single()['paths_through']
                centrality_scores[person] = paths_through
            
            print()  # New line after progress
            
            # Get person details and sort by centrality
            result = session.run("""
                MATCH (p:Person)
                RETURN p.name AS name, p.type AS type, p.risk_score AS risk_score
            """)
            
            person_details = {record['name']: record for record in result}
            
            # Sort by centrality score
            sorted_persons = sorted(centrality_scores.items(), key=lambda x: x[1], reverse=True)
            
            print("High centrality = potential money laundering bridges")
            print("-" * 60)
            
            for name, centrality in sorted_persons:
                if name in person_details:
                    details = person_details[name]
                    print(f"{name:10} | Type: {details['type']:10} | "
                          f"Risk: {details['risk_score']:2} | Centrality: {centrality}")
                    
                    if centrality == 0:  # Stop showing nodes with 0 centrality
                        break
    
    def analyze_betweenness_centrality_gds(self):
        """Calculate betweenness centrality using Neo4j GDS (requires plugin)"""
        with self.driver.session() as session:
            try:
                # Check if GDS is available
                session.run("CALL gds.version()")
                
                # Drop existing projection if it exists
                try:
                    session.run("CALL gds.graph.drop('fraud-network', false)")
                except:
                    pass
                
                # Create graph projection
                session.run("""
                    CALL gds.graph.project(
                        'fraud-network',
                        'Person',
                        {
                            TRANSACTS_WITH: {orientation: 'UNDIRECTED'},
                            TRUSTS: {orientation: 'UNDIRECTED'},
                            COMMUNICATES: {orientation: 'UNDIRECTED'}
                        }
                    )
                """)
                
                # Calculate betweenness centrality
                result = session.run("""
                    CALL gds.betweenness.stream('fraud-network')
                    YIELD nodeId, score
                    RETURN gds.util.asNode(nodeId).name AS name, 
                           gds.util.asNode(nodeId).type AS type,
                           gds.util.asNode(nodeId).risk_score AS risk_score,
                           score
                    ORDER BY score DESC
                """)
                
                print("\n=== BETWEENNESS CENTRALITY ANALYSIS (GDS) ===")
                print("High betweenness = potential money laundering bridges")
                print("-" * 60)
                
                for record in result:
                    print(f"{record['name']:10} | Type: {record['type']:10} | "
                          f"Risk: {record['risk_score']:2} | Centrality: {record['score']:.4f}")
                
                # Clean up
                session.run("CALL gds.graph.drop('fraud-network')")
                
            except Exception as e:
                print(f"GDS not available: {e}")
                print("Using fallback centrality calculation...")
                self.analyze_betweenness_centrality()
    
    def detect_cliques(self):
        """Find and analyze cliques in the network"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Person)-[r:TRANSACTS_WITH]-(connected:Person)
                WITH p, collect(DISTINCT connected) AS connections
                WHERE size(connections) >= 3
                RETURN p.name AS center, p.type AS type, p.risk_score AS risk,
                       [conn IN connections | conn.name] AS connected_to,
                       size(connections) AS degree
                ORDER BY degree DESC, risk DESC
            """)
            
            print("\n=== CLIQUE DETECTION ===")
            print("Highly connected nodes (potential fraud rings)")
            print("-" * 50)
            
            for record in result:
                print(f"{record['center']:10} | Type: {record['type']:10} | "
                      f"Risk: {record['risk']:2} | Connections: {record['degree']}")
                print(f"           Connected to: {', '.join(record['connected_to'][:5])}")
                print()
    
    def analyze_trust_patterns(self):
        """Analyze trust relationships and communication patterns"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p1:Person)-[t:TRUSTS]->(p2:Person)
                OPTIONAL MATCH (p1)-[c:COMMUNICATES]->(p2)
                RETURN p1.name AS from_person, p1.type AS from_type,
                       p2.name AS to_person, p2.type AS to_type,
                       t.strength AS trust_strength,
                       c.calls AS calls, c.messages AS messages
                ORDER BY trust_strength DESC
            """)
            
            print("\n=== TRUST & COMMUNICATION ANALYSIS ===")
            print("Web of trust relationships")
            print("-" * 60)
            
            for record in result:
                calls = record['calls'] or 0
                msgs = record['messages'] or 0
                print(f"{record['from_person']} -> {record['to_person']} | "
                      f"Trust: {record['trust_strength']:.2f} | "
                      f"Calls: {calls} | Messages: {msgs}")
    
    def suspicious_pattern_detection(self):
        """Detect suspicious patterns combining multiple factors"""
        with self.driver.session() as session:
            result = session.run("""
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
                ORDER BY suspicion_score DESC
            """)
            
            print("\n=== SUSPICIOUS PATTERN DETECTION ===")
            print("Combined risk analysis")
            print("-" * 70)
            
            for record in result:
                avg_amt = record['avg_amount'] or 0
                avg_trust = record['avg_trust'] or 0
                print(f"{record['person']:10} | Risk: {record['risk']:2} | "
                      f"Transactions: {record['transaction_count']:2} | "
                      f"Avg Amount: {avg_amt:6.0f} | "
                      f"Trust Score: {avg_trust:.2f} | "
                      f"SUSPICION: {record['suspicion_score']:.0f}")

def get_user_input(prompt, default):
    """Get user input with default value"""
    response = input(f"{prompt} (default: {default}): ").strip()
    return response if response else default

from neo4j import GraphDatabase
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    print("=== CONFIGURABLE FRAUD DETECTION WITH NEO4J ===")
    print(f"Process ID: {os.getpid()}")
    print("To terminate: Press Ctrl+C or run 'kill -9 {0}' in another terminal\n".format(os.getpid()))
    
    print("Configure network parameters (press Enter for defaults):")
    
    # Get parameters from user with defaults
    N = int(get_user_input("Number of nodes (N)", 20))
    p_comm = float(get_user_input("Communication edge probability (p_comm)", 0.25))
    p_trust = float(get_user_input("Trust edge probability (p_trust)", 0.15))
    p_noise = float(get_user_input("Noise edge ratio (p_noise)", 0.05))
    cluster_strength = float(get_user_input("Cluster strength 0-1 (cluster_strength)", 0.7))
    
    # Choose centrality method
    print("\nCentrality calculation method:")
    print("1. Fast approximation (recommended for N > 15)")
    print("2. Exact calculation (slow for large networks)")
    centrality_choice = get_user_input("Choose method (1 or 2)", "1")
    use_exact_centrality = centrality_choice == "2"
    
    if use_exact_centrality:
        print(f"\nWARNING: Exact centrality for {N} nodes may take time.")
        print(f"To cancel: Ctrl+C or 'kill -9 {os.getpid()}' from another terminal")
    
    # Initialize fraud detection system with user parameters
    fraud_detector = FraudDetection(
        N=N,
        p_comm=p_comm,
        p_trust=p_trust,
        p_noise=p_noise,
        cluster_strength=cluster_strength
    )
    
    try:
        # Clear and create network
        fraud_detector.clear_database()
        fraud_detector.create_fraud_network()
        
        # Run analyses
        fraud_detector.detect_cliques()
        
        if use_exact_centrality:
            fraud_detector.analyze_betweenness_centrality_exact()
        else:
            fraud_detector.analyze_betweenness_centrality_fast()
            
        fraud_detector.analyze_trust_patterns()
        fraud_detector.suspicious_pattern_detection()
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Neo4j is running and you've set the correct password")
    
    finally:
        fraud_detector.close()

if __name__ == "__main__":
    main()
