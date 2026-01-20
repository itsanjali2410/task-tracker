from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from fastapi.responses import FileResponse
from typing import List
import os
import uuid
from datetime import datetime, timezone
from app.schemas.attachment import AttachmentResponse
from app.models.attachment import AttachmentInDB
from app.schemas.user import UserResponse
from app.db.mongodb import get_database
from app.api.deps import get_current_user

router = APIRouter(prefix="/attachments", tags=["Attachments"])

# Configuration
UPLOAD_DIR = "/app/uploads"
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

os.makedirs(UPLOAD_DIR, exist_ok=True)

def validate_file(filename: str, file_size: int) -> tuple[bool, str]:
    """Validate file extension and size"""
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
    
    if file_size > MAX_FILE_SIZE:
        return False, f"File size exceeds {MAX_FILE_SIZE / (1024*1024)}MB limit"
    
    return True, ""

@router.post("", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    task_id: str,
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Upload file attachment to a task
    - Only authenticated users can upload
    - Users must have access to the task
    """
    db = get_database()
    
    # Verify task exists and user has access
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check authorization
    if current_user.role == "team_member" and task["assigned_to"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload files to this task"
        )
    
    # Read file content to get size
    file_content = await file.read()
    file_size = len(file_content)
    
    # Validate file
    is_valid, error_msg = validate_file(file.filename, file_size)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Create attachment document
    attachment = AttachmentInDB(
        id=str(uuid.uuid4()),
        task_id=task_id,
        uploaded_by=current_user.id,
        uploaded_by_name=current_user.full_name,
        uploaded_by_email=current_user.email,
        file_name=file.filename,
        file_type=file_ext.lstrip('.'),
        file_size=file_size,
        file_path=file_path
    )
    
    # Save to database
    attachment_dict = attachment.model_dump()
    attachment_dict["uploaded_at"] = attachment_dict["uploaded_at"].isoformat()
    
    await db.attachments.insert_one(attachment_dict)
    
    return AttachmentResponse(**attachment.model_dump())

@router.get("/task/{task_id}", response_model=List[AttachmentResponse])
async def list_task_attachments(
    task_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    List all attachments for a specific task
    """
    db = get_database()
    
    # Verify task exists and user has access
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check authorization
    if current_user.role == "team_member" and task["assigned_to"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view attachments for this task"
        )
    
    # Fetch attachments
    attachments = await db.attachments.find(
        {"task_id": task_id},
        {"_id": 0}
    ).sort("uploaded_at", -1).to_list(100)
    
    # Convert datetime strings
    for attachment in attachments:
        if isinstance(attachment.get('uploaded_at'), str):
            attachment['uploaded_at'] = datetime.fromisoformat(attachment['uploaded_at'])
    
    return [AttachmentResponse(**attachment) for attachment in attachments]

@router.get("/{attachment_id}/download")
async def download_attachment(
    attachment_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Download an attachment
    """
    db = get_database()
    
    # Get attachment
    attachment = await db.attachments.find_one({"id": attachment_id}, {"_id": 0})
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    
    # Verify task access
    task = await db.tasks.find_one({"id": attachment["task_id"]}, {"_id": 0})
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated task not found"
        )
    
    # Check authorization
    if current_user.role == "team_member" and task["assigned_to"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to download this file"
        )
    
    # Check if file exists
    if not os.path.exists(attachment["file_path"]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    return FileResponse(
        path=attachment["file_path"],
        filename=attachment["file_name"],
        media_type="application/octet-stream"
    )

@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete an attachment
    - Only uploader or admin can delete
    """
    db = get_database()
    
    # Get attachment
    attachment = await db.attachments.find_one({"id": attachment_id}, {"_id": 0})
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    
    # Check authorization - only uploader or admin can delete
    if attachment["uploaded_by"] != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this attachment"
        )
    
    # Delete file from filesystem
    if os.path.exists(attachment["file_path"]):
        os.remove(attachment["file_path"])
    
    # Delete from database
    await db.attachments.delete_one({"id": attachment_id})
    
    return None
