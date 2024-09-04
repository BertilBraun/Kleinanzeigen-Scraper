# Kleinanzeigen Scraper

Should be a simple scraper for the Kleinanzeigen website. This should allow for easier overview of the relevant items on the website to also track the price of the items and offers over time.

## Installation

```bash
pip install -r requirements.txt
```

Make a copy of the `src/config.example.py` file and rename it to `config.py`. Fill in the necessary information like the API key and the URLs of the websites that you want to scrape including your interests and the locations which interest you.

## Usage

Every time you want to scrape the new offers from the website you can run the following command:

```bash
python -m src
```

Take a look at `data/example_export.xlsx` for an example of the exported data.

If you want to scrape the websites periodically each day, you can run the `periodic_scraper.ps1` script. This script will run the scraper every day at approximately 13:00. You can insert a shortcut to this script into the `shell:startup` folder to run the script every time you start your computer.

## Costs

The cost for each offer is about 0.001€-0.002€. This is due to the fact that the added images are relatively expensive, as in they require a lot of tokens ([see here](https://platform.openai.com/docs/guides/vision)).

There are currently about $50 \cdot 25=1250$ offers for windsurfing equipment on the Kleinanzeigen website in the whole of Germany. This would mean that the cost for scraping all of the offers would be about $1.25€-2.5€$. In a 50km radius around Karlsruhe there are about $4 \cdot 25=100$ offers. This would mean that the cost for scraping all of the offers around Karlsruhe would be about $0.1€-0.2€$.

We do not reevaluate the offers that we have already scraped. This means that the cost for scraping the offers will be directly proportional to the number of new offers that are added to the website since the last scraping.

The rate of new offers being added to the website needs to be determined before we can estimate the cost of scraping the website over a longer period of time.

## Adding your own interests

### Adding a new type of item

If you want to add your own interests to the scraper, you can do so by adding types of items that you are interested in to the `src/types_to_search.py` file.

```python

@dataclass
class ExampleCar(Entry):
    brand: str = parameter('Description of the brand')
    model: str = parameter('Description of the model')
    weight: str = parameter('Description of the weight', '#.#0', lambda x: parse_numeric(x.replace('kg', '').strip()))

```

All of the attributes that you want GPT to extract from the offer need to be added as parameters to the dataclass. The `parameter` decorator is used to specify the description of the parameter, the format of the parameter and the function that is used to parse the parameter.

The new type of item that you have added needs to be added to the `ALL_TYPES` list at the bottom of the `src/types_to_search.py` file. That's it!

### Adding a new website

To add a new website to the scraper, you need to create a new scraper class that inherits from the `BaseScraper` class. You need to implement the following methods:

```python

class MyOwnScraper(BaseScraper):
    @overrides(BaseScraper)
    def filter_relevant_urls(self, urls: list[str]) -> list[str]:
        # Return only the relevant search URLs for the current scraper
        ...

    @overrides(BaseScraper)
    async def scrape_offer_url(self, url: str) -> Offer:
        # Scrape the offer details from the provided offer URL
        ...

    @overrides(BaseScraper)
    async def scrape_offer_links_from_search_url(self, base_url: str) -> list[str]:
        # Scrape the links to all offers from the provided search URL
        ...

```

After you have implemented the scraper class, you need to add the scraper to the `ALL_SCRAPERS` list in the `src/__main__.py` file. That's it!

## Future work

- Add other websites to scrape
  - [ ] Facebook Marketplace
- [ ] More fine-grained search on Kleinanzeigen. Only search for sails, masts etc. instead of windsurfing sails, windsurfing masts - Let GPT filter out only windsurfing related stuff
- [ ] Windmag.com seems to have a relatively good sail database. Maybe search in there for more information to complete the scraped entries (with another GPT call). Go to [here](https://www.windmag.com/voiles-2020-point-7-salt-pro), open the Network tab, then write something in the search box and look at the made request to <https://www.windmag.com/xwidget/testssearch/index2012?q=SEARCH_TERM>. That request could be copied after the brand and name of the sail has been extracted and send with the brand and name included in the search term. Be careful though. By far not all sails are included in there and the search is very sensitive, meaning, if it is no longer a direct match, then no items will be returned. (Also the entire website is in french as far as I saw).
- [ ] Rewrite the GPT and Typing components using OpenAIs new [Structured Output enforcing](https://platform.openai.com/docs/guides/structured-outputs/introduction)

