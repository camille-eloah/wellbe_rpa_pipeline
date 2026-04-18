from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse
from zipfile import ZIP_DEFLATED, ZipFile

import requests
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .utils import ensure_directories


LOGGER = logging.getLogger(__name__)


class InvoiceExtractionPipeline:
    def __init__(self, driver: WebDriver, timeout_seconds: int = 15, table_id: str = "tableSandbox") -> None:
        self.driver = driver
        self.timeout_seconds = timeout_seconds
        self.table_id = table_id

    def _wait(self) -> WebDriverWait:
        return WebDriverWait(self.driver, self.timeout_seconds)

    def navigate_to_invoice_page(self, invoice_url: str) -> None:
        wait = self._wait()
        try:
            link = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "a[href*='rpachallengeocr.azurewebsites.net']")
                )
            )
            self.driver.execute_script("arguments[0].click();", link)
            wait.until(lambda d: "rpachallengeocr.azurewebsites.net" in d.current_url)
        except TimeoutException:
            # Fallback for environments where menu click is intercepted.
            self.driver.get(invoice_url)

        wait.until(EC.presence_of_element_located((By.ID, self.table_id)))
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, f"#{self.table_id} tr")))
        LOGGER.info("Página de Invoice Extraction carregada: %s", self.driver.current_url)

    def get_invoice_links(self, target_indices: Iterable[int]) -> list[tuple[int, str]]:
        targets = {int(i) for i in target_indices}
        rows = self.driver.find_elements(By.CSS_SELECTOR, f"#{self.table_id} tr")
        results: list[tuple[int, str]] = []

        for row in rows:
            cells = row.find_elements(By.CSS_SELECTOR, "td")
            if len(cells) < 4:
                continue

            idx_text = cells[0].text.strip()
            if not idx_text.isdigit():
                continue

            idx = int(idx_text)
            if idx not in targets:
                continue

            link_el = cells[3].find_element(By.CSS_SELECTOR, "a[href]")
            href = link_el.get_attribute("href") or ""
            full_url = urljoin(self.driver.current_url, href)
            results.append((idx, full_url))

        LOGGER.info("Invoices selecionados para download: %s", [idx for idx, _ in results])
        return results

    def download_invoices(self, links: list[tuple[int, str]], output_dir: Path) -> list[Path]:
        ensure_directories([output_dir])
        downloaded: list[Path] = []

        with requests.Session() as session:
            session.headers.update({"User-Agent": "wellbe-rpa-pipeline/1.0"})

            for idx, url in links:
                parsed = urlparse(url)
                ext = Path(parsed.path).suffix or ".jpg"
                file_path = output_dir / f"invoice_{idx}{ext}"

                response = session.get(url, timeout=30)
                response.raise_for_status()
                file_path.write_bytes(response.content)
                downloaded.append(file_path)
                LOGGER.info("Invoice baixado: %s", file_path)

        return downloaded

    def zip_invoices(self, files: list[Path], zip_path: Path) -> Path:
        ensure_directories([zip_path.parent])
        with ZipFile(zip_path, mode="w", compression=ZIP_DEFLATED) as zipf:
            for file_path in files:
                zipf.write(file_path, arcname=file_path.name)
        LOGGER.info("Arquivo ZIP gerado: %s", zip_path)
        return zip_path

    def run(
        self,
        invoice_url: str,
        target_indices: Iterable[int],
        invoices_output_dir: Path,
        zip_output_path: Path,
    ) -> dict[str, object]:
        self.navigate_to_invoice_page(invoice_url=invoice_url)
        links = self.get_invoice_links(target_indices=target_indices)
        files = self.download_invoices(links=links, output_dir=invoices_output_dir)
        zip_path = self.zip_invoices(files=files, zip_path=zip_output_path)

        return {
            "selected_indices": [idx for idx, _ in links],
            "downloaded_files": [str(path) for path in files],
            "zip_file": str(zip_path),
        }
