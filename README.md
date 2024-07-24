# Kleinanzeigen Scraper

Should be a simple scraper for the Kleinanzeigen website. This should allow for easier overview of the relevant items on the website to also track the price of the items and offers over time.

## Installation

```bash
pip install -r requirements.txt
```

Make a copy of the `src/config.example.py` file and rename it to `config.py`. Fill in the necessary information.

## Usage

```bash
python -m src
```

## Costs

The cost for each offer is about 0.01€-0.02€. This is due to the fact that the added images are relatively expensive, as in they require a lot of tokens ([see here](https://platform.openai.com/docs/guides/vision)).

There are currently about 50*25=1250 offers for windsurfing equipment on the Kleinanzeigen website in the whole of Germany. This would mean that the cost for scraping all of the offers would be about 12.5€-25€. In a 50km radius around Karlsruhe there are about 4*25=100 offers. This would mean that the cost for scraping all of the offers would be about 1€-2€.

We do not reevaluate the offers that we have already scraped. This means that the cost for scraping the offers will be directly proportional to the number of new offers that are added to the website since the last scraping.

The rate of new offers being added to the website needs to be determined before we can estimate the cost of scraping the website over a longer period of time.
