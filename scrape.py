import pandas as pd
import os
from selenium import webdriver
from contextlib import contextmanager
from sys import platform
from webactions import WebActions
import logging
import logging.config
import json
import time
import xvfbwrapper
import sys
import codecs


LOGGING_CONFIG = {
    'formatters': {
        'brief': {
            'format': '[%(asctime)s][%(levelname)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'brief'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'brief',
            'filename': 'log.log',
            'maxBytes': 1024*1024,
            'backupCount': 3,
        },
    },
    'loggers': {
        'main': {
            'propagate': False,
            'handlers': ['console', 'file'],
            'level': 'INFO'
        }
    },
    'version': 1
}

INPUT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "urls.csv")
OUTPUT_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
BASE_DIR = "download chrome driver for windows and fix base dir"

STORES = {
    "Asda": 'asda-logo.png',
    "Ocado": 'ocado-logo.png',
    "Tesco": 'tesco-logo.png',
    "Waitrose": 'waitrose-logo.png',
}

LOADER = ".Placeholder-grayAreaAnimator-cover"
CAROUSEL = ".Carousel"
GROUP = ".AddToBasketPage-group .AddToBasketPage-group-title-text span"
SCRAPE_ATTEMPTS = 3
ITEMS_ON_CAROUSEL = 20


def read_urls():
    df = pd.read_csv(INPUT_CSV)
    idles = df.loc[df['Status'] == 'idle']
    return idles.values.tolist()


def set_status(url, status="processed"):
    df = pd.read_csv(INPUT_CSV)
    print("[INFO] {} set status: {}".format(url, status))
    df.loc[df['Url'] == url, 'Status'] = status
    df.to_csv(INPUT_CSV, index=False)


def get_logger():
    logging.config.dictConfig(LOGGING_CONFIG)
    log = logging.getLogger('main')
    log.setLevel(level=logging.getLevelName('INFO'))
    return log


@contextmanager
def get_driver(arg):

    print('[INFO] arg mode: ', arg)

    if arg == "xvfb":
        display = xvfbwrapper.Xvfb()
        display.start()
        print('[INFO] is_headless_xvfb: display started')

    chromeOptions = webdriver.ChromeOptions()

    chromeOptions.add_argument("--disable-extensions")
    chromeOptions.add_argument("--disable-infobars")
    chromeOptions.add_argument("--start-maximized")
    if arg == "xvfb":
        chromeOptions.add_argument("--no-sandbox")
        chromeOptions.add_argument("--disable-gpu")
    elif arg == "--headless":
        chromeOptions.add_argument("--no-sandbox")
        chromeOptions.add_argument("--disable-gpu")
        chromeOptions.add_argument("--headless")

    if platform == 'darwin':
        driver = webdriver.Chrome(chrome_options=chromeOptions)
    elif platform == 'linux' or platform == 'linux2':
        driver = webdriver.Chrome(chrome_options=chromeOptions)
    else:  # windows
        driver = webdriver.Chrome(os.path.join(BASE_DIR, "chromedriver.exe"),
                                  chrome_options=chromeOptions)

    yield driver
    driver.quit()

    if arg == "xvfb":
        display.stop()


def get_containers(driver, logger):

    actions = WebActions(driver, logger)

    groups = GROUP
    actions.wait_for_element_by_css(groups, visible=True)
    groups_all = actions.get_all_elements_by_css(groups)

    idxs = []
    for idx, group in enumerate(groups_all, 1):

        # exclude Uncategorised
        # --
        # if group.text == "Uncategorised":
        #     logger.info("Uncategorised: exclude group idx: %s", idx)
        # else:
        #     logger.info("%s: ok with idx: %s", group.text, idx)
        #     idxs.append(idx)

        logger.info("%s: ok with idx: %s", group.text, idx)
        idxs.append(idx)

    all_items_containers = []
    for idx in idxs:
        temp_containers = actions.get_all_elements_by_css(".AddToBasketPage-group:nth-of-type(%s) .BasketItem" % idx)
        logger.info("basketItems found: %s for group idx: %s", len(temp_containers), idx)

        for cont in temp_containers:
            all_items_containers.append(cont)

    return all_items_containers


def run(arg):

    urls = read_urls()
    logger = get_logger()

    with get_driver(arg) as driver:

        driver.get(urls[0][0])
        # driver.maximize_window()

        actions = WebActions(driver, logger)

        # news
        if actions.is_element_by_css("#newsModal", 10, visible=True):
            actions.click_by_css(".close")

        actions.wait_for_element_not_present_by_css("#newsModal", visible=True)

        # cookies
        if actions.is_element_by_css(".cookie-banner", 10, visible=True):
            actions.click_by_css(".cookie-banner .fa-times")

        actions.wait_for_element_not_present_by_css(".cookie-banner", visible=True)

        recipe = {}

        for url_idx, url in enumerate(urls):

            for i in range(SCRAPE_ATTEMPTS):

                try:

                    ingredient_products = []

                    logger.info("processing: %s attempt: %s", url[0], i)

                    actions.open_url(url[0])

                    recipe['recipe_url'] = url[0]

                    actions.wait_for_element_by_css("iframe[src*='add-to-list-healthyfoodcoukbuyonline-widget.html']")
                    actions.switch_to_iframe(driver.find_elements_by_tag_name("iframe")[1])
                    actions.click_by_css(".Button", True)
                    actions.switch_to_default_content()

                    # wait for iframe and switch to it
                    # actions.wait_for_element_by_css(".recipe-template-default[style=\"overflow: hidden;\"]")
                    actions.wait_for_element_by_css("iframe._10eWP3cjZMNSs-4dSOAX9L", visible=True)

                    time.sleep(1)
                    actions.switch_to_iframe(driver.find_element_by_css_selector("iframe._10eWP3cjZMNSs-4dSOAX9L"))

                    actions.wait_for_element_not_present_by_css(LOADER, 30)

                    if not actions.is_element_by_css(GROUP, 5):
                        logger.info("GROUP not present")
                        # inconsistent
                        # usually a shop is selected already
                        # but sometimes have got to select a shop
                        if actions.is_element_by_css(".SelectInventoryPage-inventory .Button", 5):
                            actions.click_by_css(".SelectInventoryPage-inventory .Button")
                            actions.wait_for_element_not_present_by_css(LOADER, 30)
                        else:
                            logger.info("neither select from SHOPS list button.. will try GROUP again")

                    init_all_items_containers = get_containers(driver, logger)
                    logger.info("collected total items: %s", len(init_all_items_containers))

                    products = [[] for _ in range(len(init_all_items_containers))]
                    ingredient_texts = [None for _ in range(len(init_all_items_containers))]

                    for store, store_logo in STORES.iteritems():

                        change_store = ".AddToBasketDropdown-dropdown .Link-reference"
                        actions.click_by_css(change_store)

                        store_drop_down = ".InventoriesDropdown"
                        actions.wait_for_element_by_css(store_drop_down, visible=True)

                        actions.click_by_css(".InventoriesDropdown-item-image img[src$='%s']" % store_logo)
                        logger.info("selected store: %s", store)

                        actions.wait_for_element_by_css(LOADER, 2, fail=False)
                        actions.wait_for_element_not_present_by_css(LOADER)

                        all_items_containers = get_containers(driver, logger)

                        if len(init_all_items_containers) != len(all_items_containers):
                            logger.error("item containers match failed: init (%s) != store: %s (%s) ",
                                         len(init_all_items_containers),
                                         store,
                                         len(all_items_containers))

                        for idx, container in enumerate(all_items_containers):

                            logger.info("processing product with idx: %s (json idx: %s)", idx, idx+1)

                            ingredient_text = actions.get_element_concatenate(container, ".BasketItem-slItem-text").text
                            logger.info("ingredient_text: %s", ingredient_text)

                            ingredient_texts[idx] = ingredient_text

                            item_name = actions.get_element_concatenate(container, ".BasketItem-info").text

                            if item_name.count("This item wasn"):
                                temp_product = dict()
                                temp_product['vendor'] = store
                                temp_product['status'] = "unmatched"
                                temp_product['name'] = ""
                                temp_product['qty'] = ""
                                temp_product['price'] = ""
                                temp_product['url'] = ""
                                temp_product['image_url'] = ""

                                logger.info("temp_product: %s", temp_product)

                            else:

                                qty = actions.get_element_concatenate(container, ".Counter-value").text

                                click_swap = actions.get_element_concatenate(container, ".BasketItem-info-link")
                                actions.click_if_clickable(click_swap)

                                actions.wait_for_element_by_css(CAROUSEL, visible=True)

                                items_on_carousel_sel = ".Carousel-item .Link-reference"
                                items_car = actions.get_all_elements_by_css(items_on_carousel_sel)
                                traverse_range = len(items_car)

                                logger.info("init found items on carousel: %s", traverse_range)
                                logger.info("max ITEMS_ON_CAROUSEL set to: %s", ITEMS_ON_CAROUSEL)

                                # arrow_right = "div:not(.Carousel-arrow--disabled)>.Carousel-arrow-icon--right"
                                arrow_right = "div.Carousel-arrow--right:not(.Carousel-arrow--disabled)"
                                if actions.is_element_by_css(arrow_right, 3):
                                    logger.info("arrow-icon right found!")
                                    traverse_range = ITEMS_ON_CAROUSEL

                                logger.info("traverse_range is: %s", traverse_range)

                                for carousel_idx in range(traverse_range):

                                    items_container = ".Carousel-item"
                                    item_on = actions.get_all_elements_by_css(items_container)[carousel_idx]

                                    temp_product = dict()

                                    temp_product['vendor'] = store
                                    temp_product['status'] = "matched"

                                    for _ in range(3):
                                        item_name = actions.get_element_concatenate(item_on, ".ProductSwap-item-title").text.strip("/")
                                        item_name = item_name[:item_name.find("/") - 1]
                                        temp_product['name'] = item_name

                                        if item_name != "":
                                            break
                                        else:
                                            logger.warning("item_name is empty... retry in 2 secs to read it")
                                            time.sleep(2)

                                    temp_product['qty'] = qty

                                    for _ in range(3):
                                        price = actions.get_element_concatenate(item_on, ".ProductSwap-item-title>b").text
                                        temp_product['price'] = price

                                        if price != "":
                                            break
                                        else:
                                            logger.warning("price is empty... retry in 2 secs to read it")
                                            time.sleep(2)

                                    temp_product['url'] = actions.get_element_concatenate(item_on, ".Link-reference").get_attribute("href")

                                    image_url = actions.get_element_concatenate(item_on, ".ProductSwap-item img").get_attribute("src")
                                    temp_product['image_url'] = image_url

                                    products[idx].append(temp_product)

                                    logger.info("temp_product: %s", temp_product)

                                    if carousel_idx > 1:  # only after 3 processed on carousel
                                        if actions.is_element_by_css(arrow_right, 3):
                                            logger.info("arrow-icon right enabled: go right")
                                            actions.click_by_css(arrow_right)
                                        else:
                                            logger.info("arrow-icon right disabled: exit")
                                            break

                                close_carousel_sel = ".ProductSwap-close"
                                actions.click_by_css(close_carousel_sel)

                                actions.wait_for_element_not_present_by_css(CAROUSEL, visible=True)

                    for idx, prods in enumerate(products, 1):

                        temp_ingredient_product = dict()
                        temp_ingredient_product['ingredient_index'] = idx
                        temp_ingredient_product['products'] = prods
                        temp_ingredient_product['ingredient_text'] = ingredient_texts[idx -1]

                        ingredient_products.append(temp_ingredient_product)

                    recipe['ingredient_products'] = ingredient_products

                    logger.info("recipe json: \n%s", json.dumps(recipe, indent=4, sort_keys=True))

                    try:
                        with codecs.open(os.path.join(OUTPUT_JSON, "file_{}.json".format(url_idx)), "w", "utf-8") as fh:
                            fh.write(json.dumps(recipe, indent=4, sort_keys=True))
                    except Exception as err:
                        logger.error("%s: error writing json file: %s", err.__class__.__name__, err)

                    set_status(url[0], "processed")
                    actions.clear_browser_storage()

                    break

                except Exception as err:
                    logger.error("%s => %s", err.__class__.__name__, err)

                    if i == SCRAPE_ATTEMPTS - 1:
                        set_status(url[0], "errored")
                    else:
                        set_status(url[0], "errored-retry")


if __name__ == "__main__":

    arg = None
    if len(sys.argv) > 1:
        arg = sys.argv[1]

    while read_urls():
        run(arg)