from neo4j import GraphDatabase
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

load_dotenv()

def get_user_input(prompt, default, cast_type):
    response = input(f"{prompt} (default: {default}): ").strip()
    if not response:
        return default
    return cast_type(response)

class CarouselFraudGDS:
    """
    Simulerer karusell-svindel, utfører GDS-analyser og gir interaktiv parameterstyring.
    Visualiserer graf med forklaring og fremhever topp mistenkelige noder.
    Community detection fargelegger klynger.
    """
    def __init__(self, N=40, cluster_strength=0.2, bridge_count=3, 
                 p_noise=0.1, top_n=3, uri=None, user=None, password=None):
        uri = uri or os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        user = user or os.getenv('NEO4J_USER', 'neo4j')
        password = password or os.getenv('NEO4J_PASSWORD')
        if password is None:
            password = input("Enter Neo4j password: ")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.N = N
        self.cluster_strength = cluster_strength
        self.bridge_count = bridge_count
        self.p_noise = p_noise
        self.top_n = top_n
        self.graph_name = 'fraud-carousel-network'

    def close(self):
        self.driver.close()

    def clear_database(self):
        with self.driver.session() as session:
            try:
                result = session.run("CALL gds.graph.list() YIELD graphName")
                existing_graphs = [r['graphName'] for r in result]
                if self.graph_name in existing_graphs:
                    session.run(f"CALL gds.graph.drop('{self.graph_name}') YIELD graphName")
            except:
                pass
            session.run("MATCH (n) DETACH DELETE n")
            print("Database cleared")

    def create_network(self):
        with self.driver.session() as session:
            cluster_size = int(self.N * self.cluster_strength)
            fraud_cluster = [f"Fraud_{i}" for i in range(cluster_size)]
            legit_cluster = [f"Legit_{i}" for i in range(cluster_size, self.N)]

            # Opprett noder
            for p in fraud_cluster:
                session.run("CREATE (p:Person {name:$name,type:'fraud',risk_score:$risk})",
                            name=p, risk=np.random.randint(70,95))
            for p in legit_cluster:
                session.run("CREATE (p:Person {name:$name,type:'legit',risk_score:$risk})",
                            name=p, risk=np.random.randint(10,30))

            # Karuselltransaksjoner
            for i in range(len(fraud_cluster)):
                p1 = fraud_cluster[i]
                p2 = fraud_cluster[(i+1) % len(fraud_cluster)]
                session.run("""
                    MATCH (p1:Person {name:$name1}), (p2:Person {name:$name2})
                    CREATE (p1)-[:TRANSACTS_WITH {amount:$amount,type:'carousel'}]->(p2)
                """, name1=p1, name2=p2, amount=np.random.randint(5000,15000))

            # Bro-noder
            bridges = np.random.choice(fraud_cluster, self.bridge_count, replace=False)
            for b in bridges:
                target = np.random.choice(legit_cluster, 1)[0]
                session.run("""
                    MATCH (p1:Person {name:$name1}), (p2:Person {name:$name2})
                    CREATE (p1)-[:TRANSACTS_WITH {amount:$amount,type:'bridge'}]->(p2)
                """, name1=b, name2=target, amount=np.random.randint(1000,5000))

            # Legg til støykanter
            all_nodes = fraud_cluster + legit_cluster
            max_edges = self.N * (self.N - 1) // 2
            noise_edges = int(max_edges * self.p_noise)
            for _ in range(noise_edges):
                n1, n2 = np.random.choice(all_nodes, 2, replace=False)
                session.run("""
                    MATCH (p1:Person {name:$name1}), (p2:Person {name:$name2})
                    WHERE NOT (p1)-[:TRANSACTS_WITH]-(p2)
                    CREATE (p1)-[:TRANSACTS_WITH {amount:$amount,type:'noise'}]->(p2)
                """, name1=n1, name2=n2, amount=np.random.randint(50,500))

            # Øk risk_score for karusell og bridge
            session.run("""
                MATCH (p:Person)
                WHERE EXISTS((p)-[:TRANSACTS_WITH {type:'carousel'}]->()) 
                   OR EXISTS((p)-[:TRANSACTS_WITH {type:'bridge'}]->())
                SET p.risk_score = p.risk_score + 20
            """)
            print(f"Network created: Fraud={len(fraud_cluster)}, Legit={len(legit_cluster)}, Noise edges={noise_edges}")

    def create_gds_projection(self):
        with self.driver.session() as session:
            try:
                result = session.run("CALL gds.graph.list() YIELD graphName")
                existing_graphs = [r['graphName'] for r in result]
                if self.graph_name in existing_graphs:
                    session.run(f"CALL gds.graph.drop('{self.graph_name}') YIELD graphName")
            except:
                pass
            session.run(f"""
                CALL gds.graph.project(
                    '{self.graph_name}',
                    'Person',
                    {{
                        TRANSACTS_WITH: {{orientation:'UNDIRECTED'}}
                    }},
                    {{
                        nodeProperties:['risk_score']
                    }}
                )
            """)
            print(f"✓ GDS graph projection '{self.graph_name}' created")

    def get_top_nodes(self):
        top_nodes = set()
        with self.driver.session() as session:
            betweenness = session.run(f"""
                CALL gds.betweenness.stream('{self.graph_name}')
                YIELD nodeId, score
                RETURN gds.util.asNode(nodeId).name AS name, score
                ORDER BY score DESC
                LIMIT {self.top_n}
            """)
            for r in betweenness:
                top_nodes.add(r['name'])

            pagerank = session.run(f"""
                CALL gds.pageRank.stream('{self.graph_name}')
                YIELD nodeId, score
                RETURN gds.util.asNode(nodeId).name AS name, score
                ORDER BY score DESC
                LIMIT {self.top_n}
            """)
            for r in pagerank:
                top_nodes.add(r['name'])
        return top_nodes

    def get_communities(self):
        """Returner dictionary {node: communityId}"""
        communities = {}
        with self.driver.session() as session:
            result = session.run(f"""
                CALL gds.louvain.stream('{self.graph_name}')
                YIELD nodeId, communityId
                RETURN gds.util.asNode(nodeId).name AS name, communityId
            """)
            for r in result:
                communities[r['name']] = r['communityId']
        return communities

    def visualize_network(self):
        with self.driver.session() as session:
            nodes_res = session.run("MATCH (p:Person) RETURN p.name AS name, p.type AS type, p.risk_score AS risk")
            edges_res = session.run("""
                MATCH (p1:Person)-[r:TRANSACTS_WITH]->(p2:Person)
                RETURN p1.name AS source, p2.name AS target, r.type AS type
            """)

            G = nx.DiGraph()
            for r in nodes_res:
                G.add_node(r['name'], type=r['type'], risk=r['risk'])
            for r in edges_res:
                G.add_edge(r['source'], r['target'], type=r['type'])

            top_nodes = self.get_top_nodes()
            communities = self.get_communities()

            pos = nx.spring_layout(G, seed=42)
            node_colors = []
            community_colors = list(plt.cm.tab20.colors)
            for n, d in G.nodes(data=True):
                if n in top_nodes:
                    node_colors.append('yellow')  # fremhevede noder
                elif d['type']=='fraud':
                    node_colors.append('red')
                else:
                    c_id = communities.get(n, 0)
                    node_colors.append(community_colors[c_id % len(community_colors)])

            edge_colors = []
            for u,v,d in G.edges(data=True):
                if d['type']=='carousel':
                    edge_colors.append('orange')
                elif d['type']=='bridge':
                    edge_colors.append('blue')
                elif d['type']=='noise':
                    edge_colors.append('gray')
                else:
                    edge_colors.append('black')

            node_sizes = [50 + 5*d['risk'] for n,d in G.nodes(data=True)]

            plt.figure(figsize=(14,12))
            nx.draw(G, pos, with_labels=True, node_color=node_colors, edge_color=edge_colors,
                    node_size=node_sizes, arrowsize=15, font_size=10)

            import matplotlib.patches as mpatches
            patches = [
                mpatches.Patch(color='red', label='Fraud Node'),
                mpatches.Patch(color='yellow', label='Top Suspicious Node'),
                mpatches.Patch(color='orange', label='Carousel Transaction'),
                mpatches.Patch(color='blue', label='Bridge Transaction'),
                mpatches.Patch(color='gray', label='Noise Transaction')
            ]
            plt.legend(handles=patches, loc='upper left')

            plt.title(
                "Fraud Carousel Simulation with Communities\n"
                "Node size ~ risk_score\n"
                "Yellow = top suspicious node\n"
                "Red=Fraud, Community colors indicate clusters\n"
                "Orange=Carousel, Blue=Bridge, Gray=Noise\n"
                "Key actors and clusters highlighted"
            )
            plt.show()


if __name__ == "__main__":
    print("=== Carousel Fraud Simulator ===")
    N = get_user_input("Total number of nodes (N)", 40, int)
    cluster_strength = get_user_input("Fraud cluster strength (0-1)", 0.2, float)
    bridge_count = get_user_input("Number of bridge nodes", 3, int)
    p_noise = get_user_input("Noise edge ratio (0-1)", 0.1, float)
    top_n = get_user_input("Number of top suspicious nodes to highlight", 3, int)

    sim = CarouselFraudGDS(N=N, cluster_strength=cluster_strength, bridge_count=bridge_count, 
                           p_noise=p_noise, top_n=top_n)
    sim.clear_database()
    sim.create_network()
    sim.create_gds_projection()
    sim.visualize_network()
    sim.close()
