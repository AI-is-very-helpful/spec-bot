import azure.functions as func
import os
import sys

# Add src to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from presentation.handlers.http_handler import main as http_handler_main

app = func.FunctionApp()

@app.function_name(name="messages")
@app.route(route="messages", methods=["post"], auth_level=func.AuthLevel.FUNCTION)
async def messages(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    """Handle Teams messages"""
    return await http_handler_main(req)
