import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';

export default function NetworkGraph() {
  const svgRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTopic, setSearchTopic] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  // Helper function to convert IDs to integers (if needed)
    const normalizeGraphData = (data) => {
        const normalizedNodes = data.nodes.map(node => ({
            ...node,
            id: typeof node.id === 'string' ? parseInt(node.id, 10) : node.id
        }));
        const normalizedLinks = data.links.map(link => ({
            ...link,
            source: typeof link.source === 'string' ? parseInt(link.source, 10) : link.source,
            target: typeof link.target === 'string' ? parseInt(link.target, 10) : link.target
        }));
        return { nodes: normalizedNodes, links: normalizedLinks };
    };


  // Fetch initial graph data from the server
  useEffect(() => {
    console.log("Fetching graph data from:", 'http://localhost:5001/api/get-graph');

    fetch('http://localhost:5001/api/get-graph')
      .then(response => {
        console.log("Response status:", response.status);
        if (!response.ok) {
          throw new Error(`Network response was not ok: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log("Received graph data:", data);
        setGraphData(normalizeGraphData(data)); // Normalize IDs after fetching
        setIsLoading(false);
      })
      .catch(err => {
        console.error('Error fetching graph data:', err);
        setError(err.message);
        setIsLoading(false);
      });
  }, []);

  // Handle adding a new topic to the graph
  const handleAddTopic = async (e) => {
    e.preventDefault();
    if (!searchTopic.trim()) return;

    setIsProcessing(true);

    try {
      const response = await fetch('http://localhost:5001/api/add-node', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ topic: searchTopic }),
      });

      if (!response.ok) {
        throw new Error('Failed to add node');
      }

      const data = await response.json();
      setGraphData(normalizeGraphData(data.graph));  // Normalize IDs after adding
      setSearchTopic(''); // Clear the input
    } catch (err) {
      console.error('Error adding node:', err);
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle clicking on a node to expand it
    const handleNodeClick = useCallback(async (event, d) => {
        event.stopPropagation();

        // Toggle selection if already selected
        if (selectedNode?.id === d.id) {
            setSelectedNode(null);
            return;
        }

        setSelectedNode(d);
        setIsProcessing(true);

        try {
            const response = await fetch('http://localhost:5001/api/expand-node', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    topic: d.name,
                    nodeId: d.id
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to expand node');
            }

            const data = await response.json();
            setGraphData(normalizeGraphData(data.updatedGraph)); // Normalize IDs after expanding

            // Update the selected node with additional information
            setSelectedNode(prev => ({
                ...prev,
                description: data.nodeInfo?.summary || prev.description
            }));
        } catch (err) {
            console.error('Error expanding node:', err);
            // Don't set error state here to avoid blocking the UI
        } finally {
            setIsProcessing(false);
        }
    }, [selectedNode, setSelectedNode, setGraphData, setIsProcessing]);

  useEffect(() => {
    if (!svgRef.current || isLoading || graphData.nodes.length === 0) return;

    // Clear previous SVG content
    d3.select(svgRef.current).selectAll("*").remove();

    const width = 1000;
    const height = 800;

    // Create SVG
    const svg = d3.select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", `0 0 ${width} ${height}`);

    // Create simulation
    const simulation = d3.forceSimulation(graphData.nodes)
      .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(150))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2));

    // Create links
    const link = svg.append("g")
      .selectAll("g")
      .data(graphData.links)
      .enter()
      .append("g");

    const path = link.append("path")
      .attr("class", "link")
      .attr("stroke", "#999")
      .attr("stroke-width", 2)
      .attr("fill", "none");

    // Add link labels
    const linkText = link.append("text")
      .attr("class", "link-label")
      .attr("dy", -5)
      .attr("text-anchor", "middle")
      .attr("fill", "#555")
      .attr("font-size", "12px")
      .text(d => d.label);

    // Create nodes
    const node = svg.append("g")
      .selectAll("g")
      .data(graphData.nodes)
      .enter()
      .append("g")
      .attr("class", "node")
      .on("click", handleNodeClick);  // Use the new click handler

    // Add node circles
    node.append("circle")
      .attr("r", 30)
      .attr("fill", d => selectedNode?.id === d.id ? "#ff9999" : "#69b3a2")
      .attr("stroke", "#333")
      .attr("stroke-width", 1.5);

    // Add node labels
    node.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", ".3em")
      .attr("fill", "white")
      .attr("font-size", "12px")
      .text(d => d.name);

    // Add title for hovering
    node.append("title")
      .text(d => d.name);

    // Update positions on simulation tick
    simulation.on("tick", () => {
      path.attr("d", d => {
        const sourceX = d.source.x;
        const sourceY = d.source.y;
        const targetX = d.target.x;
        const targetY = d.target.y;
        return `M${sourceX},${sourceY}L${targetX},${targetY}`;
      });

      linkText.attr("transform", d => {
        const midX = (d.source.x + d.target.x) / 2;
        const midY = (d.source.y + d.target.y) / 2;
        const dx = d.target.x - d.source.x;
        const dy = d.target.y - d.source.y;
        const angle = Math.atan2(dy, dx) * 180 / Math.PI;
        return `translate(${midX}, ${midY}) rotate(${angle})`;
      });

      node.attr("transform", d => `translate(${d.x}, ${d.y})`);
    });

    // Drag handlers
    const dragStarted = (event, d) => {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    };

    const dragged = (event, d) => {
      d.fx = event.x;
      d.fy = event.y;
    };

    const dragEnded = (event, d) => {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    };

    // Add drag behavior
    node.call(d3.drag()
      .on("start", dragStarted)
      .on("drag", dragged)
      .on("end", dragEnded));

    // Clear selection when clicking on background
    svg.on("click", () => {
      setSelectedNode(null);
    });

    return () => {
      simulation.stop();
    };
  }, [graphData, isLoading, selectedNode, handleNodeClick]);

  if (isLoading && !isProcessing) {
    return <div className="flex justify-center items-center h-64">Loading graph data...</div>;
  }

  if (error && !graphData.nodes.length) {
    return <div className="text-red-500">Error loading graph: {error}</div>;
  }

  return (
    <div className="flex flex-col items-center p-4">
      <h2 className="text-2xl font-bold mb-4">Knowledge Graph Explorer</h2>

      {/* Add topic input form */}
      <form onSubmit={handleAddTopic} className="w-full max-w-md mb-6">
        <div className="flex items-center border-b border-blue-500 py-2">
          <input
            className="appearance-none bg-transparent border-none w-full text-gray-700 mr-3 py-1 px-2 leading-tight focus:outline-none"
            type="text"
            placeholder="Enter a topic to explore"
            value={searchTopic}
            onChange={(e) => setSearchTopic(e.target.value)}
            disabled={isProcessing}
          />
          <button
            className={`flex-shrink-0 bg-blue-500 hover:bg-blue-700 border-blue-500 hover:border-blue-700 text-sm border-4 text-white py-1 px-2 rounded ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
            type="submit"
            disabled={isProcessing}
          >
            {isProcessing ? 'Processing...' : 'Add Topic'}
          </button>
        </div>
      </form>

      {/* Show details of selected node */}
      {selectedNode && (
        <div className="bg-gray-100 p-4 mb-4 rounded w-full max-w-lg">
          <h3 className="font-bold">{selectedNode.name}</h3>
          <p>{selectedNode.description || 'Click to explore this topic'}</p>
          {isProcessing && <p className="text-blue-500 mt-2">Loading topic data...</p>}
        </div>
      )}

      {/* Graph visualization */}
      <div className="relative">
        <svg ref={svgRef} className="border border-gray-300 rounded" />
        {isProcessing && !isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-50">
            <div className="text-blue-500">Processing...</div>
          </div>
        )}
      </div>
    </div>
  );
}
