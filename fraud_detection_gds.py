from neo4j import GraphDatabase
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

class FraudDetectionGDS:
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
        self.graph_name = 'fraud-network'
    
    def close(self):
        self.driver.close()
    
    def clear_database(self):
        with self.driver.session() as session:
            # Drop existing graph projection if it exists
            try:
                result = session.run("CALL gds.graph.list() YIELD graphName")
                existing_graphs = [record['graphName'] for record in result]
                if self.graph_name in existing_graphs:
                    session.run(f"CALL gds.graph.drop('{self.graph_name}') YIELD graphName")
            except:
                pass
            # Clear database
            session.run("MATCH (n) DETACH DELETE n")
            print("Database cleared")
    
    def verify_gds(self):
        """Verify GDS is installed"""
        with self.driver.session() as session:
            try:
                result = session.run("CALL gds.version()")
                version = result.single()['gdsVersion']
                print(f"✓ GDS Version: {version}")
                return True
            except Exception as e:
                print(f"✗ GDS not available: {e}")
                return False
    
    def create_fraud_network(self):
        """Create fraud network with GDS-optimized structure"""
        with self.driver.session() as session:
            cluster_size = int(self.N * self.cluster_strength)
            
            # Create fraud cluster
            fraud_cluster = [f"Person_{i}" for i in range(cluster_size)]
            for person in fraud_cluster:
                session.run(
                    "CREATE (p:Person {name: $name, type: 'suspect', risk_score: $risk, cluster: 'fraud'})",
                    name=person, risk=np.random.randint(70, 95)
                )
            
            # Create legitimate cluster
            legit_cluster = [f"Person_{i}" for i in range(cluster_size, self.N)]
            for person in legit_cluster:
                session.run(
                    "CREATE (p:Person {name: $name, type: 'legitimate', risk_score: $risk, cluster: 'legit'})",
                    name=person, risk=np.random.randint(10, 30)
                )
            
            all_persons = fraud_cluster + legit_cluster
            
            # Create transaction edges within clusters
            for cluster in [fraud_cluster, legit_cluster]:
                for i, p1 in enumerate(cluster):
                    for p2 in cluster[i+1:]:
                        if np.random.random() < self.cluster_strength:
                            amount = np.random.randint(1000, 10000) if cluster == fraud_cluster else np.random.randint(100, 2000)
                            session.run("""
                                MATCH (p1:Person {name: $name1}), (p2:Person {name: $name2})
                                CREATE (p1)-[:TRANSACTS_WITH {amount: $amount, frequency: $freq}]->(p2)
                            """, name1=p1, name2=p2, amount=amount, freq=np.random.randint(1, 10))
            
            # Add noise, communication, and trust edges
            max_edges = self.N * (self.N - 1) // 2
            noise_edges = int(max_edges * self.p_noise)
            
            for _ in range(noise_edges):
                p1, p2 = np.random.choice(all_persons, 2, replace=False)
                session.run("""
                    MATCH (p1:Person {name: $name1}), (p2:Person {name: $name2})
                    WHERE NOT (p1)-[:TRANSACTS_WITH]-(p2)
                    CREATE (p1)-[:TRANSACTS_WITH {amount: $amount, frequency: 1, type: 'noise'}]->(p2)
                """, name1=p1, name2=p2, amount=np.random.randint(50, 500))
            
            # Communication and trust edges
            for i, p1 in enumerate(all_persons):
                for p2 in all_persons[i+1:]:
                    if np.random.random() < self.p_comm:
                        session.run("""
                            MATCH (p1:Person {name: $name1}), (p2:Person {name: $name2})
                            CREATE (p1)-[:COMMUNICATES {calls: $calls, messages: $msgs}]->(p2)
                        """, name1=p1, name2=p2, calls=np.random.randint(1, 50), msgs=np.random.randint(10, 200))
                    
                    if np.random.random() < self.p_trust:
                        session.run("""
                            MATCH (p1:Person {name: $name1}), (p2:Person {name: $name2})
                            CREATE (p1)-[:TRUSTS {strength: $strength}]->(p2)
                        """, name1=p1, name2=p2, strength=np.random.uniform(0.3, 1.0))
            
            print(f"Network created: N={self.N}, p_comm={self.p_comm}, p_trust={self.p_trust}, p_noise={self.p_noise}, cluster_strength={self.cluster_strength}")
    
    def create_graph_projection(self):
        """Create GDS graph projection"""
        with self.driver.session() as session:
            # Check if graph exists and drop it
            try:
                result = session.run("CALL gds.graph.list() YIELD graphName")
                existing_graphs = [record['graphName'] for record in result]
                if self.graph_name in existing_graphs:
                    session.run(f"CALL gds.graph.drop('{self.graph_name}') YIELD graphName")
            except:
                pass
            
            # Create new projection
            session.run(f"""
                CALL gds.graph.project(
                    '{self.graph_name}',
                    'Person',
                    {{
                        TRANSACTS_WITH: {{orientation: 'UNDIRECTED'}},
                        TRUSTS: {{orientation: 'UNDIRECTED'}},
                        COMMUNICATES: {{orientation: 'UNDIRECTED'}}
                    }},
                    {{
                        nodeProperties: ['risk_score']
                    }}
                )
            """)
            print(f"✓ Graph projection '{self.graph_name}' created")
    
    def analyze_betweenness_centrality(self):
        """GDS Betweenness Centrality"""
        with self.driver.session() as session:
            result = session.run(f"""
                CALL gds.betweenness.stream('{self.graph_name}')
                YIELD nodeId, score
                RETURN gds.util.asNode(nodeId).name AS name, 
                       gds.util.asNode(nodeId).type AS type,
                       gds.util.asNode(nodeId).risk_score AS risk_score,
                       score
                ORDER BY score DESC
            """)
            
            print("\n=== BETWEENNESS CENTRALITY (GDS) ===")
            print("High centrality = potential money laundering bridges")
            print("-" * 60)
            
            for record in result:
                print(f"{record['name']:10} | Type: {record['type']:10} | "
                      f"Risk: {record['risk_score']:2} | Centrality: {record['score']:.4f}")
    
    def analyze_pagerank(self):
        """GDS PageRank Analysis"""
        with self.driver.session() as session:
            result = session.run(f"""
                CALL gds.pageRank.stream('{self.graph_name}')
                YIELD nodeId, score
                RETURN gds.util.asNode(nodeId).name AS name,
                       gds.util.asNode(nodeId).type AS type,
                       gds.util.asNode(nodeId).risk_score AS risk_score,
                       score
                ORDER BY score DESC
                LIMIT 10
            """)
            
            print("\n=== PAGERANK ANALYSIS (GDS) ===")
            print("High PageRank = influential nodes in network")
            print("-" * 60)
            
            for record in result:
                print(f"{record['name']:10} | Type: {record['type']:10} | "
                      f"Risk: {record['risk_score']:2} | PageRank: {record['score']:.4f}")
    
    def detect_communities(self):
        """GDS Community Detection"""
        with self.driver.session() as session:
            result = session.run(f"""
                CALL gds.louvain.stream('{self.graph_name}')
                YIELD nodeId, communityId
                RETURN gds.util.asNode(nodeId).name AS name,
                       gds.util.asNode(nodeId).type AS type,
                       gds.util.asNode(nodeId).risk_score AS risk_score,
                       communityId
                ORDER BY communityId, risk_score DESC
            """)
            
            print("\n=== COMMUNITY DETECTION (GDS) ===")
            print("Communities may reveal hidden fraud rings")
            print("-" * 60)
            
            current_community = None
            for record in result:
                if record['communityId'] != current_community:
                    current_community = record['communityId']
                    print(f"\n--- Community {current_community} ---")
                
                print(f"{record['name']:10} | Type: {record['type']:10} | Risk: {record['risk_score']:2}")
    
    def analyze_triangles(self):
        """GDS Triangle Count"""
        with self.driver.session() as session:
            result = session.run(f"""
                CALL gds.triangleCount.stream('{self.graph_name}')
                YIELD nodeId, triangleCount
                RETURN gds.util.asNode(nodeId).name AS name,
                       gds.util.asNode(nodeId).type AS type,
                       gds.util.asNode(nodeId).risk_score AS risk_score,
                       triangleCount
                ORDER BY triangleCount DESC
                LIMIT 10
            """)
            
            print("\n=== TRIANGLE COUNT (GDS) ===")
            print("High triangle count = tight-knit groups (potential fraud rings)")
            print("-" * 60)
            
            for record in result:
                print(f"{record['name']:10} | Type: {record['type']:10} | "
                      f"Risk: {record['risk_score']:2} | Triangles: {record['triangleCount']}")

def get_user_input(prompt, default):
    response = input(f"{prompt} (default: {default}): ").strip()
    return response if response else default

def main():
    print("=== GDS-POWERED FRAUD DETECTION ===")
    print(f"Process ID: {os.getpid()}")
    print("To terminate: Press Ctrl+C or run 'kill -9 {0}' in another terminal\n".format(os.getpid()))
    
    # Initialize detector
    detector = FraudDetectionGDS()
    
    # Verify GDS is available
    if not detector.verify_gds():
        print("Please install GDS plugin first. See install_gds_steps.md")
        detector.close()
        return
    
    try:
        print("\nConfigure network parameters (press Enter for defaults):")
        N = int(get_user_input("Number of nodes (N)", 20))
        p_comm = float(get_user_input("Communication edge probability (p_comm)", 0.25))
        p_trust = float(get_user_input("Trust edge probability (p_trust)", 0.15))
        p_noise = float(get_user_input("Noise edge ratio (p_noise)", 0.05))
        cluster_strength = float(get_user_input("Cluster strength 0-1 (cluster_strength)", 0.7))
        
        # Update detector parameters
        detector.N = N
        detector.p_comm = p_comm
        detector.p_trust = p_trust
        detector.p_noise = p_noise
        detector.cluster_strength = cluster_strength
        
        # Create network
        detector.clear_database()
        detector.create_fraud_network()
        detector.create_graph_projection()
        
        # Run GDS analyses
        detector.analyze_betweenness_centrality()
        detector.analyze_pagerank()
        detector.detect_communities()
        detector.analyze_triangles()
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        detector.close()

if __name__ == "__main__":
    main()
