

# Disaster Relief Network Optimizer

A Streamlit-based application for modeling, analyzing, and optimizing disaster relief networks. The system supports efficient route planning, evaluates network resilience, and simulates cascading failures to aid decision-making in emergency scenarios.

---

## Features

### Route Planning

* Compute optimal paths between locations
* Optimization criteria:

  * Minimum time
  * Minimum cost
  * Minimum risk
  * Custom weighted combination
* Supports required intermediate nodes (waypoints)
* Handles road blockages (manual and random)
* Displays routes with detailed metrics

### Network Analysis

* Calculates key metrics such as:

  * Network density
  * Clustering coefficient
  * Average shortest path
  * Diameter
* Identifies critical nodes using centrality measures
* Provides risk and resource distribution analysis
* Generates optimization recommendations

### Failure Simulation

* Simulates cascading node failures
* Supports multiple failure scenarios:

  * Random nodes
  * High-capacity nodes
  * Highly connected nodes
  * Critical nodes
* Visualizes failure progression and network degradation

### Visualization and Data Handling

* Interactive graph visualization
* Node and edge-level insights
* Export network as JSON
* Import saved or demo networks

---

## Technologies Used

* Python
* Streamlit
* NetworkX
* Pandas and NumPy
* Matplotlib
* st-link-analysis

---

## Installation

```bash
git clone https://github.com/your-username/disaster-relief-network.git
cd disaster-relief-network
pip install -r requirements.txt
```

If no `requirements.txt` is available:

```bash
pip install streamlit networkx pandas numpy matplotlib st-link-analysis
```

---

## Usage

```bash
streamlit run app.py
```

Open the application in your browser at:
[http://localhost:8501](http://localhost:8501)

---

## How It Works

The application generates a graph where:

* Nodes represent facilities such as hospitals, shelters, and distribution centers
* Edges represent roads with attributes like travel time, cost, risk, and condition

It applies graph algorithms (e.g., shortest path, centrality analysis) to compute optimal routes and evaluate network performance under different scenarios.

---

## Use Cases

* Disaster response and relief planning
* Emergency logistics optimization
* Infrastructure and network resilience analysis
* Academic and simulation-based studies

---

## License

This project is licensed under the MIT License.

---

