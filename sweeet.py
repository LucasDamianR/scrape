#!/usr/bin/env python
# coding: utf-8

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import requests
from time import strftime
import datetime
import re
from json import JSONDecoder

import os
from concurrent.futures import ThreadPoolExecutor
import itertools

start_time= datetime.datetime.now()
hoy = str(datetime.date.today())

url_base = 'https://www.sweetvictorian.com.ar/sweet-lady/'


def scrape(url_aux):
    
    soup = BeautifulSoup(requests.get(url_aux,headers = headers_r).text,'html.parser')
    colores = []
    for metadata in extract_json_objects(soup.find(id='hdnProductVariants').get('value')):
        colores.append([metadata['ColorName'],metadata['SizeName']])


    results = [i for i in colores if i[0] == colores[0][0]]  
    for result in results:
        result.append(soup.find('h3').text)
        result.append(soup.find(class_='ml-1 font-size-h5 font-weight-bolder text-gray-350').text)
        result.append(soup.find('a',class_='text-muted').text)
        result.append(soup.find_all(class_='breadcrumb-item active')[-2].text.replace('\n',''))
        result.append(soup.find(class_='card-img-top').get('src'))
        result.append(url_aux)
    
    return results


def extract_json_objects(text, decoder=JSONDecoder()):
    
    """Find JSON objects in text, and yield the decoded JSON data

    Does not attempt to look for JSON arrays, text, or other JSON types outside
    of a parent JSON object. 

    """
    pos = 0
    while True:
        match = text.find('{', pos)
        if match == -1:
            break
        try:
            result, index = decoder.raw_decode(text[match:])
            yield result
            pos = match + index
        except ValueError:
            pos = match + 1

def createDriver():
    
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'    

    chrome_options = Options()  
    chrome_options.add_argument("--headless")  
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_argument("--window-size=1825x1644")

    return webdriver.Chrome( options = chrome_options)

browser = createDriver()

items = []
browser.get(url_base)
url_list = []
last_page = int(browser.find_elements_by_class_name('page-item')[-2].text)
url_aux = 'https://www.sweetvictorian.com.ar/sweet-lady/?pageIndex='
page_list = [url_aux+str(i) for i in range(last_page)]
for link in page_list:
    browser.get(link)
    
    url_list += [i.get_attribute('href') for i in 
                 WebDriverWait(browser,50).until(EC.presence_of_all_elements_located((By.CLASS_NAME,'card-img-hover')))]

headers_r = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}

browser.quit()
my_list = []
for url in url_list:
    try:
        my_list.append(scrape(url))
    except:
        pass




my_result = list(itertools.chain(*my_list))

df = pd.DataFrame(my_result,columns=['Color','Talle','Descripcion','Precio','Codigo','Tipo','Imagen','Link'])
df = df[~df.Precio.str.contains('Precio')]


df['Codigo'] = df.Codigo.apply(lambda x:x.split(':')[1])
df["Precio Nuevo"] =  (df.Precio.str.extract(r"([\d,\.]+)", expand=False)
                                .str.replace(".", "",regex=True)
                                .str.replace(",", ".",regex=True)
                                .astype(float))

df["Precio Anterior"] = df["Precio Nuevo"]

df['Fecha']= datetime.date.today()

df = df.drop_duplicates(['id Producto','ID Color','Imagen'])
df = df.reset_index(drop=True)

df.to_excel('foo.xlsx',index=False)
end_time = datetime.datetime.now()

print('Tiempo de ejecución SweetLady.py: {}'.format(end_time - start_time)[:-4])