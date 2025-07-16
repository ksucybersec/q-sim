import { ConnectionAlreadyExists } from "../../../helpers/errors/connectionError";
import { SimulatorNode } from "../base/baseNode";
import * as fabric from 'fabric';
import { LineMetaData, SimulatorConnection } from "./line";
import { NetworkManager } from "../network/networkManager";
import { getLogger } from "../../../helpers/simLogger";
import { getNodeFamily } from "../base/enums";
import { QuantumAdapter } from "../base/quantum/quantumAdapter";
import { sendComponentDragEvent, sendComponentDragEventDebounced } from "@/helpers/userEvents/userEvents";


type ConnectionCallbackFunction = (line: SimulatorConnection, from: SimulatorNode, to: SimulatorNode) => void;

export class ConnectionManager {
    static #instance: ConnectionManager;

    logger = getLogger('ConnectionManager');
    connectionStore = new Map<string, SimulatorConnection>();
    inprogressLine = new Map<string, SimulatorConnection>();
    canvas;
    onConnectionCallbackFunctions: ConnectionCallbackFunction[] = [];

    constructor(canvas: fabric.Canvas) {
        this.canvas = canvas;
    }

    public static getInstance(canvas?: fabric.Canvas): ConnectionManager {
        if (!ConnectionManager.#instance && canvas) {
            console.log("Initialized Connection Manager!");
            ConnectionManager.#instance = new ConnectionManager(canvas);
        }

        return ConnectionManager.#instance;
    }

    private getLineId(...nodes: SimulatorNode[]) {
        return nodes.map(x => x.name).sort((a, b) => a > b ? 1 : -1).join('__')
    }

    updateMetaData(from: SimulatorNode, to: SimulatorNode, metaData: Partial<LineMetaData>) {
        const lineId = this.getLineId(from, to);
        if (!this.connectionStore.has(lineId)) {
            this.logger.error('Connection does not exist between', from.name, 'and', to.name);
            return;
        }

        const line = this.connectionStore.get(lineId) as SimulatorConnection;
        line.updateMetaData(metaData);
    }

    updateConnection(from: SimulatorNode, currentMousePosition: { x: number, y: number }, instantDelete = false) {
        const inProgressLineId = this.getLineId(from);

        let line: SimulatorConnection;
        if (!this.inprogressLine.has(inProgressLineId)) {
            // For new connection, starting and ending point is same.
            line = new SimulatorConnection([from.getX() + from.width / 2, from.getY() + from.height / 2, currentMousePosition.x, currentMousePosition.y], { from, connectionType: getNodeFamily(from.nodeType) }, {
                stroke: 'black'
            });
            this.canvas.add(line);
            this.inprogressLine.set(inProgressLineId, line);
        } else {
            line = this.inprogressLine.get(inProgressLineId) as SimulatorConnection;
        }
        if (line.isConnected) { return; }

        line.set({
            'x2': currentMousePosition.x,
            'y2': currentMousePosition.y
        });
        this.canvas.requestRenderAll();

        // Check if line has "entered" any other node.
        this.canvas.getObjects().forEach((obj) => {
            if (!(obj instanceof SimulatorNode) || (obj === from)) {
                return
            }
            console.log('Inside of', line.isInsideOf(obj))
            console.log('Connection acceptable',  obj.isConnectionAcceptable(from), obj.name)
            if (line.isInsideOf(obj) && obj.isConnectionAcceptable(from)) {
                try {
                    this.onConnection(line, from, obj);
                    if (instantDelete) {
                        this.inprogressLine.delete(inProgressLineId);
                    } else {
                        setTimeout(() => {
                            this.inprogressLine.delete(inProgressLineId);
                        }, 1000)
                    }
                } catch (e) {
                    if (e instanceof ConnectionAlreadyExists) {
                        this.logger.debug('Connection already exists b/w these nodes');
                        return;
                    }
                }
            }
        })
    }

    onConnection(line: SimulatorConnection, from: SimulatorNode, to: SimulatorNode) {
        const lineId = this.getLineId(from, to);

        if (this.connectionStore.has(lineId)) {
            this.cancelConnection(from);
            throw new ConnectionAlreadyExists(from.name, to.name);
        }

        this.logger.debug('Connecting to ' + to.name);
        line.isConnected = true;
        this.connectionStore.set(lineId, line);
        line.updateMetaData({ to });

        line.set({
            'x2': to.getX() + to.width / 2,
            'y2': to.getY() + to.height / 2
        })
        this.watchFromNodeMove(line, from);
        this.watchToNodeMove(line, to);
        this.sendAllLinesBackward();

        if (from instanceof QuantumAdapter) {
            from.assignAdapterNode(to);
        } else if (to instanceof QuantumAdapter) {
            to.assignAdapterNode(from);
        } else {
            NetworkManager.getInstance().onConnectionCreated(from, to);
        }

        this.onConnectionCallbackFunctions.forEach(callback => callback(line, from, to));
        return
    }

    onConnectionCallback(func: ConnectionCallbackFunction) {
        if (!this.onConnectionCallbackFunctions.includes(func)) {
            this.onConnectionCallbackFunctions.push(func);
        }
    }

    sendAllLinesBackward() {
        this.canvas.getObjects().filter(x => x instanceof SimulatorConnection).forEach(x => this.canvas.sendObjectToBack(x));
    }

    watchFromNodeMove(line: SimulatorConnection, from: SimulatorNode) {
        let isDown = false;
        const onMouseDown = (_: any) => {
            isDown = true;
        }
        from.on('mousedown', onMouseDown)
        const onMouseUp = (_: any) => {
            isDown = false;
        }
        from.on('mouseup', onMouseUp);

        const onMouseMove = (_: any) => {
            if (isDown) {
                const [oldX, oldY] = [from.getX(), from.getY()]
                line.set({
                    'x1': from.getX() + from.width / 2,
                    'y1': from.getY() + from.height / 2
                });
                sendComponentDragEventDebounced(from.name, oldX + ',' + oldY, line.getX() + ',' + line.getY())
                NetworkManager.getInstance().onNodeMoved(from);
            }
        }
        from.on('mousemove', onMouseMove);

        this.canvas.on('object:removed', (e) => {
            if (e.target === line) {
                this.logger.debug('Remove line nodeListeners', from.name);
                from.on('mouseup', onMouseUp);
                from.on('mousemove', onMouseMove);
                from.on('mousedown', onMouseDown)
            }
        });
    }

    watchToNodeMove(line: SimulatorConnection, to: SimulatorNode) {
        let isDown = false;
        const onMouseDown = (_: any) => {
            isDown = true;
        }
        to.on('mousedown', onMouseDown)
        const onMouseUp = (_: any) => {
            isDown = false;
        }
        to.on('mouseup', onMouseUp);

        const onMouseMove = (_: any) => {
            if (isDown) {
                const [oldX, oldY] = [to.getX(), to.getY()]
                line.set({
                    'x2': to.getX() + to.width / 2,
                    'y2': to.getY() + to.height / 2
                });
                sendComponentDragEventDebounced(to.name, oldX + ',' + oldY, line.getX() + ',' + line.getY())
                NetworkManager.getInstance().onNodeMoved(to);
            }
        };

        to.on('mousemove', onMouseMove)
        this.canvas.on('object:removed', (e) => {
            if (e.target === line) {
                this.logger.debug('Remove line nodeListeners', to.name);
                to.on('mouseup', onMouseUp);
                to.on('mousemove', onMouseMove);
                to.on('mousedown', onMouseDown)
            }
        });
    }

    cancelConnection(from: SimulatorNode) {
        const inProgressLineId = this.getLineId(from);
        if (!this.inprogressLine.has(inProgressLineId)) {
            // throw new ConnectionDoesNotExists(from);
            return;
        }

        if (this.inprogressLine.get(inProgressLineId)?.isConnected) {
            this.logger.debug('Line is connected, so do not cancel!');
            return;
        }
        const line = this.inprogressLine.get(inProgressLineId) as SimulatorConnection;
        this.canvas.remove(line);
        this.inprogressLine.delete(inProgressLineId);
    }

    removeLine(line: SimulatorConnection) {
        if (!line.metaData.from || !line.metaData.to) {
            this.logger.error('Line does not have from or to node metadata, cannot remove connection');
            return;
        }
        const lineId = this.getLineId(line.metaData.from, line.metaData.to);
        this.canvas.remove(line);
        this.connectionStore.delete(lineId);
        this.logger.info('Removed connection b/w', line.metaData.from.name, line.metaData.to.name);

        return NetworkManager.getInstance().onConnectionRemoved(line.metaData.from, line.metaData.to);
    }

    removeConnection(from: SimulatorNode, to: SimulatorNode) {
        const lineId = this.getLineId(from, to);
        if (!this.connectionStore.has(lineId)) {
            this.logger.error('Connection does not exist between', from.name, 'and', to.name);
            return;
        }

        const line = this.connectionStore.get(lineId);
        if (!line) {
            this.logger.error('Line not found for connection between', from.name, 'and', to.name);
            return;
        }

        this.removeLine(line);
    }

    removeAllConnectionsIfExists(deletedNode: SimulatorNode) {
        for (const [key, line] of this.connectionStore) {

            if (line.metaData.to && (line.metaData.from == deletedNode || line.metaData.to == deletedNode)) {
                const network = this.removeLine(line);

                if (network) {
                    network.deleteNodes(deletedNode)
                }
            }
        }
    }

    getAllConnections(): SimulatorConnection[] {
        return Array.from(this.connectionStore.values());
    }
}

(window as any).getConnectionManager = ConnectionManager.getInstance