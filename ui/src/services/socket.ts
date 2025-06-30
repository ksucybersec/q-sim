// Define types for WebSocket event handlers
type MessageHandler = (data: any) => void;
type ErrorHandler = (event: Event) => void; // WebSocket errors provide an Event object
type OpenHandler = () => void;
type CloseHandler = (event: CloseEvent) => void; // Close provides a CloseEvent (code, reason)

// Keep your custom events enum
export enum SocketEvents {
    SimulationEvent = 'simulation_event',
    // Add other specific event names your server might send
    ServerResponse = 'server_response',
    SimulationSummary = 'simulation_summary'
}

/**
 * Singleton WebSocket client using standard browser WebSocket API
 */
export class WebSocketClient {
    private static instance: WebSocketClient;
    private ws: WebSocket | null = null;
    // Map event names (from server messages) to handlers
    private messageHandlers: Map<string, MessageHandler[]> = new Map();
    private openHandlers: OpenHandler[] = [];
    private closeHandlers: CloseHandler[] = [];
    private errorHandlers: ErrorHandler[] = [];
    private url: string = ''; // Use ws:// or wss://
    private _connecting: boolean = false;
    private _connectionPromise: { resolve: () => void; reject: (reason?: any) => void; } | null = null;

    public simulationEventLogs: any[] = []; // Keep your specific state

    /**
     * Private constructor to prevent direct instantiation
     */
    private constructor() {
        // Store SimulationEvent messages in Memory
        // This now uses the internal routing based on the event name in the message
        this.onMessage(SocketEvents.SimulationEvent, (data) => {
            // console.log('Received Simulation Event:', data); // Optional logging
            this.simulationEventLogs.push(data);
        });
    }

    /**
     * Get singleton instance
     */
    public static getInstance(): WebSocketClient {
        if (!WebSocketClient.instance) {
            WebSocketClient.instance = new WebSocketClient();
        }
        return WebSocketClient.instance;
    }

    /**
     * Connect to the WebSocket server
     *
     * @param url Server URL (must start with ws:// or wss://)
     * @returns Promise that resolves when connected
     */
    public connect(url: string): Promise<void> {
        // Check current state
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('WebSocket already connected.');
            return Promise.resolve();
        }
        if (this._connecting || (this.ws && this.ws.readyState === WebSocket.CONNECTING)) {
            console.log('WebSocket connection attempt already in progress.');
            // Return the existing promise if available
            return new Promise((res, rej) => {
                if (this._connectionPromise) {
                     // This isn't perfect, as multiple callers might wait,
                     // but it prevents multiple connection attempts.
                     this._connectionPromise.resolve = () => { this._connectionPromise = null; res(); };
                     this._connectionPromise.reject = (reason) => { this._connectionPromise = null; rej(reason); };
                } else {
                    // Should not happen if _connecting is true, but as fallback:
                     rej(new Error("Connection in progress, but promise lost"));
                }
            });
        }

        // Validate URL scheme
        if (!url || (!url.startsWith('ws://') && !url.startsWith('wss://'))) {
            console.error('Invalid WebSocket URL. Must start with ws:// or wss://');
            return Promise.reject(new Error('Invalid WebSocket URL scheme.'));
        }

        this.url = url;
        this._connecting = true;

        return new Promise<void>((resolve, reject) => {
            console.log(`Attempting to connect WebSocket to ${this.url}...`);
            this._connectionPromise = { resolve, reject }; // Store promise controllers

            try {
                this.ws = new WebSocket(this.url);

                this.ws.onopen = () => {
                    console.log('WebSocket connected successfully.');
                    this._connecting = false;
                    this.openHandlers.forEach(handler => handler());
                    if (this._connectionPromise) {
                        this._connectionPromise.resolve(); // Resolve the promise
                        this._connectionPromise = null;
                    }
                };

                this.ws.onclose = (event: CloseEvent) => {
                    console.log(`WebSocket disconnected: Code=${event.code}, Reason=${event.reason}, WasClean=${event.wasClean}`);
                    this._connecting = false;
                    this.closeHandlers.forEach(handler => handler(event));
                    // If connection promise was pending and connection failed:
                    if (this._connectionPromise) {
                        this._connectionPromise.reject(new Error(`WebSocket closed before opening: Code=${event.code}`));
                        this._connectionPromise = null;
                    }
                    this.ws = null; // Clear the instance on close
                };

                this.ws.onerror = (event: Event) => {
                    console.error('WebSocket error:', event);
                    this._connecting = false;
                    this.errorHandlers.forEach(handler => handler(event));
                    // If connection promise was pending and connection failed:
                    if (this._connectionPromise) {
                        this._connectionPromise.reject(new Error('WebSocket connection error.'));
                        this._connectionPromise = null;
                    }
                    // Note: onerror is often followed by onclose
                };

                this.ws.onmessage = (event: MessageEvent) => {
                    // console.log('Raw message received:', event.data); // Debugging
                    try {
                        // Assuming server sends JSON strings
                        const messageData = JSON.parse(event.data);

                        // Check the expected format { event: string, data: any }
                        if (messageData && typeof messageData.event === 'string' && messageData.hasOwnProperty('data')) {
                            const eventName = messageData.event;
                            const payload = messageData.data;

                            // Find handlers for this specific event name
                            const handlers = this.messageHandlers.get(eventName);
                            if (handlers && handlers.length > 0) {
                                // console.log(`Dispatching event "${eventName}" to ${handlers.length} handlers.`);
                                handlers.forEach(handler => {
                                    try {
                                        handler(payload);
                                    } catch (handlerError) {
                                        console.error(`Error in message handler for event "${eventName}":`, handlerError);
                                    }
                                });
                            } else {
                                // console.warn(`No message handlers registered for event: ${eventName}`);
                            }
                        } else {
                            console.warn('Received message does not match expected format {event, data}:', messageData);
                            // Optionally handle messages not matching the format differently
                        }
                    } catch (e) {
                        console.error('Failed to parse incoming WebSocket message or invalid format:', event.data, e);
                    }
                };

            } catch (error) {
                console.error('Failed to create WebSocket:', error);
                this._connecting = false;
                 if (this._connectionPromise) {
                     this._connectionPromise.reject(error); // Reject the promise
                     this._connectionPromise = null;
                 }
            }
        });
    }

    /**
     * Reconnect to the server using the same URL.
     */
    public reconnect(): Promise<void> {
        console.log("Attempting WebSocket reconnect...");
        this.disconnect(); // Ensure previous connection is closed
        // Add a small delay before reconnecting if desired
        // await new Promise(resolve => setTimeout(resolve, 1000));
        return this.connect(this.url);
    }

    /**
     * Disconnect from the server.
     */
    public disconnect(): void {
        if (this.ws) {
            console.log("Closing WebSocket connection.");
            this.ws.close();
            // Handlers (onclose) will manage setting ws to null
        }
        this._connecting = false;
        this._connectionPromise = null; // Clear any pending promise
    }

    /**
     * Send data payload to the server.
     * Assumes the backend expects the raw JSON data.
     *
     * @param data Data to send (must be JSON serializable)
     */
    public send(data: any): void {
        if (!this.isConnected()) {
            console.error('WebSocket not connected. Cannot send data.');
            // Optional: throw new Error('WebSocket not connected');
            return;
        }

        try {
            const messageString = JSON.stringify(data);
            this.ws?.send(messageString);
            // console.log('Sent data:', data); // Debug logging
        } catch (error) {
            console.error('Failed to send WebSocket message:', error);
            // Optional: throw error;
        }
    }

    /**
     * Register a handler for a specific event name received from the server.
     *
     * @param eventName The 'event' string from the server message structure {event, data}
     * @param handler Handler function
     */
    public onMessage(eventName: SocketEvents | string, handler: MessageHandler): void {
        if (!this.messageHandlers.has(eventName)) {
            this.messageHandlers.set(eventName, []);
        }
        const handlers = this.messageHandlers.get(eventName)!; // Assert non-null with !
        if (!handlers.includes(handler)) { // Avoid duplicate handlers
             handlers.push(handler);
        }
    }

    /**
     * Remove a specific handler for a message event name.
     *
     * @param eventName The 'event' string
     * @param handler Handler to remove
     */
    public offMessage(eventName: string, handler: MessageHandler): void {
        const handlers = this.messageHandlers.get(eventName);
        if (!handlers) return;

        const index = handlers.indexOf(handler);
        if (index !== -1) {
            handlers.splice(index, 1);
            // Optional: if handlers array is empty, remove the map entry
            // if (handlers.length === 0) {
            //     this.messageHandlers.delete(eventName);
            // }
        }
    }

    /**
     * Register an open/connection handler.
     *
     * @param handler Handler function
     */
    public onOpen(handler: OpenHandler): void {
         if (!this.openHandlers.includes(handler)) {
             this.openHandlers.push(handler);
         }
    }

    /**
     * Register a close/disconnect handler.
     *
     * @param handler Handler function
     */
    public onClose(handler: CloseHandler): void {
         if (!this.closeHandlers.includes(handler)) {
             this.closeHandlers.push(handler);
         }
    }

    /**
     * Register an error handler.
     *
     * @param handler Handler function
     */
    public onError(handler: ErrorHandler): void {
         if (!this.errorHandlers.includes(handler)) {
             this.errorHandlers.push(handler);
         }
    }

    /**
     * Check if the WebSocket is currently connected (OPEN state).
     */
    public isConnected(): boolean {
        return !!(this.ws && this.ws.readyState === WebSocket.OPEN);
    }
}

// Export a default singleton instance
// export default WebSocketClient.getInstance();