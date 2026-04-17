from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


LOGGER = logging.getLogger(__name__)

JS_CLICK = "arguments[0].click();"
CARD_SELECTOR = "div.cardItem div.card"


@dataclass
class MovieRecord:
    name: str
    description: str


class RPAMovieScraper:
    def __init__(self, base_url: str, movie_search_path: str, timeout_seconds: int = 15, headless: bool = True) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.movie_search_path = movie_search_path
        self.timeout_seconds = timeout_seconds
        self.headless = headless
        self.driver: WebDriver | None = None

    def __enter__(self) -> "RPAMovieScraper":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    def start(self) -> None:
        options = ChromeOptions()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(self.timeout_seconds)
        LOGGER.info("WebDriver iniciado")

    def stop(self) -> None:
        if self.driver is not None:
            self.driver.quit()
            self.driver = None
            LOGGER.info("WebDriver finalizado")

    def _wait(self) -> WebDriverWait:
        if self.driver is None:
            raise RuntimeError("WebDriver nao inicializado")
        return WebDriverWait(self.driver, self.timeout_seconds)

    def open_home(self) -> None:
        assert self.driver is not None
        self.driver.get(self.base_url)
        self._wait().until(EC.presence_of_element_located((By.TAG_NAME, "nav")))

    def go_to_movie_search(self) -> None:
        assert self.driver is not None
        wait = self._wait()
        try:
            movie_search_link = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/movieSearch']"))
            )
        except TimeoutException:
            movie_search_link = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Movie Search']"))
            )
        self.driver.execute_script(JS_CLICK, movie_search_link)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='searchStr']")))

    def search_movies(self, query: str) -> None:
        assert self.driver is not None
        wait = self._wait()
        search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='searchStr']")))
        search_input.clear()
        search_input.send_keys(query)
        find_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Find']"))
        )
        self.driver.execute_script(JS_CLICK, find_button)
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, CARD_SELECTOR)))

    def _is_reveal_visible(self, card: Any) -> bool:
        try:
            reveal = card.find_element(By.CSS_SELECTOR, "div.card-reveal")
            return reveal.is_displayed()
        except NoSuchElementException:
            return False

    def _safe_close_reveal(self, card: Any) -> None:
        try:
            close_btn = card.find_element(By.CSS_SELECTOR, "div.card-reveal span.card-title")
            self.driver.execute_script(JS_CLICK, close_btn)
        except Exception:
            return

    def extract_movies(self) -> list[MovieRecord]:
        assert self.driver is not None
        wait = self._wait()
        movies: list[MovieRecord] = []

        cards = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, CARD_SELECTOR)))
        total_cards = len(cards)
        LOGGER.info("Cards encontrados: %s", total_cards)

        for idx in range(total_cards):
            cards = self.driver.find_elements(By.CSS_SELECTOR, CARD_SELECTOR)
            card = cards[idx]

            title_activator = card.find_element(By.CSS_SELECTOR, "span.card-title.activator")
            movie_name = title_activator.text.strip()

            self.driver.execute_script(JS_CLICK, title_activator)
            wait.until(lambda _driver, current_card=card: self._is_reveal_visible(current_card))

            reveal_desc = card.find_element(By.CSS_SELECTOR, "div.card-reveal p")
            description = reveal_desc.text.strip()

            movies.append(MovieRecord(name=movie_name, description=description))
            self._safe_close_reveal(card)

        return movies

    def run(self, query: str) -> list[dict[str, str]]:
        self.open_home()
        self.go_to_movie_search()
        self.search_movies(query=query)
        records = self.extract_movies()
        return [{"name": movie.name, "description": movie.description} for movie in records]
