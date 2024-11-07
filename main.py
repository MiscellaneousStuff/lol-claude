from pathlib import Path
import time
from mss import mss

import matplotlib.pyplot as plt
from PIL import Image
from ctypes import c_void_p

# Standard library imports
from matplotlib import patches
import base64
import json
import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
import re
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtCore import QTimer
import objc
from Cocoa import (
    NSWindow,
    NSApplication,
    NSFloatingWindowLevel,
    NSMainMenuWindowLevel,
    NSStatusWindowLevel,
    NSModalPanelWindowLevel,
    NSPopUpMenuWindowLevel,
    NSScreenSaverWindowLevel
)
from Quartz import (
    CGEventCreateMouseEvent,
    CGEventPost,
    CGEventGetLocation,  # Add this
    CGEventCreate,       # Add this
    kCGEventMouseMoved,
    kCGEventLeftMouseDown,
    kCGEventLeftMouseUp,
    kCGEventRightMouseDown,
    kCGEventRightMouseUp,
    kCGHIDEventTap,
    CGPoint,
    kCGMouseButtonLeft,
    kCGMouseButtonRight
)
import sys

# Third-party imports
import aiofiles
import pillow_heif
from PIL import Image, ImageEnhance, ImageGrab

# Register HEIF opener
pillow_heif.register_heif_opener()

# DOTENV
from dotenv import load_dotenv
load_dotenv()

# LLMs
from openai import OpenAI
from anthropic import Anthropic
gpt_client = OpenAI()
claude_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# PDF to Image
import pdf2image

# Typing
from typing import List

# Async
import aiohttp
import asyncio

# Register the HEIF opener with Pillow
pillow_heif.register_heif_opener()

# AWS Bedrock (Claude)
# from anthropic import AnthropicBedrock
# bedrock_client = AnthropicBedrock(
#     aws_access_key=os.getenv("AWS_ACCESS_KEY_ID"),
#     aws_secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
#     aws_region=os.getenv("AWS_REGION")
# )

from pdf2image import convert_from_path

import xml.etree.ElementTree as ET

async def pdf_to_images(pdf_path: str) -> List[str]:
    """
    Converts a PDF file to a list of image paths.

    This asynchronous function takes a PDF file path as input and converts each page
    of the PDF into a separate JPEG image. It uses the pdf2image library to perform
    the conversion in a separate thread to avoid blocking the event loop.

    Args:
        pdf_path (str): The file path of the PDF to be converted.

    Returns:
        List[str]: A list of file paths for the generated JPEG images, one for each
                   page of the PDF.

    Raises:
        Any exceptions raised by pdf2image.convert_from_path or image processing
        operations will be propagated.

    Note:
        This function creates temporary JPEG files in the same directory as the
        input PDF, named with the pattern "{pdf_path}_page_{page_number}.jpg".
        These files are not automatically deleted and should be managed by the caller.
    """

    # This function is CPU-bound, so we'll run it in a separate thread
    loop = asyncio.get_event_loop()
    images = await loop.run_in_executor(None, convert_from_path, pdf_path)
    
    image_paths = []
    for i, image in enumerate(images):
        image_path = f"{pdf_path}_page_{i+1}.jpg"
        # Convert to RGB before saving
        rgb_image = await loop.run_in_executor(None, lambda: image.convert('RGB'))
        await loop.run_in_executor(None, rgb_image.save, image_path, "JPEG")
        image_paths.append(image_path)
    
    return image_paths

async def claude(txt: str, path: str = "", temperature: float = 0.7):
    """
    Sends a request to the Claude AI model with text and optional image input.

    This function prepares the content for a request to the Anthropic API, including
    text and optional image data. It handles both PDF and image file inputs,
    converting PDFs to images when necessary.

    Args:
        txt (str): The text prompt to send to Claude.
        path (str, optional): Path to an image or PDF file to include in the request. Defaults to "".
        temperature (float, optional): The sampling temperature for the AI model. Defaults to 0.7.

    Returns:
        str: The response from the Claude AI model.

    Raises:
        HTTPException: If there's an error with the Anthropic API request or response.

    Note:
        This function requires the ANTHROPIC_API_KEY environment variable to be set.
    """
    path = str(path)
    content = [
        {
            "type": "text",
            "text": txt
        }
    ]
    if path:
        if path.endswith(".pdf"):
            # Convert PDF to images
            image_paths = await pdf_to_images(path)
        else:
            # For single image files
            image_paths = [path]
        for img_path in image_paths:
            # Process the image
            processed_img_path = await process_image(img_path, int(1024//1), int(768//1))
            base64_image = await encode_image(processed_img_path)
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64_image
                }
            })

    async with aiohttp.ClientSession() as session:
        try:
            start_time = time.time()
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": os.environ.get("ANTHROPIC_API_KEY"),
                    "anthropic-version": "2023-06-01"  # Add the required header
                },
                json={
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": content}],
                    "model": "claude-3-5-sonnet-20241022",
                    # "model": "claude-3-haiku-20240307",
                    "temperature": temperature,
                },
            ) as response:
                result = await response.json()
                end_time = time.time()
                total_time = end_time - start_time
                
                if response.status != 200:
                    error_message = result.get('error', {}).get('message', 'Unknown error occurred')
                    raise HTTPException(status_code=response.status, detail=f"Anthropic API error: {error_message}")
                
                if 'content' not in result or not result['content']:
                    raise HTTPException(status_code=500, detail="Unexpected response format from Anthropic API")
                
                time_to_first_token = result.get('usage', {}).get('time_to_first_token', 0)
                
                print(f"Total request time: {total_time:.2f} seconds")
                print(f"Time to first token: {time_to_first_token:.2f} seconds")
                
                return result["content"][0]["text"]
        except aiohttp.ClientError as e:
            raise HTTPException(status_code=500, detail=f"Error communicating with Anthropic API: {str(e)}")

async def process_image(image_path: str, target_width: int, target_height: int) -> str:
    """
    Process an image file by resizing it to the specified target dimensions.

    This asynchronous function takes an image file path as input and processes the image
    by resizing it to the given target width and height.

    Args:
        image_path (str): The file path of the input image.
        target_width (int): The desired width of the output image.
        target_height (int): The desired height of the output image.

    Returns:
        str: The file path of the processed image.

    The function performs the following steps:
    1. Opens the image file.
    2. Resizes the image to the target dimensions.
    3. Saves the processed image as a JPEG file.

    Note:
    - The function uses asyncio to run CPU-bound operations in a separate thread.
    - The processed image is saved with a "_processed.jpg" suffix added to the original filename.
    """
    loop = asyncio.get_event_loop()
    with await loop.run_in_executor(None, Image.open, image_path) as img:
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            # Create a white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            # Paste the image on the background using alpha channel as mask
            if img.mode == 'RGBA':
                background.paste(img, mask=img.split()[3])
            else:
                background.paste(img)
            img = background
        
        # Resize the image to the target dimensions
        # img = await loop.run_in_executor(None, img.resize, (target_width, target_height), Image.LANCZOS)
        
        output_path = f"{image_path}_processed.jpg"
        await loop.run_in_executor(None, img.save, output_path, "JPEG")
    
    return output_path

async def encode_image(image_path: str) -> str:
    """
    Encode an image file to base64 string.

    This asynchronous function takes an image file path as input and encodes
    the image data to a base64 string.

    Args:
        image_path (str): The file path of the input image.

    Returns:
        str: The base64 encoded string representation of the image.

    The function performs the following steps:
    1. Opens the image file asynchronously.
    2. Reads the binary data of the image.
    3. Encodes the binary data to a base64 string.
    4. Decodes the base64 bytes to a UTF-8 string.

    Note:
    - This function uses aiofiles for asynchronous file I/O operations.
    - The returned string is ready to be used in data URIs or for transmission.
    """
    async with aiofiles.open(image_path, "rb") as image_file:
        image_data = await image_file.read()
    
    return base64.b64encode(image_data).decode('utf-8')

def gpt(txt, path="", temperature=0.7):
    """
    Send a text prompt to the GPT model and optionally include image data.

    This function sends a text prompt to the GPT model and can include image data
    if a file path is provided. It supports both PDF and image files.

    Args:
        txt (str): The text prompt to send to the model.
        path (str, optional): The file path of an image or PDF to include. Defaults to "".
        temperature (float, optional): The sampling temperature for the model. Defaults to 0.7.

    Returns:
        str: The response content from the GPT model.

    The function performs the following steps:
    1. Prepares the content list with the text prompt.
    2. If a file path is provided:
       - For PDFs, converts pages to images.
       - For single images, uses the path directly.
    3. Processes and encodes each image.
    4. Sends the prepared content to the GPT model.
    5. Returns the model's response.

    Note:
    - The function uses external functions like pdf_to_images, process_image, and encode_image.
    - It assumes the existence of a gpt_client object for API communication.
    """
    model = "gpt-4o"
    content = [{"type": "text", "text": txt}]
    path = str(path)
    if path:
        if path.endswith(".pdf"):
            # Convert PDF to images
            image_paths = pdf_to_images(path)
        else:
            # For single image files
            image_paths = [path]
        for img_path in image_paths:
            # Process the image
            processed_img_path = process_image(img_path, scaling=1.0, target_size=(1440, 900))
            base64_image = encode_image(processed_img_path)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            })
    response = gpt_client.chat.completions.create(
        messages=[ {"role": "user", "content": content} ],
        model=model,
        temperature=temperature,
        max_tokens=4_096
    )
    msg = response.choices[0].message.content
    return msg

prompt = lambda target: f"""Give me the co-ordinates to click on {target}
Output the co-ordinates in the format of x,y like so:

<example>
Give me the co-ordinates to click on microphone button.
Output the co-ordinates in the format of x,y like so:
<thinking>
I know that the search box is located at <x>230</x> <y>440</y> coordinates
and the microphone button is located at <x>300</x> <y>440</y> to the right of the search box.
Therefore I'm going to click on the microphone button.
</thinking>
<coords>
<x>230</x>
<y>440</y>
</coords>
</example>

<task>
COMPLETE THE FOLLOWING XML. DO NOT FILL IT WITH ANY PREAMBLE, SIMPLY
INFILL THE REMAINING TEXT BASED ON THE TASK AND PROVIDED CONTEXT.

<x></x> and <y></y> MUST BOTH ONLY CONTAIN SINGLE PYTHON INTERPRETABLE INTEGER VALUES.
IF YOU CAN NOT FULFILL THE USERS TASK, RETURN <x>0</x> <y>0</y>
</task>

<coords>
<thinking>
"""

prompt_rect = lambda target: f"""Give me the co-ordinates to draw a rectangle around {target}
Output the co-ordinates in the format of x1,y1,x2,y2 like so:

<example>
Give me the co-ordinates to click on the bank details.
Output the co-ordinates in the format of x1,y1,x2,y2 like so:
<thinking>
I can see the bank details section in the image. It appears to be a rectangular area containing information such as account number, routing number, and possibly other banking information. To draw a rectangle around this section, I need to identify the top-left corner (x1, y1) and the bottom-right corner (x2, y2) of this area.

Based on the image, the coordinates of the bank details section are:
- Top-left corner (x1, y1): approximately (230, 440)
- Bottom-right corner (x2, y2): approximately (300, 500)

These coordinates will create a rectangle that encompasses the entire bank details section.

</thinking>
<coords>
<x1>230</x1>
<y1>440</y1>
<x2>300</x2>
<y2>440</y2>
</coords>
</example>

<task>
COMPLETE THE FOLLOWING XML. DO NOT FILL IT WITH ANY PREAMBLE, SIMPLY
INFILL THE REMAINING TEXT BASED ON THE TASK AND PROVIDED CONTEXT.

<x1></x1> and <y1></y1> and <x2></x2> and <y2></y2>
MUST ALL ONLY CONTAIN SINGLE PYTHON INTERPRETABLE INTEGER VALUES.
IF YOU CAN NOT FULFILL THE USERS TASK, RETURN <x1>0</x1> <y1>0</y1> <x2>0</x2> <y2>0</y2>
</task>

<coords>
<thinking>
"""

def parse_coords_rect(xml_string):
    # Extract x and y values
    x1_match = re.search(r'<x1>(\d+)', xml_string)
    y1_match = re.search(r'<y1>(\d+)', xml_string)
    x2_match = re.search(r'<x2>(\d+)', xml_string)
    y2_match = re.search(r'<y2>(\d+)', xml_string)

    if x1_match and y1_match and x2_match and y2_match:
        x1 = int(x1_match.group(1))
        y1 = int(y1_match.group(1))
        x2 = int(x2_match.group(1))
        y2 = int(y2_match.group(1))
        return x1, y1, x2, y2
    else:
        return None, None, None, None

def parse_coords(xml_string):
    # Extract x and y values
    x_match = re.search(r'<x>(\d+)', xml_string)
    y_match = re.search(r'<y>(\d+)', xml_string)

    if x_match and y_match:
        x = int(x_match.group(1))
        y = int(y_match.group(1))
        return x, y
    else:
        return None, None

def plot_rect_on_image(image_path, x1, y1, x2, y2):
    # Open the image
    img = Image.open(image_path)
    
    # Create a new figure with a smaller size (adjust dpi for Retina displays)
    plt.figure(figsize=(8, 6), dpi=100)  # Reduced figure size, explicit DPI

    # Create a new figure and axis
    fig, ax = plt.subplots()
    
    # Display the image
    ax.imshow(img)
    
    # Plot a rectangle using the provided coordinates
    rect = patches.Rectangle((x1, y1), x2 - x1, y2 - y1, linewidth=2, edgecolor='r', facecolor='none', alpha=0.7)
    ax.add_patch(rect)
    
    # Remove axis ticks
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Show the plot
    plt.show()

class OverlayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # Get screen geometry
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        self.point = None
        
        # Force window level using AppKit
        from AppKit import NSApplication, NSWindow
        NSApplication.sharedApplication()
        self.setProperty("_q_windowLevel", NSWindow.levelKey() + 2)

    def set_point(self, x, y):
        self.point = QPoint(x, y)
        self.update()
    
    def paintEvent(self, event):
        if self.point:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw red dot
            pen = QPen(QColor(255, 0, 0))
            pen.setWidth(10)
            painter.setPen(pen)
            painter.drawPoint(self.point)
            
            # Draw circle around point
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawEllipse(self.point, 20, 20)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def force_topmost(self):
        # Get the NSWindow instance
        window = self.windowHandle()
        if window is not None:
            try:
                # Convert the window ID to a proper NSWindow object
                ns_window = objc.objc_object(c_void_p=window.winId().__int__())
                if hasattr(ns_window, 'setLevel_'):
                    ns_window.setLevel_(NSScreenSaverWindowLevel)
                    ns_window.setIgnoresMouseEvents_(True)
            except Exception as e:
                print(f"Error setting window level: {e}")

    def showEvent(self, event):
        super().showEvent(event)
        self.force_topmost()

# async def take_screenshots():
#     while True:
#         # TODO: Implement screenshot capture logic here
#         # For now, just using the existing target file
#         path = str(Path(f"./dataset/{target}"))
        
#         try:
#             o = await claude(
#                 prompt("What should T1 Faker do next here? Consider the current ability cooldowns, the health of T1 Faker and nearby enemies. Also determine the position of enemy champions and minions."),
#                 path,
#                 temperature=0.0
#             )
#             print(o)
#             x, y = parse_coords(o)
#             plot_dot_on_image(f"./dataset/{target}_processed.jpg", x, y)
#         except Exception as e:
#             print(f"Error processing screenshot: {e}")
        
#         # Wait 1 second before next iteration
#         await asyncio.sleep(1)

def move_mouse_to(x: int, y: int, should_click: bool = False, right_click: bool = False):
    """
    Moves the mouse cursor to specified coordinates and optionally clicks.
    
    Args:
        x (int): Target x coordinate
        y (int): Target y coordinate 
        should_click (bool): Whether to perform a click after moving
        right_click (bool): If clicking, whether to right click instead of left click
    """
    # Create CGPoint for target coordinates
    point = CGPoint(x=x, y=y)
    
    # Get current mouse location
    current = CGEventGetLocation(CGEventCreate(None))
    
    # Create mouse movement event
    move_event = CGEventCreateMouseEvent(
        None, 
        kCGEventMouseMoved,
        point,
        kCGMouseButtonLeft
    )
    
    # Post the movement event
    CGEventPost(kCGHIDEventTap, move_event)
    
    if should_click:
        # Create mouse click events
        if right_click:
            down_event = CGEventCreateMouseEvent(
                None,
                kCGEventRightMouseDown,
                point, 
                kCGMouseButtonRight
            )
            up_event = CGEventCreateMouseEvent(
                None,
                kCGEventRightMouseUp,
                point,
                kCGMouseButtonRight
            )
        else:
            down_event = CGEventCreateMouseEvent(
                None,
                kCGEventLeftMouseDown,
                point,
                kCGMouseButtonLeft
            )
            up_event = CGEventCreateMouseEvent(
                None,
                kCGEventLeftMouseUp,
                point,
                kCGMouseButtonLeft
            )
            
        # Post the click events
        CGEventPost(kCGHIDEventTap, down_event)
        time.sleep(0.1)  # Small delay between down and up
        CGEventPost(kCGHIDEventTap, up_event)

# What should the Caitlyn do next here? Consider the current ability cooldowns, the health of Caitlyn and nearby enemies, etc.
if __name__ == "__main__":
    # output_image = "invoice.pdf"
    output_image = "screen.png"

    # Add near the start of main()
    Path("./dataset").mkdir(exist_ok=True)

    # Initialize screen capture
    sct = mss()

    async def main():
        while True:
            # Take a screenshot
            screenshot = ImageGrab.grab()

            # # Capture the primary monitor
            monitor = sct.monitors[1]  # Primary monitor
            screenshot = sct.grab(monitor)

            # # Convert to PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
            # # Save the screenshot
            path = str(Path(f"./dataset/{output_image}"))
            img.save(path)

            # path = str(Path(f"./dataset/{output_image}"))
            # screenshot.save(path)

            try:
                o = await claude(
                    prompt("Blue Buff, as denoted with the numbers above its HP bar. Click slightly underneath here to correctly click on the blue buff."),
                    path,
                    temperature=0.0
                )
                print(o)
                x, y = parse_coords(o)
                if x is not None and y is not None:
                    move_mouse_to(x, y, should_click=True, right_click=True)

                # plot_rect_on_image(f"./dataset/{output_image}_page_1.jpg_processed.jpg", x1, y1, x2, y2)
            except Exception as e:
                print(f"Error: {e}")

    asyncio.run(main())