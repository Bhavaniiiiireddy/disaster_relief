import streamlit as st
import networkx as nx
import random
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from itertools import permutations, islice, product
from st_link_analysis import st_link_analysis, NodeStyle, EdgeStyle
import time

# Set page config for a better UX
st.set_page_config(.0

    page_title="Disaster Relief Network Optimizer",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define node types with more detailed information
NODE_TYPES = {
    "Shelter": {"color": "#FF7F3E", "icon": "pin", "capacity": lambda: random.randint(50, 500)},
    "Hospital": {"color": "#2A629A", "icon": "hospital", "capacity": lambda: random.randint(20, 200)},
    "Distribution Center": {"color": "#A3C9A8", "icon": "warehouse", "capacity": lambda: random.randint(100, 1000)},
    "School": {"color": "#F7C873", "icon": "school", "capacity": lambda: random.randint(100, 800)},
    "Community Hall": {"color": "#7B9E87", "icon": "community", "capacity": lambda: random.randint(50, 300)},
    "Rescue Base": {"color": "#B23A48", "icon": "rescue", "capacity": lambda: random.randint(10, 50)},
    "Pharmacy": {"color": "#6D9DC5", "icon": "pharmacy", "capacity": lambda: random.randint(5, 30)},
    "Fire Station": {"color": "#E4572E", "icon": "fire", "capacity": lambda: random.randint(5, 20)},
    "Police Station": {"color": "#29335C", "icon": "police", "capacity": lambda: random.randint(10, 50)},
    "Flooded Area": {"color": "#4B8BBE", "icon": "water", "capacity": lambda: 0},
    "Warehouse": {"color": "#A3C9A8", "icon": "warehouse", "capacity": lambda: random.randint(200, 2000)},
    "Water Point": {"color": "#4B8BBE", "icon": "water", "capacity": lambda: random.randint(1000, 10000)}
}

# Enhanced graph generation with more realism and details
def generate_random_graph(num_nodes=12, edge_prob=0.25, seed=None):
    """Generate a random graph with realistic disaster relief network attributes"""
    if seed is not None:
        random.seed(seed)
        
    # Create base graph structure
    G = nx.gnp_random_graph(num_nodes, edge_prob, seed=seed)
    
    # Assign node types and properties
    node_types_list = list(NODE_TYPES.keys())
    for i, node in enumerate(G.nodes()):
        node_type = node_types_list[i % len(node_types_list)]
        G.nodes[node]['type'] = node_type
        G.nodes[node]['capacity'] = NODE_TYPES[node_type]['capacity']()
        G.nodes[node]['status'] = random.choice(["Operational", "Limited", "Critical"]) 
        G.nodes[node]['resources'] = random.randint(10, 100)
        
    # Assign edge properties with more realism
    for u, v in G.edges():
        # Travel time in minutes (more realistic range)
        G.edges[u, v]['time'] = random.randint(5, 45)
        
        # Cost in resources/fuel
        G.edges[u, v]['cost'] = random.randint(100, 1000)
        
        # Risk factor (1-10)
        G.edges[u, v]['risk'] = random.randint(1, 10)
        
        # Road conditions
        G.edges[u, v]['condition'] = random.choice(["Good", "Fair", "Poor"])
        
        # Road type
        G.edges[u, v]['road_type'] = random.choice(["Highway", "Main Road", "Secondary Road", "Dirt Road"])
        
    return G

def nx_to_elements(G, blocked_edges=None, path=None, highlight_nodes=None, 
                   node_type_filter=None, highlight_edges=None, highlight_nodes_extra=None):
    """Convert NetworkX graph to elements for visualization"""
    nodes = []
    visible_nodes = set()
    
    # Process nodes
    for n, data in G.nodes(data=True):
        if node_type_filter and data['type'] not in node_type_filter:
            continue
            
        # Determine node group for styling
        if highlight_nodes and n in highlight_nodes:
            group = "HIGHLIGHT"
        elif highlight_nodes_extra and n in highlight_nodes_extra:
            group = "EXTRA_HIGHLIGHT"
        else:
            group = data['type']
            
        # Create node data
        node_info = f"{n}: {data['type']}\nCapacity: {data['capacity']}\nStatus: {data['status']}"
        nodes.append({
            "data": {
                "id": str(n),
                "label": group,
                "name": node_info
            }
        })
        visible_nodes.add(n)
    
    # Process edges
    edges = []
    path_edges = set(zip(path, path[1:])) if path else set()
    
    for u, v, data in G.edges(data=True):
        if u not in visible_nodes or v not in visible_nodes:
            continue
            
        eid = f"{u}-{v}"
        
        # Determine edge group for styling
        if highlight_edges and ((u, v) in highlight_edges or (v, u) in highlight_edges):
            group = "EXTRA_HIGHLIGHT"
        elif blocked_edges and ((u, v) in blocked_edges or (v, u) in blocked_edges):
            group = "BLOCKED"
        elif path and ((u, v) in path_edges or (v, u) in path_edges):
            group = "PATH"
        else:
            group = "DEFAULT"
            
        # Create edge caption with complete info
        edge_caption = f"Time: {data['time']}min | Cost: {data['cost']} | Risk: {data['risk']}\n{data['condition']} {data['road_type']}"
        
        edges.append({
            "data": {
                "id": eid,
                "label": group,
                "source": str(u),
                "target": str(v),
                "caption": edge_caption,
            }
        })
    
    return {"nodes": nodes, "edges": edges}

def path_metrics(G, path):
    """Calculate metrics for a given path"""
    if not path or len(path) < 2:
        return 0, 0, 0
        
    total_time = total_cost = total_risk = 0
    for u, v in zip(path[:-1], path[1:]):
        if G.has_edge(u, v):
            edge = G[u][v]
            total_time += edge['time']
            total_cost += edge['cost']
            total_risk += edge['risk']
            
    return total_time, total_cost, total_risk

def all_simple_paths_with_metrics(G, source, target, required_nodes=None, max_paths=1000):
    """Find all simple paths with required nodes and calculate metrics"""
    all_paths = []
    
    if required_nodes:
        # Calculate paths with required waypoints
        for perm in permutations(required_nodes):
            nodes_seq = [source] + list(perm) + [target]
            try:
                segments = []
                for u, v in zip(nodes_seq[:-1], nodes_seq[1:]):
                    segments.append(list(nx.all_simple_paths(G, u, v)))
                    
                for segs in product(*segments):
                    path = segs[0]
                    for seg in segs[1:]:
                        path += seg[1:]  # Avoid duplicate nodes
                    if path not in all_paths:
                        all_paths.append(path)
                        if len(all_paths) >= max_paths:
                            break
            except nx.NetworkXNoPath:
                continue
    else:
        # Calculate direct paths
        try:
            for path in islice(nx.all_simple_paths(G, source, target), max_paths):
                all_paths.append(path)
        except Exception as e:
            st.error(f"Error finding paths: {e}")
            
    return all_paths

def calculate_network_resilience(G):
    """Calculate network resilience metrics"""
    metrics = {}
    
    # Basic connectivity metrics
    metrics["Average degree"] = sum(dict(G.degree()).values()) / G.number_of_nodes()
    
    try:
        # Network robustness metrics
        metrics["Average clustering"] = nx.average_clustering(G)
        metrics["Density"] = nx.density(G)
        
        if nx.is_connected(G):
            metrics["Average shortest path"] = nx.average_shortest_path_length(G, weight='time')
            metrics["Diameter"] = nx.diameter(G, weight='time')
        else:
            largest_cc = max(nx.connected_components(G), key=len)
            subgraph = G.subgraph(largest_cc)
            metrics["Average shortest path (largest component)"] = nx.average_shortest_path_length(subgraph, weight='time')
            metrics["Diameter (largest component)"] = nx.diameter(subgraph, weight='time')
            
        # Centrality metrics for key node identification
        betweenness = nx.betweenness_centrality(G, weight='time')
        metrics["Most critical node"] = max(betweenness.items(), key=lambda x: x[1])[0]
    except:
        # Handle exceptions for small or disconnected networks
        metrics["Note"] = "Some metrics couldn't be calculated (network may be disconnected)"
    
    return metrics

def simulate_cascading_failure(G, initial_failures=1):
    """Simulate a cascading failure in the network"""
    G_sim = G.copy()
    
    # Initial failures
    nodes = list(G_sim.nodes())
    failed_nodes = random.sample(nodes, min(initial_failures, len(nodes)))
    
    # Track failures over time
    failure_progression = [failed_nodes.copy()]
    remaining_nodes = [G_sim.number_of_nodes() - len(failed_nodes)]
    
    # Simulate cascading effect (3 steps)
    for _ in range(3):
        new_failures = []
        
        # Check neighbors of failed nodes for cascading failures
        for node in failed_nodes:
            neighbors = list(G_sim.neighbors(node))
            # 20% chance of neighbor failure
            for neighbor in neighbors:
                if neighbor not in failed_nodes and neighbor not in new_failures:
                    if random.random() < 0.2:  # 20% failure probability
                        new_failures.append(neighbor)
        
        # Add new failures to the total
        failed_nodes.extend(new_failures)
        failure_progression.append(failed_nodes.copy())
        remaining_nodes.append(G_sim.number_of_nodes() - len(failed_nodes))
    
    return failure_progression, remaining_nodes

# Main UI elements
def main():
    # App title with improved styling
    st.markdown("""
    # 🚑 Disaster Relief Network Optimizer
    ### Find optimal routes for emergency response and resource distribution
    """)
    
    # Create tabs for different functionalities
    tab1, tab2, tab3, tab4 = st.tabs(["Route Planning", "Network Analysis", "Failure Simulation", "Export/Import"])
    
    # Sidebar controls
    with st.sidebar:
        st.header("Network Configuration")
        
        # Network generation settings
        num_nodes = st.slider("Number of Points (Nodes)", 10, 30, 15)
        edge_prob = st.slider("Edge Probability", 0.1, 0.9, 0.25, 0.05)
        
        if st.button("Regenerate Network", key="regen_network"):
            st.session_state['graph_seed'] = random.randint(0, 10000)
            
        seed = st.session_state.get('graph_seed', 42)
        
        # Path optimization settings
        st.header("Path Optimization")
        optimization = st.selectbox(
            "Optimize Path For",
            ["Minimum Time", "Minimum Cost", "Minimum Risk", "Custom Weights"]
        )
        
        if optimization == "Custom Weights":
            col1, col2 = st.columns(2)
            time_weight = col1.slider("Time Weight", 0.0, 1.0, 0.33, 0.01, key="time_weight")
            cost_weight = col2.slider("Cost Weight", 0.0, 1.0, 0.33, 0.01, key="cost_weight")
            risk_weight = st.slider("Risk Weight", 0.0, 1.0, 0.34, 0.01, key="risk_weight")
            
            total_weight = time_weight + cost_weight + risk_weight
            if total_weight == 0:
                time_weight, cost_weight, risk_weight = 0.33, 0.33, 0.34
                total_weight = 1
                
            time_weight /= total_weight
            cost_weight /= total_weight
            risk_weight /= total_weight
        
        # Advanced highlighting options
        st.header("Highlighting Options")
        risk_threshold = st.slider("Highlight Edges with Risk >=", 1, 10, 8)
        cost_threshold = st.slider("Highlight Nodes with Cost >", 100, 1000, 800)

    # Initialize or reload graph
    if ('G' not in st.session_state or 
        st.session_state.get('last_num_nodes') != num_nodes or 
        st.session_state.get('last_edge_prob') != edge_prob or 
        st.session_state.get('graph_seed', None) != seed):
        
        with st.spinner("Generating network..."):
            st.session_state['G'] = generate_random_graph(num_nodes, edge_prob, seed=seed)
            st.session_state['last_num_nodes'] = num_nodes
            st.session_state['last_edge_prob'] = edge_prob
            
    G = st.session_state['G']

    # Tab 1: Route Planning
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Route Selection")
            
            # Node type filter
            all_node_types = sorted(set(nx.get_node_attributes(G, 'type').values()))
            node_type_filter = st.multiselect(
                "Show Only Node Types", 
                all_node_types, 
                default=all_node_types
            )
            
            # Node selection
            node_options = [f"{n}: {G.nodes[n]['type']}" for n in G.nodes if G.nodes[n]['type'] in node_type_filter]
            node_map = {f"{n}: {G.nodes[n]['type']}": n for n in G.nodes if G.nodes[n]['type'] in node_type_filter}
            
            source_label = st.selectbox("Select Source Location", node_options, key="source")
            target_label = st.selectbox("Select Target Location", node_options, key="target", index=min(1, len(node_options)-1))
            
            source = node_map[source_label]
            target = node_map[target_label]
            
            # Waypoint selection
            required_nodes_labels = st.multiselect(
                "Select Required (Must-Pass) Locations",
                [lbl for lbl in node_options if lbl != source_label and lbl != target_label]
            )
            required_nodes = [node_map[lbl] for lbl in required_nodes_labels]
        
        with col2:
            st.subheader("Road Conditions")
            
            # Blockage controls
            all_edges = list(G.edges)
            edge_labels = [f"{u}-{v}: {G.edges[u, v]['road_type']}" for u, v in all_edges]
            blocked_edges = []
            
            # Random blockages
            block_random = st.checkbox("Simulate Random Road Blockages")
            if block_random:
                num_block = st.slider("Number of Roads to Block", 1, min(10, len(all_edges)), 2)
                blocked_edges = random.sample(all_edges, min(num_block, len(all_edges)))
            
            # Manual blockages
            block_manual = st.checkbox("Manually Select Road Blockages")
            if block_manual:
                manual_blocked = st.multiselect("Select Roads to Block", edge_labels)
                for label in manual_blocked:
                    u, v = map(int, label.split('-')[0].split(':')[0].strip().split('-'))
                    if (u, v) in all_edges:
                        blocked_edges.append((u, v))
                    elif (v, u) in all_edges:
                        blocked_edges.append((v, u))
                        
            blocked_edges = list(set(blocked_edges))
            
            # Display blockage information
            if blocked_edges:
                st.warning(f"{len(blocked_edges)} roads are currently blocked.")
                
        # Remove blocked edges for path calculation
        G_path = G.copy()
        G_path.remove_edges_from(blocked_edges)
        
        # Highlight settings
        highlight_edges = [(u, v) for u, v, d in G.edges(data=True) if d["risk"] >= risk_threshold]
        highlight_nodes_extra = [n for n in G.nodes if any(G[n][nb]["cost"] > cost_threshold for nb in G.neighbors(n))]
        
        # Path computation
        st.header("Path Results")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            list_all = st.checkbox("List all possible routes")
            max_paths = 100 if list_all else 1
        
        with col2:
            auto_recompute = st.checkbox("Auto-recompute path", value=True)
            if not auto_recompute:
                compute_button = st.button("Compute Best Path")
            else:
                compute_button = True
    
        # Path selection logic
        if compute_button:
            try:
                with st.spinner("Computing optimal path..."):
                    # Set up weight function or key based on optimization choice
                    if optimization == "Minimum Time":
                        weight_attr = "time"
                        best_criterion = "total travel time"
                        sort_key = lambda x: x["total_time"]
                    elif optimization == "Minimum Cost":
                        weight_attr = "cost"
                        best_criterion = "total travel cost"
                        sort_key = lambda x: x["total_cost"]
                    elif optimization == "Minimum Risk":
                        weight_attr = "risk"
                        best_criterion = "total risk"
                        sort_key = lambda x: x["total_risk"]
                    else:  # Custom weights
                        def custom_weight(u, v, d):
                            return (
                                time_weight * d['time'] +
                                cost_weight * d['cost'] +
                                risk_weight * d['risk']
                            )
                        weight_attr = custom_weight
                        best_criterion = f"custom weighted sum (Time: {time_weight:.2f}, Cost: {cost_weight:.2f}, Risk: {risk_weight:.2f})"
                        sort_key = lambda x: (
                            time_weight * x["total_time"] +
                            cost_weight * x["total_cost"] +
                            risk_weight * x["total_risk"]
                        )
    
                    # Best path calculation
                    if required_nodes:
                        best_path = None
                        best_value = float("inf")
                        for perm in permutations(required_nodes):
                            nodes_seq = [source] + list(perm) + [target]
                            try:
                                path = []
                                for u, v in zip(nodes_seq[:-1], nodes_seq[1:]):
                                    segment = nx.shortest_path(G_path, u, v, weight=weight_attr)
                                    if path:
                                        segment = segment[1:]  # Avoid duplicate nodes
                                    path += segment
                                    
                                total_time, total_cost, total_risk = path_metrics(G_path, path)
                                
                                if optimization == "Minimum Time":
                                    value = total_time
                                elif optimization == "Minimum Cost":
                                    value = total_cost
                                elif optimization == "Minimum Risk":
                                    value = total_risk
                                else:
                                    value = (
                                        time_weight * total_time +
                                        cost_weight * total_cost +
                                        risk_weight * total_risk
                                    )
                                    
                                if value < best_value:
                                    best_value = value
                                    best_path = path
                            except nx.NetworkXNoPath:
                                continue
                                
                        if best_path is None:
                            raise nx.NetworkXNoPath
                            
                        best_path_metrics = {
                            "path": best_path,
                            "total_time": sum(G_path[u][v]['time'] for u, v in zip(best_path[:-1], best_path[1:])),
                            "total_cost": sum(G_path[u][v]['cost'] for u, v in zip(best_path[:-1], best_path[1:])),
                            "total_risk": sum(G_path[u][v]['risk'] for u, v in zip(best_path[:-1], best_path[1:])),
                        }
                    else:
                        # Direct path without waypoints
                        best_path = nx.shortest_path(G_path, source, target, weight=weight_attr)
                        best_path_metrics = {
                            "path": best_path,
                            "total_time": sum(G_path[u][v]['time'] for u, v in zip(best_path[:-1], best_path[1:])),
                            "total_cost": sum(G_path[u][v]['cost'] for u, v in zip(best_path[:-1], best_path[1:])),
                            "total_risk": sum(G_path[u][v]['risk'] for u, v in zip(best_path[:-1], best_path[1:])),
                        }
    
                    # Display best path results
                    path_details = (
                        f"**Best Route:** {' → '.join(str(n) for n in best_path_metrics['path'])}\n\n"
                        f"**Travel Time:** {best_path_metrics['total_time']} minutes\n"
                        f"**Resource Cost:** {best_path_metrics['total_cost']} units\n"
                        f"**Risk Level:** {best_path_metrics['total_risk']}\n\n"
                        f"**Why is this the best?**\n"
                        f"This route is selected because it has the lowest {best_criterion} among all possible routes "
                        f"based on your current optimization preference."
                    )
                    
                    st.success(path_details)
                    paths = [best_path_metrics["path"]]
                    
                    # Path list with metrics
                    if list_all:
                        all_paths = all_simple_paths_with_metrics(
                            G_path, source, target, required_nodes, max_paths=max_paths
                        )
                        
                        if all_paths:
                            path_metrics_list = []
                            for path in all_paths:
                                total_time, total_cost, total_risk = path_metrics(G_path, path)
                                path_metrics_list.append({
                                    "path": path,
                                    "total_time": total_time,
                                    "total_cost": total_cost,
                                    "total_risk": total_risk,
                                })
                                
                            # Sort paths by the selected optimization criteria
                            path_metrics_list.sort(key=sort_key)
                            
                            # Create a dataframe for better display
                            paths_df = pd.DataFrame([
                                {
                                    "Route ID": idx+1,
                                    "Path": ' → '.join(str(n) for n in pm['path']),
                                    "Time (min)": pm['total_time'],
                                    "Cost": pm['total_cost'],
                                    "Risk": pm['total_risk'],
                                    "Nodes": len(pm['path']),
                                    "Weighted Score": sort_key(pm)
                                }
                                for idx, pm in enumerate(path_metrics_list)
                            ])
                            
                            # Display all paths in a table
                            st.subheader(f"All Routes ({len(path_metrics_list)} found)")
                            st.dataframe(paths_df, use_container_width=True)
                        else:
                            st.info("No alternative paths found.")
                            
            except nx.NetworkXNoPath:
                st.error("⚠️ No path available between selected points with current blockages and required stops.")
                paths = []
            except Exception as e:
                st.error(f"Error calculating path: {e}")
                paths = []
        else:
            paths = []
        
        # Visualization
        st.header("Network Visualization")
        
        # Node and Edge Styles
        node_styles = [
            NodeStyle("EXTRA_HIGHLIGHT", "#e74c3c", "name", "star"),
            NodeStyle("HIGHLIGHT", "#FFD700", "name", "star")
        ]
        
        # Add node styles for each node type
        for node_type, props in NODE_TYPES.items():
            node_styles.append(
                NodeStyle(node_type, props["color"], "name", props["icon"])
            )
        
        edge_styles = [
            EdgeStyle("EXTRA_HIGHLIGHT", color="#e74c3c", caption="caption"),
            EdgeStyle("BLOCKED", color="#e74c3c", caption="caption"),
            EdgeStyle("PATH", color="#27ae60", caption="caption"),
            EdgeStyle("DEFAULT", color="#888", caption="caption"),
        ]
        
        # Visualize the network with the best path
        if paths:
            elements = nx_to_elements(
                G,
                blocked_edges=blocked_edges,
                path=paths[0],
                highlight_nodes=paths[0],
                node_type_filter=node_type_filter,
                highlight_edges=highlight_edges,
                highlight_nodes_extra=highlight_nodes_extra,
            )
        else:
            elements = nx_to_elements(
                G,
                blocked_edges=blocked_edges,
                path=None,
                node_type_filter=node_type_filter,
                highlight_edges=highlight_edges,
                highlight_nodes_extra=highlight_nodes_extra,
            )
        
        st_link_analysis(elements, layout="cose", node_styles=node_styles, edge_styles=edge_styles)
        
        # Interactive Node/Edge Info Panel
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Node Details")
            info_node_label = st.selectbox("Select Node", node_options, key="info_node")
            node_id = node_map[info_node_label]
            node_data = G.nodes[node_id]
            
            # Display node info in a nicer format
            st.markdown(f"**Node {node_id} ({node_data['type']})**")
            
            # Create a DataFrame for node properties display
            node_props = pd.DataFrame(
                {"Value": [node_data.get(k, "N/A") for k in ["type", "capacity", "status", "resources"]]},
                index=["Type", "Capacity", "Status", "Resources"]
            )
            st.dataframe(node_props, use_container_width=True)
            
            # Calculate node statistics
            node_neighbors = list(G.neighbors(node_id))
            st.write(f"Connected to {len(node_neighbors)} other nodes")
            
            if node_neighbors:
                st.write("Connections:")
                for neighbor in node_neighbors:
                    st.write(f"→ Node {neighbor} ({G.nodes[neighbor]['type']})")
        
        with col2:
            st.subheader("Edge Details")
            info_edge_label = st.selectbox("Select Edge", edge_labels, key="info_edge")
            u, v = map(int, info_edge_label.split(':')[0].strip().split('-'))
            
            if G.has_edge(u, v):
                edge_data = G[u][v]
                st.markdown(f"**Edge {u}-{v}**")
                
                # Create a DataFrame for edge properties display
                edge_props = pd.DataFrame(
                    {"Value": [edge_data.get(k, "N/A") for k in ["time", "cost", "risk", "condition", "road_type"]]},
                    index=["Travel Time (min)", "Resource Cost", "Risk Factor", "Road Condition", "Road Type"]
                )
                st.dataframe(edge_props, use_container_width=True)
                
                # Show the nodes this edge connects
                st.write(f"Connects: Node {u} ({G.nodes[u]['type']}) to Node {v} ({G.nodes[v]['type']})")
                
                if (u, v) in blocked_edges or (v, u) in blocked_edges:
                    st.error("⚠️ This road is currently blocked!")
            else:
                st.write("Edge not present (possibly blocked or filtered out).")
    
    # Tab 2: Network Analysis
    with tab2:
        st.subheader("Network Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Calculate and display network metrics
            metrics = calculate_network_resilience(G)
            
            metrics_df = pd.DataFrame(
                {"Value": [metrics.get(k, "N/A") for k in [
                    "Average degree", "Density", "Average clustering", 
                    "Average shortest path", "Diameter", "Most critical node"
                ]]},
                index=["Average connections per node", "Network density", "Clustering coefficient", 
                       "Average path length (min)", "Maximum path length (min)", "Most critical node"]
            )
            
            st.dataframe(metrics_df, use_container_width=True)
            
            # Node type distribution
            st.subheader("Node Type Distribution")
            node_types = [data['type'] for _, data in G.nodes(data=True)]
            node_counts = pd.Series(node_types).value_counts()
            
            fig, ax = plt.subplots(figsize=(8, 5))
            node_counts.plot(kind='bar', ax=ax)
            ax.set_ylabel('Count')
            ax.set_ylabel('Count')
            ax.set_title('Distribution of Node Types')
            ax.tick_params(axis='x', rotation=45)
            st.pyplot(fig)
            
            # Road condition distribution
            st.subheader("Road Condition Analysis")
            road_conditions = [data['condition'] for _, _, data in G.edges(data=True)]
            road_types = [data['road_type'] for _, _, data in G.edges(data=True)]
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
            pd.Series(road_conditions).value_counts().plot(kind='pie', ax=ax1, autopct='%1.1f%%')
            ax1.set_title('Road Conditions')
            ax1.set_ylabel('')
            
            pd.Series(road_types).value_counts().plot(kind='pie', ax=ax2, autopct='%1.1f%%')
            ax2.set_title('Road Types')
            ax2.set_ylabel('')
            
            st.pyplot(fig)
        
        with col2:
            # Risk heatmap
            st.subheader("Risk Analysis")
            
            # Create risk matrix
            risk_data = np.zeros((G.number_of_nodes(), G.number_of_nodes()))
            
            for u, v, data in G.edges(data=True):
                risk_data[u, v] = data['risk']
                if not G.is_directed():
                    risk_data[v, u] = data['risk']
                    
            fig, ax = plt.subplots(figsize=(8, 6))
            im = ax.imshow(risk_data, cmap='YlOrRd')
            
            # Add colorbar
            cbar = ax.figure.colorbar(im, ax=ax)
            cbar.ax.set_ylabel('Risk Level', rotation=-90, va="bottom")
            
            # Label axes
            ax.set_title("Risk Level Between Nodes")
            ax.set_xlabel("Target Node")
            ax.set_ylabel("Source Node")
            
            # Add grid
            ax.set_xticks(np.arange(G.number_of_nodes()))
            ax.set_yticks(np.arange(G.number_of_nodes()))
            
            # Set tick labels
            node_labels = [f"{n}: {G.nodes[n]['type'][:3]}" for n in range(G.number_of_nodes())]
            ax.set_xticklabels(node_labels)
            ax.set_yticklabels(node_labels)
            
            # Rotate tick labels
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
            
            st.pyplot(fig)
            
            # Network centrality analysis
            st.subheader("Critical Nodes Analysis")
            try:
                # Calculate centrality metrics
                betweenness = nx.betweenness_centrality(G, weight='time')
                closeness = nx.closeness_centrality(G, distance='time')
                
                # Create a DataFrame for centrality metrics
                centrality_df = pd.DataFrame({
                    'Betweenness': betweenness,
                    'Closeness': closeness
                })
                
                # Sort by betweenness centrality (most critical first)
                centrality_df = centrality_df.sort_values('Betweenness', ascending=False)
                
                # Add node type information
                centrality_df['Type'] = [G.nodes[n]['type'] for n in centrality_df.index]
                
                # Display top 5 most critical nodes
                st.write("Most Critical Nodes (Top 5):")
                
                # Format the dataframe for display
                display_df = centrality_df.head(5).copy()
                display_df['Betweenness'] = display_df['Betweenness'].map('{:.3f}'.format)
                display_df['Closeness'] = display_df['Closeness'].map('{:.3f}'.format)
                display_df.index = [f"Node {n}" for n in display_df.index]
                
                st.dataframe(display_df, use_container_width=True)
                
                # Visualize centrality
                fig, ax = plt.subplots(figsize=(8, 5))
                
                # Get the top 10 nodes by betweenness
                top_nodes = centrality_df.head(10).index.tolist()
                
                # Plot betweenness vs closeness for these nodes
                ax.scatter(
                    centrality_df.loc[top_nodes, 'Closeness'],
                    centrality_df.loc[top_nodes, 'Betweenness']
                )
                
                # Add node labels
                for node in top_nodes:
                    ax.annotate(
                        f"{node}",
                        (centrality_df.loc[node, 'Closeness'], centrality_df.loc[node, 'Betweenness']),
                        textcoords="offset points",
                        xytext=(0,10),
                        ha='center'
                    )
                    
                ax.set_title('Network Centrality Analysis')
                ax.set_xlabel('Closeness Centrality')
                ax.set_ylabel('Betweenness Centrality')
                
                st.pyplot(fig)
                
            except Exception as e:
                st.error(f"Error in centrality analysis: {e}")
        
        # Resource distribution analysis
        st.subheader("Resource Distribution Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            # Calculate total resources per node type
            resources_by_type = {}
            capacity_by_type = {}
            
            for n, data in G.nodes(data=True):
                node_type = data['type']
                resources = data['resources']
                capacity = data['capacity']
                
                if node_type not in resources_by_type:
                    resources_by_type[node_type] = 0
                    capacity_by_type[node_type] = 0
                    
                resources_by_type[node_type] += resources
                capacity_by_type[node_type] += capacity
                
            # Create DataFrames
            resources_df = pd.DataFrame({
                'Resources': resources_by_type,
                'Capacity': capacity_by_type
            })
            
            # Calculate resource utilization
            resources_df['Utilization'] = (resources_df['Resources'] / resources_df['Capacity'] * 100).fillna(0)
            
            # Sort by resource amount
            resources_df = resources_df.sort_values('Resources', ascending=False)
            
            # Display as a table
            st.write("Resource Distribution by Type:")
            
            # Format the dataframe
            display_df = resources_df.copy()
            display_df['Utilization'] = display_df['Utilization'].map('{:.1f}%'.format)
            
            st.dataframe(display_df, use_container_width=True)
            
        with col2:
            # Visualize resource distribution
            fig, ax = plt.subplots(figsize=(8, 5))
            
            x = np.arange(len(resources_df.index))
            width = 0.35
            
            # Plot resources and capacity
            ax.bar(x - width/2, resources_df['Resources'], width, label='Resources')
            ax.bar(x + width/2, resources_df['Capacity'], width, label='Capacity')
            
            ax.set_title('Resources vs. Capacity by Node Type')
            ax.set_ylabel('Amount')
            ax.set_xticks(x)
            ax.set_xticklabels(resources_df.index, rotation=45, ha='right')
            ax.legend()
            
            st.pyplot(fig)
            
        # Recommendation section
        st.subheader("Network Optimization Recommendations")
        
        # Identify bottlenecks and critical points
        try:
            # Get top critical nodes
            betweenness = nx.betweenness_centrality(G, weight='time')
            critical_nodes = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:3]
            
            # Get stressed edges
            stressed_edges = [(u, v) for u, v, d in G.edges(data=True) if d['risk'] >= 8]
            
            # Generate recommendations
            recommendations = []
            
            # Critical node recommendations
            for node, score in critical_nodes:
                node_type = G.nodes[node]['type']
                recommendations.append(
                    f"Improve resilience of node {node} ({node_type}) - Critical importance score: {score:.3f}"
                )
                
            # Edge recommendations
            for u, v in stressed_edges[:3]:  # Top 3 stressed edges
                road_type = G[u][v]['road_type']
                risk = G[u][v]['risk']
                recommendations.append(
                    f"Upgrade road between nodes {u} and {v} ({road_type}) - High risk level: {risk}/10"
                )
                
            # Resource balancing
            underutilized = [(t, row['Utilization']) for t, row in resources_df.iterrows() if row['Utilization'] < 30]
            for node_type, util in underutilized[:2]:  # Top 2 underutilized
                recommendations.append(
                    f"Redistribute resources from {node_type} locations (only {util:.1f}% utilized)"
                )
            
            # Output recommendations
            for i, rec in enumerate(recommendations, 1):
                st.write(f"{i}. {rec}")
                
        except Exception as e:
            st.error(f"Error generating recommendations: {e}")
    
    # Tab 3: Failure Simulation
    with tab3:
        st.header("Network Failure Simulation")
        st.write("""
        Simulate how the network would respond to cascading failures.
        This helps evaluate network resilience and identify critical vulnerabilities.
        """)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Simulation parameters
            initial_failures = st.slider(
                "Number of Initial Node Failures", 
                1, min(5, G.number_of_nodes()//2), 
                1
            )
            
            failure_types = st.selectbox(
                "Failure Scenario Type",
                ["Random Nodes", "Highest Capacity Nodes", "Most Connected Nodes", "Most Critical Nodes"]
            )
            
            if st.button("Run Simulation"):
                with st.spinner("Simulating network failures..."):
                    # Select initial failures based on scenario
                    nodes = list(G.nodes())
                    
                    if failure_types == "Random Nodes":
                        failed_nodes = random.sample(nodes, min(initial_failures, len(nodes)))
                    elif failure_types == "Highest Capacity Nodes":
                        # Sort nodes by capacity
                        sorted_nodes = sorted(
                            [(n, G.nodes[n]['capacity']) for n in G.nodes()],
                            key=lambda x: x[1],
                            reverse=True
                        )
                        failed_nodes = [n for n, _ in sorted_nodes[:initial_failures]]
                    elif failure_types == "Most Connected Nodes":
                        # Sort nodes by degree
                        sorted_nodes = sorted(
                            [(n, len(list(G.neighbors(n)))) for n in G.nodes()],
                            key=lambda x: x[1],
                            reverse=True
                        )
                        failed_nodes = [n for n, _ in sorted_nodes[:initial_failures]]
                    else:  # Most Critical Nodes
                        try:
                            # Use betweenness centrality
                            betweenness = nx.betweenness_centrality(G)
                            sorted_nodes = sorted(
                                betweenness.items(),
                                key=lambda x: x[1],
                                reverse=True
                            )
                            failed_nodes = [n for n, _ in sorted_nodes[:initial_failures]]
                        except:
                            # Fallback to random if betweenness fails
                            failed_nodes = random.sample(nodes, min(initial_failures, len(nodes)))
                    
                    # Run the simulation
                    failure_progression, remaining_nodes = simulate_cascading_failure(G, initial_failures)
                    
                    # Store simulation results in session state
                    st.session_state['failure_simulation'] = {
                        'initial_failures': initial_failures,
                        'failure_progression': failure_progression,
                        'remaining_nodes': remaining_nodes,
                        'failed_nodes': failed_nodes
                    }
        
        # Display simulation results
        if 'failure_simulation' in st.session_state:
            sim = st.session_state['failure_simulation']
            
            with col2:
                # Display summary of cascade
                st.subheader("Simulation Results")
                
                # Calculate percentage of network remaining
                initial_nodes = G.number_of_nodes()
                final_nodes = sim['remaining_nodes'][-1]
                percent_remaining = (final_nodes / initial_nodes) * 100
                
                st.markdown(f"""
                * Initial failures: **{sim['initial_failures']} nodes**
                * Cascading effect: **{len(sim['failure_progression'][-1]) - sim['initial_failures']} additional failures**
                * Total failures: **{len(sim['failure_progression'][-1])} nodes**
                * Network remaining: **{final_nodes}/{initial_nodes} nodes ({percent_remaining:.1f}%)**
                """)
                
                # Display the failure progression
                st.write("Failed Node IDs by Step:")
                for i, failures in enumerate(sim['failure_progression']):
                    if i == 0:
                        st.write(f"Step {i} (Initial): {', '.join(str(n) for n in failures)}")
                    else:
                        new_failures = set(failures) - set(sim['failure_progression'][i-1])
                        st.write(f"Step {i} (Cascade): {', '.join(str(n) for n in new_failures)}")
            
            # Visualize the failure cascade
            st.subheader("Cascade Visualization")
            
            # Create a plot of the failure progression
            fig, ax = plt.subplots(figsize=(10, 5))
            
            # Plot the number of remaining nodes over time
            steps = range(len(sim['remaining_nodes']))
            ax.plot(steps, sim['remaining_nodes'], 'o-', color='blue', linewidth=2)
            
            # Add markers for each step
            for i, count in enumerate(sim['remaining_nodes']):
                ax.annotate(
                    f"{count}",
                    (i, count),
                    textcoords="offset points",
                    xytext=(0,10),
                    ha='center'
                )
            
            ax.set_title("Network Degradation During Cascade")
            ax.set_xlabel("Cascade Step")
            ax.set_ylabel("Remaining Functional Nodes")
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Set y-axis to start from 0
            ax.set_ylim(bottom=0)
            
            # Set x-axis ticks to be whole numbers
            ax.set_xticks(steps)
            
            st.pyplot(fig)
            
            # Network visualization with failures
            st.subheader("Failed Network State")
            
            # Create a copy of the graph for visualization
            G_failed = G.copy()
            
            # Highlight the failed nodes
            failed_nodes = sim['failure_progression'][-1]  # Get the final set of failed nodes
            
            elements = nx_to_elements(
                G,
                path=None,
                highlight_nodes=failed_nodes,
                highlight_edges=None
            )
            
            # Define a special style for failed nodes
            node_styles = [
                NodeStyle("HIGHLIGHT", "#e74c3c", "name", "warning")
            ]
            
            # Add node styles for each node type
            for node_type, props in NODE_TYPES.items():
                node_styles.append(
                    NodeStyle(node_type, props["color"], "name", props["icon"])
                )
            
            edge_styles = [
                EdgeStyle("DEFAULT", color="#888", caption="caption"),
            ]
            
            st_link_analysis(elements, layout="cose", node_styles=node_styles, edge_styles=edge_styles)
            
            # Resilience recommendations based on simulation
            st.subheader("Resilience Recommendations")
            
            # Identify nodes that cause the most cascading failures
            cascade_size = len(sim['failure_progression'][-1]) - sim['initial_failures']
            
            if cascade_size > 0:
                st.write(f"The initial failure of {sim['initial_failures']} nodes led to {cascade_size} additional failures.")
                
                # Generate specific recommendations
                st.markdown("""
                **Recommendations to improve network resilience:**
                
                1. **Add redundant connections** to the most critical nodes identified in the simulation
                2. **Increase capacity** at key distribution points to handle rerouting during emergencies
                3. **Create alternative routes** between important service nodes like hospitals and rescue bases
                4. **Stockpile emergency resources** at strategic locations to minimize the impact of node failures
                5. **Deploy mobile response units** that can quickly establish temporary service points
                """)
            else:
                st.success("Good news! The network showed strong resilience with no cascading failures.")
    
    # Tab 4: Export/Import
    with tab4:
        st.header("Export/Import Network")
        st.write("Save your current network or load a previously saved one.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Export Current Network")
            
            if st.button("Generate Export Data"):
                # Convert NetworkX graph to serializable format
                nodes_data = []
                for n, data in G.nodes(data=True):
                    node_data = {"id": n}
                    node_data.update(data)
                    nodes_data.append(node_data)
                
                edges_data = []
                for u, v, data in G.edges(data=True):
                    edge_data = {"source": u, "target": v}
                    edge_data.update(data)
                    edges_data.append(edge_data)
                
                network_data = {
                    "nodes": nodes_data,
                    "edges": edges_data,
                    "metadata": {
                        "num_nodes": G.number_of_nodes(),
                        "num_edges": G.number_of_edges(),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
                
                # Convert to JSON
                json_data = json.dumps(network_data, indent=2)
                
                # Display in a text area for copying
                st.text_area("Network Data (Copy this)", json_data, height=300)
                
                # Provide download link (using a hack)
                st.download_button(
                    "Download Network Data",
                    json_data,
                    file_name="disaster_relief_network.json",
                    mime="application/json"
                )
        
        with col2:
            st.subheader("Import Network")
            
            # File uploader
            uploaded_file = st.file_uploader("Upload Network JSON", type=["json"])
            
            if uploaded_file is not None:
                try:
                    # Load JSON data
                    network_data = json.load(uploaded_file)
                    
                    # Create a new graph
                    G_imported = nx.Graph()
                    
                    # Add nodes
                    for node_data in network_data.get("nodes", []):
                        node_id = node_data.pop("id")
                        G_imported.add_node(node_id, **node_data)
                    
                    # Add edges
                    for edge_data in network_data.get("edges", []):
                        source = edge_data.pop("source")
                        target = edge_data.pop("target")
                        G_imported.add_edge(source, target, **edge_data)
                    
                    # Show import summary
                    st.success(f"Network imported successfully: {G_imported.number_of_nodes()} nodes, {G_imported.number_of_edges()} edges")
                    
                    # Option to load the imported network
                    if st.button("Load This Network"):
                        st.session_state['G'] = G_imported
                        st.info("Imported network loaded. Switch to other tabs to work with it.")
                        
                except Exception as e:
                    st.error(f"Error importing network: {e}")
            
            # Option to load a demo network
            st.subheader("Load Demo Network")
            demo_options = ["Small Town (10 nodes)", "Medium City (20 nodes)", "Large Metro (30 nodes)"]
            demo_choice = st.selectbox("Select Demo Network", demo_options)
            
            if st.button("Load Demo"):
                # Set parameters based on demo choice
                if demo_choice == "Small Town (10 nodes)":
                    nodes = 10
                    edge_prob = 0.4
                    seed = 123
                elif demo_choice == "Medium City (20 nodes)":
                    nodes = 20
                    edge_prob = 0.25
                    seed = 456
                else:  # Large Metro
                    nodes = 30
                    edge_prob = 0.15
                    seed = 789
                
                # Generate and store demo network
                G_demo = generate_random_graph(nodes, edge_prob, seed=seed)
                st.session_state['G'] = G_demo
                st.session_state['last_num_nodes'] = nodes
                st.session_state['last_edge_prob'] = edge_prob
                st.session_state['graph_seed'] = seed
                
                st.success(f"Demo network loaded with {nodes} nodes. Switch to other tabs to work with it.")

if __name__ == "__main__":
    # Initialize session state variables if they don't exist
    if 'graph_seed' not in st.session_state:
        st.session_state['graph_seed'] = 42
        
    main()