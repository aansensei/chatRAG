## presentation/websocket

WebSocket handlers for real-time features.

### Files

`chat_ws.py` - WebSocket endpoint for streaming chat. Receives a question as a WS message, streams LLM tokens back to the client one by one instead of waiting for the full response. Used for UI chat with a typing effect.
