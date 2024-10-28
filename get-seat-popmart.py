from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime as dt, timedelta
import time
import webbrowser
import unicodedata
import os
from dotenv import load_dotenv

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
value_time_sleep_loop = 1
value_time_sleep_normal_wait = 0.6
value_time_sleep_re_run = 5

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
        print("SUCCESS - Total image found: ", total_image.text)
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
        print("SUCCESS - Post image: \n", image_src)
        webbrowser.open(image_src)
        return False
  return False

def get_post_normal(target_post, driver):
  total_image_in_target_post = 0
  images = target_post.find_elements(By.TAG_NAME, "img")
  if not images:
    print("--- HAVE A ERROR - No images found in the first post ---")
    return False

  for image in images:
    image_src = image.get_attribute("src")
    if image_src.startswith(VALUE_PATH_IMAGE_UPLOADED):
        total_image_in_target_post+=1

  print("--- Total_image_in_target_post: ", len(images), total_image_in_target_post)
  if total_image_in_target_post == 1:
    print("--- SUCCESS - GET POST NORMAL ---")
    for image in images:
      image_src = image.get_attribute("src")
      if image_src.startswith(VALUE_PATH_IMAGE_UPLOADED):
        print("--- Single image found: ", image_src)
        webbrowser.open(image_src)
        return False
  else:
    total_image = check_total_image(driver)
    # if don't have total image, it mean post with one picture, take that picture and show up
    if not total_image:
      for image in images:
        image_src = image.get_attribute("src")
        if image_src.startswith(VALUE_PATH_IMAGE_UPLOADED):
          print("--- Single Image found: ", image_src)
          webbrowser.open(image_src)
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
        print("--- Image Have QR Code: ", latest_image_have_qr)
        webbrowser.open(latest_image_have_qr)
        return False
    else:
        print("--- NOT FOUND - Image QR Code note found ---")
        return False
  except Exception as e:
      print(f"An error occurred: {e}")
      return False

def find_newest_post():
  try:
      driver = webdriver.Chrome()
      driver.get(TARGET_LINK)
      driver.implicitly_wait(0.5)

      close_icon = driver.find_element(by=By.CSS_SELECTOR, value=VALUE_CLOSE_ICON)
      if close_icon:
        print("--- FOUND - Close icon login form")
        close_icon.click()
      else:
        print("--- NOT FOUND - Close icon login form ---")

      # Retry mechanism
      if check_data_presence(driver):
        print("--- SUCCESS - Target Post found ---");
      else:
        print("--- ERROR - Target Post not founds ---")
        return False

      find_target_divs = driver.find_elements(by=By.CSS_SELECTOR, value=VALUE_TARGET_POSTS)
      if not find_target_divs:
        print("--- ERROR - Target Post not founds ---")
        return False

      # TODO: don't forget change target index post
      first_post = find_target_divs[0]
      first_post_text = first_post.text
      # Get today's date and format it as dd.mm.yyyy
      target_day = dt.today() + timedelta(days=1)
      formatted_date_with_year = target_day.strftime("%d.%m.%Y") # dd/mm/yyyy
      formatted_date = target_day.strftime("%d.%m") # dd/mm
      print("formatted_date", formatted_date, formatted_date_with_year)
      expected_single_image_text = f"{VALUE_TEXT_SINGLE_POST} {formatted_date_with_year}" # post with single image
      normalized_post_text = normalize_text(first_post_text)
      normalized_single_image_post = normalize_text(expected_single_image_text)

      if normalized_single_image_post in normalized_post_text:
        print("--- SUCCESS - Today's post has match with single image ---")
        return get_post_single_image(first_post)
      else:
        print("--- SUCCESS - Today's post has mutli image ---")
        return get_post_normal(first_post, driver)

  except Exception as e:
    print(f"--- Failed to find the dynamic div: {e} ---")
    driver.quit()
while True:
    print("___Fetching dynamic div content...")
    resp = find_newest_post()
    if resp:
      break
    time.sleep(value_time_sleep_loop)  # Wait xx second before the next scrape
