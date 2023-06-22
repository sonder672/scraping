import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC    
import re

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
            print("EXCEPCIÓN NO ESPERADA CON EL BOTÓN 'CARGAR MÁS'", e)
            found_button = False

    additional_content = driver.page_source 

    driver.quit()

    soup = BeautifulSoup(additional_content, 'html.parser')

    cards = soup.find_all('div', class_='card')

    data = []

    for card in cards:
        item = card.find('h2', class_='item-title')
        author = card.find('div', class_='item-author')

        if not item:
            print("SE SALTA ESTE CICLO DEBIDO A QUE NO EXISTE UNA URL DE DETAIL")
            continue

        link_detail = item.find('a')
        href_detail = link_detail.get('href')

        if author:
            link_author = author.find('a')
            href_author = link_author.get('href') if link_author else None
            card_data = {
                'url_details': href_detail,
                'url_author': href_author
            }
        else:
            card_data = {
                'url_details': href_detail
            }

        data.append(card_data)

    return data


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

    details = {}
    details['listingId'] = id_property_element.next_sibling.strip()

    details['city'] = _get_sub_element_text(soup, 'li', 'span', class_ = 'detail-city');
    details['country'] = _get_sub_element_text(soup, 'li', 'span', class_ = 'detail-country');
    details['stateOrProvince'] = _get_sub_element_text(soup, 'li', 'span', class_ = 'detail-state');
    details['streetName'] = _get_sub_element_text(soup, 'li', 'span', class_ = 'detail-area');
    details['postalCode'] = _get_sub_element_text(soup, 'li', 'span', class_ = 'detail-zip');
    details['unstructuredAddress'] = _find_element_text('address', soup, class_='item-address')

    price_element = _find_element_text('li', soup, class_='item-price')
    details['listPrice'], details['currencyCode'] = _extract_numbers_and_currency(price_element)

    gallery_div = soup.find('div', id='property-gallery-js')
    image_elements = _find_elements_with_attribute('div', 'data-thumb', gallery_div) if gallery_div else []
    details['photos'] = [{"mediaUrl": element['data-thumb'], "mediaSequenceNumber": i + 1} for i, element in enumerate(image_elements)]
    details['photosCount'] = len(details['photos'])

    block_content_wrap = soup.find('div', class_='block-content-wrap')
    description_elements = _find_elements_with_attribute('p', None, block_content_wrap) if block_content_wrap else []
    details['publicRemarks'] = ' '.join([element.text.strip() for element in description_elements])

    property_mapping = {
        None: 'type_residence',
        'icon-hotel-double-bed-1': 'bedroomsTotal',
        'icon-bathroom-shower-1': 'bathroomsTotal',
        'icon-real-estate-dimensions-plan-1': 'livingArea'
        #'icon-car-1': 'garage'
    }
    property_values = _get_property_nonspecific_attributes(property_mapping, soup)

    if property_values is not None:
        details.update(property_values)
    
    return details;


def get_seller_information(url_author):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36'
    }

    response = requests.get(url_author, headers = headers)
    if response.status_code != 200:
        print(f'Hubo un error {response.status_code}, {response.reason}')
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')

    details = {}
    details['listAgentFullName'] = _get_sub_element_text(soup, 'div', 'h1', class_='agent-profile-header')
    details['listAgentEmail'] = _get_sub_element_text(soup, 'li', 'a', class_='email')
    details['listAgentPreferredPhone'] = _find_element_text('span', soup, class_='agent-phone')
    
    return details


def _find_element_text(element, soup, **kwargs):
    element = soup.find(element, **kwargs)
    if element is None:
        return None
    
    return element.text.strip()


def _get_sub_element_text(soup, elementAttribute, subElementAttribute, **kwargs):
    try:
        element = soup.find(elementAttribute, **kwargs);
        if element:
            sub_element = element.find(subElementAttribute)
        if sub_element:
            return sub_element.text.strip()
        
        return None
    except Exception as e:
        print(f"Error al obtener el texto del elemento: {e}")
        return None
    

def _get_property_nonspecific_attributes(property_mapping, soup):
    result = {}

    property_characteristics_elements = soup.find('div', class_='d-flex property-overview-data')

    if property_characteristics_elements:
        ul_elements = property_characteristics_elements.find_all('ul', class_='list-unstyled flex-fill')
        for ul_element in ul_elements:
            i_element = ul_element.find('i')
            strong_element = ul_element.find('strong')
            class_name = i_element.get('class')[1] if i_element else None
            property_name = property_mapping.get(class_name)

            if property_name:
                property_value = strong_element.text.strip()
                result[property_name] = property_value

    return result


def _find_elements_with_attribute(element, attribute, soup, **kwargs):
    if attribute is None:
        elements = soup.find_all(element, **kwargs)
    else:
        elements = soup.find_all(element, attrs={attribute: True}, **kwargs)

    return elements if elements else []


def _extract_numbers_and_currency(text):
    numbers = re.findall(r'\d{1,3}(?:,\d{3})*(?:\.\d+)?', text)
    
    currency = re.search(r'/(\w+)$', text)
    currency = currency.group(1) if currency else None
    
    return numbers[0], currency