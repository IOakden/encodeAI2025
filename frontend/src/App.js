import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import jsonData from './data/graph.json';


export default function NetworkGraph() {
  const svgRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    // Simulate fetching data
    setTimeout(() => {
      setGraphData(jsonData); // use imported jsonData directly
      setIsLoading(false);
    }, 500);
  }, []);
  

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
      .on("click", (event, d) => {
        setSelectedNode(selectedNode?.id === d.id ? null : d);
        event.stopPropagation();
      });
    
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
  }, [graphData, isLoading, selectedNode]);

  if (isLoading) {
    return <div className="flex justify-center items-center h-64">Loading graph data...</div>;
  }

  if (error) {
    return <div className="text-red-500">Error loading graph: {error}</div>;
  }

  return (
    <div className="flex flex-col items-center">
      <h2 className="text-xl font-bold mb-4">Network Graph</h2>
      <svg ref={svgRef} className="border border-gray-300 rounded"></svg>
    </div>
  );
}