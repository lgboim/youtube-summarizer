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
import seaborn as sns
import matplotlib.pyplot as plt

def fetch_page_text(url):
    try:
        rp = RobotFileParser()
        rp.set_url(urlparse(url).scheme + "://" + urlparse(url).netloc + "/robots.txt")
        rp.read()

        if not rp.can_fetch("*", url):
            return "Access denied by robots.txt", "", "", ""

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")

        title = soup.title.string if soup.title else "Untitled Page"

        og_image = (soup.find('meta', property='og:image') or {}).get('content')

        if not og_image:
          image = soup.find('img')
          og_image = image['src'] if image else None

        return soup.get_text(separator='\n', strip=True), "", title, og_image

    except Exception as e:
        return "", str(e), "", ""

def fetch_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en'])
        transcript_data = transcript.fetch()
        full_text = ' '.join(segment['text'] for segment in transcript_data)
        return full_text
    except Exception as e:
        st.error(f"Error fetching transcript: {e}")
        return None

def generate_output_anthropic(text, prompt, api_key, max_tokens, output_type):
    try:
        client = anthropic.Anthropic(api_key=api_key)
        if output_type == "Summary":
            prompt = f"{prompt}\n\n{text}\n\n**Aim for a summary length of approximately {max_tokens} tokens.**"
        else:
            prompt = f"Based on the following content, generate Python code using Seaborn to create a best relevant diagram. self exenable, easy to read and understand. not assume we have the relevant data, write all of it in the code. super impoertant - write just the code, withot any text before or after! start just with 'import', not ```python, end with plt.show(), not ```:\n\n{text}"
        
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        if isinstance(response.content, list) and len(response.content) > 0:
            content_block = response.content[0].text
            return content_block
        else:
            st.warning("The response content is not in the expected format.")
            return None
    except Exception as e:
        st.error(f"Failed to get response from Anthropic API: {e}")
        return None

def generate_output_groq(text, prompt, api_key, max_tokens, output_type, model):
    try:
        client = Groq(api_key=api_key)
        if output_type == "Summary":
            prompt = f"{prompt}\n\n{text}"
        else:
            prompt = f"Based on the following content, generate Python code using Seaborn to create a best relevant diagram. self exenable, easy to read and understand. not assume we have the relevant data, write all of it in the code. super impoertant - write just the code, withot any text before or after! start just with 'import', not ```python, end with plt.show(), not ```:\n\n{text}"
        
        response = client.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt}
            ],
            model=model
        )
        
        if response.choices and len(response.choices) > 0:
            content_block = response.choices[0].message.content
            return content_block
        else:
            st.warning("The response content is not in the expected format.")
            return None
    except Exception as e:
        st.error(f"Failed to get response from Groq API: {e}")
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
        initial_sidebar_state="expanded"
    )

    #with open("style.css") as f:
        #st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    st.title("Content Summarizer")
    
    with st.sidebar:
        st.subheader("Model Selection")
        selected_model_api = st.radio("Choose API:", ["Anthropic", "Groq"], key="model_api")

        if selected_model_api == "Anthropic":
            api_key = st.text_input("Enter your Anthropic API key:", type="password", key="anthropic_api_key")
            st.markdown("[Get your API key here](https://console.anthropic.com/settings/keys)")
        elif selected_model_api == "Groq":
            groq_api_key = st.text_input("Enter your Groq API key:", type="password", key="groq_api_key")
            st.markdown("[Get your API key here](https://console.groq.com/keys)")

            groq_model_options = {
                "Mixtral 8x7b": "mixtral-8x7b-32768",
                "LLaMA3 8b": "llama3-8b-8192",
                "LLaMA3 70b": "llama3-70b-8192",
                "LLaMA2 70b": "llama2-70b-4096",
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
            summarize_button = st.form_submit_button(label="Generate")
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
                "Custom": ""
            }
            selected_template = st.radio("Select a prompt template:", list(prompt_templates.keys()), key="prompt_template")

            if selected_template == "Custom":
                custom_prompt = st.text_area("Enter your custom prompt:", key="custom_prompt")
                prompt = custom_prompt
            else:
                prompt = prompt_templates[selected_template]

            st.write("Prompt:", prompt)

            output_type = st.radio("Select output type:", ["Summary", "Seaborn Diagram"], key="output_type")

    main_container = st.container()
    output = ""
    with main_container:
        if summarize_button:
            if st.session_state.content_type == "YouTube Video" and video_url:
                try:
                    video_id = video_url.split('v=')[-1]
                    video = YouTube(video_url)
                    thumbnail_url = video.thumbnail_url
                    st.image(thumbnail_url, width=400)

                    st.info("Fetching transcript...")
                    transcript_progress = st.progress(0)
                    transcript = fetch_transcript(video_id)
                    transcript_progress.progress(100)

                    if transcript:
                        st.info("Generating output...")
                        output_progress = st.progress(0)

                        if selected_model_api == "Anthropic" and api_key:
                            output = generate_output_anthropic(transcript, prompt, api_key, max_tokens, output_type)
                        elif selected_model_api == "Groq" and groq_api_key:
                            output = generate_output_groq(transcript, prompt, groq_api_key, max_tokens, output_type, groq_model_options[selected_groq_model])
                        else:
                            st.warning("Please enter the required API key for the selected model.")
                            output = None

                        output_progress.progress(100)

                        if output:
                            if output_type == "Summary":
                                st.success("Summary of the Transcript:")
                                st.write(output)
                            else:
                                st.success("Seaborn Diagram:")
                                try:
                                    exec(output)
                                    st.pyplot(plt)
                                except Exception as e:
                                    st.error(f"Error executing the generated code: {e}")
                                    st.code(output, language="python")
                        else:
                            st.error("Could not generate the output.")
                except Exception as e:
                    st.error(f"Error: {e}")
            elif st.session_state.content_type == "Web Page" and web_url:
                try:
                    st.info("Fetching web page content...")
                    content_progress = st.progress(0)
                    content, error, title, image_url = fetch_page_text(web_url)
                    content_progress.progress(100)
                    if title:
                        st.subheader(title)
                    if image_url:
                        st.image(image_url, width=400)

                    if error:
                        st.error(f"Error fetching web page content: {error}")
                    else:
                        st.info("Generating output...")
                        output_progress = st.progress(0)

                        if selected_model_api == "Anthropic" and api_key:
                            output = generate_output_anthropic(content, prompt, api_key, max_tokens, output_type)
                        elif selected_model_api == "Groq" and groq_api_key:
                            output = generate_output_groq(content, prompt, groq_api_key, max_tokens, output_type, groq_model_options[selected_groq_model])
                        else:
                            st.warning("Please enter the required API key for the selected model.")
                            output = None

                        output_progress.progress(100)

                        if output:
                            if output_type == "Summary":
                                st.success("Summary of the Web Page Content:")
                                st.write(output)
                            else:
                                st.success("Seaborn Diagram:")
                                try:
                                    exec(output)
                                    st.pyplot(plt)
                                except Exception as e:
                                    st.error(f"Error executing the generated code: {e}")
                                    st.code(output, language="python")
                        else:
                            st.error("Could not generate the output.")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please enter a valid URL.")

if __name__ == "__main__":
    main()
