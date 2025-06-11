from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, status, Body
from pydantic import BaseModel
from datetime import timedelta
import os
from typing import Dict

from uow import UnitOfWork
from services.message_handler import MessageHandler
from services.queries import (
    UserQueryService,
    MessageQueryService,
    GroupQueryService,
    DirectMessageQueryService,
)
from services.commands import (
    UserCommandService,
    MessageCommandService,
    GroupCommandService,
    DirectMessageCommandService,
)
from auth import verify_password, create_access_token, get_current_user

router = APIRouter()

# Dependency to get a UnitOfWork per request
def get_uow():
    uow = UnitOfWork()
    try:
        yield uow
    finally:
        uow.commit_close()

# Pydantic models for request bodies

class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str

class CreateMessageRequest(BaseModel):
    sender_id: str
    content: str
    reciever_user_id: str | None = None  # use "reciever_user_id" instead of "receiver_user_id"
    reciever_group_id: str | None = None  # use "reciever_group_id" instead of "receiver_group_id"

class UpdateMessageRequest(BaseModel):
    new_content: str

class CreateGroupRequest(BaseModel):
    group_name: str
    admin_id: str
    group_description: str | None = None

class UpdateGroupRequest(BaseModel):
    group_name: str
    group_description: str | None = None

class MemberRequest(BaseModel):
    member_id: str

class CreateDMRequest(BaseModel):
    user1_id: str
    user2_id: str

class LoginRequest(BaseModel):
    username: str
    password: str

#db connection test api
@router.get("/health")
def db_connection_check():
    uow = UnitOfWork()
    if uow.test_connection():
        return {"status": "ok", "message": "Database connection is healthy"}
    else:
        raise HTTPException(status_code=500, detail="Database connection failed")

# ==== Query Endpoints ====

@router.get("/users/{user_id}")
def get_user(user_id: str, uow: UnitOfWork = Depends(get_uow)):
    user_query = UserQueryService(uow)
    user = user_query.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.dict()

@router.get("/users")
def get_all_users(uow: UnitOfWork = Depends(get_uow)):
    user_query = UserQueryService(uow)
    users = user_query.get_all_users()
    return [user.dict() for user in users]

@router.get("/messages/{message_id}")
def get_message(message_id: str, uow: UnitOfWork = Depends(get_uow)):
    msg_query = MessageQueryService(uow)
    message = msg_query.get_message_by_id(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message.dict()

@router.get("/messages/sender/{sender_id}")
def get_messages_by_sender(sender_id: str, uow: UnitOfWork = Depends(get_uow)):
    msg_query = MessageQueryService(uow)
    messages = msg_query.get_messages_by_sender(sender_id)
    return {"messages": [m.dict() for m in messages]}

@router.get("/messages/conversation/{user1}/{user2}")
def get_conversation(user1: str, user2: str, uow: UnitOfWork = Depends(get_uow)):
    try:
        msg_query = MessageQueryService(uow)
        conversation = msg_query.get_conversation(user1, user2)
        print(f"convo: {conversation}")
        return {"messages": [m.dict() for m in conversation]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups/{group_id}")
def get_group(group_id: str, uow: UnitOfWork = Depends(get_uow)):
    grp_query = GroupQueryService(uow)
    group = grp_query.get_group_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group.dict()

@router.get("/users/{user_id}/groups")
def get_user_groups(user_id: str, uow: UnitOfWork = Depends(get_uow)):
    try:
        group_query = GroupQueryService(uow)
        groups = group_query.get_groups_by_user_id(user_id)
        return {"groups": [group.dict() for group in groups]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==== Command Endpoints (POST/PUT/DELETE) ====

@router.post("/users")
def create_user(
    username: str = Body(...),
    email: str = Body(...),
    password: str = Body(...),
    uow: UnitOfWork = Depends(get_uow),
):
    user_command = UserCommandService(uow)
    try:
        user_dto = user_command.create_user(username, email, password)
        return user_dto.dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/messages")
def create_message(
    sender_id: str = Body(...),
    content: str = Body(...),
    reciever_user_id: str | None = Body(None),
    reciever_group_id: str | None = Body(None),
    uow: UnitOfWork = Depends(get_uow),
):
    msg_command = MessageCommandService(uow)
    try:
        message_dto = msg_command.create_message(
            sender_id, content, reciever_user_id, reciever_group_id
        )
        return message_dto.dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/messages/{message_id}")
def update_message(
    message_id: str,
    new_content: str = Body(...),
    uow: UnitOfWork = Depends(get_uow),
):
    msg_command = MessageCommandService(uow)
    try:
        message_dto = msg_command.update_message(message_id, new_content)
        return message_dto.dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/users/{user_id}")
def update_user(
    user_id: str,
    username: str = Body(...),
    email: str = Body(...),
    password: str = Body(...),
    uow: UnitOfWork = Depends(get_uow),
):
    user_command = UserCommandService(uow)
    try:
        user_dto = user_command.update_user(user_id, username, email, password)
        return user_dto.dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.delete("/users/{user_id}")
def delete_user(user_id: str, uow: UnitOfWork = Depends(get_uow)):
    user_command = UserCommandService(uow)
    try:
        user_command.delete_user(user_id)
        return {"status": "deleted", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("users/user_status/{user_id}")
def update_user_status(
    user_id: str,
    status: str = Body(...),
    uow: UnitOfWork = Depends(get_uow),
):
    user_command = UserCommandService(uow)
    try:
        user_dto = user_command.update_user_status(user_id, status)
        return user_dto.dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        

@router.delete("/messages/{message_id}")
def delete_message(message_id: str, uow: UnitOfWork = Depends(get_uow)):
    msg_command = MessageCommandService(uow)
    try:
        msg_command.delete_message(message_id)
        return {"status": "deleted", "message_id": message_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/groups")
def create_group(
    group_name: str = Body(...),
    admin_id: str = Body(...),
    group_description: str | None = Body(None),
    uow: UnitOfWork = Depends(get_uow),
):
    grp_command = GroupCommandService(uow)
    try:
        group_dto = grp_command.create_group(group_name, admin_id, group_description)
        return group_dto.dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/groups/{group_id}")
def update_group(
    group_id: str,
    group_name: str = Body(...),
    group_description: str | None = Body(None),
    uow: UnitOfWork = Depends(get_uow),
):
    grp_command = GroupCommandService(uow)
    try:
        group_dto = grp_command.update_group(group_id, group_name, group_description)
        return group_dto.dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/groups/{group_id}/add_member")
def add_group_member(
    group_id: str,
    member_id: str = Body(...),
    uow: UnitOfWork = Depends(get_uow),
):
    grp_command = GroupCommandService(uow)
    try:
        group_dto = grp_command.add_member(group_id, member_id)
        return group_dto.dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/groups/{group_id}/remove_member")
def remove_group_member(
    group_id: str,
    member_id: str = Body(...),
    uow: UnitOfWork = Depends(get_uow),
):
    grp_command = GroupCommandService(uow)
    try:
        group_dto = grp_command.remove_member(group_id, member_id)
        return group_dto.dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/direct_messages")
def create_dm_chat(
    user1_id: str = Body(...),
    user2_id: str = Body(...),
    uow: UnitOfWork = Depends(get_uow),
):
    dm_command = DirectMessageCommandService(uow)
    try:
        dm_dto = dm_command.create_dm_chat(user1_id, user2_id)
        return dm_dto.dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(
    username: str = Body(...),
    password: str = Body(...),
    uow: UnitOfWork = Depends(get_uow)
):
    try:
        # 1) Look up user by username
        user_query_service = UserQueryService(uow)
        user = user_query_service.get_user_by_username(username)
        
        # 2) If user doesn't exist or password is wrong, immediately raise 401
        if not user or not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(
            minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        )
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "username": user.username,
            "user_id": str(user.user_id) 
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            uow.close()
        except Exception:
            pass

@router.post("/logout")
async def logout(current_user: str = Depends(get_current_user)):
    # Logout at the API layer may be as simple as returning a response
    return {"message": f"User {current_user} successfully logged out"}

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# WebSocket API for persistent connection for chat app implementation
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    user_id = None
    
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            payload = data.get("payload", {})

            if action == "authenticate":
                user_id = payload.get("user_id")
                if not user_id:
                    await websocket.send_json({"error": "Invalid authentication"})
                    continue
                    
                active_connections[user_id] = websocket
                await websocket.send_json({"action": "authenticated", "status": "success"})
                continue

            if not user_id:
                await websocket.send_json({"error": "Not authenticated"})
                continue

            handler = MessageHandler(UnitOfWork())
            result = handler.handle(action, payload)

            # For new messages, broadcast to the recipient
            if action == "create_message":
                receiver_id = payload.get("reciever_user_id")
                if receiver_id and receiver_id in active_connections:
                    receiver_ws = active_connections[receiver_id]
                    try:
                        await receiver_ws.send_json({
                            "action": "new_message",
                            "payload": {
                                "sender_id": payload["sender_id"],
                                "content": payload["content"],
                                "reciever_user_id": receiver_id,
                                "timestamp": result.get("message", {}).get("timestamp")
                            }
                        })
                    except Exception as e:
                        print(f"Error sending to receiver: {e}")

            # Send confirmation back to sender
            await websocket.send_json({
                "action": action,
                "status": "success",
                "data": result
            })

    except WebSocketDisconnect:
        if user_id and user_id in active_connections:
            del active_connections[user_id]
