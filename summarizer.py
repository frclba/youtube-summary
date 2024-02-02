import subprocess
import argparse
import os
import uuid
import textwrap
import yt_dlp
from whisper import init_whisper, transcribe_file
import openai
from pydub import AudioSegment

audio_filename = str(uuid.uuid4())
# audio_filename = "c83f1f07-e8a0-4c61-b994-04bb994c4882"

def pretty_print(text, width):
    lines = text.splitlines()
    wrapped_lines = [textwrap.fill(line, width=width) for line in lines]
    wrapped_text = '\n'.join(wrapped_lines)
    print(wrapped_text)

def download_audio(url):
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
    print(url)
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

def summarize_bullet_points(transcript):
    client = openai.OpenAI(api_key="")
    system_prompt = "You are a helpful assistant, whose sole job is to take transcripts and summarize them. Every time you see the word sponsored or this video is sponsored, you should ignore everything that follows as it is not part of the main content."
    summarize_prompt = "Summarize the following transcript into a list of 20 bullet points.\n\n\nText: {transcript}:"

    return client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": summarize_prompt.format(num_bullet_points=15, transcript=transcript),
            }
        ],
        temperature=0.1,
        max_tokens=1000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

def whisper_transcription(chunk_filename):
    print("Transcribing ", chunk_filename, "...")
    model, enc = init_whisper("large-v2", batch_size=1)
    output = transcribe_file(model, enc, chunk_filename)
    with open(audio_filename+"_transcription.txt", "a") as text_file:
        text_file.write(output)
    return output
    
def summarize_youtube(transcription):
    response = summarize_bullet_points(transcription)
    summary = response.choices[0].message.content
    with open(audio_filename+"_summary.txt", "w") as text_file:
        text_file.write(summary)
    return summary


def get_transcription():
    with open (audio_filename+"_transcription.txt", "r") as file:
        data = file.read()
    return data

def chunk_big_file():
    audio = AudioSegment.from_mp3(audio_filename+"_mono.mp3")
    audio_length = len(audio) / 1000
    chunk_size = 7 * 60  # chunk size in seconds
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


def cleanup(num_chunks):
    os.remove(audio_filename+".mp3")
    os.remove(audio_filename+"_mono.mp3")
    for i in range(num_chunks):
        os.remove(f"chunk_{i}.mp3")

def main():
    # parser = argparse.ArgumentParser(description='Summarize YouTube videos.')
    # parser.add_argument('--url', required=False, type=str, help='The URL of the YouTube video to summarize.')
    # args = parser.parse_args()
    # url = args.url
    # if not url:
    #     url = input("Please enter the URL of the YouTube video to summarize: ")
    
    # print("Donwloading audio from YouTube...")
    # download_audio(url)
    print("chunking audio...")
    num_chunks = chunk_big_file()
    num_chunks = 7
    print("Transcribing audio... Processing ", num_chunks, " chunks")
    for i in range(num_chunks):
        chunk_filename = f"chunk_{i}.mp3"
        whisper_transcription(chunk_filename)

    print("Summarizing with GPT-4...")
    summary = summarize_youtube(get_transcription())

    print("Cleaning up...: ")
    cleanup(num_chunks)
    pretty_print(summary, 80)

if __name__ == "__main__":
    main()