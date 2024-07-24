from flask import Flask, request, render_template, send_file,url_for
from openai import OpenAI
from tempfile import NamedTemporaryFile
from moviepy.editor import *
import requests
import os
app = Flask(__name__)
with open('API_KEY', 'r') as f:
    api_key = f.read()


client = OpenAI(api_key = api_key)




def generate(word):
    # generate  text
    messages = [{"role":"system", "content":"You are a information giving bot"}]
    messages.append({"role": "assistant", "content": f"give information about {word}"})
    response = client.chat.completions.create(
            model = "gpt-3.5-turbo",
            messages = messages
        )
    response_message = response.choices[0].message.content

    # generate audio

    audio_data = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input= response_message)


    with NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
        temp_audio_file.write(audio_data.read())
        temp_audio_path = temp_audio_file.name
    
    # generate images
    image_paths = []
    p = f"generate images for {word}"
    img_data = client.images.generate(model="dall-e-2",
                                    prompt=p,
                                    size="1024x1024",
                                    quality="standard",
                                    n=3)

    for img in img_data.data:
        image_url = img.url

        image_data = requests.get(image_url).content

        with NamedTemporaryFile(delete=False, suffix=".mp3") as temp_image_file:
            temp_image_file.write(image_data)
            temp_image_path = temp_image_file.name
            image_paths.append(temp_image_path)

    # generate shorts
    audio = AudioFileClip(temp_audio_path, buffersize=200000)
    audio_duration = audio.duration

    frame_size = audio_duration/len(image_paths)
    img_clip = [ImageSequenceClip([i], durations= [frame_size]) for i in image_paths]

    final_clip = concatenate_videoclips(img_clip, method= 'compose')




    final_clip = final_clip.set_audio(audio)

    static_dir = os.path.join(app.root_path, 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)

    output_path = os.path.join(static_dir, f'{word}.mp4')
    final_clip.write_videofile(output_path, fps=24)

    return output_path


@app.route('/', methods=['GET', 'POST'])
def index():
    video_url = None
    if request.method == 'POST':
        word = request.form['word']
        video_path = generate(word) 
        video_url = url_for('static', filename=os.path.basename(video_path))


    return render_template('index.html', video_url = video_url)



if __name__ == "__main__":
    app.run(debug = True)