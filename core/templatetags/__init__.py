from django import template
import re

register = template.Library()

@register.filter
def youtube_id(url):
    """
    Extract YouTube video ID from various URL formats
    """
    if not url:
        return None
    
    # Regular expression to match YouTube URLs
    regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    match = re.search(regex, url)
    return match.group(1) if match else None

@register.filter
def youtube_embed_url(url):
    """
    Convert YouTube URL to embed URL
    """
    video_id = youtube_id(url)
    if video_id:
        return f'https://www.youtube.com/embed/{video_id}'
    return None