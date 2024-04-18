import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import anthropic
from pytube import YouTube
import pyperclip

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

def summarize_text(text, prompt, api_key, max_tokens):
    try:
        # Initialize the Anthropic client
        client = anthropic.Anthropic(api_key=api_key)
        # Create a message to send to the API for summarization
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": f"{prompt}\n\n{text}"}
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

def main():
    st.set_page_config(page_title="YouTube Transcript Summarizer", page_icon=":memo:", layout="wide")

    st.title("YouTube Transcript Summarizer")

    # Add a sidebar for user inputs
    with st.sidebar:
        
        st.subheader("Input")
        api_key = st.text_input("Enter your Anthropic API key:", type="password")
        st.markdown("[Get your API key here](https://console.anthropic.com/settings/keys)")
        video_url = st.text_input("Enter the YouTube video URL:")
        max_tokens = st.slider("Select the maximum number of tokens:", min_value=100, max_value=4000, value=1000, step=100)
        st.subheader("Prompt Templates")
        prompt_templates = {
            "Summary": "Summarize the following transcript:",
            "Key Points": "What are the key points discussed in the following transcript?",
            "Outline": "Create an outline for the following transcript:",
            "Action Items": "Extract any action items or tasks mentioned in the following transcript:",
            "Questions": "What questions are raised or left unanswered in the following transcript?",
            "Emotions": "Identify the dominant emotions conveyed in the following transcript:",
            "Themes": "What are the main themes or topics covered in the following transcript?",
            "Takeaways": "What are the key takeaways or lessons learned from the following transcript?",
            "Quotes": "Extract notable quotes or statements from the following transcript:",
            "Summarize for Twitter": "Summarize the following transcript in 280 characters or less:",
            "TL;DR": "Provide a brief TL;DR (too long; didn't read) summary of the following transcript:",
            "Highlights": "What are the highlights or most important moments in the following transcript?",
            "Critique": "Provide a constructive critique of the content in the following transcript:",
            "Fact-checking": "Identify any statements in the following transcript that may require fact-checking:",
            "Opinion vs. Facts": "Distinguish between opinions and facts presented in the following transcript:",
            "Actionable Insights": "What actionable insights can be derived from the following transcript?",
            "Key Decisions": "What key decisions or conclusions are made in the following transcript?",
            "Next Steps": "Based on the following transcript, what should be the next steps or actions?",
            "Unanswered Questions": "What questions or issues are left unresolved in the following transcript?",
            "Controversial Points": "Identify any controversial or debatable points mentioned in the following transcript:",
            "Custom": st.text_area("Enter a custom prompt:")
        }
        selected_template = st.radio("Select a prompt template:", list(prompt_templates.keys()))

        if selected_template == "Custom":
            prompt = prompt_templates["Custom"]
        else:
            prompt = prompt_templates[selected_template]

        summarize_button = st.button("Summarize")

    if summarize_button:
        if video_url and api_key:
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
                    st.success("Transcript fetched successfully!")
                    st.info("Summarizing the transcript...")
                    summary_progress = st.progress(0)
                    summary = summarize_text(transcript, prompt, api_key, max_tokens)
                    summary_progress.progress(100)
                    if summary:
                        st.success("Summary of the Transcript:")
                        summary_container = st.container()
                        with summary_container:
                            summary_text = st.text_area("", value=summary, height=300)
                            copy_button = st.button("Copy Summary")
                            if copy_button:
                                pyperclip.copy(summary_text)
                                st.success("Summary copied to clipboard!")
                    else:
                        st.error("Could not generate the summary.")
                else:
                    st.error("Could not fetch the transcript.")
if __name__ == "__main__":
    main()
