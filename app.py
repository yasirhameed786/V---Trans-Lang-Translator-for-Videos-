from flask import Flask, render_template, request, send_file
from moviepy.editor import VideoFileClip, AudioFileClip
from moviepy.audio.fx.all import audio_fadein, audio_fadeout
from googletrans import Translator
from gtts import gTTS
import os
import speech_recognition as sr

app = Flask(__name__)

# Mapping of language codes to their names
LANGUAGES = {
    'ta': 'Tamil',
    'en': 'English',
    'fr': 'French',
    'es': 'Spanish',
    'ml': 'Malayalam',  # Add Malayalam
    'hi': 'Hindi',      # Add Hindi
    'te': 'Telugu',     # Add Telugu
    'de': 'German',     # Add German
    'kn': 'Kannada',    # Add Kannada
}

@app.route('/')
def index():
    return render_template('index.html', languages=LANGUAGES)

@app.route('/process_video', methods=['POST'])
def process_video():
    try:
        # Get file path, language, etc., from HTML form
        video_path = request.files['video_path']
        target_language_code = request.form['target_language']

        # Save the uploaded video file
        video_filename = "uploaded_video.mp4"
        video_path.save(video_filename)

        # Transcribe and Translate
        transcribed_text = transcribe_audio(video_filename)

        # Get the language name for display in the result page
        target_language_name = LANGUAGES.get(target_language_code, target_language_code)

        translated_text = translate_text(transcribed_text, target_language_code)

        # Convert translated text to audio
        output_audio_path = "output.mp3"
        convert_text_to_audio(translated_text, output_path=output_audio_path)

        # Create a duplicate video without audio
        duplicate_video_path = "duplicate_video.mp4"
        create_duplicate_video(video_filename, duplicate_video_path)

        # Merge audio into duplicate video
        merged_video_path = "merged_video.mp4"
        merge_audio_into_video(duplicate_video_path, output_audio_path, output_path=merged_video_path)

        result_message = "Process completed successfully."
        return render_template('result.html', result_message=result_message,
                               target_language=target_language_name)
    except Exception as e:
        error_message = f"Error: {e}"
        return render_template('result.html', error_message=error_message)

@app.route('/download_video')
def download_video():
    processed_video_path = "merged_video.mp4"
    return send_file(processed_video_path, as_attachment=True)

def transcribe_audio(video_path):
    recognizer = sr.Recognizer()

    video_clip = VideoFileClip(video_path)
    audio_clip = video_clip.audio

    temp_audio_path = "audio.wav"

    # Use write_audiofile to save the audio as a temporary WAV file
    audio_clip.write_audiofile(temp_audio_path)

    with sr.AudioFile(temp_audio_path) as source:
        audio_data = recognizer.record(source)

    transcription = recognizer.recognize_google(audio_data)
    return transcription

def translate_text(text, target_language='ta'):
    translator = Translator()
    translation = translator.translate(text, dest=target_language)
    return translation.text

def convert_text_to_audio(text, output_path="output.mp3", lang='en'):
    tts = gTTS(text=text, lang=lang)
    tts.save(output_path)

def create_duplicate_video(original_video_path, duplicate_video_path):
    original_clip = VideoFileClip(original_video_path)

    # Duplicate the original clip without audio
    duplicate_clip = original_clip.copy()
    duplicate_clip = duplicate_clip.set_audio(None)

    # Write the duplicated clip to a new video file without audio
    duplicate_clip.write_videofile(duplicate_video_path, codec="libx264", audio_codec="aac", remove_temp=True)

def merge_audio_into_video(video_path, audio_path, output_path="merged_video.mp4"):
    video_clip = VideoFileClip(video_path)
    audio_clip = AudioFileClip(audio_path)

    # Ensure the audio and video clips have the same duration
    min_duration = min(video_clip.duration, audio_clip.duration)
    video_clip = video_clip.subclip(0, min_duration)
    audio_clip = audio_clip.subclip(0, min_duration)

    # Set the audio of the video clip to the provided audio clip
    video_clip = video_clip.set_audio(audio_clip)

    # Write the combined video with audio to a new file
    video_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", remove_temp=True)

    # If needed, fade in and fade out the audio
    final_audio_clip = audio_fadein(audio_fadeout(audio_clip, 2), 2)
    final_audio_clip.write_audiofile("final_audio.mp3")

if __name__ == "__main__":
    app.run(debug=True)
