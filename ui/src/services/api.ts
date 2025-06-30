// Placeholder for API calls (implementation will be added later)

import { getLogger } from "@/helpers/simLogger";
import { exportToJSON } from "./exportService";
import { ServerSimulationStatus } from "./api.interface";
import { ExportDataI } from "./export.interface";
import { ChatRequestI } from "@/components/ai-agents/message.interface";
import simulationState from "@/helpers/utils/simulationState";
import { ConnectionConfigPreset, StartSimulationResponse } from "./apiResponse.interface";

// Blank for current host
const SERVER_HOST = '/api'

function makeFetchCall(url: string, method = 'GET', body?: any, headers: any = {}) {
    if (body) {
        body = typeof body === "string" ? body : JSON.stringify(body)
    }
    if (!headers['Content-Type']) {
        headers['Content-Type'] = 'application/json'
    }
    return fetch(url, {
        method,
        headers,
        body,
    });
}

const logger = getLogger("API")

const api = {
    createNode: async (nodeData: any): Promise<any> => {
        // Placeholder - replace with actual API call later
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({ node_id: Math.random().toString(36).substr(2, 9), name: nodeData.name }); // Simulate success
            }, 500);
        });
    },
    startAutoUpdateNetworkTopology() {
        let previousTopology: string | null = null;
        const logger = getLogger('Auto Updater');

        const scheduleUpdateCycle = () => {
            // logger.log("Scheduled auto update cycle");

            setTimeout(async () => {
                const topology = exportToJSON();

                if (!previousTopology || (JSON.stringify(topology) != previousTopology)) {
                    const resp = await this.saveTopology(topology);

                    if (resp)
                        previousTopology = JSON.stringify(topology);
                }
                scheduleUpdateCycle();
            }, 2e3);
        }

        scheduleUpdateCycle();
    },
    saveTopology: async(topology:ExportDataI | undefined): Promise<ExportDataI | undefined> => {
        try {
            const body = JSON.stringify(topology);
            let path =  `/topology/`;

            if(topology?.pk) {
                path += topology.pk
            }
            const response = await makeFetchCall(SERVER_HOST + path, 'PUT', body)

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const responseJson = await response.json();
            simulationState.setWorldId(responseJson.worldId);

            return responseJson;
        } catch (error) {
            console.error('Failed to update data:', error);
        }
    },
    getTopology: async (topologyID: string) => {
        const response = await makeFetchCall(SERVER_HOST + `/topology/` + topologyID)
        if(response.status != 200) {
            throw new Error('Error in fetching topology')
        }
        try {
            simulationState.setWorldId(topologyID);
            return await response.json() as ExportDataI
        } catch (e) {
            return null
        }
    },
    getConnectionPresets: async (): Promise<(ConnectionConfigPreset[] | null)> => {
        const response = await makeFetchCall(SERVER_HOST + `/topology/connection_config_presets`, 'GET')
        if(response.status != 200) {
            throw new Error('Error in fetching connection presets')
        }
        try {
            return await response.json()
        } catch (e) {
            logger.error(`Error in fetching connection presets`, e)
            return null
        }
    },
    listSavedTopologies: async () => {
        const response = await makeFetchCall(SERVER_HOST + `/topology/`, 'GET')

        try {
            return await response.json()
        } catch (e) {
            return null
        }
    },
    startSimulation: async (topologyID: string) => {
        const topology = exportToJSON();
        if (!topology) {
            logger.error(`Topology does not exists to start simulator`);
            return false;
        }

        const response = await makeFetchCall(SERVER_HOST + `/simulation/` + topologyID, 'POST')
        if (response.status === 201) {
            const responseJson = await response.json() as StartSimulationResponse;
            simulationState.setSimulationID(responseJson.pk);
            simulationState.setSimulationRunning(true);
            return true
        }

        simulationState.setSimulationID(null);
        simulationState.setSimulationRunning(false);
        return false
    },
    stopSimulation: async () => {
        const response = await makeFetchCall(SERVER_HOST + `/simulation/`, 'DELETE')
        if (response.status === 200) {
            return true
        }

        return false
    },
    sendMessageCommand: async (from_node_name: string, to_node_name: string, message: string) => {
        const response = await makeFetchCall(SERVER_HOST + '/simulation/message/', 'POST', {
            from_node_name, to_node_name, message
        })

        return response.status == 200;
    },
    getSimulationStatus: async () => {
        const response = await makeFetchCall(SERVER_HOST + `/simulation/status/`);

        return (await response.json()) as ServerSimulationStatus;
    },
    sendAgentMessage: async (message: ChatRequestI) => {
        const response = await makeFetchCall(SERVER_HOST + `/agent/message`, 'POST', message);

        if (!response.ok) {
            throw new Error(`Failed to send agent message: ${response.statusText}`);
        }

        return await response.json();
    }
};

export default api;