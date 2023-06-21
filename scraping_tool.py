import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC    

def scrape_all_urls(baseUrl):
    saleUrl = baseUrl + '/venta'
    rentalUrl = baseUrl + '/renta'
    allUrls = []

    allUrls.extend(full_page_scraping(saleUrl))
    allUrls.extend(full_page_scraping(rentalUrl))

    print(f"Hay un total de {len(allUrls)} propiedades divididas entre Venta/Renta")

    for url in allUrls:
        get_details(url)


def full_page_scraping(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ejecutar en modo headless sin ventana gráfica
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    found_button = True

    while found_button:
        try:
            button = driver.find_element(By.CLASS_NAME, 'btn-load-more')
            button.click()

            #'loader-show' aparece cuando se le da clic a 'Cargar más' y desaparece cuando ya carga
            wait = WebDriverWait(driver, 30)
            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, 'loader-show')))

        except NoSuchElementException:
            print("NO SE ENCONTRÓ MÁS 'CARGAR MÁS'")
            found_button = False
        except Exception as e:
            print(f"EXCEPCIÓN NO ESPERADA CON EL BOTÓN 'CARGAR MÁS': {e}")
            found_button = False

    additional_content = driver.page_source 

    driver.quit()

    soup = BeautifulSoup(additional_content, 'html.parser')

    items = soup.find_all('h2', class_= 'item-title')
    urls = []
    for item in items:
        link = item.find('a')
        href = link.get('href')
        urls.append(href)

    return urls


def get_details(url_details):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36'
    }

    response = requests.get(url_details, headers = headers)
    if response.status_code != 200:
        print(f'Hubo un error {response.status_code}, {response.reason}')
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    id_property_element = soup.find('strong', string = 'ID de propiedad:')
    if not id_property_element:
        print(f'No se encontró el ID de propiedad de {url_details}')
        return

    listing_id = id_property_element.next_sibling.strip()

    print(f'{listing_id}')


scrape_all_urls('https://bhhscancun.com')