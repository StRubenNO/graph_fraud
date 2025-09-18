from neo4j import GraphDatabase
from pyvis.network import Network
import os
from dotenv import load_dotenv

load_dotenv()

def visualize_fraud_graph_interactive(uri=None, user=None, password=None, output_file="fraud_graph.html"):
    # Koble til Neo4j
    uri = uri or os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    user = user or os.getenv('NEO4J_USER', 'neo4j')
    password = password or os.getenv('NEO4J_PASSWORD')
    if password is None:
        password = input("Enter Neo4j password: ")

    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session() as session:
        # Hent alle noder
        nodes = list(session.run("""
            MATCH (p:Person)
            RETURN p.name AS name, p.type AS type, p.risk_score AS risk
        """))
        node_data = {r['name']: r for r in nodes}
        if not node_data:
            print("⚠️ Ingen noder funnet i databasen.")
            return

        # Hent alle relasjoner
        rels = list(session.run("""
            MATCH (p1:Person)-[r]-(p2:Person)
            RETURN p1.name AS n1, p2.name AS n2, type(r) AS relType
        """))

        # Hent betweenness centrality fra GDS
        try:
            centralities = list(session.run("""
                CALL gds.betweenness.stream('fraud-network')
                YIELD nodeId, score
                RETURN gds.util.asNode(nodeId).name AS name, score
            """))
            centrality_scores = {r['name']: r['score'] for r in centralities if r['name'] in node_data}
        except:
            centrality_scores = {name: 0.0 for name in node_data.keys()}

    driver.close()

    # Opprett Pyvis-nettverk
    net = Network(height='800px', width='100%', bgcolor='#ffffff', font_color='black', notebook=False)
    net.force_atlas_2based()
    max_centrality = max(centrality_scores.values()) if centrality_scores else 1

    # Legg til noder
    for name, data in node_data.items():
        risk = data['risk']
        cent = centrality_scores.get(name, 0.0)
        size = 15 + ((risk / 100) + (cent / max_centrality)) * 25
        color = 'red' if data['type'] == 'suspect' else 'blue'
        title = f"<b>{name}</b><br>Type: {data['type']}<br>Risk: {risk}<br>Centrality: {cent:.2f}"
        net.add_node(name, label=name, color=color, size=size, title=title)

    # Legg til kanter
    for r in rels:
        color = 'green' if r['relType'] == 'TRANSACTS_WITH' else ('orange' if r['relType'] == 'TRUSTS' else 'gray')
        dash = True if r['relType'] == 'TRUSTS' else False
        width = 3 if r['relType'] == 'TRANSACTS_WITH' else 2 if r['relType'] == 'TRUSTS' else 1
        net.add_edge(r['n1'], r['n2'], color=color, width=width, dash=dash, title=r['relType'])

    # Lagre graf først
    net.save_graph(output_file)

    # Legg til sidepanel og toggle-knapp
    with open(output_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    toggle_html = """
<div style="position:fixed; top:10px; left:10px; width:250px; background:white; border:1px solid #ccc; padding:10px; z-index:9999; max-height:90%; overflow:auto;">
    <h4>🔍 Analyse & Filter</h4>
    <button onclick="toggleLegit()">Vis/Skjul legitime</button>
    <hr>
    <ul>
        <li>Røde noder = svindlere</li>
        <li>Blå noder = legitime personer</li>
        <li>Node-størrelse = risiko + betweenness centrality</li>
        <li>Grønne kanter = TRANSACTS_WITH</li>
        <li>Oransje stiplet = TRUSTS</li>
        <li>Grå = COMMUNICATES</li>
        <li>Store røde noder med høy centrality = nøkkelpersoner for politi/analytikere</li>
    </ul>
</div>
<script type="text/javascript">
function toggleLegit() {
    network.body.data.nodes.forEach(function(node) {
        if (node.title.includes("Type: legitimate")) {
            node.hidden = !node.hidden;
        }
    });
    network.redraw();
}
</script>
"""

    html_content = html_content.replace('</body>', toggle_html + '</body>')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Skriv ut filnavn INNE i funksjonen
    print(f"✅ Interaktiv graf med sidepanel og toggle lagret som {output_file}")


if __name__ == "__main__":
    visualize_fraud_graph_interactive()
