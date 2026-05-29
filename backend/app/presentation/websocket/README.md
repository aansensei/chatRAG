## presentation/websocket

WebSocket handlers cho real-time features.

### Files

`chat_ws.py` - WebSocket endpoint cho streaming chat. Nhận câu hỏi qua WS message, stream LLM tokens về client theo từng token thay vì đợi response đầy đủ. Dùng cho UI chat có typing effect.
