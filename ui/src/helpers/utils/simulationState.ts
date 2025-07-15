class SimulationState {
    private simulationRunning = false;
    private simulationID: string | null = null;
    private worldId: string | null = null;
    private userName: string | null = null;

    constructor() {
        const username = localStorage.getItem('userName')

        if(username) {
            this.setUserName(username);
        }
    }

    setSimulationID(simulationID: string | null) {
        this.simulationID = simulationID;
    }

    getSimulationID() {
        return this.simulationID;
    }

    setSimulationRunning(isRunning: boolean) {
        this.simulationRunning = isRunning;
    }

    getSimulationRunning() {
        return this.simulationRunning;
    }

    setWorldId(worldId: string | null) {
        this.worldId = worldId;
    }

    getWorldId() {
        return this.worldId;
    }

    setUserName(userName: string) {
        localStorage.setItem('userName', userName);
        this.userName = userName;
    }
    
    getUserName() {
        return this.userName;
    }

    clearUserName() {
        localStorage.removeItem('userName');
        this.userName = null;
    }
}

export default new SimulationState();