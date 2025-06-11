import logging
from dotenv import load_dotenv
from typing import Optional
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.mongo_client import MongoClient
from bson import ObjectId
from domains.view_models import UserDTO, MessageDTO, GroupDTO, DirectMessageDTO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserRepository:
    db: Database
    collection: Collection
    client: MongoClient

    def __init__(self, connection) -> None:
        load_dotenv()
        self.connection = connection
        self.db = connection.db
        self.collection = self.db["users"]
        self.client = connection.client
        logger.info("Initialized UserRepository using collection: users")

    def save(self, user_dto: UserDTO) -> str:
        try:
            # Convert DTO to dict
            user_data = user_dto.dict(exclude_none=True)
            # Remove the _id field so we use user_id as our primary key in the DB
            if "_id" in user_data:
                del user_data["_id"]
            # Insert the document
            result = self.collection.insert_one(user_data)
            logger.info(f"User inserted (ID: {result.inserted_id}) | Data: {user_data}")
            return result.inserted_id
        except Exception as e:
            logger.error(f"Error saving user to database: {e}")
            raise Exception(f"Database error while saving user: {str(e)}")

    def get(self, user_id: str) -> Optional[UserDTO]:
        try:
            query = {"user_id": user_id}
            user_data = self.collection.find_one(query)
            if user_data:
                logger.info(f"User retrieved: {user_data}")
                return UserDTO(**user_data)
            logger.info(f"No user found with user_id: {user_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving user from database: {e}")
            raise Exception(f"Database error while retrieving user: {str(e)}")

    def get_by_username(self, username: str) -> Optional[UserDTO]:
        try:
            user_data = self.collection.find_one({"username": username})
            if user_data:
                return UserDTO(**user_data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving user by username: {e}")
            raise
            
    def update(self, user_id: str, user_dto: UserDTO) -> None:
        try:
            # Convert DTO to dict for update (remove _id field)
            user_data = user_dto.dict(exclude_unset=True, exclude_none=True)
            if "_id" in user_data:
                del user_data["_id"]
            query = {"user_id": user_id}
            result = self.collection.update_one(query, {"$set": user_data})
            logger.info(f"User updated (user_id: {user_id}) | Matched: {result.matched_count} | Modified: {result.modified_count}")
            if result.matched_count == 0:
                logger.warning(f"No user found with user_id {user_id} for update")
        except Exception as e:
            logger.error(f"Error updating user in database: {e}")
            raise Exception(f"Database error while updating user: {str(e)}")
    
    def delete(self, user_id: str) -> None:
        try:
            query = {"user_id": user_id}
            result = self.collection.delete_one(query)
            logger.info(f"User deleted (user_id: {user_id}) | Deleted count: {result.deleted_count}")
            if result.deleted_count == 0:
                logger.warning(f"No user found with user_id {user_id} for deletion")
        except Exception as e:
            logger.error(f"Error deleting user from database: {e}")
            raise Exception(f"Database error while deleting user: {str(e)}")

class MessageRepository:
    db: Database
    collection: Collection
    client: MongoClient

    def __init__(self, connection) -> None:
        load_dotenv()
        self.connection = connection
        self.db = connection.db
        self.collection = self.db["messages"]
        self.client = connection.client
        logger.info("Initialized MessageRepository using collection: messages")

    def save(self, message_dto: MessageDTO) -> str:
        try:
            message_data = message_dto.dict(exclude_none=True)
            # Ensure receiver_user_id is stored properly
            if "reciever_user_id" in message_data:
                message_data["reciever_user_id"] = str(message_data["reciever_user_id"])
            
            result = self.collection.insert_one(message_data)
            logger.info(f"Message inserted (ID: {result.inserted_id}) | Data: {message_data}")
            return result.inserted_id
        except Exception as e:
            logger.error(f"Error saving message to database: {e}")
            raise Exception(f"Database error while saving message: {str(e)}")

    def get(self, message_id: str | None, sender_id: str | None) -> Optional[MessageDTO]:
        try:
            if message_id is not None:
                message_data = self.collection.find_one({"message_id": message_id})
            elif sender_id is not None:
                message_data = self.collection.find_one({"sender_id": sender_id})
            else:
                message_data = None

            if message_data:
                logger.info(f"Message retrieved: {message_data}")
                return MessageDTO(**message_data)
            logger.info("No message found with provided criteria")
            return None
        except Exception as e:
            logger.error(f"Error retrieving message: {e}")
            raise

    def get_conversation(self, user1_id: str, user2_id: str) -> list[MessageDTO]:
        try:
            # Find messages where either user is sender and the other is receiver
            messages = self.collection.find({
                "$or": [
                    {
                        "sender_id": user1_id,
                        "reciever_user_id": user2_id
                    },
                    {
                        "sender_id": user2_id,
                        "reciever_user_id": user1_id
                    }
                ]
            }).sort("sent_at", 1)  # Sort by timestamp ascending

            return [MessageDTO(**msg) for msg in messages]
        except Exception as e:
            logger.error(f"Error retrieving conversation: {e}")
            raise

    def get_messages_for_user(self, user_id: str) -> list[MessageDTO]:
        try:
            # Find all messages where user is either sender or receiver
            messages = self.collection.find({
                "$or": [
                    {"sender_id": user_id},
                    {"reciever_user_id": user_id}
                ]
            }).sort("sent_at", -1)  # Sort by timestamp descending

            return [MessageDTO(**msg) for msg in messages]
        except Exception as e:
            logger.error(f"Error retrieving messages for user: {e}")
            raise

    def update(self, message_id: str, message_dto: MessageDTO) -> None:
        message_data = message_dto.dict()
        result = self.collection.update_one({"message_id": message_id}, {"$set": message_data})
        logger.info(f"Message updated (ID: {message_id}) | Matched: {result.matched_count} | Data: {message_data}")

    def delete(self, message_id: str) -> None:
        result = self.collection.delete_one({"message_id": message_id})
        logger.info(f"Message deleted (ID: {message_id}) | Deleted count: {result.deleted_count}")

class GroupRepository:
    db: Database
    collection: Collection
    client: MongoClient

    def __init__(self, connection) -> None:
        load_dotenv()
        self.connection = connection
        self.db = connection.db
        self.collection = self.db["groups"]
        self.client = connection.client
        logger.info("Initialized GroupRepository using collection: groups")

    def save(self, group_dto: GroupDTO) -> str:
        group_data = group_dto.dict()
        result = self.collection.insert_one(group_data)
        logger.info(f"Group inserted (ID: {result.inserted_id}) | Data: {group_data}")
        return result.inserted_id

    def get(self, group_id: str | None, member_id: str | None) -> Optional[GroupDTO]:
        if group_id is not None:
            group_data = self.collection.find_one({"group_id": group_id})
        elif member_id is not None:
            group_data = self.collection.find_one({"members": member_id})
        else:
            group_data = None

        if group_data:
            logger.info(f"Group retrieved: {group_data}")
            return GroupDTO(**group_data)
        logger.info("No group found with provided criteria")
        return None

    def update(self, group_id: str, group_dto: GroupDTO) -> None:
        group_data = group_dto.dict()
        result = self.collection.update_one({"group_id": group_id}, {"$set": group_data})
        logger.info(f"Group updated (ID: {group_id}) | Matched: {result.matched_count} | Data: {group_data}")

    def delete(self, group_id: str) -> None:
        result = self.collection.delete_one({"group_id": group_id})
        logger.info(f"Group deleted (ID: {group_id}) | Deleted count: {result.deleted_count}")

class DirectMessageRepository:
    db: Database
    collection: Collection
    client: MongoClient

    def __init__(self, connection) -> None:
        load_dotenv()
        self.connection = connection
        self.db = connection.db
        self.collection = self.db["direct_messages"]
        self.client = connection.client
        logger.info("Initialized DirectMessageRepository using collection: direct_messages")

    def save(self, direct_message_dto: DirectMessageDTO) -> str:
        dm_data = direct_message_dto.dict()
        result = self.collection.insert_one(dm_data)
        logger.info(f"DirectMessage inserted (ID: {result.inserted_id}) | Data: {dm_data}")
        return result.inserted_id

    def get(self, chat_id: str | None, user1_id: str | None, user2_id: str | None) -> Optional[DirectMessageDTO]:
        if chat_id is not None:
            dm_data = self.collection.find_one({"chat_id": chat_id})
        elif user1_id is not None:
            dm_data = self.collection.find_one({"user1_id": user1_id})
        elif user2_id is not None:
            dm_data = self.collection.find_one({"user2_id": user2_id})
        else:
            dm_data = None

        if dm_data:
            logger.info(f"DirectMessage retrieved: {dm_data}")
            return DirectMessageDTO(**dm_data)
        logger.info("No direct message found with provided criteria")
        return None

    def update(self, chat_id: str, direct_message_dto: DirectMessageDTO) -> None:
        dm_data = direct_message_dto.dict()
        result = self.collection.update_one({"chat_id": chat_id}, {"$set": dm_data})
        logger.info(f"DirectMessage updated (Chat ID: {chat_id}) | Matched: {result.matched_count} | Data: {dm_data}")

    def delete(self, chat_id: str) -> None:
        result = self.collection.delete_one({"chat_id": chat_id})
        logger.info(f"DirectMessage deleted (Chat ID: {chat_id}) | Deleted count: {result.deleted_count}")