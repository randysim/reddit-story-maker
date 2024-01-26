from moviepy.editor import *
from moviepy.video.fx.all import crop
import os
from pydub import AudioSegment
import random
from scrape_reddit import get_post_data

def main():
    # post data
    post_data = get_post_data(
        subreddit="AskReddit", count=1, comment_count=10
    )

    for post in post_data:
        create_video(post)
"""
EXAMPLE POST_DATA
post_data: [
    {
        post_title: String,
        author: String,
        author_icon: String,
        subreddit: String,
        comment_count: Int,
        created: String,
        score: Int,
        content_href: String,
        img_path: String,
        audio_path: String,
        comments: [
            {
                author: String,
                score: Int,
                author_icon: String,
                content: String,
                img_path: String,
                audio_path: String
            }
        ]
    },
    ...
]
"""
def create_video(post):
    video_out = f"out/{'-'.join(post['post_title'].split(' '))}.mp4"
    print("Creating video: " + video_out)

    images = [post["img_path"]]
    audios = [post["audio_path"]]
    video_length = 60 # 60 seconds

    for comment in post["comments"]:
        images.append(comment["img_path"])
        audios.append(comment["audio_path"])

    # select a random background video
    bg_video_path = "resources/background/" + random.choice(os.listdir("resources/background"))
    video = VideoFileClip(bg_video_path)
    duration = int(video.duration)

    video_start = random.randint(0, int(duration - video_length - 10))
    video_end = video_start + 60

    video = video.subclip(video_start, video_end)
    (w, h) = video.size
    video = crop(video, width=608, height=1080, x_center=w/2, y_center=h/2)
    video = video.resize((1080, 1920))

    print("Finished cropping bg video")

    # create empty voiceover
    voiceover = AudioSegment.empty()
    current_duration = 0

    video_clips = []

    for i in range(len(images)):
        frame_image_path = images[i]
        frame_audio_path = audios[i]

        frame_audio = AudioSegment.from_mp3(frame_audio_path)
        audio_duration = frame_audio.duration_seconds

        if current_duration + audio_duration > video_length:
            # try another clip
            continue
        
        frame_image = ImageClip(frame_image_path, duration=audio_duration)
        (w, h) = frame_image.size
        scale_factor = 1080/w
        frame_image = frame_image.resize(scale_factor)

        video_clip = video.subclip(current_duration, current_duration+audio_duration)
        

        video_clip = CompositeVideoClip([video_clip, frame_image.set_position("center")], size=video_clip.size)
        voiceover += frame_audio
        current_duration += audio_duration
        video_clips.append(video_clip)
        
    
    video = concatenate_videoclips(video_clips)
    print("Finished creating resources")
    
    voiceover.export("out/voiceover.mp3", format="mp3")
    main_audio = AudioFileClip("out/voiceover.mp3")
    video = video.set_audio(main_audio)
    video.write_videofile(video_out)
    
    # delete temp files
    os.remove("out/voiceover.mp3")
    


if __name__ == "__main__":
    main()