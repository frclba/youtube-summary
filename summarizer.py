import subprocess
import argparse
import os
import uuid
import textwrap
import yt_dlp
from whisper import init_whisper, transcribe_file
import openai
import pandas as pd
from pydub import AudioSegment
from dotenv import load_dotenv
load_dotenv()


def pretty_print(text, width):
    lines = text.splitlines()
    wrapped_lines = [textwrap.fill(line, width=width) for line in lines]
    wrapped_text = '\n'.join(wrapped_lines)
    print(wrapped_text)

def download_audio(audio_filename, url):
    # Download from YouTube
    ydl_opts = {
        'outtmpl': audio_filename,
        'format': 'worstaudio',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '96',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    # Convert to mono
    command = [
        'ffmpeg',
        '-i', audio_filename + ".mp3",  # Input file
        '-ac', '1',                     # Set audio channels to 1 (mono)
        '-ab', '32k',                   # Set a lower bitrate, e.g., 32 kbps
        '-y',                           # Overwrite output file if it exists
        audio_filename + "_mono.mp3"    # Output file
    ]

    subprocess.run(command)

def summarize_bullet_points(title, transcript):
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    system_prompt = "You are a helpful assistant, whose sole job is to take transcripts and summarize them. You are helping your boss become rich and successful."
    summarize_prompt = "Summarize the following transcript. Make it as useful as possible in the context of self improvement and getting rich, this is the title of the video {title}\n\n\nThis is the Text transcript: {transcript}:"

    return client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": summarize_prompt.format(title=title, transcript=transcript),
            }
        ],
        temperature=0.1,
        max_tokens=1000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

def whisper_transcription(model, enc, chunk_filename):
    print("Transcribing ", chunk_filename, "...")
    output = transcribe_file(model, enc, chunk_filename)
    return output
    
def summarize_youtube(title, transcription):
    response = summarize_bullet_points(title, transcription)
    summary = response.choices[0].message.content
    return summary

def chunk_big_file(audio_filename):
    audio = AudioSegment.from_mp3(audio_filename+"_mono.mp3")
    audio_length = len(audio) / 1000
    chunk_size = 1 * 60
    num_chunks = int(audio_length // chunk_size)
    remaining_time = audio_length % chunk_size

    for i in range(num_chunks):
        start_time = i * chunk_size
        end_time = (i + 1) * chunk_size
        chunk = audio[start_time * 1000:end_time * 1000]
        chunk.export(f"chunk_{i}.mp3", format="mp3")

    # Handle remaining time
    if remaining_time > 0:
        start_time = num_chunks * chunk_size
        end_time = start_time + remaining_time
        chunk = audio[start_time * 1000:end_time * 1000]
        chunk.export(f"chunk_{num_chunks}.mp3", format="mp3")
        num_chunks += 1

    return num_chunks

def cleanup(audio_filename, num_chunks):
    try:
        os.remove(audio_filename+".mp3")
        os.remove(audio_filename+"_mono.mp3")
    except:
        pass
    for i in range(num_chunks):
        try:
            os.remove(f"chunk_{i}.mp3")
        except:
            continue


def main():
    parser = argparse.ArgumentParser(description='Summarize YouTube videos.')
    parser.add_argument('--url', required=False, type=str, help='The URL of the YouTube video to summarize.')
    args = parser.parse_args()
    url = args.url
    if not url:
        url = input("Please enter the URL of the YouTube video to summarize: ")
    
    video_title = str(uuid.uuid4())
    print("Donwloading audio from YouTube...")
    download_audio(video_title, url)
    print("chunking audio...")
    num_chunks = chunk_big_file(video_title)
    print("Initializing whisper...")
    model, enc = init_whisper("large-v2", batch_size=1)
    print("Transcribing audio... with", num_chunks, " chunks")
    for i in range(num_chunks):
        chunk_filename = f"chunk_{i}.mp3"
        output = whisper_transcription(model, enc, chunk_filename)
        with open(video_title+"_transcription.txt", "a") as text_file:
            text_file.write(output)

        print("Summarizing with GPT-4...")
        with open (video_title+"_transcription.txt", "r") as file:
            data = file.read()
        summary = summarize_youtube(video_title, data)
        with open(video_title+"_summary.txt", "w") as text_file:
            text_file.write(summary)

        print("Cleaning up...: ")
        cleanup(video_title, num_chunks)

if __name__ == "__main__":
    main()