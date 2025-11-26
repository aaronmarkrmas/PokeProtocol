import base64
from PIL import Image
import io
import os

class ChatDisplay:
    def __init__(self):
        self.chat_history = []
        
    def handle_chat_message(self, msg):
        """Process and display incoming chat messages"""
        sender = msg.get('sender_name', 'Unknown')
        content_type = msg.get('content_type', 'TEXT')
        
        if content_type == 'TEXT':
            message_text = msg.get('message_text', '')
            self.display_text_message(sender, message_text)
            
        elif content_type == 'STICKER':
            sticker_data = msg.get('sticker_data', '')
            self.display_sticker(sender, sticker_data)
            
        # Add to chat history
        self.chat_history.append(msg)
    
    def display_text_message(self, sender, message):
        """Display a text chat message"""
        print(f"💬 [{sender}]: {message}")
        # In a GUI app, you'd update the chat UI here
        
    def display_sticker(self, sender, base64_data):
        """Display a sticker from Base64 data"""
        try:
            # Decode Base64 data
            sticker_bytes = base64.b64decode(base64_data)
            
            # Create images directory if it doesn't exist
            os.makedirs('stickers', exist_ok=True)
            
            # Save sticker to file
            filename = f"stickers/sticker_{len(self.chat_history)}.png"
            with open(filename, 'wb') as f:
                f.write(sticker_bytes)
                
            print(f"🎨 [{sender}] sent a sticker: saved as {filename}")
            
            # Optional: Display using PIL (if running in GUI environment)
            try:
                image = Image.open(io.BytesIO(sticker_bytes))
                print(f"   Sticker size: {image.size}")
                # image.show()  # Uncomment to automatically display
            except Exception as e:
                print(f"   Could not display sticker: {e}")
                
        except Exception as e:
            print(f"Error processing sticker from {sender}: {e}")
    
    def send_text_message(self, sender_name, message_text):
        """Generate a text chat message for sending"""
        return {
            'message_type': 'CHAT_MESSAGE',
            'sender_name': sender_name,
            'content_type': 'TEXT',
            'message_text': message_text
        }
    
    def send_sticker_message(self, sender_name, image_path):
        """Generate a sticker message from image file"""
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
                
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            return {
                'message_type': 'CHAT_MESSAGE',
                'sender_name': sender_name,
                'content_type': 'STICKER',
                'sticker_data': base64_data
            }
        except Exception as e:
            print(f"Error loading sticker from {image_path}: {e}")
            return None
