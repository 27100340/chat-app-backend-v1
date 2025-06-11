from uow import UnitOfWork
from services.commands import (
    MessageCommandService,
    GroupCommandService,
    DirectMessageCommandService,
    UserCommandService
)
from services.queries import (
    MessageQueryService,
    GroupQueryService,
    DirectMessageQueryService,
    UserQueryService
)

class MessageHandler:
    def __init__(self,uow: UnitOfWork):
        self.uow = uow
        # Command services
        self.message_command = MessageCommandService(self.uow)
        self.group_command = GroupCommandService(self.uow)
        self.dm_command = DirectMessageCommandService(self.uow)
        self.user_command = UserCommandService(self.uow)
        # Query services
        self.message_query = MessageQueryService(self.uow)
        self.group_query = GroupQueryService(self.uow)
        self.dm_query = DirectMessageQueryService(self.uow)
        self.user_query = UserQueryService(self.uow)

    def handle(self, action: str, payload: dict) -> dict:
        """
        Dispatches the action to the appropriate handler.
        Expected actions:
            - create_message
            - update_message
            - delete_message
            - get_message_by_id
            - get_messages_by_sender
            - create_group
            - update_group
            - add_group_member
            - remove_group_member
            - create_dm_chat
            - get_user  (query user info)
        """
        try:
            if action == "create_message":
                return self.handle_create_message(payload)
            elif action == "update_message":
                return self.handle_update_message(payload)
            elif action == "delete_message":
                return self.handle_delete_message(payload)
            elif action == "get_message_by_id":
                return self.handle_get_message_by_id(payload)
            elif action == "get_messages_by_sender":
                return self.handle_get_messages_by_sender(payload)
            elif action == "create_group":
                return self.handle_create_group(payload)
            elif action == "update_group":
                return self.handle_update_group(payload)
            elif action == "add_group_member":
                return self.handle_add_group_member(payload)
            elif action == "remove_group_member":
                return self.handle_remove_group_member(payload)
            elif action == "create_dm_chat":
                return self.handle_create_dm_chat(payload)
            elif action == "get_user":
                return self.handle_get_user(payload)
            elif action == "get_all_user_statuses":
                return self.handle_get_all_user_statuses(payload)

            else:
                raise ValueError("Error : Unknown action '{}'".format(action))
        except Exception as e:
            return {"error": str(e)}

    def handle_create_message(self, payload: dict) -> dict:
        sender_id = payload.get("sender_id")
        content = payload.get("content")
        receiver_user_id = payload.get("reciever_user_id")  # Note the spelling matches frontend
        receiver_group_id = payload.get("reciever_group_id")
        
        msg_dto = self.message_command.create_message(
            sender_id,
            content,
            receiver_user_id,
            receiver_group_id
        )
        
        # Return a properly formatted response for WebSocket
        return {
            "type": "new_message",
            "message": {
                "sender_id": sender_id,
                "content": content,
                "reciever_user_id": receiver_user_id,
                "reciever_group_id": receiver_group_id,
                "timestamp": msg_dto.sent_at.isoformat() if hasattr(msg_dto, 'sent_at') else None
            }
        }

    def handle_update_message(self, payload: dict) -> dict:
        message_id = payload.get("message_id")
        new_content = payload.get("new_content")
        msg_dto = self.message_command.update_message(message_id, new_content)
        return msg_dto.dict()

    def handle_delete_message(self, payload: dict) -> dict:
        message_id = payload.get("message_id")
        self.message_command.delete_message(message_id)
        return {"status": "deleted", "message_id": message_id}

    def handle_get_message_by_id(self, payload: dict) -> dict:
        message_id = payload.get("message_id")
        msg_dto = self.message_query.get_message_by_id(message_id)
        if msg_dto:
            return msg_dto.dict()
        return {}

    def handle_get_messages_by_sender(self, payload: dict) -> dict:
        sender_id = payload.get("sender_id")
        messages = self.message_query.get_messages_by_sender(sender_id)
        return {"messages": [msg.dict() for msg in messages]}

    def handle_create_group(self, payload: dict) -> dict:
        group_name = payload.get("group_name")
        admin_id = payload.get("admin_id")
        group_description = payload.get("group_description")
        group_dto = self.group_command.create_group(group_name, admin_id, group_description)
        return group_dto.dict()

    def handle_update_group(self, payload: dict) -> dict:
        group_id = payload.get("group_id")
        group_name = payload.get("group_name")
        group_description = payload.get("group_description")
        group_dto = self.group_command.update_group(group_id, group_name, group_description)
        return group_dto.dict()

    def handle_add_group_member(self, payload: dict) -> dict:
        group_id = payload.get("group_id")
        member_id = payload.get("member_id")
        group_dto = self.group_command.add_member(group_id, member_id)
        return group_dto.dict()

    def handle_remove_group_member(self, payload: dict) -> dict:
        group_id = payload.get("group_id")
        member_id = payload.get("member_id")
        group_dto = self.group_command.remove_member(group_id, member_id)
        return group_dto.dict()

    def handle_create_dm_chat(self, payload: dict) -> dict:
        user1_id = payload.get("user1_id")
        user2_id = payload.get("user2_id")
        dm_dto = self.dm_command.create_dm_chat(user1_id, user2_id)
        return dm_dto.dict()

    def handle_get_user(self, payload: dict) -> dict:
        user_id = payload.get("user_id")
        user_dto = self.user_query.get_user_by_id(user_id)
        if user_dto:
            return user_dto.dict()
        return {}

    def handle_get_all_user_statuses(self, payload: dict) -> dict:
        users = self.user_query.get_all_user_statuses()
        return {"users": [user.dict() for user in users]}
    
# # Example usage (to be integrated with the API layer later):
# if __name__ == "__main__":
#     handler = MessageHandler()
#     # Example: Create a message
#     payload = {
#         "sender_id": "user123",
#         "content": "Hello, world!",
#         "receiver_user_id": "user456"
#     }
#     response = handler.handle("create_message", payload)
#     print(response)