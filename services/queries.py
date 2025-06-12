from typing import List
from uow import UnitOfWork
from domains.view_models import UserDTO, GroupDTO, MessageDTO, DirectMessageDTO, UserDTODBO

class UserQueryService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow  
    
    def get_user_by_id(self, user_id: str) -> UserDTO:
        user = self.uow.connection.db["users"].find_one({"user_id": user_id})
        if not user:
            return None
        return UserDTO(**user)
    
    def get_user_by_username(self, username: str) -> UserDTODBO:
        user = self.uow.connection.db["users"].find_one({"username": username})
        if not user:
            return None
        return UserDTODBO(**user)
    
    def get_all_users(self) -> list[UserDTO]:
        users = self.uow.connection.db["users"].find()
        users = [UserDTO(**user) for user in users]
        if not users:
            return []
        # Return the list of user DTOs
        return users

    def get_user_groups(self, user_id: str) -> list[GroupDTO]:
        groups = self.uow.connection.db["groups"].find({"members": user_id})
        groups = [GroupDTO(**group) for group in groups]
        if not groups:
            return []
        # Return the list of group DTOs
        return groups

    def get_user_messages(self, user_id: str) -> list[MessageDTO]:
        messages = self.uow.connection.db["messages"].find({"$or": [{"sender_id": user_id}, {"reciever_user_id": user_id}, {"reciever_group_id": user_id}]})
        messages = [MessageDTO(**message) for message in messages]
        if not messages:
            return []
        return messages
    
    def get_chats_for_user(self, user_id):
        # gets all the chats for a user which includes their groups as well as dms
        # first dms
        dms = self.uow.connection.db["direct_messages"].find({"$or": [{"user1_id": user_id}, {"user2_id": user_id}]})
        
        # now group chats
        gcs = self.uow.connection.db["groups"].find({"members": user_id})
        
        chats = {
            "direct_messages": dms.dict() if dms else None,
            "group_chats": gcs.dict() if gcs else None
        }
        
        return chats
    
    def get_all_user_statuses(self) -> list[UserDTO]:
        users = self.uow.connection.db["users"].find({}, {"user_id": 1, "username": 1, "status": 1})
        if not users:
            return []
        return [{"username": user["username"], 
             "status": user["status"], 
             "_id": user["_id"]} for user in users]


class MessageQueryService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_message_by_id(self, message_id: str) -> MessageDTO:
        message = self.uow.connection.db["messages"].find_one({"message_id": message_id})
        if not message:
            return None
        return MessageDTO(**message)

    def get_messages_by_sender(self, sender_id: str) -> list[MessageDTO]:
        messages = self.uow.connection.db["messages"].find({"sender_id": sender_id})
        messages = [MessageDTO(**message) for message in messages]
        if not messages:
            return []
        return messages
    
    def get_messages_for_user(self, user_id: str) -> list[MessageDTO]:
        messages = self.uow.connection.db["messages"].find({
            "$or": [
                {"sender_id": user_id},
                {"reciever_user_id": user_id}
            ]
        }).sort("sent_at", -1)
        return [MessageDTO(**msg) for msg in messages]
    
    def get_messages_for_group(self, group_id: str) -> list[MessageDTO]:
        messages = self.uow.connection.db["messages"].find({"reciever_group_id": group_id})
        messages = [MessageDTO(**message) for message in messages]
        if not messages:
            return []
        return messages
    
    def get_messages_for_chat(self, chat_id: str) -> list[MessageDTO]:
        messages = self.uow.connection.db["messages"].find({"$or": [{"reciever_group_id": chat_id}, {"reciever_user_id": chat_id}]})
        messages = [MessageDTO(**message) for message in messages]
        if not messages:
            return []
        return messages
    
    def get_conversation(self, user1: str, user2: str):
        messages = self.uow.connection.db["messages"].find({
            "$or": [
                {"sender_id": user1, "reciever_user_id": user2},
                {"sender_id": user2, "reciever_user_id": user1},
            ]
        }).sort("sent_at", 1)
        
        message_dtos = []
        for msg in messages:
            msg_data = {
                "message_id": msg.get("message_id"),
                "sender_id": msg.get("sender_id"),
                "content": msg.get("content"),
                "sent_at": msg.get("sent_at"),
                "updated_at": msg.get("updated_at", msg.get("sent_at")),  # Use sent_at as fallback
                "reciever_user_id": msg.get("reciever_user_id"),
                "reciever_group_id": None
            }
            message_dtos.append(MessageDTO(**msg_data))
        
        return message_dtos

class GroupQueryService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_group_by_id(self, group_id: str) -> GroupDTO:
        group = self.uow.connection.db["groups"].find_one({"group_id": group_id})
        if not group:
            return None
        return GroupDTO(**group)

    def get_groups_by_member(self, member_id: str) -> list[GroupDTO]:
        groups = self.uow.connection.db["groups"].find({"members": member_id})
        groups = [GroupDTO(**group) for group in groups]
        if not groups:
            return []
        return groups
    
    def get_all_groups(self) -> list[GroupDTO]:
        groups = self.uow.connection.db["groups"].find()
        groups = [GroupDTO(**group) for group in groups]
        if not groups:
            return []
        return groups
    
    def get_group_admin(self, group_id: str) -> UserDTO:
        group = self.uow.connection.db["groups"].find_one({"group_id": group_id})
        if not group or "admin" not in group:
            return None
        admin_id = group["admin"]
        admin = self.uow.connection.db["users"].find_one({"_id": admin_id})
        if not admin:
            return None
        return UserDTO(**admin)
    
    def get_groups_by_user_id(self, user_id: str) -> List[GroupDTO]:
        groups = self.uow.groups.get_by_member(user_id)
        return [GroupDTO.from_entity(group) for group in groups]

class DirectMessageQueryService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_direct_message_by_id(self, chat_id: str) -> DirectMessageDTO:
        chat = self.uow.connection.db["direct_messages"].find_one({"chat_id": chat_id})
        if not chat:
            return None
        return DirectMessageDTO(**chat)

    def get_direct_messages_by_user(self, user_id: str) -> list[DirectMessageDTO]:
        chats = self.uow.connection.db["direct_messages"].find({"$or": [{"user1_id": user_id}, {"user2_id": user_id}]})
        chats = [DirectMessageDTO(**chat) for chat in chats]
        if not chats:
            return []
        return chats
    
    def get_direct_messages_between_users(self, user1_id: str, user2_id: str) -> DirectMessageDTO:
        chat = self.uow.connection.db["direct_messages"].find_one({"$or": [{"user1_id": user1_id, "user2_id": user2_id}, {"user1_id": user2_id, "user2_id": user1_id}]})
        if not chat:
            return None
        return DirectMessageDTO(**chat)