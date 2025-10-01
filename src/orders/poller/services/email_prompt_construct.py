from ..models.email import Email, Attachment
from google.genai import types

def construct_prompt_parts(email: Email) -> list[types.Part]:
    """Construct the prompt for the Gemini API based on email content"""
    parts = []
    parts.append(types.Part(text=_construct_prompt(email)))
    for attachment in email.attachments:
        parts.append(types.Part(text=_construct_attachment_prompt(attachment)))
        parts.append(types.Part(inline_data=types.Blob(mime_type=attachment.mime_type, data=attachment.data)))
    return parts

def _construct_prompt(email: Email) -> str:
    """Construct the prompt for the Gemini API based on email content"""
    prompt = ""
    prompt += f"Email Subject: {email.subject}\n"
    prompt += f"Email Body: {email.body}\n"

    return prompt

def _construct_attachment_prompt(attachment: Attachment) -> str:
    """Construct the prompt for the Gemini API based on attachment content"""
    prompt = f"Attachment: {attachment.filename}, MIME Type: {attachment.mime_type}, Size: {attachment.size} bytes\n"
    return prompt