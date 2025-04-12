from flask_cors import CORS
from flask import Flask, request, jsonify
import json
import os
import uuid
from portia import (
    Config,
    LogLevel,
    Portia,
    StorageClass,
    LLMModel,
)
from my_custom_tools.registry import custom_tool_registry
from dotenv import load_dotenv
import time
from tenacity import retry, stop_after_attempt, wait_exponential

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

load_dotenv()

# Set up Portia
my_config = Config.from_default(
    llm_provider="OPENAI",
    llm_model_name=LLMModel.GPT_4_O,
    storage_class=StorageClass.DISK,
    storage_dir='demo_runs',
    default_log_level=LogLevel.DEBUG
)

# Instantiate a Portia instance
portia = Portia(config=my_config, tools=custom_tool_registry)

# Path to graph.json
GRAPH_JSON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'graph.json'))
print(f"Using graph path: {GRAPH_JSON_PATH}")

# Helper function to load graph data
def load_graph_data():
    try:
        if os.path.exists(GRAPH_JSON_PATH):
            with open(GRAPH_JSON_PATH, 'r') as f:
                data = json.load(f)
                # Convert IDs to integers during loading
                for node in data["nodes"]:
                    if isinstance(node["id"], str):
                        try:
                            node["id"] = int(node["id"])
                        except ValueError:
                            pass  # Keep as string if it's not a valid integer
                for link in data["links"]:
                    if isinstance(link["source"], str):
                        try:
                            link["source"] = int(link["source"])
                        except ValueError:
                            pass
                    if isinstance(link["target"], str):
                        try:
                            link["target"] = int(link["target"])
                        except ValueError:
                            pass
                return data
        # Return empty graph structure if file doesn't exist
        return {"nodes": [], "links": []}
    except Exception as e:
        print(f"Error loading graph data: {e}")
        return {"nodes": [], "links": []}

def trim_graph_data(graph_data):
    """Trim graph data to keep only first 50 nodes and their associated links"""
    if len(graph_data["nodes"]) > 50:
        # Keep only first 50 nodes
        graph_data["nodes"] = [node for node in graph_data["nodes"] if node["id"] <= 50]
        # Keep only links where both source and target are <= 50
        graph_data["links"] = [link for link in graph_data["links"] 
                             if link["source"] <= 50 and link["target"] <= 50]
    return graph_data

# Helper function to save graph data
def save_graph_data(data):
    try:
        os.makedirs(os.path.dirname(GRAPH_JSON_PATH), exist_ok=True)
        # Trim graph before saving
        data = trim_graph_data(data)
        with open(GRAPH_JSON_PATH, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving graph data: {e}")
        return False

@app.route('/api/get-graph', methods=['GET'])
def get_graph():
    """Endpoint to get the current graph data"""
    print("API get-graph called, path:", GRAPH_JSON_PATH)
    print("File exists:", os.path.exists(GRAPH_JSON_PATH))
    data = load_graph_data()
    print("Loaded data:", data)
    return jsonify(data)

@app.route('/api/add-node', methods=['POST'])
def add_node():
    """Add a new topic node to the graph"""
    data = request.json
    topic = data.get('topic')
    
    if not topic:
        return jsonify({"error": "No topic provided"}), 400
    
    # Load current graph
    graph_data = load_graph_data()
    
    # Check if node already exists
    existing_node = next((node for node in graph_data["nodes"] if node["name"].lower() == topic.lower()), None)
    
    if existing_node:
        return jsonify({"message": "Node already exists", "nodeId": existing_node["id"], "graph": graph_data})
    
    # Create new node
    new_node_id = len(graph_data['nodes']) + 1  # Use an integer ID
    new_node = {
        "id": new_node_id,
        "name": topic,
        "description": f"Topic: {topic}",
        "type": "topic"
    }
    
    # Add to graph
    graph_data["nodes"].append(new_node)
    
    # Save updated graph
    save_graph_data(graph_data)
    
    return jsonify({"message": "Node added successfully", "nodeId": new_node_id, "graph": graph_data})

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.2, min=0.2, max=1))
def run_portia_plan(plan):
    return portia.run_plan(plan)

@app.route('/api/expand-node', methods=['POST'])
def expand_node():
    """Generate content about a specific topic when node is clicked, and update the graph."""
    data = request.json
    topic = data.get('topic')
    node_id = data.get('nodeId')

    if not topic:
        return jsonify({"error": "No topic provided"}), 400

    try:
        # 1. Generate a plan for Portia to find related information.
        plan = portia.plan(f"Get all the links from the wikipedia page for {topic}. Save them to data.txt. Then, transform this into a json and store the result as graph.json. Remember to correctly indent them (with 2 spaces)")

        # 2. Run the plan.
        plan_run = run_portia_plan(plan)

        # 3. Extract the relevant information from Portia's output.
        portia_output = str(plan_run.outputs.final_output)  # Convert LocalOutput to string first

        # 4. Load the current graph data.
        graph_data = load_graph_data()

        # 5.  Create a new node for the expanded topic if it doesn't exist
        existing_node = next((node for node in graph_data["nodes"] if node["name"].lower() == topic.lower()), None)

        if not existing_node:
            new_node_id = len(graph_data['nodes']) + 1 #changed to int
            new_node = {
                "id": new_node_id,
                "name": topic,
                "description": portia_output,
                "type": "topic"
            }
            graph_data["nodes"].append(new_node)
            node_id_to_use = new_node_id
        else:
            node_id_to_use = existing_node["id"]
            existing_node["description"] = portia_output

        # 6. Add new nodes and links based on Portia's output.
        related_topics = portia_output.get("related_topics", [])

        for related_topic_name in related_topics:
            # Check if the related topic node already exists.
            related_node = next((node for node in graph_data["nodes"] if node["name"].lower() == related_topic_name.lower()), None)
            if not related_node:
                # If it doesn't exist, create a new node for it.
                new_related_node_id = len(graph_data['nodes']) + 1 #changed to int
                new_related_node = {
                    "id": new_related_node_id,
                    "name": related_topic_name,
                    "description": f"Related to {topic}",
                    "type": "topic"
                }
                graph_data["nodes"].append(new_related_node)
                # Create a link between the original node and the new related node.
                graph_data["links"].append({
                    "source": int(node_id_to_use), #changed to int
                    "target": int(new_related_node_id), #changed to int
                    "label": "related to"
                })
            else:
                graph_data["links"].append({
                    "source": int(node_id_to_use), #changed to int
                    "target": int(related_node["id"]), #changed to int
                    "label": "related to"
                })

        # 7. Save the updated graph data.
        save_result = save_graph_data(graph_data)
        if not save_result:
            return jsonify({"error": "Failed to save updated graph data."}), 500  # Return 500 error

        # 8. Return the updated graph data.
        return jsonify({
            "message": "Node expanded successfully",
            "nodeInfo": portia_output,
            "updatedGraph": graph_data
        })

    except Exception as e:
        print(f"Error expanding node with Portia: {e}")
        return jsonify({"error": str(e)}), 500  # Return 500 Internal Server Error

if __name__ == '__main__':
    # Ensure graph file exists
    if not os.path.exists(os.path.dirname(GRAPH_JSON_PATH)):
        os.makedirs(os.path.dirname(GRAPH_JSON_PATH), exist_ok=True)
    if not os.path.exists(GRAPH_JSON_PATH):
        save_graph_data({"nodes": [], "links": []})

    print(f"Graph JSON path: {os.path.abspath(GRAPH_JSON_PATH)}")
    app.run(debug=True, host='0.0.0.0', port=5001)
