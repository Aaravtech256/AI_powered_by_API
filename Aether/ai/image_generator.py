import os
import base64
from pathlib import Path

from google import genai


class ImageGenerator:

    def __init__(self, api_key):

        self.client = genai.Client(
            api_key=api_key
        )

        self.model = "gemini-3-pro-image"

        self.output_dir = Path(
            "generated_images"
        )

        self.output_dir.mkdir(
            exist_ok=True
        )

    def generate(self, prompt):

        if not prompt:
            raise ValueError(
                "Image prompt is empty."
            )

        print(
            "Generating image..."
        )

        interaction = self.client.interactions.create(

            model=self.model,

            input=prompt,

            response_format={
                "type": "image",
                "mime_type": "image/jpeg",
                "aspect_ratio": "16:9",
                "image_size": "1K"
            }
        )

        image = interaction.output_image

        if image is None:

            raise RuntimeError(
                "Gemini did not return an image."
            )

        image_data = base64.b64decode(
            image.data
        )

        filename = (
            f"aether_{len(list(self.output_dir.glob('*.jpg'))) + 1}.jpg"
        )

        path = (
            self.output_dir /
            filename
        )

        with open(path, "wb") as file:

            file.write(
                image_data
            )

        print(
            f"Image saved: {path}"
        )

        return str(path)