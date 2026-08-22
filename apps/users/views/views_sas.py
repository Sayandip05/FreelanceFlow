import logging
import uuid
import os
from datetime import datetime, timedelta, timezone
from django.conf import settings
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

logger = logging.getLogger("apps.users.views_sas")

class GenerateUploadSASTokenView(APIView):
    """
    POST /api/users/sas-token/
    Generates a secure Azure SAS upload URL (PUT) and a read public URL.
    If Azure is not configured, returns local fallback indicators.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        image_type = request.data.get("image_type", "avatar")  # "avatar" or "banner"
        filename = request.data.get("filename", "image.jpg")
        
        if image_type not in ("avatar", "banner"):
            return Response({"error": "Invalid image_type"}, status=status.HTTP_400_BAD_REQUEST)
            
        user = request.user
        ext = os.path.splitext(filename)[1].lower() or ".jpg"
        unique_name = f"{uuid.uuid4().hex}{ext}"
        relative_path = f"{image_type}s/{user.id}/{unique_name}"
        
        connection_string = getattr(settings, 'AZURE_STORAGE_CONNECTION_STRING', '')
        container_name = getattr(settings, 'AZURE_CONTAINER_NAME', 'media')
        
        if connection_string:
            try:
                from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
                
                blob_service = BlobServiceClient.from_connection_string(connection_string)
                account_name = blob_service.account_name
                account_key = blob_service.credential.account_key
                
                # 15 minutes write window
                expiry_write = datetime.now(timezone.utc) + timedelta(minutes=15)
                sas_token_write = generate_blob_sas(
                    account_name=account_name,
                    container_name=container_name,
                    blob_name=relative_path,
                    account_key=account_key,
                    permission=BlobSasPermissions(write=True, create=True),
                    expiry=expiry_write,
                )
                upload_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{relative_path}?{sas_token_write}"
                
                # 1 year read window
                expiry_read = datetime.now(timezone.utc) + timedelta(days=365)
                sas_token_read = generate_blob_sas(
                    account_name=account_name,
                    container_name=container_name,
                    blob_name=relative_path,
                    account_key=account_key,
                    permission=BlobSasPermissions(read=True),
                    expiry=expiry_read,
                )
                public_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{relative_path}?{sas_token_read}"
                
                return Response({
                    "is_local": False,
                    "upload_url": upload_url,
                    "public_url": public_url,
                    "relative_path": relative_path,
                })
            except Exception as e:
                logger.error("Failed to generate Azure SAS token: %s", e)
                
        # Local fallback details
        return Response({
            "is_local": True,
            "upload_url": "/users/upload-image/",
            "image_type": image_type,
        })
