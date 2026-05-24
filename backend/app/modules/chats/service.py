from app.modules.chats.repository import ChatRepository


class ChatService:
    def __init__(self, repository: ChatRepository) -> None:
        self._repository = repository

