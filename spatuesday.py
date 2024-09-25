import sys
import sounddevice as sd
import numpy as np
import subprocess
import serial
import os
import json
import ollama
from scipy.io.wavfile import write
import whisper_timestamped as whisper
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.embeddings import OllamaEmbeddings
from langchain.vectorstores import Chroma
from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import (
    BaseChatMessageHistory,
    InMemoryChatMessageHistory,
)
from langchain_core.messages import HumanMessage


# Initialize Arduino connection
def init_arduino(port='/dev/ttyACM0'):
    try:
        arduino = serial.Serial(port, 9600)
        return arduino
    except serial.SerialException as e:
        print(f"Error connecting to Arduino: {e}")
        sys.exit(1)

arduino = init_arduino()

# Parameters
sample_rate = 44100
output_file = "one2/outputkeith2.wav"
recording = False
audio_data = []

# Setup ChromaDB for long-term memory
embeddings = OllamaEmbeddings(model="nomic-embed-text")
chroma_db = Chroma(embedding_function=embeddings, persist_directory="./chroma_db")
memory = ConversationBufferMemory()

# Callback function for recording audio
def audio_callback(indata, frames, time, status):
    if recording:
        audio_data.append(indata.copy())

# Function to handle distance sensor input
def handle_distance_sensor():
    global recording, audio_data
    while True:
        if arduino.in_waiting > 0:
            sensor_value = arduino.readline().decode().strip()
            if sensor_value == '1' and not recording:
                audio_data.clear()
                recording = True
                print("Recording started...")
            elif sensor_value == '0' and recording:
                recording = False
                print("Recording stopped.")
                break

# Function to control servo based on volume of the speech
def control_servo(volume):
    servo_position = int(np.clip(volume * 5, 0, 180))
    arduino.write(f"{servo_position}\n".encode())

# Cleanup resources
def cleanup():
    if arduino.is_open:
        arduino.close()
    print("Cleaned up resources.")

# Function to speak text and control servo based on volume
def speak(text, voice='en-us+f3', speed=200, pitch=99):
    process = subprocess.Popen(['espeak', '-v', voice, '-s', str(speed), '-p', str(pitch), text], stdout=subprocess.PIPE)

    def speak_callback(indata, frames, time, status):
        volume_norm = np.linalg.norm(indata) * 10
        control_servo(volume_norm)

    with sd.InputStream(callback=speak_callback):
        while process.poll() is None:
            sd.sleep(100)

    control_servo(0)  # Reset servo
    print("Speaking finished.")

# Function to split text into chunks
def split_into_chunks(text, chunk_size=500):
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

system_prompt = '''You are a bad friend.
    
    Context: {context}'''
    
prompt = ChatPromptTemplate.from_messages(
    [
        ('system', system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ] # This is passed directly
)

history = InMemoryChatMessageHistory()
 #formatted_prompt = prompt.format(context=context, user_input=user_input)
def get_session_history() -> BaseChatMessageHistory:
    return history
model = ChatOllama(model="buzzy")
chain = prompt | model
with_message_history = RunnableWithMessageHistory(chain, get_session_history, input_messages_key="messages")

# Function to handle transcription and chatbot response
def transcribe_and_respond():
    if len(audio_data) == 0:
        return
    audio_data_np = np.concatenate(audio_data, axis=0)
    write(output_file, sample_rate, audio_data_np)
    print(f"Audio saved to {output_file}")

    audio = whisper.load_audio(output_file)
    model = whisper.load_model("tiny", device="cpu")
    result = whisper.transcribe(model, audio, language="en")
    print(result)
    
    if result['text'] == '':
        return

    conversation = [
        {'role': 'system', 'content': 'You are a bad friend.'},
        {'role': 'user', 'content': result['text']}
    ]

    json_file_path = os.path.join("one2", "outputkeith2.json")
    with open(json_file_path, 'w') as json_file:
        json.dump(result, json_file, indent=2, ensure_ascii=False)
    print(f"JSON file created: {json_file_path}")

    # Split the result text into chunks for memory processing
    chunks = split_into_chunks(result['text'], 500)  # Adjust this function to your needs
    for chunk in chunks:
        chroma_db.add_texts([chunk], metadatas=[{"speaker": "user"}])

    # Retrieve context from long-term memory
    related_context = chroma_db.similarity_search(result['text'], k=5)

    # Create the prompt template correctly without multiple 'input_variables' issues
    
    context = " ".join([doc.page_content for doc in related_context])
    print(context)

    # Initialize and run the conversation chain
    print(','.join([h.content for h in history.messages]))
    # Run the conversation chain and respond
    #response = chain.run(context=context, user_input=result['text'])
    response = with_message_history.invoke({'context':context, 'messages':[HumanMessage(content=result['text'])]}, config={"configurable": {"session_id": None}})
    print(response.content)
    speak(response.content, voice='en-us', speed=80, pitch=40)

# Main loop
def main():
    while True:
        print("Move your hand close to the sensor to start recording. Move it away to stop.")
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16', callback=audio_callback):
            handle_distance_sensor()

        transcribe_and_respond()

        #print("Move your hand close to the sensor to record again or press 'Esc' to exit.")
        #handle_distance_sensor()

if __name__ == "__main__":
    main()
