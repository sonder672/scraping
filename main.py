from scraping_tool import full_page_scraping
from scraping_tool import get_details
from scraping_tool import get_seller_information
from persistence import get_cache
from persistence import set_cache

def scrape_all_urls(baseUrl):
    saleUrl = baseUrl + '/venta'
    rentalUrl = baseUrl + '/renta'
    allUrls = []

    allUrls.extend(full_page_scraping(saleUrl))
    allUrls.extend(full_page_scraping(rentalUrl))

    print(f"Hay un total de {len(allUrls)} propiedades divididas entre Venta/Renta")

    all_information = []

    for url in allUrls:
        url_details = url['url_details']
        details = get_details(url_details)

        if 'url_author' in url and url.get('url_author'):
            url_author = url['url_author']
            seller_information_cache = get_cache(url_author)

            if seller_information_cache is None:
                seller_information = get_seller_information(url_author)
                set_cache(url_author, seller_information)

            if details is not None:
                details.update(seller_information or seller_information_cache)
                print(details)

        all_information.append(details)

    print(all_information)

scrape_all_urls('https://bhhscancun.com')