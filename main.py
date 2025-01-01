import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import matplotlib.pyplot as plt

from playwright.sync_api import sync_playwright

from playwright.sync_api import sync_playwright

def fetch_cex_prices(item_name):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        url = f"https://uk.webuy.com/search?stext={item_name.replace(' ', '%20')}"
        page.goto(url)
        page.wait_for_selector(".ais-Hits")  # Wait until products load

        # Extract product details
        items = []
        while True:
            product_records = page.query_selector_all(".content")
            for product in product_records:
                name = product.query_selector(".card-title").inner_text()
                price = product.query_selector(".price-wrapper").inner_text()
                items.append({"name": name, "price": price})

            # Check if there is a "next page" button and navigate
            next_button = page.query_selector("Next Page")  # Update selector if necessary
            if next_button and next_button.is_visible():
                    next_button.click()
            else:
                # Exit the loop if no next page is found
                break

        browser.close()
        return items


# Store data in a DataFrame
def update_price_data(item_name, df):
    """
    Update the data with new prices and timestamps.
    """
    prices = fetch_cex_prices(item_name)
    if prices is not None:
        timestamp = pd.Timestamp.now()
        for item in prices:
            df = pd.concat([df, pd.DataFrame([{"name": item["name"], "price": item["price"], "timestamp": timestamp}])], ignore_index=True)
    return df

# Save and load data
def save_data(df, file_name="prices.csv"):
    df.to_csv(file_name, index=False)

def load_data(file_name="prices.csv"):
    try:
        return pd.read_csv(file_name, parse_dates=["timestamp"])
    except FileNotFoundError:
        return pd.DataFrame(columns=["name", "price", "timestamp"])

# Visualize trends
def plot_price_trend(df, item_name):
    """
    Plot the price trends for a specific item.
    """
    item_data = df[df["name"].str.contains(item_name, case=False, na=False)]
    if item_data.empty:
        print("No data available for this item.")
        return
    
    item_data = item_data.sort_values("timestamp")
    plt.figure(figsize=(10, 6))
    for name in item_data["name"].unique():
        subset = item_data[item_data["name"] == name]
        plt.plot(subset["timestamp"], subset["price"], label=name)

    plt.title(f"Price Trend for '{item_name}'")
    plt.xlabel("Time")
    plt.ylabel("Price (£)")
    plt.legend()
    plt.show()

# Main workflow
if __name__ == "__main__":
    data_file = "prices.csv"
    item = input("Enter the item name to track: ")
    data = load_data(data_file)
    
    while True:
        print(f"Fetching prices for {item}...")
        data = update_price_data(item, data)
        save_data(data, data_file)
        plot_price_trend(data, item)
        print("Data updated. Waiting for the next cycle...")
        time.sleep(3600)  # Wait for an hour before fetching again
