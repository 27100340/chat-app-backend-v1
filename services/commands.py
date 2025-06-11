import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from uow import UnitOfWork
from domains.view_models import UserDTO, MessageDTO, GroupDTO,DirectMessageDTO,UserDTODBO
from domains.models import User,Message,Group,DirectMessage
from typing import Optional
from datetime import datetime
import uuid
from auth import get_password_hash, verify_password

class UserCommandService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def create_user(self, username: str, email: str, password: str) -> UserDTO:
        try:
            user = User()
            hashed_pw = get_password_hash(password)
            user.create_user(username,email,hashed_pw)
            user_dto = UserDTODBO(
                username=user.username,
                status=user.status,
                email=user.email,
                _id=user._id,  # Already a string
                user_id = user.user_id,
                joined_at=user.joined_at.isoformat() if user.joined_at else None,
                updated_at=user.updated_at.isoformat() if user.updated_at else None,
                password=hashed_pw  # Store hashed password
            )
            self.uow.user_repository.save(user_dto)
            return user_dto
        except Exception as e:
            raise ValueError(f"Error creating user: {e}")
    
    def update_user(self, user_id: str, username: Optional[str], status: Optional[str], email: Optional[str]) -> UserDTO:
        user = self.uow.user_repository.get(user_id)
        if not user:
            raise ValueError("User not found")
        try:
            user.update_user_details(username, status, email)
            self.uow.user_repository.update(user_id, user)
            return user.convert_to_dto()
        except Exception as e:
            raise ValueError(f"Error updating user: {e}")

    def change_password(self, user_id: str, new_password: str) -> None:
        user = self.uow.user_repository.get(user_id)
        if not user:
            raise ValueError("User not found")
        try:
            user.change_password(get_password_hash(new_password))
            self.uow.user_repo.update(user_id, user)
        except Exception as e:
            raise ValueError(f"Error changing password: {e}")

    def delete_user(self, user_id: str) -> None:
        user = self.uow.user_repository.get(user_id)
        if not user:
            raise ValueError("User not found")
        try:
            self.uow.user_repo.delete(user_id)
        except Exception as e:
            raise ValueError(f"Unable to delete user: {e}")

class MessageCommandService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def create_message(self, sender_id: str, content: str, receiver_user_id: str | None, receiver_group_id: str | None) -> MessageDTO:
        try:
            # Verify sender exists
            sender = self.uow.user_repository.get(sender_id)
            if not sender:
                logger.error(f"Sender not found: {sender_id}")
                raise ValueError(f"Sender not found: {sender_id}")

            # Verify receiver exists if provided
            if receiver_user_id:
                receiver = self.uow.user_repository.get(receiver_user_id)
                if not receiver:
                    logger.error(f"Receiver not found: {receiver_user_id}")
                    raise ValueError(f"Receiver not found: {receiver_user_id}")

            # Create and save message
            message = Message()
            message.create_message(
                sender_id=sender_id,
                content=content,
                reciever_user_id=receiver_user_id,
                reciever_group_id=receiver_group_id
            )
            
            message_dto = message.convert_to_dto()
            self.uow.message_repository.save(message_dto)
            logger.info(f"Message created: {message_dto.message_id}")
            return message_dto
            
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            raise ValueError(f"Error creating message: {e}")

    def update_message(self, message_id: str, new_content: str) -> MessageDTO:
        message_dto = self.uow.message_repository.get(message_id, None)
        if not message_dto:
            raise ValueError("Message not found")
        try:
            # Convert DTO to domain model:
            message = Message()
            message.sender_id = message_dto.sender_id
            message.content = message_dto.content
            message.sent_at = datetime.fromisoformat(message_dto.sent_at)
            message.message_id = message_dto.message_id
            message.updated_at = datetime.fromisoformat(message_dto.updated_at)
            message.reciever_user_id = message_dto.reciever_user_id
            message.reciever_group_id = message_dto.reciever_group_id

            # Call domain method to update message content
            message.update_message_content(new_content)
            updated_dto = message.convert_to_dto()
            self.uow.message_repository.update(message_id, updated_dto)
            return updated_dto
        except Exception as e:
            raise ValueError(f"Error updating message: {e}")

    def delete_message(self, message_id: str) -> None:
        message = self.uow.message_repository.get(message_id,None)
        if not message:
            raise ValueError("Message not found")
        try:
            if message.delete_message():
                self.uow.message_repository.delete(message_id)
        except Exception as e:
            raise ValueError(f"Error deleting message: {e}")

class GroupCommandService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def create_group(self, group_name: str, admin_id: str, group_description: str = None) -> GroupDTO:
        try:
            group = Group()
            group.create_group(group_name, group_description, admin_id)
            group.add_member(admin_id)  # Add creator as first member
            group_dto = group.convert_to_dto()
            self.uow.groups_repository.save(group_dto)
            return group_dto
        except Exception as e:
            raise ValueError(f"Error creating group: {e}")

    def add_member(self, group_id: str, member_id: str) -> GroupDTO:
        group = self.uow.groups_repository.get(group_id)
        if not group:
            raise ValueError("Group not found")
        try:
            group.add_member(member_id)
            self.uow.groups_repository.update(group_id, group)
            return group.convert_to_dto()
        except Exception as e:
            raise ValueError(f"Error adding member: {e}")

    def remove_member(self, group_id: str, member_id: str) -> GroupDTO:
        group = self.uow.groups_repository.get(group_id)
        if not group:
            raise ValueError("Group not found")
        try:
            group.remove_member(member_id)
            self.uow.groups_repository.update(group_id, group)
            return group.convert_to_dto()
        except Exception as e:
            raise ValueError(f"Error removing member: {e}")

    def update_group(self, group_id: str, group_name: str = None, group_description: str = None) -> GroupDTO:
        group = self.uow.groups_repository.get(group_id)
        if not group:
            raise ValueError("Group not found")
        try:
            group.update_group_details(group_name, group_description)
            self.uow.groups_repository.update(group_id, group)
            return group.convert_to_dto()
        except Exception as e:
            raise ValueError(f"Error updating group: {e}")
        
    def change_group_admin(self, group_id: str, new_admin_id: str) -> GroupDTO:
        group = self.uow.groups_repository.get(group_id)
        if not group:
            raise ValueError("Group not found")
        try:
            group.admin = new_admin_id
            self.uow.groups_repository.update(group_id, group)
            return group.convert_to_dto()
        except Exception as e:
            raise ValueError(f"Error changing group admin: {e}")
        
    def delete_group(self, group_id: str) -> None:
        group = self.uow.groups_repository.get(group_id)
        if not group:
            raise ValueError("Group not found")
        try:
            self.uow.groups_repository.delete(group_id)
        except Exception as e:
            raise ValueError(f"Error deleting group: {e}")

class DirectMessageCommandService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def create_dm_chat(self, user1_id: str, user2_id: str) -> DirectMessageDTO:
        try:
            dm = DirectMessage()
            dm.create_dm(user1_id, user2_id)
            dm_dto = dm.convert_to_dto()
            self.uow.dm_repository.save(dm_dto)
            return dm_dto
        except Exception as e:
            raise ValueError(f"Error creating DM chat: {e}")

    def delete_dm_chat(self, chat_id: str) -> None:
        dm = self.uow.dm_repository.get(chat_id)
        if not dm:
            raise ValueError("DM chat not found")
        try:
            self.uow.dm_repository.delete(chat_id)
        except Exception as e:
            raise ValueError(f"Error deleting DM chat: {e}")







