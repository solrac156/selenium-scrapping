# Importo los modulos necesarios, como el driver del navegador, esperas para el driver, maneras de buscar elementos,
# condiciones para las esperas, algunas excepciones, pandas para el manejo de la estructura de datos, sys para el logger
# que implemente, y string para limpiar las cadenas que obtuve.
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
import pandas as pd
import sys
import string


# Defino una funcion que abre un navegador Chrome, con una opcion para que no cargue las imagenes porque no seran
# relevantes para mi scrapping. Ademas, incluyo un campo en el driver para hacer mas facil el acceso a las esperas. Le
# asigne 120 segundos por problemas con la conexion, aunque con la opcion de quitar las imagenes no deberia tardar tanto
def init_driver():
    options = webdriver.ChromeOptions()
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option('prefs', prefs)
    browser = webdriver.Chrome(chrome_options=options)
    browser.wait = WebDriverWait(browser, 120)
    return browser


# Una funcion que limpia el texto que recibo para poder guardarlo en el archivo CSV
def clean_text(text):
    return_text = ''.join([char for char in text if char in string.printable])
    return_text = return_text.replace(',', ' ').replace(';', ' ').strip()
    return return_text


# Funcion usada para extraer todos los links de los libros que estan en la pagina a la que haremos scrapping. Los links
# se extraen por su xPath (todos son etrquetas a que contienen la misma clase), y se retorna una lista que solo contiene
# el atributo href de cada una de las etiquetas.
def get_book_links(browser):
    link_elements = browser.find_elements_by_xpath('//a[@class="bookTitle"]')
    links = [link.get_attribute('href') for link in link_elements]
    return links


# Funcion para extraer el nombre del libro al cual poseen los reviews, se extraer por su xPath y se retorna el nombre
# luego de limpiar la salida.
def get_book_title(browser):
    book_name_element = browser.find_element_by_xpath('//h1[@id="bookTitle"]')
    return clean_text(book_name_element.text)


# Funcion para extraer todos los elementos de reviews de la pagina, segun su xPath. Se extraen los elementos y se
# retorna una lista con ellos, sin hacerle ningun tipo de modificacion.
def get_reviews(browser):
    review_elements = browser.find_elements_by_xpath('//div[@class="review"] | //div[@class="review nosyndicate"]')
    return review_elements


# Funcion para hacer click en el boton de siguiente pagina de reviews. Se accede al boton por su xPath y se le hace
# click.
def get_next_page(browser):
    next_button = browser.find_element_by_xpath('//a[@class="next_page"]')
    next_button.click()


# Funcion para expandir los textos en los que existe spoilers y asi poder obtener el texto del review. Si el boton no
# existe, la funcion no hace nada.
def expand_spoilers(element):
    try:
        expand_spoiler_button = element.find_element_by_xpath('.//div[@class="reviewText stacked"]/em/a')
        expand_spoiler_button.click()
    except NoSuchElementException:
        pass


# Funcion para expandir los textos cuando los reviews son muy largos, y poder obtener el texto completo. Si el boton no
# existe, la funcion no hace nada.
def expand_review_texts(element):
    try:
        more_button = element.find_element_by_xpath('.//div[@class="reviewText stacked"]/span[@class="readable"]/a')
        more_button.click()
    except NoSuchElementException:
        pass


# Funcion para extraer el nombre de usuario del review. Se le pasa el review, y con el xPath se extrae el usuario, luego
# se limpia la salida y se retorna.
def extract_user(element):
    user_element = element.find_element_by_xpath('.//span[@itemprop="author"]')
    user = clean_text(user_element.text)
    return user


# Funcion para extraer el titulo de la cantidad de estrellas del review. Se le pasa el review, y con el xPath se extrae
# el campo, luego se limpia la salida y se retorna. Si el review no tiene estrellas porque solo se agrego a una lista
# o se marco, se retorna None.
def extract_static_stars_title(element):
    try:
        stars_element = element\
            .find_element_by_xpath('.//div[@class="reviewHeader uitext stacked"]/span[@class=" staticStars"]')
        static_stars_title = clean_text(stars_element.get_attribute('title'))
    except NoSuchElementException:
        static_stars_title = 'None'
    return static_stars_title


# Funcion para extraer la fecha del review. Se le pasa el review, y con el xPath se extrae la fecha, luego se limpia la
# salida y se retorna.
def extract_date(element):
    review_date_element = element\
        .find_element_by_xpath('.//div[@class="reviewHeader uitext stacked"]/a[@class="reviewDate createdAt right"]')
    review_date = clean_text(review_date_element.text)
    return review_date


# Funcion para extraer el texto del review. Se le pasa el review, y con el xPath se extrae el texto, luego se limpia la
# salida y se retorna. En caso de que no exista el primer xPath, significa que el texto es muy corto y no tiene una
# etiqueta span donde exta completo, esta completo en la primera, por lo que se busca en esta etiqueta, se extrae y
# luego se limpia y retorna la salida.
def extract_text(element):
    try:
        review_text_element = element\
            .find_element_by_xpath('.//div[@class="reviewText stacked"]/span[@class="readable"]/span[2]')
        review_text = clean_text(review_text_element.text)
    except NoSuchElementException:
        review_text_element = element\
            .find_element_by_xpath('.//div[@class="reviewText stacked"]/span[@class="readable"]/span')
        review_text = clean_text(review_text_element.text)
    return review_text


# Funcion para extraer la cantidad de likes que posee un review. Se le pasa el review, y con el xPath la cantidad de
# likes. Luego se limpia la salida y se retorna. En caso de que el review no tenga likes se retorna 0 likes.
def extract_like_count(element):
    try:
        like_element = element.find_element_by_xpath('.//span[@class="likeItContainer"]//span[@class="likesCount"]')
        like_count = clean_text(like_element.text)
    except NoSuchElementException:
        like_count = '0 likes'
    return like_count


if __name__ == "__main__":
    # Para poder debugear mi codigo, y saber que estaba pasando implemente un logger. Para usarlo solo es necesario
    # correr el script con la opcion --log. Si no se corre con esta opcion no habra salida en el terminal, y si se corre
    # se podra saber que esta haciendo el script en cada momento.
    if len(sys.argv) > 1 and sys.argv[1] == '--log':
        log = True
    else:
        log = False
    # Diccionario para guardar la informacion de los reviews.
    reviews_output = {
        'book_name': [],
        'user': [],
        'static_stars_title': [],
        'review_date': [],
        'review': [],
        'likes_count': []
    }
    # Uso un bloque try para mi codigo, para atrapar cualquier error que obtenga.
    try:
        # Obtengo la instancia del navegador
        driver = init_driver()
        if log:
            print('Getting https://www.goodreads.com/list/show/1.Best_Books_Ever')
        driver.get("https://www.goodreads.com/list/show/1.Best_Books_Ever")
        driver.wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, '//a[@class="bookTitle"]')
        ))
        if log:
            print('Waiting done')
        books = get_book_links(driver)
        for book in books:
            if log:
                print('Getting ' + book)
            driver.get(book)
            driver.wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, '//div[@class="review"] | //div[@class="review nosyndicate"]')
            ))
            if log:
                print('Waiting done')
            title = get_book_title(driver)
            if log:
                print('Processing book ' + title)
            reviews = get_reviews(driver)
            if log:
                print('Reviews extracted')
            for i, review in enumerate(reviews):
                if log:
                    print('Processing review ' + str(i))
                expand_spoilers(review)
                expand_review_texts(review)
                reviews_output['book_name'].append(title.encode('utf-8'))
                reviews_output['user'].append(extract_user(review).encode('utf-8'))
                reviews_output['static_stars_title'].append(extract_static_stars_title(review).encode('utf-8'))
                reviews_output['review_date'].append(extract_date(review).encode('utf-8'))
                reviews_output['review'].append(extract_text(review).encode('utf-8'))
                reviews_output['likes_count'].append(extract_like_count(review).encode('utf-8'))
                if log:
                    print('Processing review ' + str(i) + ' done')
            if log:
                print('Getting second page of reviews')
            get_next_page(driver)
            driver.wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, '//a[@class="previous_page"]')
            ))
            if log:
                print('Waiting done')
            reviews = get_reviews(driver)
            if log:
                print('Reviews extracted')
            for i, review in enumerate(reviews):
                if log:
                    print('Processing review ' + str(i))
                expand_spoilers(review)
                expand_review_texts(review)
                reviews_output['book_name'].append(title.encode('utf-8'))
                reviews_output['user'].append(extract_user(review).encode('utf-8'))
                reviews_output['static_stars_title'].append(extract_static_stars_title(review).encode('utf-8'))
                reviews_output['review_date'].append(extract_date(review).encode('utf-8'))
                reviews_output['review'].append(extract_text(review).encode('utf-8'))
                reviews_output['likes_count'].append(extract_like_count(review).encode('utf-8'))
                if log:
                    print('Processing review ' + str(i) + ' done')
            if log:
                print('Processing book ' + title + ' done')
        # Una vez llegado este punto, ya tengo la informacion de todos los reviews de los libros que me interesaban en
        # mi diccionario, por lo que cierro la instancia del navegador, guardo la informacion en un dataframe de pandas
        # y lo transformo a un archivo CSV
        driver.quit()
        df = pd.DataFrame(reviews_output)
        df.to_csv('./salida', index=0)
    except TimeoutException as e:
        # En caso de una excepcion por que el internet este lento, informo sobre la excepcion, cierro el navegador y
        # guardo los datos que tenia hasta el momento del error
        print("Timed out waiting for page to load.")
        df = pd.DataFrame(reviews_output)
        df.to_csv('./salida', index=0)
        driver.quit()
    except StaleElementReferenceException as e:
        # En caso de que este tratando de usar un elemento que ya no existe en el DOM informo sobre ello y salgo.
        print ('Stale Reference!')
        driver.quit()
