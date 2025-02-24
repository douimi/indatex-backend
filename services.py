from selenium import webdriver
from selenium.common import TimeoutException, ElementClickInterceptedException, ElementNotInteractableException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import time
import re
import logging
from flask import Flask
from flask_cors import CORS
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import os
from datetime import datetime

# Configure logging for Heroku
app = Flask(__name__)
CORS(app)  # This enables CORS for all routes


# Mailtrap configuration
SMTP_SERVER = "sandbox.smtp.mailtrap.io"
SMTP_PORT = 2525
SMTP_USERNAME = "8bb83b25f0a139"
SMTP_PASSWORD = "bb4796d29dd74f"
SENDER_EMAIL = "notification@indatex.com"


def send_simple_email(recipient, notification_type):
    """
    Helper function to send emails using Mailtrap SMTP
    """
    try:
        # Create message
        message = MIMEMultipart()
        message["From"] = f"Santander Trade API <{SENDER_EMAIL}>"
        message["To"] = recipient

        # Set subject and body based on notification type
        if notification_type == "1":
            subject = "Nouvelle demande"
            body = "Vous avez une nouvelle demande de type 1"
        else:
            subject = "Notification"
            body = "Vous avez une notification de type 2"

        message["Subject"] = subject

        # Create HTML body
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>{subject}</h2>
                <div style="margin: 20px 0;">
                    {body}
                </div>
                <div style="color: gray; font-size: 12px; margin-top: 30px;">
                    Envoyé le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
            </body>
        </html>
        """

        message.attach(MIMEText(html_body, "html"))

        # Send email using Mailtrap
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)

        return True, None

    except Exception as e:
        return False, str(e)

def setup_logging():
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create handlers
    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setLevel(logging.INFO)

    # Create formatters and add it to handlers
    format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(format)

    # Add handlers to the logger
    logger.addHandler(c_handler)

    # Set Flask app logger to use this configuration
    app.logger.handlers = logger.handlers
    app.logger.setLevel(logging.INFO)

def get_chrome_driver():
    app.logger.info("Setting up Chrome driver")
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--silent")
    chrome_options.add_argument("--incognito")

    chrome_binary_path = os.environ.get("GOOGLE_CHROME_SHIM", None)
    if chrome_binary_path:
        chrome_options.binary_location = chrome_binary_path

    service = Service(log_path=os.devnull)
    return webdriver.Chrome(service=service, options=chrome_options)
    # return webdriver.Chrome(options=chrome_options)


def extract_data(driver):
    app.logger.info("Extracting data from the page")
    tenders = []
    trade_shows = []
    summary = {}

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Extract summary information
    summary_card = soup.find('div', class_='card tile')
    if summary_card:
        summary_items = summary_card.find_all('li')
        for item in summary_items:
            if "market reports" in item.text.lower():
                summary['market_reports'] = int(item.find('strong').text.replace(',', ''))
            elif "trade shows" in item.text.lower():
                summary['trade_shows'] = int(item.find('strong').text.replace(',', ''))
            elif "tenders" in item.text.lower():
                summary['tenders'] = int(item.find('strong').text.replace(',', ''))

    # Extract tenders
    tender_cards = soup.find_all('div', class_='card-report-component')
    for card in tender_cards:
        # Check if this is a content update card (which we want to exclude)
        if card.find('span', class_='tag-content-update'):
            continue  # Skip this card and move to the next one

        title_elem = card.find('span', class_='head-title')
        date_elem = card.find('span', class_='head-item head-item-right')
        country_elem = card.find('p', class_='text-ellipsis')

        if title_elem and date_elem and country_elem:
            title = title_elem.text.strip()
            date_posted = date_elem.text.strip().replace('Posted ', '')
            country = country_elem.find('strong').text.strip()

            # Only include the tender if a valid country is found
            if country and country != "N/A":
                tenders.append({
                    "title": title,
                    "type": "Tender",
                    "datePosted": date_posted,
                    "country": country
                })

    # Extract trade shows
    trade_show_cards = soup.find_all('div', class_='card-trade-component')
    for card in trade_show_cards:
        title_elem = card.find('span', class_='head-title')
        date_elem = card.find('span', class_='head-item head-item-right')
        description_elem = card.find('p', class_='description')
        date_info = card.find_all('p', class_='')
        location_elem = card.find('div', class_='col-text')

        if title_elem and date_elem:
            title = title_elem.text.strip()
            date_posted = date_elem.text.strip().replace('Posted ', '')
            description = description_elem.text.strip() if description_elem else "N/A"
            start_date = date_info[0].find('strong').text.strip() if len(date_info) > 0 else "N/A"
            end_date = date_info[1].find('strong').text.strip() if len(date_info) > 1 else "N/A"
            location = location_elem.find('strong').text.strip() if location_elem else "N/A"

            trade_shows.append({
                "title": title,
                "type": "Trade show",
                "description": description,
                "datePosted": date_posted,
                "startDate": start_date,
                "endDate": end_date,
                "location": location
            })

    app.logger.info(f"Extracted {len(tenders)} tenders and {len(trade_shows)} trade shows")
    return summary, tenders, trade_shows


def wait_for_overlay_disappear(driver, timeout=30):
    app.logger.info(f"Waiting for overlay to disappear (timeout: {timeout}s)")
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.find_element(By.ID, "card-load").get_attribute("style") == "display: none;"
        )
        app.logger.info("Overlay disappeared")
    except TimeoutException:
        app.logger.warning("Timeout waiting for overlay to disappear")


def scroll_to_element_and_click(driver, element):
    app.logger.info("Attempting to scroll to element and click using JavaScript")
    driver.execute_script("arguments[0].scrollIntoView(true);", element)
    time.sleep(1)  # Give the page a moment to settle after scrolling
    driver.execute_script("arguments[0].click();", element)


def click_with_retry(driver, element, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            element.click()
            app.logger.info(f"Successfully clicked element on attempt {attempt + 1}")
            return True
        except (ElementClickInterceptedException, ElementNotInteractableException):
            if attempt < max_attempts - 1:
                app.logger.warning(f"Click failed, retrying (attempt {attempt + 1})")
                time.sleep(1)
                wait_for_overlay_disappear(driver)
                scroll_to_element_and_click(driver, element)
            else:
                app.logger.error(f"Failed to click element after {max_attempts} attempts")
                return False


def search_and_extract(driver, country, interest=None):
    app.logger.info(f"Searching for country: {country}, interest: {interest}")

    time.sleep(2)
    # click on accept cookies button
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="accept-necessary-cookie"]'))
    ).click()

    # Wait for the input field and fill it
    input_field = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, "/html/body/div[2]/div/div[2]/form/div/div/div[2]/div/div/span/span[1]/span/ul/li/input"))
    )

    input_field.send_keys(country)
    input_field.send_keys(Keys.RETURN)

    # Click the search button
    search_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div/div[2]/form/div/div/div[2]/div/div/button"))
    )
    click_with_retry(driver, search_button)

    # Wait for the loading overlay to disappear
    wait_for_overlay_disappear(driver)

    # If interest is provided, add it to the search
    if interest:
        app.logger.info(f"Adding interest: {interest} to the search")
        # Click the industry filter button
        industry_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='btn_filter_industries']"))
        )
        if not click_with_retry(driver, industry_button):
            app.logger.warning("Failed to click industry button using normal methods. Attempting JavaScript click.")
            scroll_to_element_and_click(driver, industry_button)

        # Wait for the modal to appear and fill the interest
        interest_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@id='modal-filter-interex']/div/div/div[2]/span/span[1]/span/ul/li/input"))
        )
        time.sleep(2)
        interest_input.send_keys(interest)
        interest_input.send_keys(Keys.RETURN)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="btn_close_filter_industry"]'))
        ).click()
        time.sleep(5)

    # Extract data
    return extract_data(driver)


def extract_economic_political_outline(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    outline_info = {
        "economic_outline": {},
        "political_outline": {},
        "covid_19_response": {}
    }

    # Extract Economic Outline
    economic_section = soup.find('h2', text='Economic Outline')
    if economic_section:
        # Extract Economic Overview
        overview = economic_section.find_next('h3', text='Economic Overview')
        if overview:
            overview_text = overview.find_next('p').text.strip()
            outline_info["economic_outline"]["overview"] = overview_text

        # Extract Breakdown of Economic Activity By Sector
        breakdown_table = soup.find('th', text='Breakdown of Economic Activity By Sector')
        if breakdown_table:
            table = breakdown_table.find_parent('table')
            rows = table.find_all('tr')[1:]  # Skip header row
            breakdown_data = {}
            for row in rows:
                cells = row.find_all(['th', 'td'])
                category = cells[0].text.strip()
                breakdown_data[category] = {
                    "Agriculture": cells[1].text.strip(),
                    "Industry": cells[2].text.strip(),
                    "Services": cells[3].text.strip()
                }
            outline_info["economic_outline"]["economic_activity_breakdown"] = breakdown_data

        # Extract Main Indicators
        indicators_table = soup.find('th', text='Main Indicators')
        if indicators_table:
            table = indicators_table.find_parent('table')
            rows = table.find_all('tr')[1:]  # Skip header row
            indicators_data = {}
            years = ["2022", "2023 (E)", "2024 (E)", "2025 (E)", "2026 (E)"]
            for row in rows:
                cells = row.find_all(['th', 'td'])
                indicator = cells[0].text.strip()
                values = [cell.text.strip() for cell in cells[1:]]
                indicators_data[indicator] = dict(zip(years, values))
            outline_info["economic_outline"]["main_indicators"] = indicators_data

        # Extract Main Sectors of Industry
        sectors = economic_section.find_next('h3', text='Main Sectors of Industry')
        if sectors:
            sectors_text = sectors.find_next('p').decode_contents()
            outline_info["economic_outline"]["main_sectors"] = sectors_text

        # Extract Economic Freedom Indicator
        economic_freedom = soup.find('h3', text='Indicator of Economic Freedom')
        if economic_freedom:
            freedom_info = economic_freedom.find_next('dl', class_='informations')
            if freedom_info:
                outline_info["economic_outline"]["economic_freedom"] = {
                    "score": freedom_info.find('dt', text='Score:').find_next('dd').text.strip(),
                    "world_rank": freedom_info.find('dt', text='World Rank:').find_next('dd').text.strip(),
                    "regional_rank": freedom_info.find('dt', text='Regional Rank:').find_next('dd').text.strip()
                }

        # Extract Business Environment Ranking
        business_env = soup.find('h3', text='Business environment ranking')
        if business_env:
            env_info = business_env.find_next('dl', class_='informations')
            if env_info:
                outline_info["economic_outline"]["business_environment"] = {
                    "score": env_info.find('dt', text='Score:').find_next('dd').text.strip(),
                    "world_rank": env_info.find('dt', text='World Rank:').find_next('dd').text.strip()
                }

        # Extract Country Risk
        country_risk = soup.find('h3', text='Country Risk')
        if country_risk:
            risk_text = country_risk.find_next('p').text.strip()
            outline_info["economic_outline"]["country_risk"] = risk_text

        # Extract Sources of General Economic Information
        sources = soup.find('h3', text='Sources of General Economic Information')
        if sources:
            sources_info = sources.find_next('dl', class_='informations')
            if sources_info:
                outline_info["economic_outline"]["sources"] = {}
                for dt in sources_info.find_all('dt'):
                    category = dt.text.strip()
                    links = dt.find_next('dd').find_all('a')
                    outline_info["economic_outline"]["sources"][category] = [
                        {"name": link.text.strip(), "url": link['href']} for link in links]

    # Extract Political Outline
    political_section = soup.find('h2', text='Political Outline')
    if political_section:
        info_dl = political_section.find_next('dl', class_='informations')
        if info_dl:
            for dt in info_dl.find_all('dt'):
                key = dt.text.strip()
                if key == "Next Election Dates":
                    value = dt.find_next('dd').decode_contents()
                    outline_info["political_outline"][key] = value
                else:
                    value = dt.find_next('dd').text.strip()
                    outline_info["political_outline"][key] = value

        # Extract Freedom of the Press
        press_freedom = soup.find('h3', text='Indicator of Freedom of the Press')
        if press_freedom:
            freedom_info = press_freedom.find_next('dl', class_='informations')
            if freedom_info:
                outline_info["political_outline"]["freedom_of_press"] = {
                    "world_rank": freedom_info.find('dt', text='World Rank:').find_next('dd').text.strip()
                }

        # Extract Political Freedom
        political_freedom = soup.find('h3', text='Indicator of Political Freedom')
        if political_freedom:
            freedom_info = political_freedom.find_next('dl', class_='informations')
            if freedom_info:
                outline_info["political_outline"]["political_freedom"] = {
                    "ranking": freedom_info.find('dt', text='Ranking:').find_next('dd').text.strip(),
                    "political_freedom": freedom_info.find('dt', text='Political Freedom:').find_next(
                        'dd').text.strip(),
                    "civil_liberties": freedom_info.find('dt', text='Civil Liberties:').find_next('dd').text.strip()
                }

    # Extract COVID-19 Country Response
    covid_section = soup.find('h2', text='COVID-19 Country Response')
    if covid_section:
        info_dl = covid_section.find_next('dl', class_='informations')
        if info_dl:
            for dt in info_dl.find_all('dt'):
                key = dt.text.strip()
                value = dt.find_next('dd').text.strip()
                outline_info["covid_19_response"][key] = value

    return outline_info


def extract_general_info(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    general_info = {}

    # Extract country name
    country_name = soup.select_one('#pays_v1 span.txt-h1_v1')
    if country_name:
        general_info['country_name'] = country_name.text.strip()

    # Extract basic information
    basic_info = soup.select_one('#donnees1')
    if basic_info:
        for div in basic_info.select('div.titre-donnees'):
            key = div.select_one('span.sous-titre-encart')
            if key:
                key = key.text.strip().rstrip(':')
                value = div.text.replace(key, '').strip().lstrip(':').strip()
                general_info[key] = value

    # Extract telecommunication information
    telecom_info = soup.select_one('#donnees2')
    if telecom_info:
        for div in telecom_info.select('div.titre-donnees'):
            key = div.select_one('span.sous-titre-encart')
            if key:
                key = key.text.strip().rstrip(':')
                value = div.text.replace(key, '').strip().lstrip(':').strip()
                general_info[key] = value

    # Extract foreign trade information
    trade_table = soup.select_one('table')
    if trade_table:
        trade_info = []
        headers = [th.text.strip() for th in trade_table.select('thead th')]
        for row in trade_table.select('tbody tr'):
            row_data = [td.text.strip() for td in row.select('td')]
            trade_info.append(dict(zip(headers, row_data)))
        general_info['foreign_trade'] = trade_info

    return general_info


def extract_foreign_trade_forecasts(soup):
    try:
        # Find all tables in the document
        tables = soup.find_all('table')

        for table in tables:
            # Check if the table contains the text "Foreign Trade Forecasts"
            if 'Foreign Trade Forecasts' in table.text:
                app.logger.info("Foreign Trade Forecasts table found")

                # Extract headers (years)
                headers = [th.text.strip() for th in table.find_all('th')[1:]]  # Skip the first header
                app.logger.debug(f"Extracted headers: {headers}")

                # Initialize data structure
                data = {"Indicator": []}
                for header in headers:
                    data[header] = []

                # Extract rows
                rows = table.find_all('tr')[1:]  # Skip header row

                for row in rows:
                    cells = row.find_all(['th', 'td'])
                    if cells:
                        # Extract indicator
                        indicator = cells[0].text.strip()
                        data["Indicator"].append(indicator)
                        app.logger.debug(f"Extracted indicator: {indicator}")

                        # Extract values for each year
                        for i, cell in enumerate(cells[1:], 1):
                            if i <= len(headers):
                                value = cell.text.strip()
                                data[headers[i - 1]].append(value)
                                app.logger.debug(f"Extracted value for {headers[i - 1]}: {value}")

                app.logger.info("Data extraction complete for Foreign Trade Forecasts")
                app.logger.debug(f"Extracted data: {data}")
                return {"title": "Foreign Trade Forecasts", "data": data}

        app.logger.warning("Foreign Trade Forecasts table not found")
        return {"title": "Foreign Trade Forecasts", "data": {}}

    except Exception as e:
        app.logger.error(f"Error extracting Foreign Trade Forecasts table: {str(e)}", exc_info=True)
        return {"title": "Foreign Trade Forecasts", "data": {}}


def extract_overview(soup):
    try:
        overview_div = soup.find('div', id='encart-theme-atlas')
        if overview_div:
            overview_p = overview_div.find('p')
            if overview_p:
                return overview_p.text.strip()
        app.logger.warning("Overview not found")
        return ""
    except Exception as e:
        app.logger.error(f"Error extracting overview: {str(e)}", exc_info=True)
        return ""


def extract_table_by_content(soup, table_name):
    try:
        tables = soup.find_all('table')

        for table in tables:
            if table_name.lower() in table.text.lower():
                app.logger.info(f"Table '{table_name}' found")

                # Extract headers from the thead section
                thead = table.find('thead')
                if thead:
                    headers = [td.text.strip() for td in thead.find_all('td') if td.get('class') != ['simple']]
                else:
                    headers = [th.text.strip() for th in table.find_all('th') if th.get('class') != ['simple']]

                app.logger.debug(f"Headers extracted: {headers}")

                # Initialize data structure
                data = {"Indicator": []}
                for header in headers:
                    data[header] = []

                # Extract rows from the tbody section
                tbody = table.find('tbody')
                if tbody:
                    rows = tbody.find_all('tr')
                else:
                    rows = table.find_all('tr')[1:]  # Skip header row if no tbody

                app.logger.debug(f"Number of rows found: {len(rows)}")

                for row in rows:
                    cells = row.find_all('td')
                    app.logger.debug(f"Number of cells in row: {len(cells)}")
                    if cells:
                        # Extract indicator from the first cell
                        indicator = ' '.join(cells[0].stripped_strings)
                        indicator = re.sub(r'\s+', ' ', indicator).strip()
                        data["Indicator"].append(indicator)
                        app.logger.debug(f"Indicator extracted: {indicator}")

                        # Extract values for each year
                        for i, cell in enumerate(cells[1:], 1):
                            if i <= len(headers):
                                value = cell.text.strip()
                                data[headers[i - 1]].append(value)
                                app.logger.debug(f"Value extracted for {headers[i - 1]}: {value}")

                app.logger.info(f"Data extraction complete for '{table_name}'")
                app.logger.debug(f"Extracted data: {data}")
                return {"title": table_name, "data": data}

        app.logger.warning(f"Table '{table_name}' not found")
        return {"title": table_name, "data": {}}
    except Exception as e:
        app.logger.error(f"Error extracting table '{table_name}': {str(e)}", exc_info=True)
        return {"title": table_name, "data": {}}


def extract_text_content(soup, section_name):
    try:
        dt = soup.find('dt', string=re.compile(section_name, re.IGNORECASE))
        if dt:
            dd = dt.find_next('dd')
            if dd:
                return dd.text.strip()
        app.logger.warning(f"Section '{section_name}' not found")
        return ""
    except Exception as e:
        app.logger.error(f"Error extracting text content for '{section_name}': {str(e)}", exc_info=True)
        return ""


def extract_partner_table(soup, table_name):
    try:
        table_class = 'tableau1' if "customer" in table_name.lower() else 'tableau2'
        table = soup.find('table', class_=table_class)
        if not table:
            app.logger.warning(f"Partner table '{table_name}' not found")
            return {"title": table_name, "data": []}

        rows = table.find_all('tr')[1:]  # Skip header row
        data = []
        for row in rows:
            cells = row.find_all('td')
            if len(cells) == 2:
                country = cells[0].text.strip()
                percentage = cells[1].text.strip()
                if country and percentage != "N/A" and not country.startswith("Close Extended List"):
                    data.append({"Country": country, "Percentage": percentage})

        return {"title": table_name, "data": data}
    except Exception as e:
        app.logger.error(f"Error extracting partner table '{table_name}': {str(e)}", exc_info=True)
        return {"title": table_name, "data": []}

def extract_import_export_flow(driver, flow, code, reporter, partners):
    try:
        url = f"https://santandertrade.com/en/portal/analyse-markets/import-export-flow?flow={flow}&code={code}&reporter={reporter}&partners={partners}"
        driver.get(url)

        # Wait for the content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ief-widget_result-table"))
        )

        # Extract the page content
        page_content = driver.page_source
        soup = BeautifulSoup(page_content, 'html.parser')

        # Extract the title and description
        title = soup.select_one('.ief-widget_result-title').text.strip()
        description = soup.select_one('.ief-widget_result-description').text.strip()

        # Extract the table data
        table = soup.select_one('.ief-widget_result-table')
        headers = [th.text.strip() for th in table.select('th')]
        rows = []
        for tr in table.select('tr')[1:]:  # Skip the header row
            row = [td.text.strip() for td in tr.select('td')]
            rows.append(dict(zip(headers, row)))

        # Extract the source information
        source = soup.select_one('.ief-widget_result-source').text.strip()

        data = {
            "title": title,
            "description": description,
            "data": rows,
            "source": source
        }

        return data

    except Exception as e:
        app.logger.error(f"Error extracting import-export flow data: {str(e)}", exc_info=True)
        return {"error": str(e)}


def extract_trading_countries(soup, block_class, is_growth=False):
    """
    Extract trading country data from a specific block
    """
    data = []
    block = soup.find('div', class_=block_class)

    if not block:
        return data

    # For growth sections, find the second instance if it exists
    if is_growth:
        blocks = soup.find_all('div', class_=block_class)
        if len(blocks) > 1:
            block = blocks[1]

    # Extract country data from tables
    tables = block.find_all('table', class_='invisible')
    for table in tables:
        # Skip the "See More Countries" link table
        if table.find('a', text=lambda t: t and 'See More Countries' in t):
            continue

        row = table.find('tr')
        if row:
            cells = row.find_all('td')
            if len(cells) >= 2:
                country_data = {
                    "country": cells[0].text.strip(),
                    "value": cells[1].text.strip()
                }
                data.append(country_data)

    # Extract total value if available
    total = block.find('p', class_='total-surligne')
    if total:
        total_text = total.text.strip()
        # Add it as the last item with a special key
        data.append({"total": total_text})

    return data


def extract_legal_forms_selenium(driver):
    """Extract legal forms of companies information using Selenium"""
    legal_forms = {}
    try:
        # Find the legal forms section
        forms_elements = driver.find_elements(By.XPATH,
                                              "//h2[contains(text(),'Legal Forms of Companies')]/following-sibling::div[1]//dl/dt")

        for form_element in forms_elements:
            company_type = form_element.text.strip()
            details = {}

            # Get the next dd element after this dt
            dd_element = form_element.find_element(By.XPATH, "following-sibling::dd[1]")
            spans = dd_element.find_elements(By.XPATH, ".//span")

            for span in spans:
                text = span.text.strip()
                if ':' in text:
                    key, value = text.split(':', 1)
                    details[key.strip().replace('b>', '')] = value.strip()

            legal_forms[company_type] = details

        return legal_forms
    except Exception as e:
        app.logger.error(f"Error extracting legal forms: {str(e)}")
        return {}


def extract_business_setup_selenium(driver):
    """Extract business setup procedures information using Selenium"""
    setup_info = {
        'procedures': {},
        'competent_organisation': '',
        'further_information': []
    }

    try:
        # Extract procedures table
        rows = driver.find_elements(By.XPATH, "//table[contains(@class,'colonnes-5')]//tr")
        headers = rows[0].find_elements(By.XPATH, ".//th")
        header_texts = [h.text.strip() for h in headers]

        for row in rows[1:]:
            cells = row.find_elements(By.XPATH, ".//td")
            if cells:
                metric = cells[0].text.strip()
                setup_info['procedures'][metric] = {
                    header_texts[1]: cells[1].text.strip(),
                    header_texts[2]: cells[2].text.strip()
                }

        # Extract competent organisation
        org_element = driver.find_element(By.XPATH,
                                          "//dt[contains(text(),'The Competent Organisation')]/following-sibling::dd[1]")
        setup_info['competent_organisation'] = org_element.text.strip()

        # Extract further information
        info_elements = driver.find_elements(By.XPATH,
                                             "//dt[contains(text(),'For Further Information')]/following-sibling::dd[1]//a")
        for element in info_elements:
            setup_info['further_information'].append({
                'name': element.text.strip(),
                'url': element.get_attribute('href')
            })

        return setup_info
    except Exception as e:
        app.logger.error(f"Error extracting business setup: {str(e)}")
        return setup_info


def extract_financial_directories_selenium(driver):
    """Extract financial information directories using Selenium"""
    directories = []
    try:
        directory_elements = driver.find_elements(By.XPATH,
                                                  "//h2[contains(text(),'Financial Information Directories')]/following-sibling::p")

        for element in directory_elements:
            link = element.find_element(By.XPATH, ".//a")
            directories.append({
                'name': link.text.strip(),
                'url': link.get_attribute('href'),
                'description': element.text.replace(link.text, '').strip()
            })

        return directories
    except Exception as e:
        app.logger.error(f"Error extracting financial directories: {str(e)}")
        return []


def extract_recovery_procedures_selenium(driver):
    """Extract recovery procedures information using Selenium"""
    recovery = {}
    try:
        sections = driver.find_elements(By.XPATH,
                                        "//h2[contains(text(),'Recovery Procedures')]/following-sibling::dl[1]/dt")

        for section in sections:
            key = section.text.strip()
            dd_element = section.find_element(By.XPATH, "following-sibling::dd[1]")
            recovery[key] = dd_element.text.strip()

        return recovery
    except Exception as e:
        app.logger.error(f"Error extracting recovery procedures: {str(e)}")
        return {}


def extract_active_population_selenium(driver):
    """Extract active population figures using Selenium"""
    population_data = {
        'labour_force': {},
        'activity_rates': {},
        'further_information': {}
    }

    try:
        # Wait for the active population section
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[text()='The Active Population in Figures']"))
        )

        # Extract labour force data
        try:
            # Find the first table
            labour_force_table = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH,
                                                "//h2[text()='The Active Population in Figures']/following::table[1]"))
            )

            # Get headers
            headers = labour_force_table.find_elements(By.XPATH, ".//th[@class='simple']")
            header_texts = [h.text.strip() for h in headers]

            # Get data row
            data_cells = labour_force_table.find_elements(By.XPATH, ".//tr[th[contains(@class, 'gras')]]/td")

            for i, header in enumerate(header_texts):
                if i < len(data_cells):
                    value = data_cells[i].text.strip()
                    if value:
                        population_data['labour_force'][header] = value
        except Exception as e:
            app.logger.warning(f"Error extracting labour force data: {str(e)}")

        # Extract activity rates
        try:
            # Find the second table
            rates_table = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH,
                                                "//h2[text()='The Active Population in Figures']/following::table[2]"))
            )

            # Get headers
            rate_headers = rates_table.find_elements(By.XPATH, ".//th[@class='simple']")
            rate_header_texts = [h.text.strip() for h in rate_headers]

            # Get rows with rate data
            rate_rows = rates_table.find_elements(By.XPATH, ".//tr[th[contains(@class, 'gras')]]")

            for row in rate_rows:
                try:
                    rate_type = row.find_element(By.XPATH, ".//th").text.strip()
                    rate_cells = row.find_elements(By.XPATH, ".//td")
                    rate_data = {}

                    for i, header in enumerate(rate_header_texts):
                        if i < len(rate_cells):
                            value = rate_cells[i].text.strip().replace('%', '')
                            if value:
                                rate_data[header] = value

                    if rate_data:
                        population_data['activity_rates'][rate_type] = rate_data
                except Exception as e:
                    app.logger.warning(f"Error processing rate row: {str(e)}")
                    continue
        except Exception as e:
            app.logger.warning(f"Error extracting activity rates: {str(e)}")

        # Extract further information
        try:
            # Find both "For Further Statistics" and "For Further Information" sections
            info_sections = driver.find_elements(By.XPATH,
                                                 "//dt[contains(text(), 'For Further')]")

            for section in info_sections:
                try:
                    category = section.text.strip()
                    # Find the corresponding dd element
                    dd_element = section.find_element(By.XPATH, "following-sibling::dd[1]")

                    # Find all links within this dd element
                    links = dd_element.find_elements(By.XPATH, ".//a")

                    if category not in population_data['further_information']:
                        population_data['further_information'][category] = []

                    for link in links:
                        try:
                            link_data = {
                                'name': link.text.strip(),
                                'url': link.get_attribute('href')
                            }
                            population_data['further_information'][category].append(link_data)
                        except Exception as e:
                            app.logger.warning(f"Error processing link: {str(e)}")
                            continue
                except Exception as e:
                    app.logger.warning(f"Error processing section {category}: {str(e)}")
                    continue
        except Exception as e:
            app.logger.warning(f"Error extracting further information: {str(e)}")

        return population_data

    except Exception as e:
        app.logger.error(f"Error extracting active population: {str(e)}")
        return population_data


def extract_working_conditions_selenium(driver):
    """Extract working conditions information using Selenium"""
    working_conditions = {}
    try:
        # Wait for working conditions section
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(text(),'Working Conditions')]"))
        )

        # Extract opening hours section
        opening_hours = driver.find_elements(By.XPATH,
                                             "//dt[text()='Opening Hours']/following-sibling::dt[position()=1]/ul/li")
        if opening_hours:
            working_conditions['opening_hours'] = {}
            for item in opening_hours:
                # Get the li text and its corresponding dd
                key = item.text.strip()
                value = item.find_element(By.XPATH, "ancestor::dt/following-sibling::dd[1]").text.strip()
                working_conditions['opening_hours'][key] = value

        # Extract general working conditions
        condition_elements = driver.find_elements(By.XPATH, "//dt[@class='agauche gras']")
        for element in condition_elements:
            key = element.text.strip()
            if key:
                value = element.find_element(By.XPATH, "following-sibling::dd[1]").text.strip()
                working_conditions[key] = value

        return working_conditions

    except Exception as e:
        app.logger.error(f"Error extracting working conditions: {str(e)}")
        return {}


def extract_labour_cost_selenium(driver):
    """Extract labour cost information using Selenium"""
    labour_cost = {
        'pay': {},
        'other_forms_of_pay': {}
    }
    try:
        # Wait for labour cost section
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(text(),'The Cost of Labour')]"))
        )

        # Extract main pay information (minimum wage, average wage)
        pay_elements = driver.find_elements(By.XPATH, "//dt[@class='agauche gras']")
        for element in pay_elements:
            key = element.text.strip()
            if key in ['Minimum Wage', 'Average Wage']:
                value = element.find_element(By.XPATH, "following-sibling::dd[1]").text.strip()
                labour_cost['pay'][key] = value

        # Extract other forms of pay
        other_pay_elements = driver.find_elements(By.XPATH, "//dt[.//li[contains(text(),'Pay For')]]")
        for element in other_pay_elements:
            key = element.find_element(By.XPATH, ".//li").text.strip()
            value = element.find_element(By.XPATH, "following-sibling::dd[1]").text.strip()
            labour_cost['other_forms_of_pay'][key] = value

        return labour_cost

    except Exception as e:
        app.logger.error(f"Error extracting labour cost: {str(e)}")
        return {'pay': {}, 'other_forms_of_pay': {}}


def extract_social_security_selenium(driver):
    """Extract social security costs information using Selenium"""
    social_security = {}
    try:
        # Wait for social security section
        section = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h3[contains(text(),'Social Security Costs')]"))
        )

        # Extract areas covered
        areas_element = driver.find_element(By.XPATH,
                                            "//dt[contains(text(),'The Areas Covered')]/following-sibling::dd[1]")
        if areas_element:
            social_security['areas_covered'] = areas_element.text.strip()

        # Extract contributions
        contributions_element = driver.find_element(By.XPATH,
                                                    "//dt[contains(text(),'Contributions')]/following-sibling::dd[1]")
        if contributions_element:
            # Split employer and employee contributions
            contributions_text = contributions_element.text.strip()
            employer_contributions = []
            employee_contributions = []

            # Process the text content
            lines = contributions_text.split('\n')
            current_category = None

            for line in lines:
                if 'Contributions Paid By the Employer:' in line:
                    current_category = 'employer'
                    continue
                elif 'Contributions Paid By the Employee:' in line:
                    current_category = 'employee'
                    continue

                if current_category == 'employer':
                    employer_contributions.append(line.strip())
                elif current_category == 'employee':
                    employee_contributions.append(line.strip())

            social_security['contributions'] = {
                'employer': employer_contributions,
                'employee': employee_contributions
            }

        return social_security

    except Exception as e:
        app.logger.error(f"Error extracting social security: {str(e)}")
        return {}


def extract_corporate_taxes_selenium(driver):
    """Extract corporate taxes information using Selenium"""
    corporate_taxes = {
        'tax_base': '',
        'tax_rates': [],
        'foreign_companies': '',
        'capital_gains': '',
        'allowable_deductions': '',
        'other_taxes': '',
        'country_comparison': {}
    }

    try:
        # Wait for corporate taxes section
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[text()='Corporate Taxes']"))
        )

        # Extract tax base
        tax_base = driver.find_element(By.XPATH,
                                       "//dt[contains(text(), 'Tax Base For Resident')]/following-sibling::dd[1]")
        if tax_base:
            corporate_taxes['tax_base'] = tax_base.text.strip()

        # Extract tax rates table
        tax_rates_table = driver.find_elements(By.XPATH,
                                               "//h4[text()='Tax Rate']/following-sibling::table[1]//tr")
        for row in tax_rates_table:
            cells = row.find_elements(By.XPATH, ".//td")
            if len(cells) == 2:
                corporate_taxes['tax_rates'].append({
                    'category': cells[0].text.strip(),
                    'rate': cells[1].text.strip()
                })

        # Extract foreign companies info
        foreign_companies = driver.find_element(By.XPATH,
                                                "//dt[contains(text(), 'Tax Rate For Foreign Companies')]/following-sibling::dd[1]")
        if foreign_companies:
            corporate_taxes['foreign_companies'] = foreign_companies.text.strip()

        # Extract capital gains info
        capital_gains = driver.find_element(By.XPATH,
                                            "//dt[contains(text(), 'Capital Gains Taxation')]/following-sibling::dd[1]")
        if capital_gains:
            corporate_taxes['capital_gains'] = capital_gains.text.strip()

        # Extract allowable deductions
        deductions = driver.find_element(By.XPATH,
                                         "//dt[contains(text(), 'Main Allowable Deductions')]/following-sibling::dd[1]")
        if deductions:
            corporate_taxes['allowable_deductions'] = deductions.text.strip()

        # Extract other taxes
        other_taxes = driver.find_element(By.XPATH,
                                          "//dt[contains(text(), 'Other Corporate Taxes')]/following-sibling::dd[1]")
        if other_taxes:
            corporate_taxes['other_taxes'] = other_taxes.text.strip()

        # Extract country comparison table
        comparison_table = driver.find_elements(By.XPATH,
                                                "//h4[contains(text(), 'Country Comparison')]/following-sibling::table[1]//tr")
        headers = [th.text.strip() for th in comparison_table[0].find_elements(By.XPATH, ".//th")]

        for row in comparison_table[1:]:
            metric = row.find_element(By.XPATH, ".//th").text.strip()
            values = row.find_elements(By.XPATH, ".//td")
            corporate_taxes['country_comparison'][metric] = {
                headers[i]: values[i].text.strip()
                for i in range(len(headers))
            }

        return corporate_taxes

    except Exception as e:
        app.logger.error(f"Error extracting corporate taxes: {str(e)}")
        return corporate_taxes


def extract_accounting_rules_selenium(driver):
    """Extract accounting rules information using Selenium"""
    accounting_rules = {
        'accounting_system': {},
        'accounting_practices': {},
        'accountancy_profession': {}
    }

    try:
        # Wait for accounting rules section
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[text()='Accounting Rules']"))
        )

        # Extract accounting system info
        system_section = driver.find_element(By.XPATH, "//h3[text()='Accounting System']")
        if system_section:
            dts = system_section.find_elements(By.XPATH,
                                               "following-sibling::dl[1]/dt")
            for dt in dts:
                key = dt.text.strip()
                dd = dt.find_element(By.XPATH, "following-sibling::dd[1]")
                accounting_rules['accounting_system'][key] = dd.text.strip()

        # Extract accounting practices
        practices_section = driver.find_element(By.XPATH, "//h3[text()='Accounting Practices']")
        if practices_section:
            dts = practices_section.find_elements(By.XPATH,
                                                  "following-sibling::dl[1]/dt")
            for dt in dts:
                key = dt.text.strip()
                dd = dt.find_element(By.XPATH, "following-sibling::dd[1]")
                accounting_rules['accounting_practices'][key] = dd.text.strip()

        # Extract accountancy profession info
        profession_section = driver.find_element(By.XPATH, "//h3[text()='Accountancy Profession']")
        if profession_section:
            dts = profession_section.find_elements(By.XPATH,
                                                   "following-sibling::dl[1]/dt")
            for dt in dts:
                key = dt.text.strip()
                dd = dt.find_element(By.XPATH, "following-sibling::dd[1]")
                accounting_rules['accountancy_profession'][key] = dd.text.strip()

        return accounting_rules

    except Exception as e:
        app.logger.error(f"Error extracting accounting rules: {str(e)}")
        return accounting_rules


def extract_individual_taxes_selenium(driver):
    """Extract individual taxes information using Selenium"""
    individual_taxes = {
        'tax_base': '',
        'tax_rates': [],
        'allowable_deductions': '',
        'special_expatriate_regime': '',
        'capital_tax_rate': ''
    }

    try:
        # Wait for individual taxes section
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[text()='Individual Taxes']"))
        )

        # Extract tax base
        tax_base = driver.find_element(By.XPATH,
                                       "//dt[contains(text(), 'Tax Base For Residents')]/following-sibling::dd[1]")
        if tax_base:
            individual_taxes['tax_base'] = tax_base.text.strip()

        # Extract tax rates table
        tax_rates_table = driver.find_elements(By.XPATH,
                                               "//h4[text()='Tax Rate']/following-sibling::table[1]//tr")
        for row in tax_rates_table:
            cells = row.find_elements(By.XPATH, ".//td")
            if len(cells) == 2:
                individual_taxes['tax_rates'].append({
                    'bracket': cells[0].text.strip(),
                    'rate': cells[1].text.strip()
                })

        # Extract other sections
        sections = {
            'allowable_deductions': "//dt[contains(text(), 'Allowable Deductions')]/following-sibling::dd[1]",
            'special_expatriate_regime': "//dt[contains(text(), 'Special Expatriate')]/following-sibling::dd[1]",
            'capital_tax_rate': "//dt[contains(text(), 'Capital Tax Rate')]/following-sibling::dd[1]"
        }

        for key, xpath in sections.items():
            element = driver.find_element(By.XPATH, xpath)
            if element:
                individual_taxes[key] = element.text.strip()

        return individual_taxes

    except Exception as e:
        app.logger.error(f"Error extracting individual taxes: {str(e)}")
        return individual_taxes


def extract_taxation_treaties_selenium(driver):
    """Extract double taxation treaties information using Selenium"""
    treaties = {
        'countries': [],
        'withholding_taxes': '',
        'bilateral_agreement': ''
    }

    try:
        # Wait for treaties section
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Double Taxation Treaties')]"))
        )

        # Extract countries with treaties
        countries_element = driver.find_element(By.XPATH,
                                                "//dt[contains(text(), 'Countries With Whom')]/following-sibling::dd[1]")
        if countries_element:
            links = countries_element.find_elements(By.XPATH, ".//a")
            for link in links:
                treaties['countries'].append({
                    'name': link.text.strip(),
                    'url': link.get_attribute('href')
                })

        # Extract withholding taxes info
        withholding = driver.find_element(By.XPATH,
                                          "//dt[text()='Withholding Taxes']/following-sibling::dd[1]")
        if withholding:
            treaties['withholding_taxes'] = withholding.text.strip()

        # Extract bilateral agreement info if exists
        bilateral = driver.find_element(By.XPATH,
                                        "//dt[text()='Bilateral Agreement']/following-sibling::dd[1]")
        if bilateral:
            treaties['bilateral_agreement'] = bilateral.text.strip()

        return treaties

    except Exception as e:
        app.logger.error(f"Error extracting taxation treaties: {str(e)}")
        return treaties


def extract_fiscal_sources_selenium(driver):
    """Extract sources of fiscal information using Selenium"""
    sources = {
        'tax_authorities': [],
        'domestic_resources': [],
        'country_guides': []
    }

    try:
        # Wait for sources section
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Sources of Fiscal Information')]"))
        )

        # Extract all source sections
        sections = {
            'tax_authorities': "//dt[text()='Tax Authorities']/following-sibling::dd[1]",
            'domestic_resources': "//dt[text()='Other Domestic Resources']/following-sibling::dd[1]",
            'country_guides': "//dt[text()='Country Guides']/following-sibling::dd[1]"
        }

        for key, xpath in sections.items():
            element = driver.find_element(By.XPATH, xpath)
            if element:
                links = element.find_elements(By.XPATH, ".//a")
                for link in links:
                    sources[key].append({
                        'name': link.text.strip(),
                        'url': link.get_attribute('href')
                    })

        return sources

    except Exception as e:
        app.logger.error(f"Error extracting fiscal sources: {str(e)}")
        return sources


def extract_business_contract_selenium(driver):
    """Extract business contract information using Selenium"""
    contract_info = {
        'general_observation': '',
        'applicable_law': '',
        'incoterms': '',
        'language': '',
        'other_laws': ''
    }

    try:
        # Wait for business contract section
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[text()='Business Contract']"))
        )

        # Extract each subsection
        sections = {
            'general_observation': "//dt[text()='General Observation']/following-sibling::dd[1]",
            'applicable_law': "//dt[text()='Law Applicable to the Contract']/following-sibling::dd[1]",
            'incoterms': "//dt[text()='Advisable Incoterms']/following-sibling::dd[1]",
            'language': "//dt[text()='Language of Domestic Contract']/following-sibling::dd[1]",
            'other_laws': "//dt[text()='Other Laws Which Can Be Used in Domestic Contracts']/following-sibling::dd[1]"
        }

        for key, xpath in sections.items():
            element = driver.find_element(By.XPATH, xpath)
            if element:
                contract_info[key] = element.text.strip()

        return contract_info
    except Exception as e:
        app.logger.error(f"Error extracting business contract info: {str(e)}")
        return contract_info


def extract_intellectual_property_selenium(driver):
    """Extract intellectual property information using Selenium"""
    ip_info = {
        'national_organisations': '',
        'regional_organisations': '',
        'international_membership': [],
        'regulations': []
    }

    try:
        # Wait for IP section
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[text()='Intellectual Property']"))
        )

        # Extract basic information
        basic_sections = {
            'national_organisations': "//dt[text()='National Organisations']/following-sibling::dd[1]",
            'regional_organisations': "//dt[text()='Regional Organisations']/following-sibling::dd[1]"
        }

        for key, xpath in basic_sections.items():
            element = driver.find_element(By.XPATH, xpath)
            if element:
                ip_info[key] = element.text.strip()

        # Extract international membership
        membership = driver.find_element(By.XPATH, "//dt[text()='International Membership']/following-sibling::dd[1]")
        if membership:
            links = membership.find_elements(By.XPATH, ".//a")
            for link in links:
                ip_info['international_membership'].append({
                    'name': link.text.strip(),
                    'url': link.get_attribute('href')
                })

        # Extract regulations table
        table = driver.find_element(By.XPATH, "//h4[contains(text(), 'National Regulation')]/following::table[1]")
        if table:
            rows = table.find_elements(By.XPATH, ".//tr[td]")
            for row in rows:
                cells = row.find_elements(By.XPATH, ".//td")
                if len(cells) >= 3:
                    regulation = {
                        'type': cells[0].text.strip(),
                        'validity': cells[1].text.strip(),
                        'agreements': cells[2].text.strip()
                    }
                    ip_info['regulations'].append(regulation)

        return ip_info
    except Exception as e:
        app.logger.error(f"Error extracting intellectual property info: {str(e)}")
        return ip_info


def extract_legal_framework_selenium(driver):
    """Extract legal framework information"""
    framework = {
        'equity_judgments': {},
        'legal_codes': [],
        'jurisdictions': [],
        'court_officials': {}
    }

    try:
        # Extract equity of judgments
        sections = {
            'language': "//dt[text()='The Language of Justice']/following-sibling::dd[1]",
            'interpreter': "//dt[text()='Recourse to an Interpreter']/following-sibling::dd[1]",
            'similarities': "//dt[text()='Legal Similarities']/following-sibling::dd[1]"
        }

        for key, xpath in sections.items():
            element = driver.find_element(By.XPATH, xpath)
            if element:
                framework['equity_judgments'][key] = element.text.strip()

        # Extract legal codes
        codes_table = driver.find_element(By.XPATH, "//h3[text()='The Different Legal Codes']/following::table[1]")
        if codes_table:
            rows = codes_table.find_elements(By.XPATH, ".//tr")
            for row in rows:
                cells = row.find_elements(By.XPATH, ".//td")
                if len(cells) == 2:
                    code = {
                        'name': cells[0].text.strip(),
                        'reference': cells[1].text.strip()
                    }
                    framework['legal_codes'].append(code)

        # Extract jurisdictions
        jurisdictions_table = driver.find_element(By.XPATH, "//h3[text()='The Jurisdictions']/following::table[1]")
        if jurisdictions_table:
            rows = jurisdictions_table.find_elements(By.XPATH, ".//tr")
            for row in rows:
                cells = row.find_elements(By.XPATH, ".//td")
                if len(cells) == 2:
                    jurisdiction = {
                        'name': cells[0].text.strip(),
                        'description': cells[1].text.strip()
                    }
                    framework['jurisdictions'].append(jurisdiction)

        # Extract court officials
        officials_section = driver.find_element(By.XPATH, "//h3[text()='Court Officials']")
        if officials_section:
            dts = officials_section.find_elements(By.XPATH, "following-sibling::dl[1]/dt")
            for dt in dts:
                role = dt.text.strip()
                dd = dt.find_element(By.XPATH, "following-sibling::dd[1]")
                framework['court_officials'][role] = dd.text.strip()

        return framework
    except Exception as e:
        app.logger.error(f"Error extracting legal framework info: {str(e)}")
        return framework


def extract_dispute_resolution_selenium(driver):
    """Extract international dispute resolution information"""
    resolution = {
        'arbitration': '',
        'arbitration_law': '',
        'conformity': '',
        'appointment': '',
        'procedure': '',
        'permanent_bodies': []
    }

    try:
        # Wait for dispute resolution section
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'Dispute Resolution')]"))
        )

        # Extract main sections
        sections = {
            'arbitration': "//dt[text()='Arbitration']/following-sibling::dd[1]",
            'arbitration_law': "//dt[text()='Arbitration Law']/following-sibling::dd[1]",
            'conformity': "//dt[contains(text(), 'Conformity')]/following-sibling::dd[1]",
            'appointment': "//dt[text()='Appointment of Arbitrators']/following-sibling::dd[1]",
            'procedure': "//dt[text()='Arbitration Procedure']/following-sibling::dd[1]"
        }

        for key, xpath in sections.items():
            element = driver.find_element(By.XPATH, xpath)
            if element:
                resolution[key] = element.text.strip()

        # Extract permanent bodies
        bodies = driver.find_element(By.XPATH, "//dt[text()='Permanent Arbitration Bodies']/following-sibling::dd[1]")
        if bodies:
            links = bodies.find_elements(By.XPATH, ".//a")
            for link in links:
                body = {
                    'name': link.text.strip(),
                    'url': link.get_attribute('href')
                }
                # Get the sector if available (in parentheses after the link)
                parent_span = link.find_element(By.XPATH, "./parent::span")
                if '(Sectors Covered:' in parent_span.text:
                    body['sectors'] = parent_span.text.split('(Sectors Covered:')[1].strip(')')
                resolution['permanent_bodies'].append(body)

        return resolution
    except Exception as e:
        app.logger.error(f"Error extracting dispute resolution info: {str(e)}")
        return resolution


def extract_foreign_investment_selenium(driver):
    """Extract foreign investment information using Selenium"""
    investment_info = {
        'fdi_figures': {
            'summary': '',
            'fdi_data': {},
            'investing_countries': [],
            'invested_sectors': [],
            'company_info': {
                'preferred_company_form': '',
                'preferred_establishment': '',
                'main_companies': '',
                'statistics_sources': ''
            }
        },
        'investment_considerations': {
            'strong_points': '',
            'weak_points': '',
            'government_measures': ''
        },
        'investment_protection': {
            'bilateral_conventions': '',
            'international_controversies': '',
            'assistance_organizations': '',
            'miga_membership': '',
            'protection_indices': {}
        },
        'investment_procedures': {
            'establishment_freedom': '',
            'holdings_acquisition': '',
            'declaration_obligation': '',
            'competent_organisation': '',
            'specific_authorisations': ''
        },
        'real_estate': {
            'temporary_solutions': '',
            'buying_possibility': '',
            'expropriation_risk': ''
        },
        'investment_aid': {
            'forms': '',
            'privileged_domains': '',
            'privileged_zones': '',
            'free_trade_zones': '',
            'public_aid': ''
        },
        'investment_opportunities': {
            'key_sectors': '',
            'high_potential_sectors': '',
            'privatization': '',
            'tenders': ''
        },
        'limited_sectors': {
            'monopolistic_sectors': ''
        },
        'assistance_info': {
            'investment_aid_agency': '',
            'useful_resources': '',
            'business_guides': ''
        }
    }

    try:
        # Extract FDI Figures section
        try:
            fdi_summary = driver.find_element(By.XPATH, "//h2[text()='FDI in Figures']/following-sibling::p")
            if fdi_summary:
                investment_info['fdi_figures']['summary'] = fdi_summary.text.strip()

            # Extract FDI data table
            fdi_table = driver.find_element(By.XPATH,
                                            "//th[contains(text(), 'Foreign Direct Investment')]/ancestor::table")
            if fdi_table:
                rows = fdi_table.find_elements(By.XPATH, ".//tr")
                for row in rows[1:]:  # Skip header
                    cells = row.find_elements(By.XPATH, ".//th|.//td")
                    if len(cells) >= 4:
                        metric = cells[0].text.strip()
                        investment_info['fdi_figures']['fdi_data'][metric] = {
                            '2020': cells[1].text.strip(),
                            '2021': cells[2].text.strip(),
                            '2022': cells[3].text.strip()
                        }

            # Extract investing countries
            countries_table = driver.find_element(By.XPATH,
                                                  "//th[contains(text(), 'Main Investing Countries')]/ancestor::table")
            if countries_table:
                rows = countries_table.find_elements(By.XPATH, ".//tr[td]")
                for row in rows:
                    cells = row.find_elements(By.XPATH, ".//td")
                    if len(cells) == 2:
                        investment_info['fdi_figures']['investing_countries'].append({
                            'country': cells[0].text.strip(),
                            'percentage': cells[1].text.strip()
                        })

            # Extract invested sectors
            sectors_table = driver.find_element(By.XPATH,
                                                "//th[contains(text(), 'Main Invested Sectors')]/ancestor::table")
            if sectors_table:
                rows = sectors_table.find_elements(By.XPATH, ".//tr[td]")
                for row in rows:
                    cells = row.find_elements(By.XPATH, ".//td")
                    if len(cells) == 2:
                        investment_info['fdi_figures']['invested_sectors'].append({
                            'sector': cells[0].text.strip(),
                            'percentage': cells[1].text.strip()
                        })

            # Extract company information
            company_fields = {
                'preferred_company_form': "//dt[contains(text(), 'Form of Company Preferred')]/following-sibling::dd[1]",
                'preferred_establishment': "//dt[contains(text(), 'Form of Establishment Preferred')]/following-sibling::dd[1]",
                'main_companies': "//dt[contains(text(), 'Main Foreign Companies')]/following-sibling::dd[1]",
                'statistics_sources': "//dt[contains(text(), 'Sources of Statistics')]/following-sibling::dd[1]"
            }

            for key, xpath in company_fields.items():
                element = driver.find_element(By.XPATH, xpath)
                if element:
                    investment_info['fdi_figures']['company_info'][key] = element.text.strip()

        except Exception as e:
            app.logger.error(f"Error extracting FDI figures: {str(e)}")

        # Extract Investment Considerations
        try:
            considerations = {
                'strong_points': "//dt[text()='Strong Points']/following-sibling::dd[1]",
                'weak_points': "//dt[text()='Weak Points']/following-sibling::dd[1]",
                'government_measures': "//dt[contains(text(), 'Government Measures')]/following-sibling::dd[1]"
            }

            for key, xpath in considerations.items():
                element = driver.find_element(By.XPATH, xpath)
                if element:
                    investment_info['investment_considerations'][key] = element.text.strip()
        except Exception as e:
            app.logger.error(f"Error extracting investment considerations: {str(e)}")

        # Extract Investment Protection
        try:
            protection_fields = {
                'bilateral_conventions': "//dt[contains(text(), 'Bilateral Investment Conventions')]/following-sibling::dd[1]",
                'international_controversies': "//dt[contains(text(), 'International Controversies')]/following-sibling::dd[1]",
                'assistance_organizations': "//dt[contains(text(), 'Organizations Offering Their Assistance')]/following-sibling::dd[1]",
                'miga_membership': "//dt[contains(text(), 'Member of the Multilateral Investment')]/following-sibling::dd[1]"
            }

            for key, xpath in protection_fields.items():
                element = driver.find_element(By.XPATH, xpath)
                if element:
                    investment_info['investment_protection'][key] = element.text.strip()

            # Extract protection indices table
            indices_table = driver.find_element(By.XPATH,
                                                "//td[contains(text(), 'Country Comparison For the Protection of Investors')]/ancestor::table")
            if indices_table:
                rows = indices_table.find_elements(By.XPATH, ".//tr[position()>1]")
                for row in rows:
                    cells = row.find_elements(By.XPATH, ".//th|.//td")
                    if len(cells) >= 5:
                        index_name = cells[0].text.strip()
                        investment_info['investment_protection']['protection_indices'][index_name] = {
                            'morocco': cells[1].text.strip(),
                            'mena': cells[2].text.strip(),
                            'us': cells[3].text.strip(),
                            'germany': cells[4].text.strip()
                        }
        except Exception as e:
            app.logger.error(f"Error extracting investment protection: {str(e)}")

        # Extract other sections similarly...
        sections = {
            'investment_procedures': {
                'establishment_freedom': "//dt[text()='Freedom of Establishment']/following-sibling::dd[1]",
                'holdings_acquisition': "//dt[text()='Acquisition of Holdings']/following-sibling::dd[1]",
                'declaration_obligation': "//dt[text()='Obligation to Declare']/following-sibling::dd[1]",
                'competent_organisation': "//dt[contains(text(), 'Competent Organisation')]/following-sibling::dd[1]",
                'specific_authorisations': "//dt[contains(text(), 'Requests For Specific')]/following-sibling::dd[1]"
            },
            'real_estate': {
                'temporary_solutions': "//dt[text()='Possible Temporary Solutions']/following-sibling::dd[1]",
                'buying_possibility': "//dt[contains(text(), 'The Possibility of Buying')]/following-sibling::dd[1]",
                'expropriation_risk': "//dt[text()='Risk of Expropriation']/following-sibling::dd[1]"
            },
            'investment_aid': {
                'forms': "//dt[text()='Forms of Aid']/following-sibling::dd[1]",
                'privileged_domains': "//dt[text()='Privileged Domains']/following-sibling::dd[1]",
                'privileged_zones': "//dt[text()='Privileged Geographical Zones']/following-sibling::dd[1]",
                'free_trade_zones': "//dt[text()='Free-trade zones']/following-sibling::dd[1]",
                'public_aid': "//dt[contains(text(), 'Public aid and funding')]/following-sibling::dd[1]"
            },
            'investment_opportunities': {
                'key_sectors': "//dt[contains(text(), 'The Key Sectors')]/following-sibling::dd[1]",
                'high_potential_sectors': "//dt[text()='High Potential Sectors']/following-sibling::dd[1]",
                'privatization': "//dt[text()='Privatization Programmes']/following-sibling::dd[1]",
                'tenders': "//dt[contains(text(), 'Tenders, Projects')]/following-sibling::dd[1]"
            },
            'limited_sectors': {
                'monopolistic_sectors': "//dt[text()='Monopolistic Sectors']/following-sibling::dd[1]"
            },
            'assistance_info': {
                'investment_aid_agency': "//dt[text()='Investment Aid Agency']/following-sibling::dd[1]",
                'useful_resources': "//dt[text()='Other Useful Resources']/following-sibling::dd[1]",
                'business_guides': "//dt[text()='Doing Business Guides']/following-sibling::dd[1]"
            }
        }

        for section, fields in sections.items():
            for field, xpath in fields.items():
                try:
                    element = driver.find_element(By.XPATH, xpath)
                    if element:
                        investment_info[section][field] = element.text.strip()
                except Exception as e:
                    app.logger.error(f"Error extracting {section}.{field}: {str(e)}")

        return investment_info
    except Exception as e:
        app.logger.error(f"Error extracting foreign investment info: {str(e)}")
        return investment_info


def extract_business_practices_selenium(driver):
    """Extract business practices information using Selenium"""
    practices_info = {
        'business_culture': {
            'fundamental_principles': '',
            'first_contact': '',
            'time_management': '',
            'greetings_titles': '',
            'gift_policy': '',
            'dress_code': '',
            'business_cards': '',
            'meetings_management': '',
            'information_sources': ''
        },
        'opening_hours': {
            'general_hours': '',
            'public_holidays': [],
            'closing_periods': [],
            'hotel_resources': ''
        }
    }

    try:
        # Wait for content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'atlas')]"))
        )

        # Extract Business Culture section
        try:
            culture_fields = {
                'fundamental_principles': "//dt[contains(text(), 'The Fundamental Principles')]/following-sibling::dd[1]",
                'first_contact': "//dt[contains(text(), 'First Contact')]/following-sibling::dd[1]",
                'time_management': "//dt[contains(text(), 'Time Management')]/following-sibling::dd[1]",
                'greetings_titles': "//dt[contains(text(), 'Greetings and Titles')]/following-sibling::dd[1]",
                'gift_policy': "//dt[contains(text(), 'Gift Policy')]/following-sibling::dd[1]",
                'dress_code': "//dt[contains(text(), 'Dress Code')]/following-sibling::dd[1]",
                'business_cards': "//dt[contains(text(), 'Business Cards')]/following-sibling::dd[1]",
                'meetings_management': "//dt[contains(text(), 'Meetings Management')]/following-sibling::dd[1]",
                'information_sources': "//dt[contains(text(), 'Sources for Further Information')]/following-sibling::dd[1]"
            }

            for field, xpath in culture_fields.items():
                try:
                    element = driver.find_element(By.XPATH, xpath)
                    if element:
                        practices_info['business_culture'][field] = element.text.strip()
                except Exception as e:
                    app.logger.error(f"Error extracting business culture {field}: {str(e)}")

        except Exception as e:
            app.logger.error(f"Error extracting business culture section: {str(e)}")

        # Extract Opening Hours section
        try:
            # Extract general opening hours
            hours_element = driver.find_element(By.XPATH,
                                                "//dt[contains(text(), 'Opening Hours and Days')]/following-sibling::dd[1]")
            if hours_element:
                practices_info['opening_hours']['general_hours'] = hours_element.text.strip()

            # Extract public holidays table
            holidays_table = driver.find_element(By.XPATH,
                                                 "//h4[contains(text(), 'Public Holidays')]/following::table[1]")
            if holidays_table:
                rows = holidays_table.find_elements(By.XPATH, ".//tr")
                for row in rows:
                    cells = row.find_elements(By.XPATH, ".//td")
                    if len(cells) == 2:
                        practices_info['opening_hours']['public_holidays'].append({
                            'holiday': cells[0].text.strip(),
                            'date': cells[1].text.strip()
                        })

            # Extract closing periods table
            closing_table = driver.find_element(By.XPATH,
                                                "//h4[contains(text(), 'Periods When Companies Usually Close')]/following::table[1]")
            if closing_table:
                rows = closing_table.find_elements(By.XPATH, ".//tr")
                for row in rows:
                    cells = row.find_elements(By.XPATH, ".//td")
                    if len(cells) == 2:
                        practices_info['opening_hours']['closing_periods'].append({
                            'period': cells[0].text.strip(),
                            'time': cells[1].text.strip()
                        })

            # Extract hotel reservation resources
            hotel_element = driver.find_element(By.XPATH,
                                                "//dt[contains(text(), 'Hotel reservation')]/following-sibling::dd[1]")
            if hotel_element:
                practices_info['opening_hours']['hotel_resources'] = hotel_element.text.strip()

        except Exception as e:
            app.logger.error(f"Error extracting opening hours section: {str(e)}")

        return practices_info
    except Exception as e:
        app.logger.error(f"Error extracting business practices info: {str(e)}")
        return practices_info


def extract_entry_requirements_selenium(driver):
    """Extract entry requirements information using Selenium"""
    requirements_info = {
        'passport_visa': {
            'passport_visa_service': [],  # Changed to array to store link objects
            'hotel_reservation': '',
            'embassy_contact': '',
            'additional_info': ''
        },
        'customs_taxes': {
            'consumption_tax_refund': '',
            'other_requirements': ''
        },
        'health_precautions': {
            'vaccinations': '',
            'hotel_resources': '',
            'travel_health_advice': ''
        },
        'safety_conditions': {
            'resources': []
        }
    }

    try:
        # Wait for content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'atlas')]"))
        )

        # Extract Passport and Visa section
        try:
            # Get passport and visa service links
            service_element = driver.find_element(By.XPATH,
                                                  "//dt[text()='Passport and Visa Service']/following-sibling::dd[1]")
            if service_element:
                links = service_element.find_elements(By.XPATH, ".//a")
                for link in links:
                    requirements_info['passport_visa']['passport_visa_service'].append({
                        'name': link.text.strip(),
                        'url': link.get_attribute('href')
                    })

            # Get hotel reservation info
            hotel_element = driver.find_element(By.XPATH,
                                                "//dt[contains(text(), 'Hotel reservation websites')]/following-sibling::dd[1]")
            if hotel_element:
                requirements_info['passport_visa']['hotel_reservation'] = hotel_element.text.strip()

            # Get embassy contact
            embassy_element = driver.find_element(By.XPATH,
                                                  "//dt[contains(text(), 'Contact the Embassy')]/following-sibling::dd[1]")
            if embassy_element:
                requirements_info['passport_visa']['embassy_contact'] = embassy_element.text.strip()

            # Get additional info (IATA link paragraph)
            additional_info_element = driver.find_element(By.XPATH,
                                                          "//a[contains(@href, 'iatatravelcentre')]/parent::span")
            if additional_info_element:
                requirements_info['passport_visa']['additional_info'] = additional_info_element.text.strip()

        except Exception as e:
            app.logger.error(f"Error extracting passport and visa info: {str(e)}")

        # Extract Customs and Taxes section
        try:
            # Get consumption tax refund info
            tax_element = driver.find_element(By.XPATH,
                                              "//dt[contains(text(), 'How to Refund Consumption Tax')]/following-sibling::dd[1]")
            if tax_element:
                requirements_info['customs_taxes']['consumption_tax_refund'] = tax_element.text.strip()

            # Get other requirements
            requirements_element = driver.find_element(By.XPATH,
                                                       "//dt[text()='Other Requirements']/following-sibling::dd[1]")
            if requirements_element:
                requirements_info['customs_taxes']['other_requirements'] = requirements_element.text.strip()

        except Exception as e:
            app.logger.error(f"Error extracting customs and taxes info: {str(e)}")

        # Extract Health Precautions section
        try:
            # Get vaccination info
            vaccination_element = driver.find_element(By.XPATH,
                                                      "//dt[contains(text(), 'Obligatory Vaccination')]/following-sibling::dd[1]")
            if vaccination_element:
                requirements_info['health_precautions']['vaccinations'] = vaccination_element.text.strip()

            # Get hotel resources for health
            hotel_health_element = driver.find_element(By.XPATH,
                                                       "//dt[contains(text(), 'Hotel reservation websites')]/following-sibling::dd[1]")
            if hotel_health_element:
                requirements_info['health_precautions']['hotel_resources'] = hotel_health_element.text.strip()

            # Get travel health advice
            advice_element = driver.find_element(By.XPATH,
                                                 "//dt[contains(text(), 'Travel Health Advice')]/following-sibling::dd[1]")
            if advice_element:
                requirements_info['health_precautions']['travel_health_advice'] = advice_element.text.strip()

        except Exception as e:
            app.logger.error(f"Error extracting health precautions info: {str(e)}")

        # Extract Safety Conditions section
        try:
            safety_links = driver.find_elements(By.XPATH, "//h2[text()='Safety Conditions']/following::dd[1]//a")
            for link in safety_links:
                requirements_info['safety_conditions']['resources'].append({
                    'name': link.text.strip(),
                    'url': link.get_attribute('href')
                })

        except Exception as e:
            app.logger.error(f"Error extracting safety conditions info: {str(e)}")

        return requirements_info
    except Exception as e:
        app.logger.error(f"Error extracting entry requirements info: {str(e)}")
        return requirements_info


def extract_practical_info_selenium(driver):
    """Extract practical information using Selenium"""
    practical_info = {
        'accommodation': {
            'hotel_websites': []
        },
        'eating_out': {
            'rules': '',
            'specialties': '',
            'drinks': '',
            'dietary_restrictions': '',
            'table_manners': ''
        },
        'getting_around': {
            'urban_transport': {
                'services': [],
                'taxi_services': []
            },
            'airports': [],
            'train_services': [],
            'airlines': [],
            'car_rental': []
        },
        'time': {
            'local_time': '',
            'summer_time': ''
        },
        'climate': {
            'type': '',
            'weather_websites': []
        },
        'electrical_standards': {
            'measurement_system': '',
            'temperature_unit': '',
            'voltage': '',
            'frequency': '',
            'socket_type': '',
            'telephone_socket': '',
            'dvd_zone': ''
        },
        'paying': {
            'currency': '',
            'iso_code': '',
            'currency_info': '',
            'payment_methods': ''
        },
        'speaking': {
            'official_language': '',
            'other_languages': '',
            'business_language': ''
        },
        'emergency': {
            'numbers': {}
        },
        'communications': {
            'telephone': {
                'dial_from': '',
                'dial_to': '',
                'mobile_standards': '',
                'operators': []
            },
            'internet': {
                'suffix': '',
                'providers': ''
            }
        }
    }

    try:
        # Extract Accommodation section
        try:
            hotel_links = driver.find_elements(By.XPATH,
                                               "//dt[text()='Hotel reservation websites']/following-sibling::dd[1]//a")
            for link in hotel_links:
                practical_info['accommodation']['hotel_websites'].append({
                    'name': link.text.strip(),
                    'url': link.get_attribute('href')
                })
        except Exception as e:
            app.logger.error(f"Error extracting accommodation info: {str(e)}")

        # Extract Eating Out section
        try:
            eating_fields = {
                'rules': "//dt[contains(text(), 'Rules For Eating Out')]/following-sibling::dd[1]",
                'specialties': "//dt[text()='Food Specialties']/following-sibling::dd[1]",
                'drinks': "//dt[text()='Drinks']/following-sibling::dd[1]",
                'dietary_restrictions': "//dt[text()='Dietary Restrictions']/following-sibling::dd[1]",
                'table_manners': "//dt[text()='Table Manners']/following-sibling::dd[1]"
            }

            for field, xpath in eating_fields.items():
                element = driver.find_element(By.XPATH, xpath)
                if element:
                    practical_info['eating_out'][field] = element.text.strip()
        except Exception as e:
            app.logger.error(f"Error extracting eating out info: {str(e)}")

        # Extract Getting Around section
        try:
            # Urban transport services
            transport_services = driver.find_elements(By.XPATH,
                                                      "//dt[text()='Urban transport services']/following-sibling::dd[1]//span")
            for service in transport_services:
                practical_info['getting_around']['urban_transport']['services'].append(service.text.strip())

            # Taxi services
            taxi_links = driver.find_elements(By.XPATH, "//dt[text()='Taxi services']/following-sibling::dd[1]//a")
            for link in taxi_links:
                practical_info['getting_around']['urban_transport']['taxi_services'].append({
                    'name': link.text.strip(),
                    'url': link.get_attribute('href')
                })

            # Airports
            airport_rows = driver.find_elements(By.XPATH, "//th[contains(., 'Airport')]/ancestor::table//tbody/tr")
            for row in airport_rows:
                cells = row.find_elements(By.XPATH, ".//td")
                if len(cells) >= 6:
                    airport_info = {
                        'name': cells[0].text.strip(),
                        'distance': cells[1].text.strip(),
                        'taxi': cells[2].text.strip(),
                        'bus': cells[3].text.strip(),
                        'train': cells[4].text.strip(),
                        'car_rental': cells[5].text.strip()
                    }
                    practical_info['getting_around']['airports'].append(airport_info)

            # Airlines
            airline_rows = driver.find_elements(By.XPATH, "//h4[text()='Major airlines']/following::table[1]//tbody/tr")
            for row in airline_rows:
                cells = row.find_elements(By.XPATH, ".//td")
                if len(cells) >= 4:
                    link = cells[0].find_element(By.XPATH, ".//a")
                    airline_info = {
                        'name': link.text.strip(),
                        'url': link.get_attribute('href'),
                        'type': cells[1].text.strip(),
                        'domestic': cells[2].text.strip(),
                        'international': cells[3].text.strip()
                    }
                    practical_info['getting_around']['airlines'].append(airline_info)

            # Car rental agencies
            rental_links = driver.find_elements(By.XPATH,
                                                "//dt[text()='Car rental agencies']/following-sibling::dd[1]//a")
            for link in rental_links:
                practical_info['getting_around']['car_rental'].append({
                    'name': link.text.strip(),
                    'url': link.get_attribute('href')
                })

        except Exception as e:
            app.logger.error(f"Error extracting getting around info: {str(e)}")

        # Extract Time section
        try:
            time_fields = {
                'local_time': "//dt[text()='Current Local Time']/following-sibling::dd[1]",
                'summer_time': "//dt[text()='Summer Time']/following-sibling::dd[1]"
            }

            for field, xpath in time_fields.items():
                element = driver.find_element(By.XPATH, xpath)
                if element:
                    practical_info['time'][field] = element.text.strip()
        except Exception as e:
            app.logger.error(f"Error extracting time info: {str(e)}")

        # Extract Climate section
        try:
            climate_element = driver.find_element(By.XPATH, "//dt[text()='Type of Climate']/following-sibling::dd[1]")
            if climate_element:
                practical_info['climate']['type'] = climate_element.text.strip()

            weather_links = driver.find_elements(By.XPATH,
                                                 "//h2[text()='Climate']/following::dt[text()='Hotel reservation websites']/following-sibling::dd[1]//a")
            for link in weather_links:
                practical_info['climate']['weather_websites'].append({
                    'name': link.text.strip(),
                    'url': link.get_attribute('href')
                })
        except Exception as e:
            app.logger.error(f"Error extracting climate info: {str(e)}")

        # Extract Electrical Standards section
        try:
            electrical_fields = {
                'measurement_system': "//dt[text()='System of Measurement Used']/following-sibling::dd[1]",
                'temperature_unit': "//dt[text()='Unit of Measurement of Temperature']/following-sibling::dd[1]",
                'voltage': "//ul/li[text()='Voltage']/ancestor::dt/following-sibling::dd[1]",
                'frequency': "//ul/li[text()='Frequency']/ancestor::dt/following-sibling::dd[1]",
                'socket_type': "//dt[text()='Type of Electric Socket']/following-sibling::dd[1]",
                'telephone_socket': "//dt[text()='Type of Telephone Socket']/following-sibling::dd[1]",
                'dvd_zone': "//dt[text()='DVD Zoning']/following-sibling::dd[1]"
            }

            for field, xpath in electrical_fields.items():
                element = driver.find_element(By.XPATH, xpath)
                if element:
                    practical_info['electrical_standards'][field] = element.text.strip()
        except Exception as e:
            app.logger.error(f"Error extracting electrical standards info: {str(e)}")

        # Extract Paying section
        try:
            paying_fields = {
                'currency': "//dt[text()='Domestic Currency']/following-sibling::dd[1]",
                'iso_code': "//dt[text()='ISO Code']/following-sibling::dd[1]",
                'currency_info': "//dt[text()='To Obtain Domestic Currency']/following-sibling::dd[1]",
                'payment_methods': "//dt[text()='Possible Means of Payment']/following-sibling::dd[1]"
            }

            for field, xpath in paying_fields.items():
                element = driver.find_element(By.XPATH, xpath)
                if element:
                    practical_info['paying'][field] = element.text.strip()
        except Exception as e:
            app.logger.error(f"Error extracting paying info: {str(e)}")

        # Extract Speaking section
        try:
            speaking_fields = {
                'official_language': "//dt[text()='Official Language']/following-sibling::dd[1]",
                'other_languages': "//dt[text()='Other Languages Spoken']/following-sibling::dd[1]",
                'business_language': "//dt[text()='Business Language']/following-sibling::dd[1]"
            }

            for field, xpath in speaking_fields.items():
                element = driver.find_element(By.XPATH, xpath)
                if element:
                    practical_info['speaking'][field] = element.text.strip()
        except Exception as e:
            app.logger.error(f"Error extracting speaking info: {str(e)}")

        # Extract Emergency Numbers section
        try:
            emergency_rows = driver.find_elements(By.XPATH, "//h2[text()='Emergency Numbers']/following::table[1]//tr")
            for row in emergency_rows:
                cells = row.find_elements(By.XPATH, ".//td")
                if len(cells) == 2:
                    service = cells[0].text.strip()
                    number = cells[1].text.strip()
                    practical_info['emergency']['numbers'][service] = number
        except Exception as e:
            app.logger.error(f"Error extracting emergency numbers: {str(e)}")

        # Extract Communications section
        try:
            # Telephone info
            practical_info['communications']['telephone']['dial_from'] = driver.find_element(By.XPATH,
                                                                                             "//dt[text()='Telephone Codes']/following-sibling::dd[1]").text.strip()

            mobile_standards = driver.find_element(By.XPATH,
                                                   "//dt[text()='Mobile Telephone Standards']/following-sibling::dd[1]")
            if mobile_standards:
                practical_info['communications']['telephone']['mobile_standards'] = mobile_standards.text.strip()

            operators_element = driver.find_element(By.XPATH,
                                                    "//dt[text()='National Mobile Phone Operators']/following-sibling::dd[1]")
            if operators_element:
                links = operators_element.find_elements(By.XPATH, ".//a")
                for link in links:
                    practical_info['communications']['telephone']['operators'].append({
                        'name': link.text.strip(),
                        'url': link.get_attribute('href')
                    })

            # Internet info
            internet_fields = {
                'suffix': "//dt[text()='Internet Suffix']/following-sibling::dd[1]",
                'providers': "//dt[text()='National Internet Access Providers']/following-sibling::dd[1]"
            }

            for field, xpath in internet_fields.items():
                element = driver.find_element(By.XPATH, xpath)
                if element:
                    practical_info['communications']['internet'][field] = element.text.strip()

        except Exception as e:
            app.logger.error(f"Error extracting communications info: {str(e)}")

        return practical_info
    except Exception as e:
        app.logger.error(f"Error extracting practical info: {str(e)}")
        return practical_info


def extract_living_info_selenium(driver):
    """Extract living in the country information using Selenium"""
    living_info = {
        'expatriates': {
            'number': '',
            'blogs': [],
            'expat_sites': [],
            'immigration_authority': [],
            'moving_companies': [],
            'embassy_info': {
                'contact_embassy': '',
                'contact_your_embassy': ''
            }
        },
        'cities_ranking': {
            'cost_of_living': '',
            'quality_of_life': '',
            'ranking_resources': []
        },
        'renting': {
            'lease_term': '',
            'rental_costs': '',
            'rental_agencies': [],
            'rental_resources': []
        },
        'school_system': {
            'education_system': '',
            'international_schools': '',
            'education_resources': []
        },
        'health_system': {
            'healthcare': '',
            'international_hospitals': '',
            'insurance_body': [],
            'health_ministry': []
        },
        'tourism_culture': {
            'tourism_types': {
                'historical': '',
                'cultural': '',
                'nature': '',
                'religious': '',
                'thermal': '',
                'beach': '',
                'winter_sports': '',
                'outdoor': '',
                'shopping': ''
            },
            'city_highlights': [],
            'country_highlights': [],
            'organizations': {
                'tourism': [],
                'cultural': [],
                'resources': []
            }
        },
        'freedoms': {
            'civil_liberty': '',
            'press_freedom': ''
        }
    }

    try:
        # Extract Expatriates section
        try:
            expat_number = driver.find_element(By.XPATH,
                                               "//dt[text()='The Number of Expatriates']/following-sibling::dd[1]")
            if expat_number:
                living_info['expatriates']['number'] = expat_number.text.strip()

            # Get expat blogs
            blog_links = driver.find_elements(By.XPATH, "//dt[text()='Blogs For Expats']/following-sibling::dd[1]//a")
            for link in blog_links:
                living_info['expatriates']['blogs'].append({
                    'name': link.text.strip(),
                    'url': link.get_attribute('href')
                })

            # Get expat sites
            site_links = driver.find_elements(By.XPATH,
                                              "//dt[contains(text(), 'Hotel reservation websites')]/following-sibling::dd[1]//a")
            for link in site_links:
                living_info['expatriates']['expat_sites'].append({
                    'name': link.text.strip(),
                    'url': link.get_attribute('href')
                })

            # Get immigration authority
            authority_links = driver.find_elements(By.XPATH,
                                                   "//dt[text()='Immigration Authority']/following-sibling::dd[1]//a")
            for link in authority_links:
                living_info['expatriates']['immigration_authority'].append({
                    'name': link.text.strip(),
                    'url': link.get_attribute('href')
                })

            # Get moving companies
            moving_links = driver.find_elements(By.XPATH,
                                                "//dt[contains(text(), 'Transportation Companies')]/following-sibling::dd[1]//a")
            for link in moving_links:
                living_info['expatriates']['moving_companies'].append({
                    'name': link.text.strip(),
                    'url': link.get_attribute('href')
                })

            # Embassy info
            embassy_contact = driver.find_element(By.XPATH,
                                                  "//dt[text()='Contact the Embassy']/following-sibling::dd[1]")
            your_embassy = driver.find_element(By.XPATH, "//dt[text()='Contact Your Embassy']/following-sibling::dd[1]")
            if embassy_contact:
                living_info['expatriates']['embassy_info']['contact_embassy'] = embassy_contact.text.strip()
            if your_embassy:
                living_info['expatriates']['embassy_info']['contact_your_embassy'] = your_embassy.text.strip()

        except Exception as e:
            app.logger.error(f"Error extracting expatriates info: {str(e)}")

        # Extract Cities Ranking section
        try:
            cost_living = driver.find_element(By.XPATH, "//dt[text()='Cost of Living']/following-sibling::dd[1]")
            quality_life = driver.find_element(By.XPATH, "//dt[text()='Quality of Life']/following-sibling::dd[1]")

            if cost_living:
                living_info['cities_ranking']['cost_of_living'] = cost_living.text.strip()
            if quality_life:
                living_info['cities_ranking']['quality_of_life'] = quality_life.text.strip()

            ranking_links = driver.find_elements(By.XPATH,
                                                 "//h2[text()='Ranking of Cities']/following::dt[contains(text(), 'Hotel reservation websites')]/following-sibling::dd[1]//a")
            for link in ranking_links:
                living_info['cities_ranking']['ranking_resources'].append({
                    'name': link.text.strip(),
                    'url': link.get_attribute('href')
                })

        except Exception as e:
            app.logger.error(f"Error extracting cities ranking info: {str(e)}")

        # Extract Renting section
        try:
            lease_term = driver.find_element(By.XPATH, "//dt[text()='Average Lease Term']/following-sibling::dd[1]")
            rental_costs = driver.find_element(By.XPATH, "//dt[text()='Average Rental Costs']/following-sibling::dd[1]")

            if lease_term:
                living_info['renting']['lease_term'] = lease_term.text.strip()
            if rental_costs:
                living_info['renting']['rental_costs'] = rental_costs.text.strip()

            agency_links = driver.find_elements(By.XPATH,
                                                "//dt[text()='Rental Agency Websites']/following-sibling::dd[1]//a")
            for link in agency_links:
                living_info['renting']['rental_agencies'].append({
                    'name': link.text.strip(),
                    'url': link.get_attribute('href')
                })

            rental_resource_links = driver.find_elements(By.XPATH,
                                                         "//h2[text()='Renting an Apartment']/following::dt[contains(text(), 'Hotel reservation websites')]/following-sibling::dd[1]//a")
            for link in rental_resource_links:
                living_info['renting']['rental_resources'].append({
                    'name': link.text.strip(),
                    'url': link.get_attribute('href')
                })

        except Exception as e:
            app.logger.error(f"Error extracting renting info: {str(e)}")

        # Extract School System section
        try:
            education_system = driver.find_element(By.XPATH,
                                                   "//dt[text()='The Education System']/following-sibling::dd[1]")
            international_schools = driver.find_element(By.XPATH,
                                                        "//dt[text()='International Schools']/following-sibling::dd[1]")

            if education_system:
                living_info['school_system']['education_system'] = education_system.text.strip()
            if international_schools:
                living_info['school_system']['international_schools'] = international_schools.text.strip()

            education_links = driver.find_elements(By.XPATH,
                                                   "//h2[text()='School System']/following::dt[contains(text(), 'Hotel reservation websites')]/following-sibling::dd[1]//a")
            for link in education_links:
                living_info['school_system']['education_resources'].append({
                    'name': link.text.strip(),
                    'url': link.get_attribute('href')
                })

        except Exception as e:
            app.logger.error(f"Error extracting school system info: {str(e)}")

        # Extract Health System section
        try:
            healthcare = driver.find_element(By.XPATH, "//dt[text()='The Healthcare System']/following-sibling::dd[1]")
            int_hospitals = driver.find_element(By.XPATH,
                                                "//dt[text()='International Hospitals']/following-sibling::dd[1]")

            if healthcare:
                living_info['health_system']['healthcare'] = healthcare.text.strip()
            if int_hospitals:
                living_info['health_system']['international_hospitals'] = int_hospitals.text.strip()

            insurance_links = driver.find_elements(By.XPATH,
                                                   "//dt[text()='Health System Insurance Body']/following-sibling::dd[1]//a")
            for link in insurance_links:
                living_info['health_system']['insurance_body'].append({
                    'name': link.text.strip(),
                    'url': link.get_attribute('href')
                })

            ministry_links = driver.find_elements(By.XPATH,
                                                  "//dt[text()='Health Ministry']/following-sibling::dd[1]//a")
            for link in ministry_links:
                living_info['health_system']['health_ministry'].append({
                    'name': link.text.strip(),
                    'url': link.get_attribute('href')
                })

        except Exception as e:
            app.logger.error(f"Error extracting health system info: {str(e)}")

        # Extract Tourism and Culture section
        try:
            # Tourism types
            tourism_types = [
                ('Historical', "//dt[text()='Historical']/following-sibling::dd[1]"),
                ('Cultural', "//dt[text()='Cultural']/following-sibling::dd[1]"),
                ('Nature', "//dt[text()='Nature']/following-sibling::dd[1]"),
                ('Religious', "//dt[text()='Religious']/following-sibling::dd[1]"),
                ('Thermal', "//dt[text()='Thermal']/following-sibling::dd[1]"),
                ('Beach', "//dt[text()='Beach']/following-sibling::dd[1]"),
                ('Winter Sports', "//dt[text()='Winter Sports']/following-sibling::dd[1]"),
                ('Outdoor Activities', "//dt[text()='Outdoor Activities']/following-sibling::dd[1]"),
                ('Shopping', "//dt[text()='Shopping']/following-sibling::dd[1]")
            ]

            for tourism_type, xpath in tourism_types:
                try:
                    element = driver.find_element(By.XPATH, xpath)
                    if element:
                        field_name = tourism_type.lower().replace(' ', '_')
                        living_info['tourism_culture']['tourism_types'][field_name] = element.text.strip()
                except Exception:
                    app.logger.warning(f"Tourism type {tourism_type} not found")

            # City highlights
            try:
                city_table = driver.find_element(By.XPATH, "//table[@class='tableau1']")
                city_links = city_table.find_elements(By.XPATH, ".//td/a")
                for link in city_links:
                    living_info['tourism_culture']['city_highlights'].append({
                        'name': link.text.strip(),
                        'url': link.get_attribute('href')
                    })
            except Exception as e:
                app.logger.error(f"Error extracting city highlights: {str(e)}")

            # Country highlights
            try:
                country_table = driver.find_element(By.XPATH, "//table[@class='tableau2']")
                country_links = country_table.find_elements(By.XPATH, ".//td/a")
                for link in country_links:
                    living_info['tourism_culture']['country_highlights'].append({
                        'name': link.text.strip(),
                        'url': link.get_attribute('href')
                    })
            except Exception as e:
                app.logger.error(f"Error extracting country highlights: {str(e)}")

            # Tourism organizations
            tourism_org_links = driver.find_elements(By.XPATH,
                                                     "//dt[text()='Tourism Organisations']/following-sibling::dd[1]//a")
            for link in tourism_org_links:
                living_info['tourism_culture']['organizations']['tourism'].append({
                    'name': link.text.strip(),
                    'url': link.get_attribute('href')
                })

            # Cultural organizations
            cultural_org_links = driver.find_elements(By.XPATH,
                                                      "//dt[text()='Cultural Organizations']/following-sibling::dd[1]//a")
            for link in cultural_org_links:
                living_info['tourism_culture']['organizations']['cultural'].append({
                    'name': link.text.strip(),
                    'url': link.get_attribute('href')
                })

            # Tourism resources
            resource_links = driver.find_elements(By.XPATH,
                                                  "//h2[text()='Tourism and Culture']/following::dt[contains(text(), 'Hotel reservation websites')]/following-sibling::dd[1]//a")
            for link in resource_links:
                living_info['tourism_culture']['organizations']['resources'].append({
                    'name': link.text.strip(),
                    'url': link.get_attribute('href')
                })

        except Exception as e:
            app.logger.error(f"Error extracting tourism and culture info: {str(e)}")

        # Extract Individual and Civic Freedoms section
        try:
            # Get civil liberty
            try:
                civil_liberty = driver.find_element(By.XPATH, "//dt[text()='Civil Liberty']/following-sibling::dd[1]")
                if civil_liberty:
                    living_info['freedoms']['civil_liberty'] = civil_liberty.text.strip()
            except Exception:
                app.logger.warning("Civil liberty information not found")

            # Get press freedom - handling empty dt case
            try:
                press_freedom = driver.find_element(By.XPATH,
                                                    "//dt[not(text())]/following-sibling::dd[1]//span[contains(text(), 'World Ranking')]")
                if press_freedom:
                    living_info['freedoms']['press_freedom'] = press_freedom.text.strip()
            except Exception:
                app.logger.warning("Press freedom information not found")

        except Exception as e:
            app.logger.error(f"Error extracting freedoms info: {str(e)}")

        return living_info
    except Exception as e:
        app.logger.error(f"Error extracting living info: {str(e)}")
        return living_info


def extract_trade_shows(driver, keyword="", industry="", country=""):
    """
    Scrape trade shows data from Santander Trade website

    Parameters:
    driver (WebDriver): Selenium WebDriver instance
    keyword (str): Keyword to search for
    industry (str): Industry to filter by (id or name)
    country (str): Country to filter by (id or name)

    Returns:
    dict: Dictionary containing scraped trade show data
    """
    try:
        # Navigate to the main page and handle login first
        driver.get("https://santandertrade.com/en/portal/reach-business-counterparts/trade-shows")

        time.sleep(1)
        # Click on accept cookies button
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="accept-all-cookies"]'))
        ).click()

        # Wait for the login button to be present
        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="btn_login_menu"]'))
        )

        # Execute JavaScript to click the button
        driver.execute_script("arguments[0].click();", login_button)

        time.sleep(1)

        # Wait for the username field and fill it using JavaScript
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_identifiant"]'))
        )
        driver.execute_script("arguments[0].value = 'edgarcayuelas@indegate.com';", username_field)

        # Wait for the password field and fill it using JavaScript
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_mot_de_passe"]'))
        )
        driver.execute_script("arguments[0].value = 'Indegate@2020';", password_field)

        # Wait for the submit button and click it using JavaScript
        submit_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_go"]'))
        )
        driver.execute_script("arguments[0].click();", submit_button)

        time.sleep(1)

        # Now navigate to the trade shows page
        driver.get("https://santandertrade.com/en/portal/reach-business-counterparts/trade-shows")

        # Wait for the search form to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="keyword"]'))
        )

        # Fill in the search form
        if keyword:
            keyword_field = driver.find_element(By.XPATH, '//*[@id="keyword"]')
            keyword_field.clear()
            keyword_field.send_keys(keyword)

        # Select industry if provided
        if industry:
            industry_dropdown = driver.find_element(By.XPATH, '//*[@id="code_secteur"]')

            # Try to select by ID first
            try:
                select = Select(industry_dropdown)
                # Try to select by value (if industry is an ID)
                select.select_by_value(str(industry))
            except:
                # If that fails, try to select by visible text
                try:
                    select.select_by_visible_text(industry)
                except:
                    app.logger.warning(f"Could not select industry: {industry}")

        # Select country if provided
        if country:
            country_dropdown = driver.find_element(By.XPATH, '//*[@id="pays_recherche"]')

            # Try to select by ID first
            try:
                select = Select(country_dropdown)
                # Try to select by value (if country is an ID)
                select.select_by_value(str(country))
            except:
                # If that fails, try to select by visible text
                try:
                    select.select_by_visible_text(country)
                except:
                    app.logger.warning(f"Could not select country: {country}")

        time.sleep(2)

        # Click search button
        search_button = driver.find_element(By.XPATH, '//*[@id="form-submit"]')
        driver.execute_script("arguments[0].click();", search_button)

        # Wait for results to load
        time.sleep(3)


        # Extract total count of trade shows
        total_count = 0
        try:
            total_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//h2[contains(@class, "no-bg-bd")]/span'))
            )
            count_text = total_element.text
            # Extract number from text like "123 Trade shows"
            import re
            match = re.search(r'(\d+)', count_text)
            if match:
                total_count = int(match.group(1))
        except:
            app.logger.warning("Could not extract total count of trade shows")

        # Extract results
        trade_shows = []

        try:
            # Wait for the results container to be present
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "desc-resultats")]'))
            )

            # Get all trade show cards
            trade_show_cards = driver.find_elements(By.XPATH, '//div[contains(@class, "desc-resultats")]')

            for card in trade_show_cards:
                try:
                    # Extract title
                    title_elem = card.find_element(By.XPATH, './/div[contains(@class, "titre-haut-salon")]/a')
                    title = title_elem.text.strip()

                    # Extract location
                    location_elem = card.find_element(By.XPATH, './/div[contains(@class, "country")]')
                    location = location_elem.text.strip()

                    # Extract date
                    date_elem = card.find_element(By.XPATH, './/div[contains(@class, "type")]')
                    date = date_elem.text.strip()

                    # Extract description
                    description_elem = card.find_element(By.XPATH, './/div[contains(@class, "resumer")]')
                    description = description_elem.text.strip()

                    # Extract sectors
                    sectors_elem = card.find_element(By.XPATH, './/div[contains(@class, "text-overflow-row")]')
                    sectors = sectors_elem.text.strip()

                    # Clean up sectors text (remove icon)
                    sectors = re.sub(r'^\s*\S+\s+', '', sectors).strip()

                    # Get link
                    link = ""
                    try:
                        link = title_elem.get_attribute("href")
                    except:
                        pass

                    trade_shows.append({
                        "title": title,
                        "location": location,
                        "date": date,
                        "description": description,
                        "sectors": sectors,
                        "link": link
                    })
                except Exception as e:
                    app.logger.warning(f"Error extracting trade show data: {str(e)}")
                    continue
        except Exception as e:
            app.logger.error(f"Error extracting trade shows list: {str(e)}")

        # Get search parameters
        search_params = {
            "keyword": keyword,
            "industry": industry,
            "country": country
        }

        # Return structured data
        result = {
            "total_count": total_count,
            "trade_shows": trade_shows,
            "search_params": search_params
        }

        return result

    except Exception as e:
        app.logger.exception(f"Error in extract_trade_shows: {str(e)}")
        return {"error": str(e)}