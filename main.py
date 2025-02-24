import time

from services import *
from flask import request, jsonify




@app.route('/country_info', methods=['GET'])
def country_info():
    country = request.args.get('country', '')
    if not country:
        app.logger.error("Missing 'country' parameter")
        return jsonify({"error": "Missing 'country' parameter"}), 400

    driver = None
    try:
        app.logger.info(f"Processing request for country: {country}")
        driver = get_chrome_driver()
        driver.get("https://santandertrade.com/en")

        summary, tenders, trade_shows = search_and_extract(driver, country)

        response = jsonify({
            "summary": summary,
            "tenders": tenders,
            "trade_shows": trade_shows
        })
        app.logger.info(f"Successfully processed request for country: {country}")
        return response

    except Exception as e:
        app.logger.exception(f"Error processing request for country: {country}")
        return jsonify({"error": str(e)}), 500

    finally:
        if driver:
            driver.quit()


@app.route('/country_interest_info', methods=['GET'])
def country_interest_info():
    country = request.args.get('country', '')
    interest = request.args.get('interest', '')
    if not country or not interest:
        app.logger.error("Missing 'country' or 'interest' parameter")
        return jsonify({"error": "Missing 'country' or 'interest' parameter"}), 400

    driver = None
    try:
        app.logger.info(f"Processing request for country: {country}, interest: {interest}")
        driver = get_chrome_driver()
        driver.get("https://santandertrade.com/en")

        summary, tenders, trade_shows = search_and_extract(driver, country, interest)

        response = jsonify({
            "summary": summary,
            "tenders": tenders,
            "trade_shows": trade_shows
        })
        app.logger.info(f"Successfully processed request for country: {country}, interest: {interest}")
        return response

    except Exception as e:
        app.logger.exception(f"Error processing request for country: {country}, interest: {interest}")
        return jsonify({"error": str(e)}), 500

    finally:
        if driver:
            driver.quit()


@app.route('/country_general_info', methods=['GET'])
def country_general_info():
    country = request.args.get('country', '')
    if not country:
        app.logger.error("Missing 'country' parameter")
        return jsonify({"error": "Missing 'country' parameter"}), 400

    driver = None
    try:
        app.logger.info(f"Processing request for country general info: {country}")
        driver = get_chrome_driver()

        driver.get("https://santandertrade.com/en")

        time.sleep(2)
        # click on accept cookies button
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="accept-necessary-cookie"]'))
        ).click()

        # Wait for the element to be present
        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="btn_login_menu"]'))
        )

        # Execute JavaScript to click the button
        driver.execute_script("arguments[0].click();", login_button)

        time.sleep(2)

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

        time.sleep(2)

        # Navigate to the country general information page
        driver.get(f"https://santandertrade.com/en/portal/analyse-markets/{country}/general-presentation")

        # Wait for the content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "pays_v1"))
        )

        # Get the page source
        page_source = driver.page_source

        # Extract the general information
        general_info = extract_general_info(page_source)

        response = jsonify(general_info)
        app.logger.info(f"Successfully processed request for country general info: {country}")
        return response

    except Exception as e:
        app.logger.exception(f"Error processing request for country general info: {country}")
        return jsonify({"error": str(e)}), 500

    finally:
        if driver:
            driver.quit()


@app.route('/country_economic_political_outline', methods=['GET'])
def country_economic_political_outline():
    country = request.args.get('country', '')
    if not country:
        app.logger.error("Missing 'country' parameter")
        return jsonify({"error": "Missing 'country' parameter"}), 400

    driver = None
    try:
        app.logger.info(f"Processing request for country economic and political outline: {country}")
        driver = get_chrome_driver()

        driver.get("https://santandertrade.com/en")

        time.sleep(2)
        # click on accept cookies button
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="accept-necessary-cookie"]'))
        ).click()

        # Wait for the element to be present
        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="btn_login_menu"]'))
        )

        # Execute JavaScript to click the button
        driver.execute_script("arguments[0].click();", login_button)

        time.sleep(2)

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

        time.sleep(2)

        # Navigate to the country economic and political outline page
        driver.get(f"https://santandertrade.com/en/portal/analyse-markets/{country}/economic-political-outline")

        # Wait for the content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "pays_v1"))
        )

        # Get the page source
        page_source = driver.page_source

        # Extract the economic and political outline information
        outline_info = extract_economic_political_outline(page_source)

        response = jsonify(outline_info)
        app.logger.info(f"Successfully processed request for country economic and political outline: {country}")
        return response

    except Exception as e:
        app.logger.exception(f"Error processing request for country economic and political outline: {country}")
        return jsonify({"error": str(e)}), 500

    finally:
        if driver:
            driver.quit()


@app.route('/foreign_trade_data', methods=['GET'])
def foreign_trade_data():
    country = request.args.get('country', '')
    if not country:
        app.logger.error("Missing 'country' parameter")
        return jsonify({"error": "Missing 'country' parameter"}), 400

    driver = None
    try:
        app.logger.info(f"Processing request for foreign trade data: {country}")
        driver = get_chrome_driver()

        driver.get("https://santandertrade.com/en")

        time.sleep(2)
        # click on accept cookies button
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="accept-necessary-cookie"]'))
        ).click()

        # Wait for the element to be present
        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="btn_login_menu"]'))
        )

        # Execute JavaScript to click the button
        driver.execute_script("arguments[0].click();", login_button)

        time.sleep(2)

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

        time.sleep(2)

        # Navigate to the specific country page
        target_url = f"https://santandertrade.com/en/portal/analyse-markets/{country}/foreign-trade-in-figures"
        driver.get(target_url)
        app.logger.info(f"Navigated to {target_url}")

        # Wait for the content to load
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "encart-theme-atlas"))
            )
        except TimeoutException:
            app.logger.error("Timeout waiting for page content to load")
            return jsonify({"error": "Page content did not load in time"}), 500

        # Extract the page content
        page_content = driver.page_source
        soup = BeautifulSoup(page_content, 'html.parser')

        # Extract and structure the data
        data = {
            "overview": extract_overview(soup),
            "foreign_trade_values": extract_table_by_content(soup, "Foreign Trade Values"),
            "foreign_trade_indicators": extract_table_by_content(soup, "Foreign Trade Indicators"),
            "foreign_trade_forecasts": extract_foreign_trade_forecasts(soup),
            "international_economic_cooperation": extract_text_content(soup, "International Economic Cooperation"),
            "free_trade_agreements": extract_text_content(soup, "Free Trade Agreements"),
            "main_customers": extract_partner_table(soup, "Main Customers"),
            "main_suppliers": extract_partner_table(soup, "Main Suppliers")
        }

        return jsonify(data)

    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

    finally:
        if driver:
            driver.quit()


@app.route('/country_consumer_info', methods=['GET'])
def country_consumer_info():
    country = request.args.get('country', '')
    if not country:
        app.logger.error("Missing 'country' parameter")
        return jsonify({"error": "Missing 'country' parameter"}), 400

    driver = None
    try:
        app.logger.info(f"Processing request for country consumer info: {country}")
        driver = get_chrome_driver()

        driver.get("https://santandertrade.com/en")

        time.sleep(2)
        # click on accept cookies button
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="accept-necessary-cookie"]'))
        ).click()

        # Wait for the element to be present
        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="btn_login_menu"]'))
        )

        # Execute JavaScript to click the button
        driver.execute_script("arguments[0].click();", login_button)

        time.sleep(2)

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

        time.sleep(2)

        # Navigate to the country consumer info page
        driver.get(f"https://santandertrade.com/en/portal/analyse-markets/{country}/reaching-the-consumers")

        # Wait for the content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "pays_v1"))
        )

        # Get the page source
        page_source = driver.page_source

        # Extract the consumer information
        consumer_info = extract_consumer_info(page_source)

        response = jsonify(consumer_info)
        app.logger.info(f"Successfully processed request for country consumer info: {country}")
        return response

    except Exception as e:
        app.logger.exception(f"Error processing request for country consumer info: {country}")
        return jsonify({"error": str(e)}), 500

    finally:
        if driver:
            driver.quit()


def extract_consumer_info(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    consumer_info = {}

    # Extract consumer profile
    consumer_profile = soup.find('h2', text='Consumer Profile')
    if consumer_profile:
        profile_section = consumer_profile.find_next('div')
        consumer_info['consumer_profile'] = {}
        for dt in profile_section.find_all('dt'):
            title = dt.text.strip()
            content = dt.find_next('dd').text.strip() if dt.find_next('dd') else ''
            consumer_info['consumer_profile'][title] = content

    # Extract population figures
    population_section = soup.find('h3', text='Population in Figures')
    if population_section:
        population_data = population_section.find_next('dl')
        consumer_info['population_figures'] = {}
        for dt, dd in zip(population_data.find_all('dt'), population_data.find_all('dd')):
            key = dt.text.strip().rstrip(':')
            value = dd.text.strip()
            consumer_info['population_figures'][key] = value

    # Extract population of main cities
    cities_table = soup.find('h3', text='Population of main cities')
    if cities_table:
        cities_table = cities_table.find_next('table')
        if cities_table:
            consumer_info['main_cities'] = []
            for row in cities_table.find_all('tr')[1:]:  # Skip header row
                cells = row.find_all('td')
                if len(cells) >= 2:
                    city = cells[0].text.strip()
                    population = cells[1].text.strip()
                    consumer_info['main_cities'].append({'city': city, 'population': population})

    def extract_table_data(table, table_type):
        data = []
        rows = table.find_all('tr')
        headers = [th.text.strip() for th in rows[0].find_all(['th', 'td'])]

        if table_type in ['Household Final Consumption Expenditure', 'Purchasing Power Parity']:
            for row in rows[1:]:
                cells = row.find_all(['th', 'td'])
                if len(cells) == len(headers):
                    row_data = {headers[0]: cells[0].text.strip()}
                    for i in range(1, len(headers)):
                        row_data[headers[i]] = cells[i].text.strip()
                    data.append(row_data)
        elif table_type == 'Information Technology and Communication Equipment, per 100 Inhabitants':
            for row in rows[1:]:
                cells = row.find_all(['th', 'td'])
                if len(cells) == 2:
                    data.append({
                        table_type: cells[0].text.strip(),
                        "%": cells[1].text.strip()
                    })
        else:  # For 'Distribution of the Population By Age Bracket in %' and 'Life Expectancy in Years'
            for row in rows[1:]:
                cells = row.find_all(['th', 'td'])
                if len(cells) == 2:
                    data.append({cells[0].text.strip(): cells[1].text.strip()})

        return data

    # Extract all tables
    tables = soup.find_all('table')
    for table in tables:
        caption = table.find('caption')
        if caption:
            caption_text = caption.text.strip()
        else:
            first_row = table.find('tr')
            if first_row:
                first_cell = first_row.find(['th', 'td'])
                if first_cell:
                    caption_text = first_cell.text.strip()
                else:
                    continue
            else:
                continue

        if "Life Expectancy in Years" in caption_text:
            consumer_info["Life Expectancy in Years"] = extract_table_data(table, "Life Expectancy in Years")
        elif "Purchasing Power Parity" in caption_text:
            consumer_info["Purchasing Power Parity"] = extract_table_data(table, "Purchasing Power Parity")
        elif "Distribution of the Population By Age Bracket in %" in caption_text:
            consumer_info["Distribution of the Population By Age Bracket in %"] = extract_table_data(table,
                                                                                                     "Distribution of the Population By Age Bracket in %")
        elif "Household Final Consumption Expenditure" in caption_text:
            consumer_info["Household Final Consumption Expenditure"] = extract_table_data(table,
                                                                                          "Household Final Consumption Expenditure")
        elif "Information Technology and Communication Equipment" in caption_text:
            consumer_info[
                "Information Technology and Communication Equipment, per 100 Inhabitants"] = extract_table_data(table,
                                                                                                                "Information Technology and Communication Equipment, per 100 Inhabitants")

    # Extract media advertising information
    media_section = soup.find('h3', text='Media in Which to Advertise')
    if media_section:
        media_info = media_section.find_next('dl')
        consumer_info['media_advertising'] = {}
        for dt in media_info.find_all('dt'):
            title = dt.text.strip()
            content = dt.find_next('dd').text.strip() if dt.find_next('dd') else ''
            consumer_info['media_advertising'][title] = content

    return consumer_info

@app.route('/import_export_flow', methods=['GET'])
def import_export_flow():
    flow = request.args.get('flow', '')
    code = request.args.get('code', '')
    reporter = request.args.get('reporter', '')
    partners = request.args.get('partners', '')

    if not all([flow, code, reporter, partners]):
        app.logger.error("Missing required parameters")
        return jsonify({"error": "Missing required parameters"}), 400

    driver = None
    try:
        app.logger.info(f"Processing request for import-export flow: {flow}, {code}, {reporter}, {partners}")
        driver = get_chrome_driver()

        driver.get("https://santandertrade.com/en")

        time.sleep(2)
        # click on accept cookies button
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="accept-necessary-cookie"]'))
        ).click()

        # Wait for the element to be present
        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="btn_login_menu"]'))
        )

        # Execute JavaScript to click the button
        driver.execute_script("arguments[0].click();", login_button)

        time.sleep(2)

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

        time.sleep(2)

        # Extract the import-export flow data
        data = extract_import_export_flow(driver, flow, code, reporter, partners)

        response = jsonify(data)
        app.logger.info(f"Successfully processed request for import-export flow")
        return response

    except Exception as e:
        app.logger.exception(f"Error processing request for import-export flow")
        return jsonify({"error": str(e)}), 500

    finally:
        if driver:
            driver.quit()


@app.route('/send_notification', methods=['GET'])
def send_notification():
    """
    Route to send email notifications
    Parameters:
    - type: "1" or "2"
    - recipient: email address
    """
    try:
        # Get parameters
        notification_type = request.args.get('type')
        recipient = request.args.get('recipient')

        # Validate parameters
        if not notification_type or not recipient:
            return jsonify({
                "error": "Missing parameters",
                "message": "Please provide both 'type' and 'recipient' parameters"
            }), 400

        if notification_type not in ["1", "2"]:
            return jsonify({
                "error": "Invalid type",
                "message": "Type must be either '1' or '2'"
            }), 400

        if not '@' in recipient or not '.' in recipient:
            return jsonify({
                "error": "Invalid email",
                "message": "Please provide a valid email address"
            }), 400

        # Send email
        success, error = send_simple_email(recipient, notification_type)

        if success:
            app.logger.info(f"Successfully sent type {notification_type} notification to {recipient}")
            return jsonify({
                "status": "success",
                "message": "Notification sent successfully to Mailtrap inbox"
            }), 200
        else:
            app.logger.error(f"Failed to send notification: {error}")
            return jsonify({
                "error": "Send failed",
                "message": str(error)
            }), 500

    except Exception as e:
        app.logger.exception("Error in send_notification endpoint")
        return jsonify({
            "error": "Server error",
            "message": str(e)
        }), 500


@app.route('/best_trading_countries', methods=['GET'])
def best_trading_countries():
    flow = request.args.get('flow', '')
    industry = request.args.get('industry', '')
    sector = request.args.get('sector', '')
    exporting_country = request.args.get('exporting_country', '')

    if not all([flow, industry, sector]):
        app.logger.error("Missing required parameters")
        return jsonify({"error": "Missing 'flow', 'industry', or 'sector' parameter"}), 400

    if flow.lower() not in ['import', 'export']:
        app.logger.error("Invalid flow parameter")
        return jsonify({"error": "Flow must be either 'import' or 'export'"}), 400

    driver = None
    try:
        app.logger.info(
            f"Processing request for best trading countries: flow={flow}, industry={industry}, sector={sector}, exporting_country={exporting_country}")
        driver = get_chrome_driver()
        driver.get("https://santandertrade.com/en/portal/analyse-markets/best-trading-countries")

        # Wait for and accept cookies
        time.sleep(2)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="accept-necessary-cookie"]'))
        ).click()
        time.sleep(2)

        # Login process
        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="btn_login_menu"]'))
        )
        driver.execute_script("arguments[0].click();", login_button)

        time.sleep(2)

        # Fill login credentials
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_identifiant"]'))
        )
        driver.execute_script("arguments[0].value = 'edgarcayuelas@indegate.com';", username_field)

        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_mot_de_passe"]'))
        )
        driver.execute_script("arguments[0].value = 'Indegate@2020';", password_field)

        submit_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_go"]'))
        )
        driver.execute_script("arguments[0].click();", submit_button)

        time.sleep(30)

        # Select flow (Import/Export)
        flow_value = 'I' if flow.lower() == 'import' else 'E'
        flow_radio = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f'//input[@value="{flow_value}"]'))
        )
        flow_radio.click()

        # Select industry
        # First click to open the dropdown
        industry_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "code_hs_industry"))
        )
        industry_dropdown.click()

        # Find and click the option containing the specified industry text
        industry_option = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//select[@id='code_hs_industry']/option[contains(text(), '{industry}')]"))
        )
        driver.execute_script("arguments[0].selected = true;", industry_option)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", industry_dropdown)

        time.sleep(2)

        # Select sector
        # First click to open the dropdown
        sector_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "code_hs_secteur"))
        )
        sector_dropdown.click()

        # Find and click the option containing the specified sector text
        sector_option = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//select[@id='code_hs_secteur']/option[contains(text(), '{sector}')]"))
        )
        driver.execute_script("arguments[0].selected = true;", sector_option)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", sector_dropdown)

        time.sleep(2)

        if exporting_country:
            # Click first "Modify" button and select country in first dropdown
            modify_button1 = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="change_country_1"]'))
            )
            modify_button1.click()

            # Wait for and select from first country dropdown
            country_dropdown1 = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="ideclarant_1"]'))
            )
            country_option1 = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//select[@id='ideclarant_1']/option[contains(text(), '{exporting_country}')]"))
            )
            country_option1.click()

            time.sleep(2)

            # Click second "Modify" button and select country in second dropdown
            modify_button2 = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="change_country_2"]'))
            )
            modify_button2.click()

            # Wait for and select from second country dropdown
            country_dropdown2 = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="ideclarant_2"]'))
            )
            country_option2 = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//select[@id='ideclarant_2']/option[contains(text(), '{exporting_country}')]"))
            )
            country_option2.click()

            time.sleep(2)

        # Click all "See More Countries" links
        see_more_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'See More Countries')]")
        for link in see_more_links:
            try:
                driver.execute_script("arguments[0].click();", link)
                time.sleep(1)
            except:
                continue

        # Extract data
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        data = {
            "global_importers": extract_trading_countries(soup, "bloc-trading-gauche"),
            "country_specific_importers": extract_trading_countries(soup, "bloc-trading-droite"),
            "growth_global": extract_trading_countries(soup, "bloc-trading-gauche", is_growth=True),
            "growth_country_specific": extract_trading_countries(soup, "bloc-trading-droite", is_growth=True)
        }

        app.logger.info(f"Successfully processed request for best trading countries")
        return jsonify(data)

    except Exception as e:
        app.logger.exception(f"Error processing request for best trading countries")
        return jsonify({"error": str(e)}), 500

    finally:
        if driver:
            driver.quit()


@app.route('/company_operating_info', methods=['GET'])
def company_operating_info():
    country = request.args.get('country', '')
    if not country:
        app.logger.error("Missing 'country' parameter")
        return jsonify({"error": "Missing 'country' parameter"}), 400

    driver = None
    try:
        app.logger.info(f"Processing request for company operating info: {country}")
        driver = get_chrome_driver()

        # Navigate to login page and handle authentication
        driver.get("https://santandertrade.com/en")

        # Wait for and handle cookie acceptance
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="accept-necessary-cookie"]'))
        ).click()

        # Login process
        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="btn_login_menu"]'))
        )
        driver.execute_script("arguments[0].click();", login_button)

        time.sleep(2)

        # Fill login credentials
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_identifiant"]'))
        )
        driver.execute_script("arguments[0].value = 'edgarcayuelas@indegate.com';", username_field)

        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_mot_de_passe"]'))
        )
        driver.execute_script("arguments[0].value = 'Indegate@2020';", password_field)

        submit_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_go"]'))
        )
        driver.execute_script("arguments[0].click();", submit_button)

        time.sleep(2)

        # Navigate to the company operating info page
        target_url = f"https://santandertrade.com/en/portal/establish-overseas/{country}/operating-a-business"
        driver.get(target_url)

        # Wait for the main content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'atlas')]"))
        )

        # Extract all required information using Selenium
        operating_info = {
            "legal_forms": extract_legal_forms_selenium(driver),
            "business_setup": extract_business_setup_selenium(driver),
            "financial_directories": extract_financial_directories_selenium(driver),
            "recovery_procedures": extract_recovery_procedures_selenium(driver),
            "active_population": extract_active_population_selenium(driver),
            "working_conditions": extract_working_conditions_selenium(driver),
            "labour_cost": extract_labour_cost_selenium(driver),
            "social_security": extract_social_security_selenium(driver)
        }

        response = jsonify(operating_info)
        app.logger.info(f"Successfully processed request for company operating info: {country}")
        return response

    except Exception as e:
        app.logger.exception(f"Error processing request for company operating info: {country}")
        return jsonify({"error": str(e)}), 500

    finally:
        if driver:
            driver.quit()


@app.route('/tax_system_info', methods=['GET'])
def tax_system_info():
    country = request.args.get('country', '')
    if not country:
        app.logger.error("Missing 'country' parameter")
        return jsonify({"error": "Missing 'country' parameter"}), 400

    driver = None
    try:
        app.logger.info(f"Processing request for tax system info: {country}")
        driver = get_chrome_driver()

        # Navigate and handle login
        driver.get("https://santandertrade.com/en")

        # Handle cookie acceptance
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="accept-necessary-cookie"]'))
        ).click()

        # Login process
        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="btn_login_menu"]'))
        )
        driver.execute_script("arguments[0].click();", login_button)

        time.sleep(2)

        # Fill credentials
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_identifiant"]'))
        )
        driver.execute_script("arguments[0].value = 'edgarcayuelas@indegate.com';", username_field)

        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_mot_de_passe"]'))
        )
        driver.execute_script("arguments[0].value = 'Indegate@2020';", password_field)

        submit_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_go"]'))
        )
        driver.execute_script("arguments[0].click();", submit_button)

        time.sleep(2)

        # Navigate to tax system page
        driver.get(f"https://santandertrade.com/en/portal/establish-overseas/{country}/tax-system")

        # Wait for content
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'atlas')]"))
        )

        # Extract all sections
        tax_info = {
            "corporate_taxes": extract_corporate_taxes_selenium(driver),
            "accounting_rules": extract_accounting_rules_selenium(driver),
            "individual_taxes": extract_individual_taxes_selenium(driver),
            "taxation_treaties": extract_taxation_treaties_selenium(driver),
            "fiscal_sources": extract_fiscal_sources_selenium(driver)
        }

        response = jsonify(tax_info)
        app.logger.info(f"Successfully processed request for tax system info: {country}")
        return response

    except Exception as e:
        app.logger.exception(f"Error processing request for tax system info: {country}")
        return jsonify({"error": str(e)}), 500

    finally:
        if driver:
            driver.quit()


@app.route('/legal_environment_info', methods=['GET'])
def legal_environment_info():
    country = request.args.get('country', '')
    if not country:
        app.logger.error("Missing 'country' parameter")
        return jsonify({"error": "Missing 'country' parameter"}), 400

    driver = None
    try:
        app.logger.info(f"Processing request for legal environment info: {country}")
        driver = get_chrome_driver()

        # Navigate and handle login
        driver.get("https://santandertrade.com/en")

        # Handle cookie acceptance
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="accept-necessary-cookie"]'))
        ).click()

        # Login process
        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="btn_login_menu"]'))
        )
        driver.execute_script("arguments[0].click();", login_button)

        time.sleep(2)

        # Fill credentials
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_identifiant"]'))
        )
        driver.execute_script("arguments[0].value = 'edgarcayuelas@indegate.com';", username_field)

        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_mot_de_passe"]'))
        )
        driver.execute_script("arguments[0].value = 'Indegate@2020';", password_field)

        submit_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_go"]'))
        )
        driver.execute_script("arguments[0].click();", submit_button)

        time.sleep(3)

        # Navigate to legal environment page
        driver.get(f"https://santandertrade.com/en/portal/establish-overseas/{country}/legal-environment")

        # Wait for content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'atlas')]"))
        )

        # Extract all sections
        legal_info = {
            "business_contract": extract_business_contract_selenium(driver),
            "intellectual_property": extract_intellectual_property_selenium(driver),
            "legal_framework": extract_legal_framework_selenium(driver),
            "dispute_resolution": extract_dispute_resolution_selenium(driver)
        }

        response = jsonify(legal_info)
        app.logger.info(f"Successfully processed request for legal environment info: {country}")
        return response

    except Exception as e:
        app.logger.exception(f"Error processing request for legal environment info: {country}")
        return jsonify({"error": str(e)}), 500

    finally:
        if driver:
            driver.quit()


# Add new endpoint to main.py
@app.route('/foreign_investment_info', methods=['GET'])
def foreign_investment_info():
    country = request.args.get('country', '')
    if not country:
        app.logger.error("Missing 'country' parameter")
        return jsonify({"error": "Missing 'country' parameter"}), 400

    driver = None
    try:
        app.logger.info(f"Processing request for foreign investment info: {country}")
        driver = get_chrome_driver()

        # Navigate and handle login
        driver.get("https://santandertrade.com/en")

        # Handle cookie acceptance
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="accept-necessary-cookie"]'))
        ).click()

        # Login process
        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="btn_login_menu"]'))
        )
        driver.execute_script("arguments[0].click();", login_button)

        time.sleep(2)

        # Fill credentials
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_identifiant"]'))
        )
        driver.execute_script("arguments[0].value = 'edgarcayuelas@indegate.com';", username_field)

        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_mot_de_passe"]'))
        )
        driver.execute_script("arguments[0].value = 'Indegate@2020';", password_field)

        submit_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_go"]'))
        )
        driver.execute_script("arguments[0].click();", submit_button)

        time.sleep(3)

        # Navigate to foreign investment page
        driver.get(f"https://santandertrade.com/en/portal/establish-overseas/{country}/foreign-investment")

        # Wait for content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'atlas')]"))
        )

        # Extract foreign investment information
        investment_info = extract_foreign_investment_selenium(driver)

        response = jsonify(investment_info)
        app.logger.info(f"Successfully processed request for foreign investment info: {country}")
        return response

    except Exception as e:
        app.logger.exception(f"Error processing request for foreign investment info: {country}")
        return jsonify({"error": str(e)}), 500

    finally:
        if driver:
            driver.quit()


@app.route('/business_practices_info', methods=['GET'])
def business_practices_info():
    country = request.args.get('country', '')
    if not country:
        app.logger.error("Missing 'country' parameter")
        return jsonify({"error": "Missing 'country' parameter"}), 400

    driver = None
    try:
        app.logger.info(f"Processing request for business practices info: {country}")
        driver = get_chrome_driver()

        # Navigate and handle login
        driver.get("https://santandertrade.com/en")

        # Handle cookie acceptance
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="accept-necessary-cookie"]'))
        ).click()

        # Login process
        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="btn_login_menu"]'))
        )
        driver.execute_script("arguments[0].click();", login_button)

        time.sleep(2)

        # Fill credentials
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_identifiant"]'))
        )
        driver.execute_script("arguments[0].value = 'edgarcayuelas@indegate.com';", username_field)

        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_mot_de_passe"]'))
        )
        driver.execute_script("arguments[0].value = 'Indegate@2020';", password_field)

        submit_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_go"]'))
        )
        driver.execute_script("arguments[0].click();", submit_button)

        time.sleep(3)

        # Navigate to business practices page
        driver.get(f"https://santandertrade.com/en/portal/establish-overseas/{country}/business-practices")

        # Wait for content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'atlas')]"))
        )

        # Extract business practices information
        practices_info = extract_business_practices_selenium(driver)

        response = jsonify(practices_info)
        app.logger.info(f"Successfully processed request for business practices info: {country}")
        return response

    except Exception as e:
        app.logger.exception(f"Error processing request for business practices info: {country}")
        return jsonify({"error": str(e)}), 500

    finally:
        if driver:
            driver.quit()


# Add new endpoint to main.py
@app.route('/entry_requirements_info', methods=['GET'])
def entry_requirements_info():
    country = request.args.get('country', '')
    if not country:
        app.logger.error("Missing 'country' parameter")
        return jsonify({"error": "Missing 'country' parameter"}), 400

    driver = None
    try:
        app.logger.info(f"Processing request for entry requirements info: {country}")
        driver = get_chrome_driver()

        # Navigate and handle login
        driver.get("https://santandertrade.com/en")

        # Handle cookie acceptance
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="accept-necessary-cookie"]'))
        ).click()

        # Login process
        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="btn_login_menu"]'))
        )
        driver.execute_script("arguments[0].click();", login_button)

        time.sleep(2)

        # Fill credentials
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_identifiant"]'))
        )
        driver.execute_script("arguments[0].value = 'edgarcayuelas@indegate.com';", username_field)

        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_mot_de_passe"]'))
        )
        driver.execute_script("arguments[0].value = 'Indegate@2020';", password_field)

        submit_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_go"]'))
        )
        driver.execute_script("arguments[0].click();", submit_button)

        time.sleep(3)

        # Navigate to entry requirements page
        driver.get(f"https://santandertrade.com/en/portal/establish-overseas/{country}/entry-requirements")

        # Wait for content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'atlas')]"))
        )

        # Extract entry requirements information
        requirements_info = extract_entry_requirements_selenium(driver)

        response = jsonify(requirements_info)
        app.logger.info(f"Successfully processed request for entry requirements info: {country}")
        return response

    except Exception as e:
        app.logger.exception(f"Error processing request for entry requirements info: {country}")
        return jsonify({"error": str(e)}), 500

    finally:
        if driver:
            driver.quit()


# Add new endpoint to main.py
@app.route('/practical_info', methods=['GET'])
def practical_info():
    country = request.args.get('country', '')
    if not country:
        app.logger.error("Missing 'country' parameter")
        return jsonify({"error": "Missing 'country' parameter"}), 400

    driver = None
    try:
        app.logger.info(f"Processing request for practical info: {country}")
        driver = get_chrome_driver()

        # Navigate and handle login
        driver.get("https://santandertrade.com/en")

        # Handle cookie acceptance
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="accept-necessary-cookie"]'))
        ).click()

        # Login process
        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="btn_login_menu"]'))
        )
        driver.execute_script("arguments[0].click();", login_button)

        time.sleep(2)

        # Fill credentials
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_identifiant"]'))
        )
        driver.execute_script("arguments[0].value = 'edgarcayuelas@indegate.com';", username_field)

        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_mot_de_passe"]'))
        )
        driver.execute_script("arguments[0].value = 'Indegate@2020';", password_field)

        submit_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_go"]'))
        )
        driver.execute_script("arguments[0].click();", submit_button)

        time.sleep(3)

        # Navigate to practical information page
        driver.get(f"https://santandertrade.com/en/portal/establish-overseas/{country}/practical-information")

        # Wait for content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'atlas')]"))
        )

        # Extract practical information
        practical_info = extract_practical_info_selenium(driver)

        response = jsonify(practical_info)
        app.logger.info(f"Successfully processed request for practical info: {country}")
        return response

    except Exception as e:
        app.logger.exception(f"Error processing request for practical info: {country}")
        return jsonify({"error": str(e)}), 500

    finally:
        if driver:
            driver.quit()


# Add new endpoint to main.py
@app.route('/living_info', methods=['GET'])
def living_info():
    country = request.args.get('country', '')
    if not country:
        app.logger.error("Missing 'country' parameter")
        return jsonify({"error": "Missing 'country' parameter"}), 400

    driver = None
    try:
        app.logger.info(f"Processing request for living info: {country}")
        driver = get_chrome_driver()

        # Navigate and handle login
        driver.get("https://santandertrade.com/en")

        # Handle cookie acceptance
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="accept-necessary-cookie"]'))
        ).click()

        # Login process
        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="btn_login_menu"]'))
        )
        driver.execute_script("arguments[0].click();", login_button)

        time.sleep(2)

        # Fill credentials
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_identifiant"]'))
        )
        driver.execute_script("arguments[0].value = 'edgarcayuelas@indegate.com';", username_field)

        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_mot_de_passe"]'))
        )
        driver.execute_script("arguments[0].value = 'Indegate@2020';", password_field)

        submit_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="identification_go"]'))
        )
        driver.execute_script("arguments[0].click();", submit_button)

        time.sleep(3)

        # Navigate to living in the country page
        driver.get(f"https://santandertrade.com/en/portal/establish-overseas/{country}/living-in-the-country")

        # Wait for content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'atlas')]"))
        )

        # Extract living information
        living_info = extract_living_info_selenium(driver)

        response = jsonify(living_info)
        app.logger.info(f"Successfully processed request for living info: {country}")
        return response

    except Exception as e:
        app.logger.exception(f"Error processing request for living info: {country}")
        return jsonify({"error": str(e)}), 500

    finally:
        if driver:
            driver.quit()


@app.route('/trade_shows', methods=['GET'])
def trade_shows():
    """
    Endpoint to fetch and return trade shows from Santander Trade

    Parameters (query string):
    - keyword: Optional keyword to search for
    - industry: Optional industry ID or name
    - country: Optional country ID or name

    Returns:
    JSON response with trade shows data
    """
    keyword = request.args.get('keyword', '')
    industry = request.args.get('industry', '')
    country = request.args.get('country', '')

    driver = None
    try:
        app.logger.info(
            f"Processing request for trade shows: keyword={keyword}, industry={industry}, country={country}")
        driver = get_chrome_driver()

        # Execute the scraping function
        trade_shows_data = extract_trade_shows(driver, keyword, industry, country)

        response = jsonify(trade_shows_data)
        app.logger.info(f"Successfully processed request for trade shows")
        return response

    except Exception as e:
        app.logger.exception(f"Error processing request for trade shows")
        return jsonify({"error": str(e)}), 500

    finally:
        if driver:
            driver.quit()

@app.route('/')
def home():
    app.logger.info("Home page accessed")
    return "Welcome to the Santander Trade API. Use /country_info?country=your_country or /country_interest_info?country=your_country&interest=your_interest to get information."


if __name__ == '__main__':
    setup_logging()
    app.logger.info("Starting Santander Trade API")
    app.run(debug=False)
