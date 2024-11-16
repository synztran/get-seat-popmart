from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime as dt, timedelta
import time
import webbrowser
import unicodedata
import os
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import RetryAfter
import asyncio
import schedule
import pytz


# read from env file
load_dotenv()
TARGET_LINK = os.getenv("TARGET_LINK")
VALUE_CLOSE_ICON = os.getenv("CLOSE_ICON")
VALUE_TARGET_POSTS = os.getenv("POSTS")
VALUE_NUMBER_OF_IMAGES = os.getenv("NUMBER_IMAGE")
VALUE_PREVIOUS_BUTTON = os.getenv("PREVIOUS_BUTTON")
VALUE_LATEST_IMAGE_PARENT = os.getenv("LATEST_PARENT_IMAGE")
VALUE_LATEST_IMAGE_HAVE_QR = os.getenv("IMAGE_HAVE_QR")
VALUE_PATH_IMAGE_UPLOADED = os.getenv("PATH_IMAGE_UPLOADED")
VALUE_TEXT_SINGLE_POST = os.getenv("TEXT_SINGLE_POST")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

hanoi_tz = pytz.timezone('Asia/Ho_Chi_Minh')

map_schedule_call = [
  {
    "startTime": "09:00",
    "endTime": "09:02",
  },
  {
    "startTime": "13:00",
    "endTime": "13:02",
  },
  {
    "startTime": "13:30",
    "endTime": "13:32",
  },
  {
    "startTime": "14:00",
    "endTime": "14:02",
  },
  {
    "startTime": "14:30",
    "endTime": "14:32",
  },
  {
    "startTime": "19:00",
    "endTime": "19:02",
  },
  {
    "startTime": "19:30",
    "endTime": "19:32",
  },
  {
    "startTime": "20:00",
    "endTime": "20:02",
  },
  {
    "startTime": "20:30",
    "endTime": "20:32",
  },
  {
    "startTime": "21:00",
    "endTime": "21:02",
  },
  {
    "startTime": "21:30",
    "endTime": "21:32",
  },
]

if TARGET_LINK is None or TELEGRAM_BOT_TOKEN is None or TELEGRAM_CHAT_ID is None:
    print("Environment variables TARGET_LINK, FB_EMAIL, FB_PASSWORD, TELEGRAM_BOT_TOKEN, or TELEGRAM_CHAT_ID are not set.")
    exit(1)
else:
    print(f"TARGET_LINK: {TARGET_LINK}")

value_time_sleep_loop = 2
value_time_sleep_normal_wait = 1
value_time_sleep_re_run = 1
value_target_post_index = 0

def send_telegram_message(message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
      asyncio.run(bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message))
      # bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except RetryAfter as e:
        print(f"Flood control exceeded. Retry in {e.retry_after} seconds.")
        time.sleep(e.retry_after)
        asyncio.run(bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message))
        # bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except TimeoutError as e:
        print(f"Timeout error occurred: {e}")
        time.sleep(5)
        asyncio.run(bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message))
        # bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

def send_telegram_image(image_path):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        asyncio.run(bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=image_path, caption=""))
    except RetryAfter as e:
        print(f"Flood control exceeded. Retry in {e.retry_after} seconds.")
        time.sleep(e.retry_after)
        asyncio.run(bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=image_path, caption=""))
    except TimeoutError as e:
      print(f"Request timed out. Retrying in 5 seconds.")
      time.sleep(5)
      asyncio.run(bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=image_path, caption=""))

def normalize_text(text):
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    # Remove special characters and extra spaces
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = ' '.join(text.split())
    return text.lower()

def check_total_image(driver):
  try:
      total_image = driver.find_element(by=By.CSS_SELECTOR, value=VALUE_NUMBER_OF_IMAGES)
      if total_image:
        print("SUCCESS - Total image found: ", total_image.text, total_image)
        return total_image
      else:
        print("ERROR - Total image not found")
        return False
  except Exception as e:
      print(f"An error occurred while checking total image: {e}")

      return None

def get_post_single_image(target_post):
  # Locate images within the first post
  images = target_post.find_elements(By.TAG_NAME, "img")
  print("GET single image post - image len", len(images))
  if not images:
    print(" HAVE A ERROR - No images found in the first post")
    return False
  else:
    for image in images:
      image_src = image.get_attribute("src")
      if image_src.startswith(VALUE_PATH_IMAGE_UPLOADED):
        send_telegram_image(image_src)
        # webbrowser.open(image_src)
        return False
  return False

def get_post_normal(target_post, driver):
  total_image_in_target_post = 0
  images = target_post.find_elements(By.TAG_NAME, "img")

  for image in images:
    image_src = image.get_attribute("src")
    if image_src.startswith(VALUE_PATH_IMAGE_UPLOADED):
        total_image_in_target_post+=1

  print("--- Total_image_in_target_post: ", len(images), total_image_in_target_post) # maybe it is a video
  if total_image_in_target_post == 0:
    print("--- ERROR - No images found in the first post ---")
    return False

  if total_image_in_target_post == 1:
    print("--- SUCCESS - GET POST NORMAL ---")
    for image in images:
      image_src = image.get_attribute("src")
      if image_src.startswith(VALUE_PATH_IMAGE_UPLOADED):
        send_telegram_image(image_src)
        driver.quit()
        # webbrowser.open(image_src)
        return False
  else:
    total_image = check_total_image(driver)
    # if don't have total image, it mean post with one picture, take that picture and show up
    if not total_image:
      for image in images:
        image_src = image.get_attribute("src")
        if image_src.startswith(VALUE_PATH_IMAGE_UPLOADED):
          send_telegram_image(image_src)
          driver.quit()
          # webbrowser.open(image_src)
          return False
    else:
      first_matching_tag_a = None
      tag_a_in_post = target_post.find_elements(By.TAG_NAME, "a")
      for tag_a in tag_a_in_post:
        tag_a_href = tag_a.get_attribute("href")
        if tag_a_href.startswith("https://www.facebook.com/photo"):
          first_matching_tag_a = tag_a
          break

    if first_matching_tag_a:
      driver.execute_script("arguments[0].scrollIntoView(true);", first_matching_tag_a) # action scroll down to target post
      time.sleep(value_time_sleep_normal_wait)
      first_matching_tag_a.click() # click to open image
      time.sleep(value_time_sleep_normal_wait)
      interact_with_modal(driver)
    return False

def check_data_presence(driver):
  try:
      # Check if the required data is present
      find_target_divs = driver.find_elements(by=By.CSS_SELECTOR, value=VALUE_TARGET_POSTS)
      return bool(find_target_divs)
  except Exception as e:
      print(f"An error occurred while checking data presence: {e}")
      return False

def interact_with_modal(driver):
  try:
    previous_button_ele = driver.find_element(by=By.CSS_SELECTOR, value=VALUE_PREVIOUS_BUTTON)
    if previous_button_ele:
        previous_button_ele.click()
        time.sleep(value_time_sleep_normal_wait)
    else:
        print("--- ERROR - Previous photo button not found ---")
        return False
    latest_image_have_qr = driver.find_element(by=By.CSS_SELECTOR, value=VALUE_LATEST_IMAGE_HAVE_QR).get_attribute("src")
    if latest_image_have_qr:
        send_telegram_image(latest_image_have_qr)
        driver.quit()
        # webbrowser.open(latest_image_have_qr)
        return False
    else:
        print("--- NOT FOUND - Image QR Code note found ---")
        return False
  except Exception as e:
      print(f"An error occurred: {e}")
      return False

def find_newest_post():
  try:
      options = Options()
      options.headless = True
      options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
      options.add_argument("--disable-blink-features=AutomationControlled")
      options.add_argument("--window-size=720,2000")  # Set a standard window size
      options.add_argument("--no-sandbox")  # Useful for some CI/CD systems
      driver = webdriver.Chrome(options=options)
      driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
      driver.get(TARGET_LINK)
      driver.implicitly_wait(0.5)

      try:
        close_icon = driver.find_element(by=By.CSS_SELECTOR, value=VALUE_CLOSE_ICON)
        if close_icon:
          print("--- FOUND - Close icon login form")
          close_icon.click()
      except:
          print("--- NOT FOUND - Close icon login form ---")
          driver.get(TARGET_LINK)
          driver.implicitly_wait(1)
          driver.refresh();
          close_icon = driver.find_element(by=By.CSS_SELECTOR, value=VALUE_CLOSE_ICON)
          if close_icon:
            print("--- FOUND - Close icon login form")
            close_icon.click()

      # scroll down x time
      for i in range(1):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(value_time_sleep_normal_wait)

      # Retry mechanism
      if check_data_presence(driver):
        print("--- SUCCESS - Target Post found ---");
      else:
        print("--- ERROR - Target Post not founds ---")
        return False

      find_target_divs = driver.find_elements(by=By.CSS_SELECTOR, value=VALUE_TARGET_POSTS)
      if not find_target_divs:
        print("--- ERROR - Target Post not founds ---")
        send_telegram_message("--- ERROR - Target Post not founds ---")
        return False

      # TODO: don't forget change target index post
      first_post = find_target_divs[value_target_post_index]
      first_post_text = first_post.text
       # Get today's date and format it as dd.mm.yyyy
      target_day = dt.today() + timedelta(days=1)
      formatted_date_with_year = target_day.strftime("%d.%m.%Y") # dd/mm/yyyy
      formatted_date = target_day.strftime("%d.%m") # dd/mm
      # expected_single_image_text = f"{VALUE_TEXT_SINGLE_POST} {formatted_date_with_year}" # post with single image
      expected_single_image_text = f"{formatted_date}" # post with single image
      normalized_post_text = normalize_text(first_post_text)
      normalized_single_image_post = normalize_text(expected_single_image_text)

      print("--- Thông báo: Lấy thông tin bài post thành công ---")
      return get_post_normal(first_post, driver)

  except Exception as e:
    print(f"--- Failed to find the dynamic div: {e} ---")
    driver.quit()

def is_time_between(start_time_str, end_time_str):
    # Convert time strings to datetime objects
    current_time = dt.now()
    start_time = dt.strptime(start_time_str, "%H:%M")
    end_time = dt.strptime(end_time_str, "%H:%M")

    # Ensure the comparison includes today's date
    start_time = current_time.replace(hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0)
    end_time = current_time.replace(hour=end_time.hour, minute=end_time.minute, second=0, microsecond=0)

    # Check if current time is within the range
    return start_time <= current_time <= end_time

def is_near_checking_time(start_time_str):
  current_time = dt.now()
  start_time = dt.strptime(start_time_str, "%H:%M")
  start_time = current_time.replace(day=current_time.day, month=current_time.month, year=current_time.year, hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0)

  if start_time < current_time:
    start_time += timedelta(days=1)

  # Check if the difference between start_time and current_time is within 2 minutes
  if start_time - current_time <= timedelta(seconds=10):
    return True
  return False

def schedule_tasks():
  for schedule_item in map_schedule_call:
    start_time = schedule_item["startTime"]
    end_time = schedule_item["endTime"]
    if is_time_between(start_time, end_time):
      find_newest_post()

def send_current_time():
    now_in_hanoi = dt.now(hanoi_tz).strftime("%H:%M:%S")
    send_telegram_message(f"--- Thời gian hiện tại: {now_in_hanoi}")

def announce_near_checking_time():
  for schedule_item in map_schedule_call:
    start_time = schedule_item["startTime"]
    end_time = schedule_item["endTime"]
    if is_near_checking_time(start_time):
      send_telegram_message(f"--- Thông báo: gần đến khung giờ checking: {start_time} - {end_time} ---")

schedule.every(1).seconds.do(schedule_tasks)
schedule.every(2).seconds.do(announce_near_checking_time)
while True:
    now_in_hanoi = dt.now(hanoi_tz).strftime("%H:%M:%S")
    print(f"--- Current time in Hanoi: {now_in_hanoi} ---")
    schedule.run_pending()
    time.sleep(value_time_sleep_loop)  # Wait xx second before the next scrape
