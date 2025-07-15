import * as fabric from 'fabric';
import { SimulatorNode } from '../base/baseNode';
import { isLineInObject } from './utils';
import { NodeFamily } from '../base/enums';
import { ConnectionI } from '@/services/export.interface';

export interface LineMetaData {
    from: SimulatorNode;
    to?: SimulatorNode;
    connectionType: NodeFamily;
    lossPerKm?: number;

    // Quantum Channel specific
    noise_model?: string;
    noise_strength?: number;
    error_rate_threshold?: number;
    qbits?: number;

    // Classical Connection specific
    bandwidth?: number;
    latency?: number;
    packet_loss_rate?: number;
    packet_error_rate?: number;
    mtu?: number;
    connection_config_preset?: string;
}

export class SimulatorConnection extends fabric.Line {
    connectionID: string = Math.random().toString(36).substring(2, 15);
    metaData: LineMetaData;
    isConnected = false;
    selectable = false;
    private distanceLabel?: fabric.Text;

    constructor([x1, y1, x2, y2] = [0, 0, 0, 0], metadata: LineMetaData, options: fabric.TOptions<fabric.FabricObjectProps> = {}) {
        if (metadata.from === metadata.to) {
            throw new Error('Cannot connect to itself');
        }

        if (metadata.connectionType === NodeFamily.QUANTUM) {
            options.stroke = 'blue';
        }

        super([x1, y1, x2, y2], options);
        this.metaData = metadata;
        this.metaData.lossPerKm = this.metaData.lossPerKm || 0.1;

        this.on('added', () => {
            this.createDistanceLabel();
        })

        this.on('drag', () => {
            // Update distance label when the line is moved
            this.updateDistanceLabel();
        })

        this.on('removed', () => {
            if(this.distanceLabel) {
                this.distanceLabel.canvas?.remove(this.distanceLabel);
            }
        })
    }

    private createDistanceLabel() {
        const dx = this.x2 - this.x1;
        const dy = this.y2 - this.y1;
        const distance = Math.sqrt(dx * dx + dy * dy);
        const distanceInKm = distance.toFixed(1);

        const midX = (this.x1 + this.x2) / 2;
        const midY = (this.y1 + this.y2) / 2;

        this.distanceLabel = new fabric.FabricText(`${distanceInKm}km`, {
            left: midX,
            top: midY - 10,
            fontSize: 10,
            fill: '#414A4C',
            backgroundColor: 'white',
            selectable: false,
            evented: false
        });
        this.canvas?.add(this.distanceLabel);
    }

    private updateDistanceLabel() {
        if (!this.distanceLabel) return;

        const dx = this.x2 - this.x1;
        const dy = this.y2 - this.y1;
        const distance = Math.sqrt(dx * dx + dy * dy);
        const distanceInKm = distance.toFixed(1);

        const midX = (this.x1 + this.x2) / 2;
        const midY = (this.y1 + this.y2) / 2;

        this.distanceLabel.set({
            left: midX,
            top: midY - 10,
            text: `${distanceInKm}km`
        });
    }
    
      set(key: string | Record<string, any>, value?: any) {
        this.updateDistanceLabel();
        return super.set(key, value);
      }

    updateMetaData(metaData: Partial<LineMetaData>) {
        Object.keys(metaData).forEach((k) => {
            (this.metaData as any)[k] = (metaData as any)[k];
        });
    }

    isInsideOf(node: SimulatorNode): boolean {
        return isLineInObject(this.x1, this.y1, this.x2, this.y2, node.getX(), node.getY(), node.width, node.height);
    }

    toExportJson(): ConnectionI {
        const dx = this.x2 - this.x1;
        const dy = this.y2 - this.y1;
        const distance = Math.sqrt(dx * dx + dy * dy); // Distance in canvas units
        const distanceInKm = distance.toFixed(2); // Assuming 1 canvas unit = 1 km

        return {
            "from_node": this.metaData.from.name,
            "to_node": this.metaData.to?.name,
            "length": parseFloat(distanceInKm), // Distance in kilometers
            "loss_per_km": this.metaData.lossPerKm || 0,
            "noise_model": this.metaData.noise_model || "none",
            "noise_strength": this.metaData.noise_strength || 0,
            "name": `${this.metaData.from.name}-${this.metaData.to?.name}`,
            connection_config_preset: this.metaData.connection_config_preset || 'none',
            qbits: this.metaData.qbits,
            error_rate_threshold: this.metaData.error_rate_threshold,

            "bandwidth": this.metaData.bandwidth || 999999999,
            "latency": this.metaData.latency || 0,
            mtu: this.metaData.mtu || 9999999999,
            packet_loss_rate: this.metaData.packet_loss_rate || 0,
            packet_error_rate: this.metaData.packet_error_rate || 0,
        }
    }
}