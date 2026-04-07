import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.models import AnonymousUser

from .services import send_message, get_or_create_conversation


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat.
    """
    
    async def connect(self):
        self.contract_id = self.scope['url_route']['kwargs']['contract_id']
        self.room_group_name = f'chat_{self.contract_id}'
        
        # Authenticate user
        self.user = await self.get_user_from_token()
        
        if isinstance(self.user, AnonymousUser):
            await self.close()
            return
        
        # Check if user is part of the contract
        is_participant = await self.is_contract_participant()
        if not is_participant:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data.get('message', '')
        
        # Save message to database
        try:
            conversation = await database_sync_to_async(
                get_or_create_conversation
            )(int(self.contract_id))
            
            message = await database_sync_to_async(send_message)(
                sender=self.user,
                conversation_id=conversation.id,
                content=message_content,
            )
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message.id,
                        'content': message.content,
                        'sender': {
                            'id': self.user.id,
                            'email': self.user.email,
                            'full_name': self.user.get_full_name(),
                        },
                        'created_at': message.created_at.isoformat(),
                    }
                }
            )
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))
    
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event['message']))
    
    @database_sync_to_async
    def get_user_from_token(self):
        """Get user from JWT token in query string."""
        query_string = self.scope.get('query_string', b'').decode()
        
        # Parse token from query string
        if 'token=' in query_string:
            token = query_string.split('token=')[1].split('&')[0]
            try:
                access_token = AccessToken(token)
                from apps.users.models import User
                return User.objects.get(id=access_token['user_id'])
            except Exception:
                pass
        
        return AnonymousUser()
    
    @database_sync_to_async
    def is_contract_participant(self):
        """Check if user is a participant in the contract."""
        from apps.bidding.models import Contract
        try:
            contract = Contract.objects.get(id=self.contract_id)
            return self.user in [
                contract.bid.freelancer,
                contract.bid.project.client
            ]
        except Contract.DoesNotExist:
            return False
