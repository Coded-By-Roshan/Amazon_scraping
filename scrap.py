from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import mysql.connector
from selenium.webdriver import ActionChains
import requests
from PIL import Image
import ftplib
import pandas

ftp = ftplib.FTP('ip_address','user_mail', 'username')
ftp.encoding = "utf-8"  

mydb = mysql.connector.connect(
host="ip_address",
user="username",
password="password",
database='database_name'
)


filename = '/Users/apple/Downloads/scraping_amazon/products.xlsx'
data = pandas.read_excel(filename)

for i in range(0,len(data.index)):
    try:
        PRODUCT_URL = data.iloc[i,data.columns.get_loc('product_url')]
        product_category_id = int(data.iloc[i,data.columns.get_loc('product_category_id')])
        product_store_id = int(data.iloc[i,data.columns.get_loc('product_store_id')])
        product_parent_category = int(data.iloc[i,data.columns.get_loc('product_parent_category')])
        driver = webdriver.Chrome('/Users/apple/Downloads/scraping_amazon/chdriver')
        driver.get(PRODUCT_URL)
        time.sleep(3)
        try:
            product_name = driver.find_element_by_id('productTitle')
            desc1 = driver.find_element_by_id('productOverview_feature_div')
            desc2 = driver.find_element_by_id('feature-bullets')
            info = desc1.text + desc2.text
        except:
            product_name = 'product_name'
            info = 'info'
        try:
            info = (info).replace("See more product details",'')
        except:
            info = info

        
        get_images = driver.find_elements_by_class_name('imageThumbnail')
        image_url = []
        image_names = []

        imgs = driver.find_elements_by_class_name('imageThumbnail')

        for i in imgs:
            ActionChains(driver).click(i).perform()

        a = driver.find_elements_by_class_name('maintain-height')


        for i in a:
            try:
                b = i.find_element_by_tag_name('img')
            except:
                pass
            image_url.append(b.get_attribute('src'))


        for img_url in image_url:
            response = requests.get(img_url)
            if response.status_code:
                name = img_url.split('/')
                fp = open(name[-1], 'wb')
                fp.write(response.content)
                fp.close()
                image_names.append(name[-1])

        for filename in image_names:
            with open(filename, 'rb') as file:
                ftp.storbinary("STOR %s" % (filename),file)
        product_code = image_names[0].split('.')
        product_code = product_code[0]
        print("Data Scraped")
        print("Storing the data in the database.......")
        cursor = mydb.cursor()
        add_information = """ INSERT INTO `mv_product` (
            `product_name`,
            `product_category_id`,
            `product_store_id`,
            `product_is_offer`,
            `product_status`,
            `product_image`,
            `product_parent_category`,
            `product_description`,
            `return_policy`,
            `is_return`,
            `product_code`
            )
            VALUES (%s, %s, %s,%s, %s, %s,%s, %s, %s,%s,%s)
            
            """
        p_id = cursor.lastrowid
        datas = (product_name.text, product_category_id,product_store_id,1,1,image_names[0],product_parent_category, info,"Exchange within 1 day. No Return",0,product_code)
        cursor.execute(add_information, datas)
        p_id = cursor.lastrowid

        def add_info():
            add_information = """INSERT INTO `mv_product_images` (`product_id`, `image_name`) 
            VALUES (%s, %s)
            """
            for i in range(2,len(image_names)):
                datas = (p_id, image_names[i])
                cursor.execute(add_information, datas)
            mydb.commit()
            
        add_info()
        driver.close()
        print("Data Stoted successfully !!!")
    except:
        print(f"Failed Url: {PRODUCT_URL}")

mydb.close()
cursor.close()