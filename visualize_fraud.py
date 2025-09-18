import matplotlib.pyplot as plt
import networkx as nx
from neo4j import GraphDatabase
import numpy as np
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FraudVisualizer:
    def __init__(self, uri=None, user=None, password=None):
        uri = uri or os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')
        user = user or os.getenv('NEO4J_USER', 'neo4j')
        password = password or os.getenv('NEO4J_PASSWORD')
        
        if password is None:
            password = input("Enter Neo4j password: ")
            
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def get_graph_data(self):
        """Hent data fra Neo4j"""
        with self.driver.session() as session:
            # Hent noder
            nodes_result = session.run("""
                MATCH (p:Person)
                RETURN p.name AS name, p.type AS type, p.risk_score AS risk
            """)
            
            # Hent relasjoner
            edges_result = session.run("""
                MATCH (p1:Person)-[r]->(p2:Person)
                RETURN p1.name AS from_node, p2.name AS to_node, 
                       type(r) AS relationship_type,
                       CASE 
                         WHEN r.amount IS NOT NULL THEN r.amount
                         WHEN r.strength IS NOT NULL THEN r.strength * 1000
                         ELSE 1
                       END AS weight
            """)
            
            nodes = list(nodes_result)
            edges = list(edges_result)
            
            return nodes, edges
    
    def create_networkx_graph(self, nodes, edges):
        """Lag NetworkX graf"""
        G = nx.Graph()
        
        # Legg til noder med attributter
        for node in nodes:
            G.add_node(node['name'], 
                      type=node['type'], 
                      risk=node['risk'])
        
        # Legg til kanter
        for edge in edges:
            G.add_edge(edge['from_node'], edge['to_node'],
                      relationship=edge['relationship_type'],
                      weight=edge['weight'])
        
        return G
    
    def visualize_fraud_network(self):
        """Visualiser fraud network med farger og størrelser"""
        nodes, edges = self.get_graph_data()
        G = self.create_networkx_graph(nodes, edges)
        
        plt.figure(figsize=(15, 10))
        
        # Posisjonering
        pos = nx.spring_layout(G, k=3, iterations=50, seed=42)
        
        # Fargekoding basert på type
        color_map = {
            'suspect': '#FF4444',    # Rød for svindlere
            'legitimate': '#44FF44', # Grønn for legitime
            'bridge': '#FFAA00'      # Orange for broer
        }
        
        node_colors = [color_map.get(G.nodes[node]['type'], '#CCCCCC') for node in G.nodes()]
        
        # Størrelse basert på risikoscore og connections
        node_sizes = []
        for node in G.nodes():
            risk = G.nodes[node]['risk']
            connections = len(list(G.neighbors(node)))
            size = (risk * 10) + (connections * 50)  # Kombinert størrelse
            node_sizes.append(size)
        
        # Tegn noder
        nx.draw_networkx_nodes(G, pos, 
                              node_color=node_colors,
                              node_size=node_sizes,
                              alpha=0.8,
                              edgecolors='black',
                              linewidths=2)
        
        # Tegn kanter med forskjellige farger
        edge_colors = []
        edge_widths = []
        for edge in G.edges(data=True):
            if edge[2]['relationship'] == 'TRUSTS':
                edge_colors.append('#0066CC')  # Blå for trust
                edge_widths.append(3)
            else:
                edge_colors.append('#666666')  # Grå for transaksjoner
                edge_widths.append(1)
        
        nx.draw_networkx_edges(G, pos,
                              edge_color=edge_colors,
                              width=edge_widths,
                              alpha=0.6)
        
        # Legg til labels
        nx.draw_networkx_labels(G, pos, 
                               font_size=12, 
                               font_weight='bold',
                               font_color='white')
        
        # Legg til legend
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF4444', 
                      markersize=15, label='Suspects (Svindlere)'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#44FF44', 
                      markersize=15, label='Legitimate (Legitime)'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#FFAA00', 
                      markersize=15, label='Bridges (Broer)'),
            plt.Line2D([0], [0], color='#0066CC', linewidth=3, label='Trust Relations'),
            plt.Line2D([0], [0], color='#666666', linewidth=1, label='Transactions')
        ]
        
        plt.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
        
        plt.title('Fraud Detection Network\nNode size = Risk Score + Connections\nColors = Actor Type', 
                 fontsize=16, fontweight='bold', pad=20)
        
        plt.axis('off')
        plt.tight_layout()
        plt.show()
    
    def print_analysis(self):
        """Print detaljert analyse"""
        nodes, edges = self.get_graph_data()
        G = self.create_networkx_graph(nodes, edges)
        
        print("=== FRAUD NETWORK ANALYSIS ===\n")
        
        # Betweenness centrality
        centrality = nx.betweenness_centrality(G)
        print("🌉 BETWEENNESS CENTRALITY (Bro-noder):")
        for node, score in sorted(centrality.items(), key=lambda x: x[1], reverse=True):
            node_type = G.nodes[node]['type']
            risk = G.nodes[node]['risk']
            print(f"  {node:10} | Type: {node_type:8} | Risk: {risk:2} | Centrality: {score:.3f}")
        
        print("\n📊 NODE CONNECTIONS:")
        for node in G.nodes():
            connections = len(list(G.neighbors(node)))
            node_type = G.nodes[node]['type']
            risk = G.nodes[node]['risk']
            print(f"  {node:10} | Type: {node_type:8} | Risk: {risk:2} | Connections: {connections}")
        
        print("\n🔗 TRUST RELATIONSHIPS:")
        for edge in G.edges(data=True):
            if edge[2]['relationship'] == 'TRUSTS':
                weight = edge[2]['weight'] / 1000  # Convert back to trust strength
                print(f"  {edge[0]} → {edge[1]} | Trust: {weight:.2f}")

def main():
    visualizer = FraudVisualizer()
    
    try:
        print("Generating fraud network visualization...")
        visualizer.print_analysis()
        visualizer.visualize_fraud_network()
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        visualizer.close()

if __name__ == "__main__":
    main()
