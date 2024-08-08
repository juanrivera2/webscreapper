from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import streamlit as st
import re 
from collections import Counter
from matplotlib import pyplot as plt
from streamlit_star_rating import st_star_rating
from datetime import date

#sets our page so that images can fit into the UI.
st.set_page_config(layout="wide")
## Functions that once data is scrapped it cleans it up to be passed to UI.
def convert_tofloat(str1):
    val1 =0.0
    valtab= []
    valtab = re.findall(r'\d+\.?\d*', str1)
    if valtab == []:
        val1 = 0.0
    else: val1 = valtab[0]
        
    return float(val1)
    
def convert_tofloatrate(str2):
    x1=0.0
    numbers = re.findall(r'\d+\.?\d*', str2)
    if numbers == []:
        x1 = 0.0
    else : x1=numbers[0]
    
    return float(x1)
    
def convert_stock(string_av):
    number1 = 0.0
    val = []
    if string_av == "In Stock": # En Stock In Stock
        number1 = 15.0
    elif string_av == "Not Available":
        number1 = 0.0
    else: 
        val = re.findall(r'\d+\.?\d*', string_av)
        if val == []:
            number1 = 0.0
        else: number1 = val[0]
    
    return float(number1)
    

def convert_delivery(string_del):
    number2 = 0.0
    listnum= []
    today = str(date.today())
    listt = []
    if string_del == "Not Available":
        number2 = 0.0
    else: 
        listnum = re.findall(r'\d+\.?\d*', string_del)
        listt = re.findall(r'\d+\.?\d*', today)
        if listnum == []: 
            number2 = 0.0
        else: number2 = float(listnum[0]) - float(listt[2])

    return float(number2)
### end of functions that clean up the scrapped data.

# Function to extract Product Title
def get_title(soup):
    try:
        
        title = soup.find("span", attrs={"id": 'productTitle'})
        title_value = title.text
        title_string = title_value.strip()
    except AttributeError:
        title_string = ""
    return title_string

# Function to extract Product Price, priceblock_ourprice

def get_price(soup):
    try:
        price = soup.find("span", attrs={'class': 'a-price'})
        price = price.find("span").string.strip()
    except AttributeError:
        try:
            price = soup.find("span", attrs={'class': 'a-price'})
            price = price.find("span").string.strip()
        except:
            price = ""
    return convert_tofloat(price)

# Function to extract Product Rating
def get_rating(soup):
    try:
        rating = soup.find("i", attrs={'class': 'a-icon a-icon-star a-star-4-5'}).string.strip()
    except AttributeError:
        try:
            rating = soup.find("span", attrs={'class': 'a-icon-alt'}).string.strip()
        except:
            rating = ""
    return convert_tofloatrate(rating)

# Function to extract Number of User Reviews
def get_review_count(soup):
    try:
        review_count = soup.find("span", attrs={'id': 'acrCustomerReviewText'}).string.strip()
    except AttributeError:
        review_count = ""
    return convert_tofloat(review_count)

# Function to extract Availability Status
def get_availability(soup):
    try:
        available = soup.find("div", attrs={'id': 'availability'})
        available = available.find("span").string.strip()
    except AttributeError:
        available = "Not Available"
    return convert_stock(available)
# Function that gets the estimated delivary time.
def get_delivery(soup):
    try:
        # Find the <div> with id 'mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE'
        div_tag = soup.find("div", id="mir-layout-DELIVERY_BLOCK-slot-PRIMARY_DELIVERY_MESSAGE_LARGE")
        if div_tag:
            # Find the <span> with class 'a-text-bold' within the <div>
            span_tag = div_tag.find("span", class_="a-text-bold")
            if span_tag:
                # Extract and return the text
                delivery_text = span_tag.get_text(strip=True)
            else:
                delivery_text = "Delivery span tag not found"
        else:
            delivery_text = "Delivery div tag not found"
    except Exception as e:
        delivery_text = f"Error occurred: {e}"
    return convert_delivery(delivery_text)
# Function that extracts the top review
def get_topreview(soup):
    try:
        available = soup.find("span", attrs={'data-hook': 'review-body'})
        available = available.find("span").string.strip()
    except AttributeError:
        available = "Not Available"
    return available
# function that extracts the pictures paths.
def get_picture(soup):
    try:
        # Find the <div> with id 'imgTagWrapperId'
        div_tag = soup.find("div", id="imgTagWrapperId")
        if div_tag:
            # Find the <img> tag within the <div>
            img_tag = div_tag.find("img")
            if img_tag:
                # Extract the 'src' attribute
                img_url = img_tag.get("src", "Not Available")
            else:
                img_url = "Not Available"
        else:
            img_url = "Not Available"
    except Exception as e:
        img_url = "Not Available"
    return img_url

# Function to fetch product data from Amazon
def fetch_amazon_data(query):
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US, en;q=0.5'
    }
    URL = f"https://www.amazon.com/s?k={query.replace(' ', '+')}"
    
    try:
        webpage = requests.get(URL, headers=HEADERS)
        webpage.raise_for_status()  # Ensure we notice bad responses
        
        soup = BeautifulSoup(webpage.content, "html.parser")
        
        links = soup.find_all("a", attrs={'class': 'a-link-normal s-no-outline'},)
        
        if not links:
            st.write("No products found.")
            return pd.DataFrame()  # Return empty DataFrame if no products found
        links_list = []
        counter = 0
        for link in links:
            if counter <=10:
                links_list.append(link.get('href'))
                counter = counter+1
        #links_list = [link.get('href') for link in links]
        
        d = {"title": [], "price": [], "rating": [], "reviews": [], "availability": [],"pictures": [],"topreview":[],"delivery":[]}
        
        for link in links_list:
            full_link = f"https://www.amazon.com{link}"
            try:
                new_webpage = requests.get(full_link, headers=HEADERS)
                new_webpage.raise_for_status()
                new_soup = BeautifulSoup(new_webpage.content, "html.parser")
                d['title'].append(get_title(new_soup))
                d['price'].append(get_price(new_soup))
                d['rating'].append(get_rating(new_soup))
                d['reviews'].append(get_review_count(new_soup))
                d['availability'].append(get_availability(new_soup))
                d['pictures'].append(get_picture(new_soup))
                d['topreview'].append(get_topreview(new_soup))
                d['delivery'].append(get_delivery(new_soup))
                
            except requests.RequestException as e:
                st.write(f"Error fetching product details: {e}")
        
        return d

    except requests.RequestException as e:
        st.write(f"Error fetching search results: {e}")
        return d


########################################################################################################################

# The UI of our application.

# Maintains the search sesssion so the user doesn't have to fetch the data everytime the radio button is pressed.
if 'data' not in st.session_state:
    st.session_state.data = {}
if 'query' not in st.session_state:
    st.session_state.query = ""


## Web page introduction.
st.header("Welcome to Prod Top.")
st.subheader("Please Search for an Item to get the most instructive topics")

# Will get the input from the user.
query = st.text_input("Search for products:", st.session_state.query)
# calls the web scrapper function.
if st.button("Search"):
    with st.spinner("Fetching data..."):
        st.session_state.data = fetch_amazon_data(query)
        st.session_state.query = query
else:
    if st.session_state.data:
        st.write("Displaying previous search results.")
    else:
        st.write("No products found or there was an error fetching data.")
#defualt data so that no error displays.
data = {}
data = st.session_state.data
#this where the web scrapper will take all the data from the topics to be diplayed as a radio botton based on the search result.
options =['Price','Rating','Reviews','Availability','Delivery']
st.sidebar.write("Types of Analysis")
sel_option = st.sidebar.radio("Select Any Plot",options)

categories = data.get('title', 'Key not found')
picturesD = data.get('pictures', 'Key not found')
topreview = data.get('topreview', 'Key not found')
ratings = data.get('rating', 'Key not found')

#Displays the bar graghs depending on which radio button was pressed.        
if sel_option == 'Price':
    values = data.get('price', 'Key not found')
    fig, ax = plt.subplots()
    ax.bar(categories, values, color='skyblue')
    plt.xticks(rotation=45, ha='right')
    ax.set_title('Bar Chart for Price')
    ax.set_xlabel('Category')
    ax.set_ylabel('Value')
    st.write(fig)
                
elif sel_option == 'Rating':
    values = data.get('rating', 'Key not found')
    fig, ax = plt.subplots()
    ax.bar(categories, values, color='skyblue')
    plt.xticks(rotation=45, ha='right')
    ax.set_title('Bar Chart for item ratings')
    ax.set_xlabel('Category')
    ax.set_ylabel('Value')
    st.write(fig)
elif sel_option == 'Reviews':
    values = data.get('reviews', 'Key not found')
    fig, ax = plt.subplots()
    ax.bar(categories, values, color='skyblue')
    plt.xticks(rotation=45, ha='right')
    ax.set_title('Bar Chart of number of reviews')
    ax.set_xlabel('Category')
    ax.set_ylabel('Value')
    st.write(fig)
elif sel_option == 'Availability':
    values = data.get('availability', 'Key not found')
    fig, ax = plt.subplots()
    ax.bar(categories, values, color='skyblue')
    plt.xticks(rotation=45, ha='right')
    ax.set_title('Bar Chart for availability of product')
    ax.set_xlabel('Category')
    ax.set_ylabel('Value')
    st.write(fig)

else:
    values = data.get('delivery', 'Key not found')
    fig, ax = plt.subplots()
    ax.bar(categories, values, color='skyblue')
    plt.xticks(rotation=45, ha='right')
    ax.set_title('Bar Chart for days that it would take to deliver product.')
    ax.set_xlabel('Category')
    ax.set_ylabel('Value')
    st.write(fig)
          

#Divides the sections.
st.markdown(' ')
if data != {}:
#Devides the most common 3 items and the best reviews based on the radio topic hit.
    col1,col2,col3 = st.columns(3)
    col1.text(categories[1])
    col2.text(categories[2])
    col3.text(categories[3])

#This were we implemented the star rating system based on the top 3 items using our web scrappaer.


    image1,image2,image3 = st.columns(3)
    image_check1 = "../ProjectPhase4group4v1/istockphoto-1055079680-612x612.jpg"
    image_check2 = "../ProjectPhase4group4v1/istockphoto-1055079680-612x612.jpg"
    image_check3 = "../ProjectPhase4group4v1/istockphoto-1055079680-612x612.jpg"
    
    if picturesD[1] == "Not Available":
        image_check1 = "../ProjectPhase4group4v1/istockphoto-1055079680-612x612.jpg"
    else: image_check1 = picturesD[1]

    if picturesD[2] == "Not Available":
        image_check2 = "../ProjectPhase4group4v1/istockphoto-1055079680-612x612.jpg"
    else: image_check2 = picturesD[2]

    if picturesD[3] == "Not Available":
        image_check3 = "../ProjectPhase4group4v1/istockphoto-1055079680-612x612.jpg"
    else: image_check3 = picturesD[3]
            
    with image1:
        st.image(image_check1, use_column_width = "always")
        st.code(st_star_rating(label = '', maxValue = 5, defaultValue = ratings[1], key = "rating", dark_theme = True, read_only = True))
    with image2:
        st.image(image_check2,use_column_width = "always")
        st.code(st_star_rating(label = '', maxValue = 5, defaultValue = ratings[2], key = "rating1", dark_theme = True, read_only = True))
    with image3:
        st.image(image_check3,use_column_width = "always")
        st.code(st_star_rating(label = '', maxValue = 5, defaultValue = ratings[3], key = "rating3", dark_theme = True, read_only = True))


#this is the review section with temporary information that is going to be replaced by the variable of the web scraper.

    box1,box2,box3 = st.columns(3)


    with box1:
        st.markdown('Review item 1:')
        st.markdown(topreview[1])
            
    with box2:
        st.markdown('Review item 2:')
        st.markdown(topreview[2])

    with box3:
        st.markdown('Review item 1:')
        st.markdown(topreview[3])
###################################################################################################################

