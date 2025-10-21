from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from ..ws_manager import manager
from ..dependencies import get_current_user_ws
from db.models import User

router = APIRouter(prefix="/ws", tags=["WebSocket"])

@router.websocket("")
async def websocket_endpoint(websocket: WebSocket, user: User = Depends(get_current_user_ws)):
    if not user:
        await websocket.close(code=1008)
        return
    await manager.connect(user.id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user.id)
