import base64
import csv
import os
import json
import asyncio
import aiohttp
from slugify import slugify
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def read_csv(file_path):
    print(f"Reading CSV file: {file_path}")
    days_and_events = []
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            print(row['day'])
            days_and_events.append(row['day'])
    print(f"Days and events: {days_and_events}\n")
    print(f"Number of days and events: {len(days_and_events)}\n")
    return days_and_events


def generate_dalle_prompts(event_name):
    quantity = 3
    print(f"Generating prompts for event: {event_name}")
    slug_event_name = slugify(event_name)
    if os.path.exists(slug_event_name):
        print(f"Prompts for event {event_name} may already exist.")
        if os.path.exists(os.path.join(event_name, "prompts.txt")):
            with open(os.path.join(event_name, "prompts.txt"), 'r') as prompts_file:
                dalle_prompts = prompts_file.readlines()
                print(f"Number of prompts: {len(dalle_prompts)}\n")
                if len(dalle_prompts) > 0:
                    return dalle_prompts
    completion = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system",
             "content": f"DALLE Sticker Prompt Engineer is specialized in crafting detailed and imaginative prompts for DALLE to create stickers. Begin by describing the desired result to DALLE - explaining explicitly that it is a sticker. Use specific details and descriptive language to convey the scene, mood, objects, and any relevant actions or interactions in the sticker. This includes colors, styles, emotions, and setting. Use descriptions like 'in the style of Impressionism' or 'reminiscent of 1950s fashion.'"},
            {"role": "user", "content": f"Provide {quantity} prompts for die cut stickers. Each prompt focuses on a different theme or value of {event_name}. These prompts promote the ethos or cause it represents, without mentioning it by name. The prompts include specific visual elements and action-oriented text. Each illustration is cute, vibrant, or colorful. Instruct DALLE that the sticker includes no border around the design and a simple background."}
        ]
    )
    dalle_prompts = completion.choices[0].message.content
    dalle_prompts = dalle_prompts.strip().split('\n')
    print(f"\n{event_name}")
    print(f"Number of prompts: {len(dalle_prompts)}\n")
    for prompt in dalle_prompts[:]:
        print(prompt)
        if len(prompt) < 10:
            dalle_prompts.remove(prompt)
            continue
        # if the prompt starts with 1. 2. etc. remove the prefix
        if prompt[0].isdigit() and prompt[1] == '.':
            dalle_prompts[dalle_prompts.index(prompt)] = prompt[3:].strip()
            print(prompt[3:].strip())
        # if the first word is "Illustrate", "Design", "Create", "Make", "Illustration:", "Design:" remove it
        if prompt.split()[0] in ["Illustrate", "Design", "Create", "Make", "Illustration:", "Design:"]:
            dalle_prompts[dalle_prompts.index(prompt)] = ' '.join(prompt.split()[1:]).strip()
            print(' '.join(prompt.split()[1:]).strip())
            if prompt.split()[1] in ["of"]:
                dalle_prompts[dalle_prompts.index(prompt)] = ' '.join(prompt.split()[2:]).strip()
                print(' '.join(prompt.split()[2:]).strip())
    print(f"Number of prompts: {len(dalle_prompts)}\n")
    if len(dalle_prompts) != quantity:
        # assume it gave each prompt a title on a separate line if there are 2x quantity prompts
        if len(dalle_prompts) == 2 * quantity:
            dalle_prompts = dalle_prompts[1::2]
    if not os.path.exists(slug_event_name):
        os.makedirs(slug_event_name)
    final_prompts = [prompt.strip() for prompt in dalle_prompts if prompt]
    with open(os.path.join(slug_event_name, "prompts.txt"), 'w') as prompts_file:
        prompts_file.write('\n'.join(final_prompts))
    return final_prompts


async def generate_metadata_for_image(image_base64, event_name):
    print(f"Generating metadata for image")
    completion = openai.chat.completions.create(
        model="gpt-4-1106-vision-preview",
        messages=[
            {"role": "system",
             "content": "Generate metadata for an image. The metadata should include a title (4 to 8 words), tags (up to 15 tags, 50 characters limit, comma-separated), and a short description. Format your response as follows: Title: [Your title here] Tags: [Your tags here] Description: [Your description here]."},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": f"This image is for {event_name}."
                    }
                ],
            }
        ]
    )
    content = completion.choices[0].message.content
    content = content.strip()
    print(f"\n{content}\n")
    return content


def parse_metadata(metadata_content):
    lines = metadata_content.split('\n')
    title = lines[0].replace('Title: ', '').strip()
    tags = lines[1].replace('Tags: ', '').strip().split(', ')
    description = lines[2].replace('Description: ', '').strip()
    return title, tags, description


async def fetch_image_content_and_base64(image_uri, session):
    async with session.get(image_uri) as response:
        if response.status == 200:
            image_content = await response.read()
            # Convert image content to base64
            synthetic_image_base64 = base64.b64encode(image_content).decode('utf-8')
            return image_content, synthetic_image_base64
        else:
            raise Exception(f"Failed to fetch image from {image_uri}, status code {response.status}")


async def evaluate_image_gpt4_vision(image_base64, event_name):
    evaluation_score = None
    retry_count = 0
    max_retries = 2
    while evaluation_score is None and retry_count < max_retries:

        evaluation_response = openai.chat.completions.create(
            model="gpt-4-1106-vision-preview",
            messages=[
                {"role": "system",
                 "content": f"Evaluate if the image matches the original desired outcome. Your response must only be an integer between 0 and 100 indicating your perceived level of success."},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": f"The original intent was to create a die cut sticker design that captures the ethos of {event_name}. Please evaluate the image on a scale of 0 to 100 with no additional comments or text." if retry_count > 0 else f"The original intent was to create a die cut sticker design that captures the ethos of {event_name}."
                        }
                    ],
                }
            ]
        )
        evaluation_content = evaluation_response.choices[0].message.content
        try:
            evaluation_score = int(evaluation_content)
            print(f"Image evaluation score: {evaluation_score}")
            return evaluation_score
        except ValueError:
            print(f"Failed to evaluate image, retrying...")
            retry_count += 1
    return evaluation_score


async def process_image_and_metadata(prompt, event_name, session):
    print(f"Processing image for prompt: {prompt} and event: {event_name}")
    # check number of images, if any, in the folder for the event
    # if the number of images is greater than x (3), skip this prompt
    if os.path.exists(event_name):
        if len([name for name in os.listdir(event_name) if os.path.isfile(os.path.join(event_name, name))]) > 3:
            print(f"Skipping prompt for event {event_name} as the number of images is greater than 3.")
            return

    satisfactory = False
    iteration = 0
    max_iterations = 3

    while not satisfactory and iteration < max_iterations:
        iteration += 1
        image_response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="hd",
            n=1,
        )
        image_uri = image_response.data[0].url

        image_content, image_base64 = await fetch_image_content_and_base64(image_uri, session)
        evaluation_score = await evaluate_image_gpt4_vision(image_base64, event_name)
        if evaluation_score is not None and evaluation_score >= 70:
            satisfactory = True
            metadata_content = await generate_metadata_for_image(image_base64, event_name)
            title, tags, description = parse_metadata(metadata_content)
            title_slug = slugify(title)
            folder_name = slugify(event_name)

            async with session.get(image_uri) as response:
                image_content = await response.read()
            file_path = os.path.join(folder_name, f"{title_slug}.webp")
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            with open(file_path, 'wb') as image_file:
                image_file.write(image_content)

            metadata = {"title": title, "tags": tags, "description": description}
            with open(os.path.join(folder_name, f"{title_slug}.json"), 'w') as json_file:
                json.dump(metadata, json_file)


async def main(file_path, limit=3):
    while True:
        days_and_events = read_csv(file_path)
        if len(days_and_events) == 0:
            print("No more days and events to process.")
            break
        tasks = []

        # for testing purposes, only process the first 3 days and events
        days_and_events = days_and_events[:limit]

        async with aiohttp.ClientSession() as session:
            for day_event in days_and_events:
                for prompt in generate_dalle_prompts(day_event):
                    task = asyncio.create_task(process_image_and_metadata(prompt, day_event, session))
                    tasks.append(task)

            # Wait for all tasks to complete, with error handling for each task
            for task in tasks:
                try:
                    await task
                except Exception as e:
                    print(f"Error processing task: {e}")

            for day_event in days_and_events:
                print(f"Completed processing images for event: {day_event}\n")
                # remove that line item from the csv file
                with open(file_path, 'r') as csvfile:
                    lines = csvfile.readlines()
                with open(file_path, 'w') as csvfile:
                    for line in lines:
                        if day_event not in line:
                            csvfile.write(line)


if __name__ == "__main__":
    file_path = "days.csv"
    asyncio.run(main(file_path, 3))
