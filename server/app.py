from fastapi import FastAPI

from server.socket_server.socket_server import websocket_endpoint

REACT_BUILD_FOLDER = "../ui/dist"

# Create a new app factory function
def get_app(lifespan):
    app = FastAPI(title="Network Simulator API", version="1.0.0", lifespan=lifespan)
    # CORS(app, origins='*')
    
    # Register routes
    from server.routes import register_routes
    register_routes(app)
    
    app.add_websocket_route("/api/ws", websocket_endpoint)
    
    return app
