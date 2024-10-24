import streamlit as st
from openai import OpenAI
from openai.types.beta.assistant_stream_event import ThreadMessageDelta
from openai.types.beta.threads.text_delta_block import TextDeltaBlock
import re
import base64

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
ASSISTANT_ID = st.secrets["ASSISTANT_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)
assistant = client.beta.assistants.retrieve(assistant_id=ASSISTANT_ID)


def clean_response(text):
    # Remove citation-like markers such as
    cleaned_text = re.sub(r"【\d+:\d+†source】", "", text)
    return cleaned_text


def text_to_speech(text, voice):
    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice=voice,
        input=text,
    ) as response:
        response.stream_to_file("speech.mp3")
    audio_file = open("speech.mp3", "rb")

    # Convert speech to base64 encoding
    speech_base64 = base64.b64encode(audio_file.read()).decode("utf-8")
    md = f"""
        <audio id="audioTag" controls autoplay>
        <source src="data:audio/mp3;base64,{speech_base64}" type="audio/mpeg" format="audio/mpeg">
        </audio>
        """
    st.markdown(
        md,
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="Banking Chatbot", page_icon="💬", layout="centered")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {
            "role": "assistant",
            "content": "How can I support your financial needs today?",
        }
    ]
st.title("🏦 Banking chatbot")
with st.expander('About this app'):
    st.info(
        """
        This bot is created by **The Byte Squad!** \n
        You’re now interacting with our finance-focused chatbot powered by OpenAI’s GPT-4 API, designed to assist you with smart, personalized financial insights. 
        Running on a synthetic dataset tailored for the financial sector, we're here to help you manage your finances, plan debt repayment, and more.
        """,
        icon="🤘",
    )

with st.sidebar:
    voice_bot = st.selectbox(
        "Choosing chatbot's voice",
        ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
        help="Previews can be found [here](https://platform.openai.com/docs/guides/text-to-speech/voice-options)"
    )

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_query := st.chat_input("Input a prompt..."):
    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
    with st.chat_message("user"):
        st.markdown(user_query)
    st.session_state.chat_history.append({"role": "user", "content": user_query})

    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id, role="user", content=user_query
    )

    with st.chat_message("assistant"):
        stream = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id, assistant_id=ASSISTANT_ID, stream=True
        )

        assistant_reply_box = st.empty()

        assistant_reply = ""

        for event in stream:
            if isinstance(event, ThreadMessageDelta):
                if isinstance(event.data.delta.content[0], TextDeltaBlock):
                    assistant_reply_box.empty()
                    assistant_reply += clean_response(
                        event.data.delta.content[0].text.value
                    )
                    assistant_reply_box.markdown(assistant_reply)
        
        with st.spinner('Generating your audio - this can take up a while'):
            text_to_speech(assistant_reply, voice_bot)

        st.session_state.chat_history.append(
            {"role": "assistant", "content": assistant_reply}
        )
