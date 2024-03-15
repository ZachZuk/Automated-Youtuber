import praw
from praw.models import MoreComments
from gtts import gTTS
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
from moviepy.editor import VideoFileClip, ImageClip, AudioFileClip, CompositeVideoClip

import random

# Used for estimating lengths, 14 charachters is 1 sec
charToLengthRatio = 14

# Creates webdriver object
driver = webdriver.Edge()

# Creating reddit api object
reddit = praw.Reddit(
    client_id="Enter Yours",
    client_secret="Enter Yours",
    user_agent="Enter Yours",
)


# Gets post from reddit, returns array with name and comments
# Array format: 0 post url, 1 post title, rest is comments
def getPost(commentsLimit, postNum):
    # Array to store post data
    postInfo = []
    # Retrieve top posts
    top_posts = list(reddit.subreddit("AskReddit").top(time_filter='day', limit=postNum+2))
    # Loop through the retrieved posts
    for i, post in enumerate(top_posts):
        # We don't want anything crazy for now
        if post.over_18 == False:
            if i == postNum:
                # Filling the array
                postInfo.append([post.url, 0])
                postInfo.append([post.title, str(post.author)])
                # Get comments
                post.comments.replace_more(limit=0)  # Ensure all comments are loaded
                for comment in post.comments.list()[:commentsLimit]:
                    postInfo.append([comment.body, str(comment.author)])
                # Returns array
                return postInfo
        else:
            postNum += 1


# Generates audion for a post array and length limit
def generateAudio(postArray, charLimit):
    # Uses string initially so audion needs to be rendered once
    audioText = ""
    # Adds title to text string
    audioText += postArray[1][0]
    # Adds the comments with variable post array length
    for i in range(len(postArray)-2):
        audioText += postArray[i+2][0]
        if len(audioText) > charLimit:
            break
    # Renders the text as audio and saves it
    audio = gTTS(audioText, lang='en')
    audio.save('test.mp3')

def getScreenshots(postArray, retList):
    # Array to store the screenshot file names
    shots = []
    # Opens up reddit post in Selenium
    driver.get(postArray[0][0])
    # Making sure it loads?
    time.sleep(1)
    # Get screenshot for post
    post_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f"//shreddit-post[@author='{postArray[1][1]}']")))
    post_screenshot = post_element.screenshot_as_png
    with open(f"post.png", "wb") as f:
        f.write(post_screenshot)
    shots.append('post.png')
    # Get screenshots of comments
    for i in range(len(postArray)-2):
        print(f'//*[@id="comment-tree"]/shreddit-comment[{i+1}]')
        comment_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f"//shreddit-comment[@author='{postArray[i+2][1]}']")))
        driver.execute_script("arguments[0].scrollIntoView(true);", comment_element) 
        driver.execute_script("window.scrollBy(0, -50);")

        comment_screenshot = comment_element.screenshot_as_png
        with open(f"comment{i}.png", "wb") as f:
            f.write(comment_screenshot)
        shots.append(f"comment{i}.png")
    if(retList):
        return shots

def generateVideo(audioFile, screenshots, postArray, exportPath):
    # Variable to store the current time so images line up
    curTime = 0
    # List to store image duration and file names
    images = []
    # List to store imageclip objects
    imageClips = []
    # Creating the background video
    bgvid = VideoFileClip("mcbgvid.mp4")
    # Start and end times to have a random start in bg video that is the duration of audio
    startTime = random.uniform(0, bgvid.duration - AudioFileClip(audioFile).duration)
    endTime = startTime + AudioFileClip(audioFile).duration
    # Clipping the background video
    bgvid = bgvid.subclip(startTime, endTime)
    # Making the audio of the bg video the voiceover
    bgvid.audio = AudioFileClip(audioFile)
    # Filling the images list with filenames and durations
    for i in range(len(screenshots)):
        images.append((screenshots[i], len(postArray[i+1][0])/charToLengthRatio))
    # Filling the imageclips list
    for img_path, duration in images[:-1]:
        imageClips.append(ImageClip(img_path).set_duration(duration).set_start(curTime).set_position("center").resize(width=1080))
        curTime += duration
    # Doing last clip seperately to make it fill up rest of time left
    imageClips.append(ImageClip(images[len(images)-1][0]).set_duration(bgvid.duration - curTime).set_start(curTime).set_position("center").resize(width=1080))
    # Combining the images and bg vid
    bgvid = CompositeVideoClip([bgvid] + imageClips)
    # Writing video towards path
    bgvid.write_videofile(exportPath, fps=24)
    # Removing temporary files

for i in range(5):
    post = getPost(4, i)
    generateAudio(post, 60*charToLengthRatio)
    generateVideo("test.mp3", getScreenshots(post, True), post, f"final{i}.mp4")

time.sleep(5)

os.remove("test.mp3")
