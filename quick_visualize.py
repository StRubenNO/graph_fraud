import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

def create_demo_graph():
    """Lag demo graf uten Neo4j"""
    G = nx.Graph()
    
    # Fraud ring (clique)
    fraud_ring = ["Alice", "Bob", "Charlie", "David", "Eve"]
    for person in fraud_ring:
        G.add_node(person, type='suspect', risk_score=np.random.randint(70, 95))
    
    # Legitimate business ring
    business_ring = ["Frank", "Grace", "Henry", "Iris"]
    for person in business_ring:
        G.add_node(person, type='legitimate', risk_score=np.random.randint(10, 30))
    
    # Bridge nodes
    bridges = ["Jack", "Kate", "Liam"]
    for person in bridges:
        G.add_node(person, type='bridge', risk_score=np.random.randint(40, 60))
    
    # Create clique connections (fraud ring)
    for i, person1 in enumerate(fraud_ring):
        for person2 in fraud_ring[i+1:]:
            G.add_edge(person1, person2, relationship='TRANSACTS_WITH', weight=np.random.randint(1000, 10000))
    
    # Create clique connections (business ring)
    for i, person1 in enumerate(business_ring):
        for person2 in business_ring[i+1:]:
            G.add_edge(person1, person2, relationship='TRANSACTS_WITH', weight=np.random.randint(100, 2000))
    
    # Bridge connections
    G.add_edge("Alice", "Jack", relationship='TRUSTS', weight=800)
    G.add_edge("Jack", "Frank", relationship='TRUSTS', weight=900)
    G.add_edge("Eve", "Kate", relationship='TRANSACTS_WITH', weight=5000)
    G.add_edge("Kate", "Grace", relationship='TRUSTS', weight=850)
    G.add_edge("Charlie", "Liam", relationship='TRUSTS', weight=600)
    G.add_edge("Liam", "Henry", relationship='TRUSTS', weight=750)
    
    return G

def visualize_fraud_network():
    """Visualiser fraud network med farger og størrelser"""
    G = create_demo_graph()
    
    plt.figure(figsize=(16, 12))
    
    # Posisjonering med bedre layout
    pos = nx.spring_layout(G, k=4, iterations=100, seed=42)
    
    # Fargekoding basert på type
    color_map = {
        'suspect': '#FF3333',     # Rød for svindlere
        'legitimate': '#33AA33',  # Grønn for legitime
        'bridge': '#FF8800'       # Orange for broer
    }
    
    node_colors = [color_map.get(G.nodes[node]['type'], '#CCCCCC') for node in G.nodes()]
    
    # Størrelse basert på risikoscore og connections
    node_sizes = []
    for node in G.nodes():
        risk = G.nodes[node]['risk_score']
        connections = len(list(G.neighbors(node)))
        size = (risk * 15) + (connections * 100)  # Større forskjeller
        node_sizes.append(size)
    
    # Tegn noder med outline
    nx.draw_networkx_nodes(G, pos, 
                          node_color=node_colors,
                          node_size=node_sizes,
                          alpha=0.9,
                          edgecolors='black',
                          linewidths=3)
    
    # Tegn kanter med forskjellige farger og tykkelser
    trust_edges = [(u, v) for u, v, d in G.edges(data=True) if d['relationship'] == 'TRUSTS']
    transaction_edges = [(u, v) for u, v, d in G.edges(data=True) if d['relationship'] == 'TRANSACTS_WITH']
    
    # Trust relationships (blå, tykke)
    nx.draw_networkx_edges(G, pos,
                          edgelist=trust_edges,
                          edge_color='#0066CC',
                          width=4,
                          alpha=0.8,
                          style='dashed')
    
    # Transaction relationships (grå, tynne)
    nx.draw_networkx_edges(G, pos,
                          edgelist=transaction_edges,
                          edge_color='#666666',
                          width=2,
                          alpha=0.6)
    
    # Labels med bedre styling
    nx.draw_networkx_labels(G, pos, 
                           font_size=11, 
                           font_weight='bold',
                           font_color='white',
                           font_family='Arial')
    
    # Legg til risikoscore som tekst
    risk_labels = {}
    for node in G.nodes():
        x, y = pos[node]
        risk = G.nodes[node]['risk_score']
        plt.text(x, y-0.15, f'Risk: {risk}', 
                horizontalalignment='center',
                fontsize=9, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
    
    # Legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF3333', 
                  markersize=15, label='Suspects (Høy risiko: 70-95)', markeredgecolor='black', markeredgewidth=2),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#33AA33', 
                  markersize=15, label='Legitimate (Lav risiko: 10-30)', markeredgecolor='black', markeredgewidth=2),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF8800', 
                  markersize=15, label='Bridges (Medium risiko: 40-60)', markeredgecolor='black', markeredgewidth=2),
        plt.Line2D([0], [0], color='#0066CC', linewidth=4, linestyle='--', label='Trust Relations'),
        plt.Line2D([0], [0], color='#666666', linewidth=2, label='Transactions')
    ]
    
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0.02, 0.98), fontsize=12)
    
    # Tittel og info
    plt.title('Fraud Detection Network Visualization\n' + 
             'Node størrelse = Risk Score + Antall forbindelser\n' +
             'Farger = Aktørtype | Linjer = Relasjonstype', 
             fontsize=16, fontweight='bold', pad=30)
    
    # Legg til statistikk
    stats_text = f"""Network Statistics:
• Total nodes: {G.number_of_nodes()}
• Total edges: {G.number_of_edges()}
• Suspects: {len([n for n in G.nodes() if G.nodes[n]['type'] == 'suspect'])}
• Legitimate: {len([n for n in G.nodes() if G.nodes[n]['type'] == 'legitimate'])}
• Bridges: {len([n for n in G.nodes() if G.nodes[n]['type'] == 'bridge'])}"""
    
    plt.text(0.02, 0.02, stats_text, transform=plt.gca().transAxes, 
             fontsize=10, verticalalignment='bottom',
             bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgray', alpha=0.8))
    
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def print_analysis():
    """Print detaljert analyse"""
    G = create_demo_graph()
    
    print("=== FRAUD NETWORK ANALYSIS ===\n")
    
    # Betweenness centrality
    centrality = nx.betweenness_centrality(G)
    print("🌉 BETWEENNESS CENTRALITY (Bro-noder):")
    for node, score in sorted(centrality.items(), key=lambda x: x[1], reverse=True):
        node_type = G.nodes[node]['type']
        risk = G.nodes[node]['risk_score']
        print(f"  {node:10} | Type: {node_type:10} | Risk: {risk:2} | Centrality: {score:.3f}")
    
    print("\n📊 NODE CONNECTIONS & RISK:")
    for node in sorted(G.nodes(), key=lambda x: G.nodes[x]['risk_score'], reverse=True):
        connections = len(list(G.neighbors(node)))
        node_type = G.nodes[node]['type']
        risk = G.nodes[node]['risk_score']
        print(f"  {node:10} | Type: {node_type:10} | Risk: {risk:2} | Connections: {connections}")
    
    print("\n🔗 TRUST RELATIONSHIPS:")
    trust_edges = [(u, v, d) for u, v, d in G.edges(data=True) if d['relationship'] == 'TRUSTS']
    for edge in trust_edges:
        weight = edge[2]['weight'] / 1000  # Convert to trust strength
        print(f"  {edge[0]} ↔ {edge[1]} | Trust: {weight:.2f}")

if __name__ == "__main__":
    print_analysis()
    print("\nGenerating visualization...")
    visualize_fraud_network()
