import subprocess
import argparse
import os
import uuid
import textwrap
import yt_dlp
from whisper import init_whisper, transcribe_file
import openai

audio_filename = str(uuid.uuid4())

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
    system_prompt = "You are a helpful assistant, whose sole job is to take transcripts and summarize them."
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

def whisper_transcription():
    model, enc = init_whisper("large-v2", batch_size=1)
    output = transcribe_file(model, enc, audio_filename+"_mono.mp3")
    return output

def transcribe_youtube(url):
    
    download_audio(url)
    output = whisper_transcription()
    
    with open(audio_filename+"_transcription.txt", "w") as text_file:
        text_file.write(url + "\n\n")
        text_file.write(output)

    text_file.close()
    os.remove(audio_filename+".mp3")
    os.remove(audio_filename+"_mono.mp3")
    return output
    
def summarize_youtube(transcription):
    response = summarize_bullet_points(transcription)
    summary = response.choices[0].message.content
    with open(audio_filename+"_summary.txt", "w") as text_file:
        text_file.write(summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description='Summarize YouTube videos.')
    parser.add_argument('--url', required=False, type=str, help='The URL of the YouTube video to summarize.')
    args = parser.parse_args()
    url = args.url
    if not url:
        url = input("Please enter the URL of the YouTube video to summarize: ")
    transcription = transcribe_youtube(url)
    summary = summarize_youtube(transcription)
    pretty_print(summary, 80)

if __name__ == "__main__":
    main()