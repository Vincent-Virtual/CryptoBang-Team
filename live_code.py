import requests
from bs4 import BeautifulSoup

# URL of the Coindesk Bitcoin price page
url = "https://www.coindesk.com/price/bitcoin/"

# Send a GET request to the URL
response = requests.get(url)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Parse the HTML content of the page
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the element containing the Bitcoin price
    price_element = soup.find("div")
    print(price_element.text)
#
#     # Extract the text content of the element
#     bitcoin_price = price_element.text.strip()
#
#     # Print the result
#     print(f"Bitcoin Price: {bitcoin_price}")
#
# else:
#     print(f"Failed to retrieve page. Status code: {response.status_code}")
