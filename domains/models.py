import uuid as uuid
from datetime import datetime
from domains.view_models import UserDTO, MessageDTO, GroupDTO, DirectMessageDTO

DEFAULT_STATUS = "Hi I just joined Baqir's chat app!"
MESSAGE_EDIT_ALLOWED_TIME = 60 #seconds
MESSAGE_DELETE_ALLOWED_TIME = 120 #seconds

class User():
    def __init__(self):
        self.username = None
        self.status = None
        self._id = None
        self.user_id = None
        self.joined_at = None
        self.updated_at = None
        self.email = None
        self.password = None

    def create_user(self, username: str, email: str, password: str) -> None:
        self.username = username
        self.status = DEFAULT_STATUS
        # Generate a string ID instead of a UUID object
        self._id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())
        self.joined_at = datetime.now()
        self.updated_at = datetime.now()
        self.email = email
        self.password = password

    def change_password(self, new_password: str) -> None:
        self.password = new_password
        self.updated_at = datetime.now()

    def update_user_details(self, username: str | None, status: str | None, email: str | None) -> None:
        if username is not None:
            self.username = username
        if status is not None:
            self.status = status
        if email is not None:
            self.email = email
        self.updated_at = datetime.now()

    def check_password(self, password: str) -> bool:
        # Compares password hashes
        if self.password == password:
            return True
        else:
            return False
        
    def delete_user(self) -> None:
        # To be handled in repo layer
        pass

    def convert_to_dto(self) -> UserDTO:
        user_dto = UserDTO(
            username=self.username,
            status=self.status,
            email=self.email,
            _id=self._id,  # Already a string
            user_id = self.user_id,
            joined_at=self.joined_at.isoformat() if self.joined_at else None,
            updated_at=self.updated_at.isoformat() if self.updated_at else None
        )
        return user_dto

class Message():
    def __init__(self):
        pass

    def create_message(self, sender_id: str, content: str,reciever_user_id : str | None,reciever_group_id: str|None) -> None:
        self.sender_id = sender_id
        self.content = content
        self.sent_at = datetime.now()
        self.message_id = str(uuid.uuid4())
        self.updated_at = datetime.now()
        self.reciever_user_id = reciever_user_id
        self.reciever_group_id = reciever_group_id

    def update_time_checker(self) -> bool:
        current_time = datetime.now()
        if (current_time - self.sent_at).total_seconds() > MESSAGE_EDIT_ALLOWED_TIME:
            return False
        else:
            return True

    def update_message_content(self, new_content: str) -> None:
        if not self.update_time_checker():
            raise ValueError("Message edit time limit exceeded.")
        else:
            if not new_content:
                raise ValueError("Content cannot be empty.")
            else:
                self.content = new_content
                self.updated_at = datetime.now()

    def delete_message(self) -> bool:
        current_time = datetime.now()
        if (current_time - self.sent_at).total_seconds() > MESSAGE_DELETE_ALLOWED_TIME:
            raise ValueError("Message delete time limit exceeded.")
        else:
            return True
        
    def convert_to_dto(self) -> MessageDTO:
        message_dto = MessageDTO(
            sender_id=self.sender_id,
            content=self.content,
            sent_at=self.sent_at.isoformat(),
            message_id=str(self.message_id),
            updated_at=self.updated_at.isoformat(),
            reciever_user_id=self.reciever_user_id,
            reciever_group_id=self.reciever_group_id
        )
        return message_dto

class Group():
    def __init__(self):
        pass

    def create_group(self, group_name: str, group_description: str | None, admin_id: str | None) -> None:
        self.group_id = str(uuid.uuid4())
        self.group_name = group_name
        self.group_description = group_description
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.members = []
        self.admin_id = admin_id

    def add_member(self, member_id: str) -> None:
        if member_id not in self.members:
            self.members.append(member_id)
            self.updated_at = datetime.now()
        else:
            raise ValueError("Member already exists in the group.")
    
    def remove_member(self, member_id: str) -> None:
        if member_id in self.members:
            self.members.remove(member_id)
            self.updated_at = datetime.now()
        else:
            raise ValueError("Member does not exist in the group.")
    
    def update_group_details(self, group_name: str | None, group_description: str | None) -> None:
        if group_name is not None:
            self.group_name = group_name
        if group_description is not None:
            self.group_description = group_description
        self.updated_at = datetime.now()
    
    def convert_to_dto(self) -> GroupDTO:
        group_dto = GroupDTO(
            group_id=str(self.group_id),
            group_name=self.group_name,
            group_description=self.group_description,
            created_at=self.created_at.isoformat(),
            updated_at=self.updated_at.isoformat(),
            members=self.members,
            admin=self.admin_id
        )
        return group_dto

class DirectMessage():
    def __init__(self):
        pass

    def create_dm(self, user1_id: str, user2_id: str) -> None:
        self.chat_id = str(uuid.uuid4())
        self.user1_id = user1_id
        self.user2_id = user2_id
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def convert_to_dto(self) -> DirectMessageDTO:
        dm_dto = DirectMessageDTO(
            chat_id = str(self.chat_id),
            user1_id = self.user1_id,
            user2_id = self.user2_id,
            created_at = self.created_at.isoformat(),
            updated_at = self.updated_at.isoformat()
        )
        return dm_dto

            
         


    

