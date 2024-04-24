# Auto-Sticker-Generator

Welcome to the Auto-Sticker-Generator, an innovative tool powered by OpenAI technologies, including GPT for text generation and DALL-E for image creation. This tool automatically generates stickers based on input themes such as holidays and specific days.

## Features

- **Day-Based Sticker Generation:** Generates stickers by identifying key attributes of days and special events.
- **Holiday Themes:** Utilizes historical holiday data to create festive and relevant stickers.
- **OpenAI Integration:** Leverages the capabilities of GPT and DALL-E models to produce textual and visual content.

## Installation

To get started with Auto-Sticker-Generator, follow these steps:

1. Clone the repository:
    ```bash
    git clone https://github.com/Cfomodz/Auto-Sticker-Generator.git
    cd Auto-Sticker-Generator
    ```
2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3. Set up the environment variables:
  Copy the .env_example file to .env and adjust the variables to match your configuration needs.

## Usage
To run the Auto-Sticker-Generator, execute the main script:
  ```bash
  python gpt_dalle_loop.py
  ```

The script will process input data from days.csv and holiday_history.json, generate text using GPT, and create corresponding stickers using DALL-E.

## Contributing
Contributions to the Auto-Sticker-Generator are welcome! Here's how you can contribute:
  Submit Bugs and Feature Requests: Feel free to open an issue if you encounter a bug or have a suggestion for improving the tool.
  Pull Requests: If you have made improvements or added new features, please submit a pull request with a clear description of your changes.

## License
  This project is licensed under the GPL-3.0 license - see the LICENSE file for details.

Acknowledgments
OpenAI for the amazing technologies that power this project.
Contributors and community for their ongoing support.
Thank you for your interest in Auto-Sticker-Generator! Let's create something amazing together.
