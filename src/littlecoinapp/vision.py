"""OpenAI vision-based coin identification."""

import base64
import mimetypes
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from littlecoinapp.models import CoinIdentity

SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def identify_coin(image_path: Path, model: str) -> CoinIdentity:
    if not image_path.is_file():
        raise ValueError(f"Image file does not exist: '{image_path}'")

    media_type, _ = mimetypes.guess_type(image_path.name)
    if media_type not in SUPPORTED_IMAGE_TYPES:
        supported = ", ".join(sorted(SUPPORTED_IMAGE_TYPES))
        raise ValueError(
            f"Unsupported image type for '{image_path}'. Supported types: {supported}"
        )

    image_data = base64.b64encode(image_path.read_bytes()).decode("ascii")
    image_url = f"data:{media_type};base64,{image_data}"

    load_dotenv()
    client = OpenAI()
    response = client.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Identify the coin shown in the image. Report only details "
                    "that are visible or well-supported. Use null for unknown "
                    "attributes. Do not invent a market price or claim a "
                    "certified condition grade. Include uncertainty in the "
                    "description and set confidence from 0 to 1."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Identify the coin and describe its visible condition.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url, "detail": "high"},
                    },
                ],
            },
        ],
        response_format=CoinIdentity,
    )

    if not response.choices:
        raise ValueError("The vision service returned no response.")

    message = response.choices[0].message
    if message.refusal:
        raise ValueError(f"The vision service refused the request: {message.refusal}")
    if message.parsed is None:
        raise ValueError("The vision service returned no structured coin identification.")
    return message.parsed
