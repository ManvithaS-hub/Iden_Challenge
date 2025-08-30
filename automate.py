from playwright.sync_api import sync_playwright
import json, os
from dotenv import load_dotenv
import json
from playwright.sync_api import Error as PlaywrightError,TimeoutError 
load_dotenv()

"""This playwright script checks all below objectives:
1)First checks for an existing session and attempts to use it.
2)If no session exists, authenticate with the application using the provided credentials and saves the session for future use.
3)Navigates the hidden path to the product table: Click the 'Menu' button, then select 'Data Management', then 'Inventory',
 and finally 'View All Products' from the dropdown menu to reveal the product data.
4)Capture all product data from the table, including handling any pagination or dynamic loading.
5)Export the harvested data to a structured JSON file for analysis."""



SESSION_FILE = "session.json"
#Stored confidential in .env file
username=os.getenv("IDEN_EMAIL")
password=os.getenv("IDEN_PASSWORD")
LOGIN_URL="https://hiring.idenhq.com/"
INST_URL="https://hiring.idenhq.com/instructions"
    

def save_session(context):
    page = context.pages[0]
    # Extract sessionStorage key "current_user"
    user_data = page.evaluate("sessionStorage.getItem('current_user')")
    if user_data:
        with open(SESSION_FILE, "w") as f:
            json.dump({"current_user": json.loads(user_data)}, f, indent=4)
        print("Session saved.")
    else:
        print("No sessionStorage found!")

def login(playwright):
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(LOGIN_URL)

    # Perform login
    page.fill('input[type="email"]', username)
    page.fill('input[type="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")

    # Check for login failure
    try:
        page.wait_for_selector(
            "div.grid.gap-1 div:text('Login failed')", timeout=10000) #found div selector by inspecting the element
        print("Login failed.")
        context.close()
        browser.close()# Close browser to avoid orphan processes
        return None, None
    except TimeoutError:
        pass

    # Save session
    save_session(context)
    return context, page


#function to load existing session
def load_session(playwright):
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            data = json.load(f)

        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(LOGIN_URL)

        # Inject sessionStorage
        page.evaluate(f"sessionStorage.setItem('current_user', '{json.dumps(data['current_user'])}')")

        # Refresh to apply session
        page.reload()
        print("Session restored.")
        return context, page
    else:
        return login(playwright)
    




def save_to_json(data, filename="products.json"):#creates a json file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {filename}")


#If we use BeautifulSoup here, it will load all the rows at once and may cause memory issues but it was faster
def scroll_and_collect(page, total_count, save_file="products.json"):
    """
    Scroll through the table until total_count is reached.
    Collect rows incrementally and save to JSON.
    Stops gracefully if the browser/page is closed.
    """
    collected_ids = set()
    all_data = []
    prev_count = 0
    max_attempts = 500
    container_selector = "div.rounded-md.border.shadow-sm.bg-card > div"

    print(f"Starting to collect product data")
    #To handle unexpected browser/page closure, wrap in try-except
    try:
        for attempt in range(max_attempts):
            # Scroll the table container
            try:
                page.eval_on_selector(container_selector, "el => el.scrollTo(0, el.scrollHeight)")
            except PlaywrightError:
                print("Browser closed. Stopping collection.")
                break

            page.wait_for_timeout(1000)  # wait for rows to load

            # Wait if loader "..." appears as it indicates loading more rows
            loader_found = False
            try:
                page.wait_for_selector("tbody tr:has-text('...')", state="visible", timeout=1000)
                loader_found = True
                print("Loader appeared, waiting...")
                page.wait_for_selector("tbody tr:has-text('...')", state="detached", timeout=5000)
            except PlaywrightError:
                pass

            # handle unexpected browser/page closure during row collection
            try:
                rows = page.query_selector_all("tbody tr.infinite-table-row-appear")
            except PlaywrightError:
                print("Browser closed during row collection. Stopping.")
                break

            for row in rows:
                try:
                    cols = row.query_selector_all("td")
                    #Check for valid row
                    if len(cols) < 9:
                        continue
                    if any(c.inner_text().strip() == "..." for c in cols):#skip loading rows
                        continue

                    prod_id = cols[0].inner_text().strip()#helps to avoid duplicates
                    if prod_id in collected_ids:
                        continue

                    collected_ids.add(prod_id)#track collected IDs to avoid duplicates
                    rating_span = cols[7].query_selector("span")#as span is collecting rating value
                    item = {
                        "ID": prod_id,
                        "Last Updated": cols[1].inner_text().strip(),
                        "Category": cols[2].inner_text().strip(),
                        "Material": cols[3].inner_text().strip(),
                        "Price": cols[4].inner_text().strip(),
                        "Weight (kg)": cols[5].inner_text().strip(),
                        "Item": cols[6].inner_text().strip(),
                        "Rating": float(rating_span.inner_text().strip()) if rating_span else 0,
                        "Manufacturer": cols[8].inner_text().strip(),
                    }
                    all_data.append(item)#appending as soon as item is created

                    # Save incrementally
                    with open(save_file, "w", encoding="utf-8") as f:
                        json.dump(all_data, f, indent=4)

                    # Stop if total_count reached
                    if len(all_data) >= total_count:
                        print(f"Reached total count: {total_count}")
                        return all_data

                except PlaywrightError:
                    continue  # skip row if page closes mid-access

            cur_count = len(rows)
            if cur_count == prev_count and not loader_found:#also checks if no row is not being added
                print("Reached end of table (no more rows).")
                break
            prev_count = cur_count

    except PlaywrightError:
        print("Browser/page closed unexpectedly. Returning collected data so far.")

    print(f"Total collected: {len(all_data)} rows")
    return all_data

#function to launch the challenge and navigate to product table
def launch_challenge(page):
    page.set_default_timeout(10000)
    page.slow_mo = 5000

    # Listen for network responses to capture totalItemCount
    #We are counting totalItemCount beacuse it helps in knowing how many items to scrape
    #We can also get this from sessionStorage but this is more dynamic
    total_count = 0
    def handle_response(response):
        nonlocal total_count
        url = response.url
        ct = response.headers.get("content-type", "")
        if "application/json" in ct and "get_user_config_safe" in url:#as its storing totalItemCount in this api response
            try:
                data = response.json()
                if isinstance(data, list) and "config" in data[0]:
                    total_count = data[0]["config"].get("totalItemCount", 0)
                    print(f"totalItemCount detected: {total_count}")
            except:
                pass

    page.on("response", handle_response)

    # Scroll to bottom first
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")#as "Launch Challenge" button is at the bottom
    page.wait_for_timeout(1000)


    page.wait_for_selector("text=Launch Challenge", timeout=10000)
    page.click("text=Launch Challenge")
    page.wait_for_load_state("networkidle")
    print("Clicked Launch Challenge button.")

    # Navigate through the menu to reach the product table
    steps = [
        ("text=Menu", "Menu Opened."),
        ("text=Data Management", "Data Management Opened."),
        ("text=Inventory", "Inventory Opened."),
        ("text=View All Products", "All Products Opened."),
        ("text=Load Product Table", "Product Table Loaded.")
    ]

    for selector, success_message in steps:#success message for checking if step is completed
        page.wait_for_selector(selector, state="visible", timeout=10000)#state visible to ensure element is interactable
        page.wait_for_timeout(800)
        page.click(selector)
        page.wait_for_load_state("networkidle", timeout=10000)
        print(success_message)
        page.wait_for_timeout(800)

    # Collect table data incrementally
    all_products = scroll_and_collect(page, total_count)
    return all_products
    

with sync_playwright() as p:
    #Checks if session exist
    if os.path.exists(SESSION_FILE):
        context, page = load_session(p)
    #If no session found, login and store the credentials
    else:
        context, page = login(p)
    
    if context is None or page is None:
        print("Exiting due to login failure.")
        exit(1)

    # Continue automation...
    page.goto(INST_URL)
    #wait until network is idle(finished loading all network activity)
    page.wait_for_load_state("networkidle")
    page.slow_mo = 800
    launch_challenge(page)


