import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import platform
from youtube_transcript_api import YouTubeTranscriptApi
import anthropic
from pytube import YouTube
import pyperclip
from groq import Groq

def fetch_page_text(url):
    try:
        # Parse robots.txt for the target website
        rp = RobotFileParser()
        rp.set_url(urlparse(url).scheme + "://" + urlparse(url).netloc + "/robots.txt")
        rp.read()

        # Check if scraping the target URL is allowed
        if not rp.can_fetch("*", url):
            return "Access denied by robots.txt", ""

        # Set a user-agent to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")

        return soup.get_text(separator='\n', strip=True), ""

    except Exception as e:
        return str(e), ""

def fetch_transcript(video_id):
    try:
        # Fetch available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        # Get transcript for English
        transcript = transcript_list.find_transcript(['en'])
        # Fetch the actual transcript data
        transcript_data = transcript.fetch()
        # Combine all segments into a single text
        full_text = ' '.join(segment['text'] for segment in transcript_data)
        return full_text
    except Exception as e:
        st.error(f"Error fetching transcript: {e}")
        return None

def summarize_text_anthropic(text, prompt, api_key, max_tokens):
    try:
        # Initialize the Anthropic client
        client = anthropic.Anthropic(api_key=api_key)
        # Create a message to send to the API for summarization
        response = client.messages.create(
            model="claude-3-haiku-20240307",  # You can change the model here
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": f"{prompt}\n\n{text}\n\n**Aim for a summary length of approximately {max_tokens} tokens.**"}
            ]
        )
        # Assuming response.content is a list of ContentBlock objects
        if isinstance(response.content, list) and len(response.content) > 0:
            # Extract the text block from the first ContentBlock
            content_block = response.content[0].text
            return content_block
        else:
            st.warning("The response content is not in the expected format.")
            return None
    except Exception as e:
        st.error(f"Failed to get response from Anthropic API: {e}")
        return None

def get_device_data():
    device_data = {
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "version": platform.version(),
        "python_version": platform.python_version(),
    }
    return device_data

def main():
    st.set_page_config(
        page_title="Content Summarizer",
        page_icon=":memo:",
        layout="wide",
        initial_sidebar_state="expanded"  # Keep sidebar open by default
    )

    # Add custom CSS for styling
   #  with open("style.css") as f:
        # st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    st.title("Content Summarizer")

    # Add a sidebar for user inputs
    with st.sidebar:
        st.subheader("Model Selection")
        selected_model_api = st.radio("Choose API:", ["Anthropic", "Groq"], key="model_api")

        if selected_model_api == "Anthropic":
            api_key = st.text_input("Enter your Anthropic API key:", type="password", key="anthropic_api_key")
            st.markdown("[Get your API key here](https://console.anthropic.com/settings/keys)")
        elif selected_model_api == "Groq":
            groq_api_key = st.text_input("Enter your Groq API key:", type="password", key="groq_api_key")
            st.markdown("[Get your API key here](https://console.groq.com/keys)")  # Update with Groq API key link

            groq_model_options = {
                "LLaMA3 8b": "llama3-8b-8192",
                "LLaMA3 70b": "llama3-70b-8192",
                "LLaMA2 70b": "llama2-70b-4096",
                "Mixtral 8x7b": "mixtral-8x7b-32768",
                "Gemma 7b": "gemma-7b-it"
            }
            selected_groq_model = st.selectbox("Select Groq Model:", list(groq_model_options.keys()), key="groq_model")

        def update_content_type():
            st.session_state.content_type = st.session_state.selected_content_type

        content_type_options = ["YouTube Video", "Web Page"]
        selected_content_type = st.radio("Select content type:", content_type_options, key="selected_content_type", on_change=update_content_type)

        if "content_type" not in st.session_state:
            st.session_state.content_type = selected_content_type

        if st.session_state.content_type == "YouTube Video":
            video_url = st.text_input("Enter the YouTube video URL:", key="video_url")
        else:
            web_url = st.text_input("Enter the web page URL:", key="web_url")

        with st.form("input_form"):
            max_tokens = st.slider("Select the maximum number of tokens:", min_value=100, max_value=4000, value=1000, step=100, key="max_tokens")

            st.subheader("Prompt Templates")
            prompt_templates = {
                "Summary": "Summarize the following content:",
                "Key Points": "What are the key points discussed in the following content?",
                "Outline": "Create an outline for the following content:",
                "Action Items": "Extract any action items or tasks mentioned in the following content:",
                "Questions": "What questions are raised or left unanswered in the following content?",
                "Emotions": "Identify the dominant emotions conveyed in the following content:",
                "Themes": "What are the main themes or topics covered in the following content?",
                "Takeaways": "What are the key takeaways or lessons learned from the following content?",
                "Quotes": "Extract notable quotes or statements from the following content:",
                "Summarize for Twitter": "Summarize the following content in 280 characters or less:",
                "TL;DR": "Provide a brief TL;DR (too long; didn't read) summary of the following content:",
                "Highlights": "What are the highlights or most important moments in the following content?",
                "Critique": "Provide a constructive critique of the content:",
                "Fact-checking": "Identify any statements in the following content that may require fact-checking:",
                "Opinion vs. Facts": "Distinguish between opinions and facts presented in the following content:",
                "Actionable Insights": "What actionable insights can be derived from the following content?",
                "Key Decisions": "What key decisions or conclusions are made in the following content?",
                "Next Steps": "Based on the following content, what should be the next steps or actions?",
                "Unanswered Questions": "What questions or issues are left unresolved in the following content?",
                "Controversial Points": "Identify any controversial or debatable points mentioned in the following content:",
                "Custom": st.text_area("Enter a custom prompt:")
            }
            selected_template = st.radio("Select a prompt template:", list(prompt_templates.keys()), key="prompt_template")

            if selected_template == "Custom":
                prompt = st.text_area("Enter a custom prompt:", key="custom_prompt")
            else:
                prompt = prompt_templates[selected_template]

            summarize_button = st.form_submit_button("Summarize")

    main_container = st.container()

    with main_container:
        if summarize_button:
            if st.session_state.content_type == "YouTube Video" and video_url:
                try:
                    video_id = video_url.split('v=')[-1]
                    video = YouTube(video_url)
                    thumbnail_url = video.thumbnail_url
                    st.image(thumbnail_url, width=400)  # Display the video thumbnail

                    st.info("Fetching transcript...")
                    transcript_progress = st.progress(0)
                    transcript = fetch_transcript(video_id)
                    transcript_progress.progress(100)

                    if transcript:
                        st.info("Summarizing the transcript...")
                        summary_progress = st.progress(0)

                        if selected_model_api == "Anthropic" and api_key:
                            summary = summarize_text_anthropic(transcript, prompt, api_key, max_tokens)
                        elif selected_model_api == "Groq" and groq_api_key:
                            client = Groq(api_key=groq_api_key)
                            response = client.chat.completions.create(
                                messages=[
                                    {"role": "user", "content": f"{prompt}\n\n{transcript}"}
                                ],
                                model=groq_model_options[selected_groq_model]
                            )
                            summary = response.choices[0].message.content
                        else:
                            st.warning("Please enter the required API key for the selected model.")
                            summary = None

                        summary_progress.progress(100)

                        if summary:
                            st.success("Summary of the Transcript:")
                            summary_placeholder = st.empty()
                            summary_placeholder.text(summary)

                            # Use a container to prevent refresh on copy button click
                            copy_container = st.container()
                            with copy_container:
                                copy_button = st.button("Copy Summary", key="copy_button")
                                if copy_button:
                                    pyperclip.copy(summary)
                                    st.success("Summary copied to clipboard!")
                        else:
                            st.error("Could not generate the summary.")
                except Exception as e:
                    st.error(f"Error: {e}")
            elif st.session_state.content_type == "Web Page" and web_url:
                try:
                    st.info("Fetching web page content...")
                    content_progress = st.progress(0)
                    content, error = fetch_page_text(web_url)
                    content_progress.progress(100)

                    if error:
                        st.error(f"Error fetching web page content: {error}")
                    else:
                        st.info("Summarizing the web page content...")
                        summary_progress = st.progress(0)

                        if selected_model_api == "Anthropic" and api_key:
                            summary = summarize_text_anthropic(content, prompt, api_key, max_tokens)
                        elif selected_model_api == "Groq" and groq_api_key:
                            client = Groq(api_key=groq_api_key)
                            response = client.chat.completions.create(
                                messages=[
                                    {"role": "user", "content": f"{prompt}\n\n{content}"}
                                ],
                                model=groq_model_options[selected_groq_model]
                            )
                            summary = response.choices[0].message.content
                        else:
                            st.warning("Please enter the required API key for the selected model.")
                            summary = None

                        summary_progress.progress(100)

                        if summary:
                            st.success("Summary of the Web Page Content:")
                            summary_placeholder = st.empty()
                            summary_placeholder.text(summary)

                            # Use a container to prevent refresh on copy button click
                            copy_container = st.container()
                            with copy_container:
                                copy_button = st.button("Copy Summary", key="copy_button")
                                if copy_button:
                                    pyperclip.copy(summary)
                                    st.success("Summary copied to clipboard!")
                        else:
                            st.error("Could not generate the summary.")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please enter a valid URL.")

if __name__ == "__main__":
    main()
