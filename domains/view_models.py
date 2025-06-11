from pydantic import BaseModel
from datetime import datetime, timedelta
MESSAGE_DELETE_ALLOWED_TIME = 60 * 60

class UserDTO(BaseModel): #actual dto for api responses since it contains pw hash
    username: str
    status: str
    email: str | None 
    _id: str 
    user_id : str 
    joined_at: str | None
    updated_at: str | None

class UserDTODBO(BaseModel):
    username: str
    status: str
    email: str | None 
    _id: str 
    user_id : str
    joined_at: str | None
    updated_at: str | None
    password: str | None  #password is not returned in API responses but may be used internally

class MessageDTO(BaseModel):
    sender_id: str
    content: str
    sent_at: str
    message_id: str
    updated_at: str
    reciever_user_id: str | None = None
    reciever_group_id: str | None = None

    def delete_message(self) -> bool:
        current_time = datetime.now()
        sent_at_dt = datetime.fromisoformat(self.sent_at)  #converting string to datetime isoformat obj
        if (current_time - sent_at_dt).total_seconds() > MESSAGE_DELETE_ALLOWED_TIME:
            raise ValueError("Message delete time limit exceeded.")
        else:
            return True

class GroupDTO(BaseModel):
    group_id: str
    group_name: str
    group_description: str | None
    created_at: str
    updated_at: str
    members: list[str] = []
    admin: str | None

class DirectMessageDTO(BaseModel):
    chat_id : str
    user1_id : str
    user2_id : str
    created_at : str
    updated_at : str