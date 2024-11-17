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


def set_bg_hack(main_bg):
    # set bg name
    main_bg_ext = "png"
        
    st.markdown(
         f"""
         <style>
         .stApp {{
             background: url(data:image/{main_bg_ext};base64,{base64.b64encode(open(main_bg, "rb").read()).decode()});
             background-size: cover;
         }}
         </style>
         """,
         unsafe_allow_html=True
     )


set_bg_hack("./assets/bg_reduced.png")


if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {
            "role": "assistant",
            "content": "Hello, how can I help you today with your financial needs?",
        }
    ]
st.title("🏦 Banking chatbot")
with st.expander("What is this app about?"):
    st.warning(
        """
        This bot was created by **The Byte Squad!**
        You are currently interacting with a finance-focused chatbot, powered by OpenAI's GPT-4 API, designed to provide you with smart and personalized financial insights.
        Running on a curated dataset tailored for the financial sector, we are ready to assist you with financial management, debt repayment planning, and much more.
        """,
        icon="🤘",
    )
    st.success(
        """
        **How to use:**

        To begin, you will be asked to enter your customer ID. Since this is a small dataset, you can use one of the following sample IDs: 1, 2, 3, 4, etc.

        Once your customer ID is confirmed, you can inquire about details such as your balance, outstanding debts, loan balances, and similar financial information. Additionally, you can seek guidance on creating an effective financial plan to manage and repay your loans efficiently.

        You can enable or disable speech output using the toggle option available on the sidebar. This feature provides auditory responses to assist older users or individuals less familiar with technology, ensuring accessibility for all.
        """,
        icon="ℹ️"
    )


with st.sidebar:
    voice_bot = st.selectbox(
        "Select chatbot voice",
        ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
        help="Previews can be found [here](https://platform.openai.com/docs/guides/text-to-speech/voice-options)",
    )

    speech_on = st.toggle("Enable speech output?")

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

        if speech_on:
            with st.spinner("Generating your audio - this can take up a while"):
                text_to_speech(assistant_reply, voice_bot)

        st.session_state.chat_history.append(
            {"role": "assistant", "content": assistant_reply}
        )
