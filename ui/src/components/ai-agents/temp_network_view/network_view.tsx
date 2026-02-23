import { NetworkManager } from '@/components/node/network/networkManager';
import { Button } from '@/components/ui/button';
import { ExportDataI } from '@/services/export.interface';
import { importFromJSON } from '@/services/importService';
import React, { useEffect, useRef } from 'react';
import { Edge, Network, Node, Options } from 'vis-network/standalone';
import 'vis-network/styles/vis-network.css';

interface NetworkVisualizerProps {
    topologyStringifiedData: string
}

const NetworkVisualizer = ({ topologyStringifiedData }: NetworkVisualizerProps) => {
    const topologyData: ExportDataI = JSON.parse(topologyStringifiedData);

    const networkRef = useRef<HTMLElement>(null);

    useEffect(() => {
        if (!topologyData || !networkRef.current) return;

        const containerWidth = networkRef.current.clientWidth || 800;
        const containerHeight = networkRef.current.clientHeight || 600;

        // Get topology dimensions
        const topologyWidth = topologyData.size[0] || 1000;
        const topologyHeight = topologyData.size[1] || 1000;


        // Create nodes and edges arrays for vis-network
        const nodes: Node[] = [];
        const edges: Edge[] = [];

        // Track IDs to avoid duplicates
        const nodeIds = new Set();

        // Approach 1: Use the location coordinates from data
        topologyData.zones.forEach(zone => {

            zone.networks.forEach(network => {
                // Process hosts within network
                network.hosts.forEach(host => {
                    const hostId = host.name;

                    // Set colors based on host type
                    const isServer = host.type === 'SERVER';
                    const hostColor = isServer ?
                        { background: '#ccffcc', border: '#009900' } :
                        { background: '#ffe6cc', border: '#cc6600' };

                    // Normalize coordinates to container dimensions
                    const normalizedX = (host.location[0] / topologyWidth) * containerWidth;
                    const normalizedY = (host.location[1] / topologyHeight) * containerHeight;

                    if (!nodeIds.has(hostId)) {
                        nodes.push({
                            id: hostId,
                            label: `${host.name}\n${host.address}\n(${host.type})`,
                            shape: 'box',
                            color: hostColor,
                            font: { size: 12 },
                            x: normalizedX,
                            y: normalizedY
                        });
                        nodeIds.add(hostId);
                    }
                });


                // Add connections if present
                if (network.connections && network.connections.length > 0) {
                    network.connections.forEach(connection => {
                        if (!connection.to_node) return;
                        edges.push({
                            from: connection.from_node,
                            to: connection.to_node,
                            smooth: {
                                type: 'cubicBezier',
                                roundness: 0.5,
                                enabled: true
                            }
                        });
                    });
                }
            });

            zone.adapters.forEach((adapter) => {
                // Normalize coordinates to container dimensions
                const normalizedX = (adapter.location[0] / topologyWidth) * containerWidth;
                const normalizedY = (adapter.location[1] / topologyHeight) * containerHeight;

                const hostColor =
                    { background: '#ffe6cc', border: '#cc6600' };

                nodes.push({
                    id: adapter.name,
                    label: `${adapter.name}\n${adapter.address}\n(${adapter.type})`,
                    shape: 'box',
                    color: hostColor,
                    font: { size: 12 },
                    x: normalizedX,
                    y: normalizedY
                });
                nodeIds.add(adapter.name);

                // Match main canvas: adapter sits between classical and quantum host (two edges, not one)
                edges.push({
                    from: adapter.classicalHost,
                    to: adapter.name,
                    smooth: {
                        type: 'cubicBezier',
                        roundness: 0.5,
                        enabled: true
                    }
                });
                edges.push({
                    from: adapter.name,
                    to: adapter.quantumHost,
                    smooth: {
                        type: 'cubicBezier',
                        roundness: 0.5,
                        enabled: true
                    }
                });
            })
        });


        // Create vis-network options
        const options: Options = {
            nodes: {
                shape: 'box',
                margin: { bottom: 10, left: 10, right: 10, top: 10 },
                widthConstraint: {
                    maximum: 200
                }
            },
            edges: {
                smooth: {
                    type: 'continuous',
                    enabled: true,
                    roundness: 8
                }
            },
            physics: {
                enabled: false // Disable physics to keep nodes at their specified positions
            },
            interaction: {
                dragNodes: true,
                dragView: true,
                zoomView: true
            }
        };

        // Create the network
        const network = new Network(
            networkRef.current,
            { nodes, edges },
            options
        );

        // Fit the network to the container
        network.fit();

        // Cleanup
        return () => {
            network.destroy();
        };
    }, [topologyData]);

    const useThisTopology = () => {
        importFromJSON(topologyData, NetworkManager.getInstance().canvas);
    }

    return (
        <div className="network-view-container">
            <Button className="mt-2"
                onClick={() => {
                    window.location.href = `/?topologyID=${topologyData.pk}&temp=${topologyData.temporary_world}`;
                }}
            >Use this topology</Button>
            <div
                ref={networkRef as any}
                style={{
                    width: '100%',
                    height: '450px',
                    border: '1px solid #ddd',
                    borderRadius: '4px'
                }}
            />
        </div>
    );
};

export default NetworkVisualizer;