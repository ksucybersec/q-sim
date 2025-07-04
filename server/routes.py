import os
from fastapi import APIRouter, FastAPI, Request, Response
# from flask import Blueprint, request, Response, Flask, send_from_directory
from fastapi.responses import StreamingResponse
import httpx


def proxy_to_live_app(app):
    REACT_DEV_SERVER_URL = "http://localhost:5173"
    async_client = httpx.AsyncClient(base_url=REACT_DEV_SERVER_URL)

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
    async def proxy_to_react(path: str, request: Request):
        """
        Proxies requests to the React development server.
        """
        # Construct the target URL within the React dev server
        # httpx handles joining the base_url with the relative path
        url = httpx.URL(path=f"/{path}", query=request.url.query.encode("utf-8"))

        # Prepare the request for forwarding
        fwd_request = async_client.build_request(
            method=request.method,
            url=url,
            headers={k: v for k, v in request.headers.items() if k.lower() != 'host'}, # Exclude host header
            content=await request.body(), # Read the request body
            cookies=request.cookies,
        )

        try:
            # Send the request to the React dev server
            resp = await async_client.send(fwd_request, stream=True, follow_redirects=False)

            # Prepare headers for the client response (filter excluded headers)
            excluded_headers = {
                "content-encoding",
                "content-length", # StreamingResponse calculates this
                "transfer-encoding",
                "connection",
            }
            response_headers = {
                name: value
                for (name, value) in resp.headers.items()
                if name.lower() not in excluded_headers
            }

            # Use StreamingResponse to efficiently forward the content
            return StreamingResponse(
                content=resp.aiter_bytes(), # Async iterator for the response body
                status_code=resp.status_code,
                headers=response_headers,
                media_type=resp.headers.get("content-type"), # Forward the original content type
            )

        except httpx.RequestError as e:
            # Handle errors connecting to the dev server (e.g., server not running)
            error_message = f"Proxy error: Unable to connect to React dev server at {REACT_DEV_SERVER_URL}. Error: {e}"
            print(f"[PROXY ERROR] {error_message}") # Log the error
            return Response(content=error_message, status_code=502) # Bad Gateway


REACT_BUILD_FOLDER = "/home/sahil/QUANTUM/network_simulator_project/simulator_1/ui/dist"

def serve_dist(app):
    # Serve main page
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        # If path is an API route, skip handling it here
        if path.startswith('api/'):
            # Return None to let Flask continue to the next matching route
            return None
        print(os.path.join(REACT_BUILD_FOLDER, path))
        # If path exists as a file, serve it directly
        if path and os.path.exists(os.path.join(REACT_BUILD_FOLDER, path)):
            return send_from_directory(REACT_BUILD_FOLDER, path)
        
        # Otherwise return index.html for client-side routing
        return send_from_directory(REACT_BUILD_FOLDER, 'index.html')
    
    # Optional: Explicitly handle assets folder
    @app.route('/assets/<path:path>')
    def serve_assets(path):
        return send_from_directory(os.path.join(REACT_BUILD_FOLDER, 'assets'), path)

def register_blueprints(app: FastAPI):
    # Create the main router for the /api prefix
    api_router = APIRouter(
        prefix="/api",
        tags=["API Root"] # Optional: Helps organize docs
    )
    
    from server.api.topology.topology import topology_router
    api_router.include_router(topology_router) 


    from server.api.simulation.simulation import simulation_router
    api_router.include_router(simulation_router) 

    from server.api.agent.agent import agent_router
    api_router.include_router(agent_router)

    from server.api.conversation.conversation_api import conversation_router
    api_router.include_router(conversation_router)

    @api_router.get("/{rest_of_path:path}")
    async def handle_404(rest_of_path: str):
        return Response(content="Route not found", status_code=404)

    app.include_router(api_router)


def register_routes(app: FastAPI):
    register_blueprints(app)
    if os.getenv('SERVE_DIST'):
        print("Serve UI Build")
        serve_dist(app)
    else:
        proxy_to_live_app(app)
