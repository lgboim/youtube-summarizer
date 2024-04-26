# YouTube & Web Summarizer with Anthropic & Groq

YouTube Summarizer is a Streamlit application that allows users to generate summaries or Seaborn diagrams from YouTube video transcripts or web page content using Anthropic or Groq AI models.

## Demo

Check out the live demo of the YouTube Summarizer application:

[Summarizer Demo](https://youtube-summarizer-xtjw2qzjbbmgogyanyfh9j.streamlit.app/)

## Features

- Summarize YouTube video transcripts or web page content
- Generate Seaborn diagrams based on the content
- Choose between Anthropic and Groq AI models
- Customize the prompt using predefined templates or a custom prompt
- Adjust the maximum number of tokens for the generated output

## Installation

1. Clone the repository:

```bash
git clone https://github.com/lgboim/youtube-summarizer.git
```

2. Change to the project directory:

```bash
cd youtube-summarizer
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit application:

```bash
streamlit run yo.py
```

2. Open the application in your web browser.

3. Select the AI model API (Anthropic or Groq) and enter the corresponding API key.

4. Choose the content type (YouTube Video or Web Page) and enter the URL.

5. Select the desired prompt template or enter a custom prompt.

6. Choose the output type (Summary or Seaborn Diagram).

7. Click the "Generate" button to generate the output.

## Configuration

- To use the Anthropic API, you need to obtain an API key from [Anthropic](https://console.anthropic.com/settings/keys).

- To use the Groq API, you need to obtain an API key from [Groq](https://console.groq.com/keys).

## Dependencies

- streamlit
- requests
- beautifulsoup4
- youtube_transcript_api
- anthropic
- pytube
- pyperclip
- groq
- seaborn
- matplotlib

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgements

- [Anthropic](https://www.anthropic.com/) for providing the AI model API
- [Groq](https://www.groq.com/) for providing the AI model API
- [Streamlit](https://streamlit.io/) for the web application framework

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

---

Feel free to customize the content further based on your specific project details and requirements.
