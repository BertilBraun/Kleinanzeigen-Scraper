# Kleinanzeigen Scraper

Should be a simple scraper for the Kleinanzeigen website. This should allow for easier overview of the relevant items on the website to also track the price of the items and offers over time.

## Installation

```bash
pip install -r requirements.txt
```

Make a copy of the `src/config.example.py` file and rename it to `config.py`. Fill in the necessary information like the API key and the URL of the Kleinanzeigen website that you want to scrape.

## Usage

Every time you want to scrape the new offers from the website you can run the following command:

```bash
python -m src
```

Take a look at `data/example_export.xlsx` for an example of the exported data.

If you want to scrape the websites periodically each day, on windows you can use the task scheduler and queue the job to run the script each day at a specific time. This can be done by running `.\queue_periodic_scraper.ps1` from an elevated powershell terminal.

## Costs

The cost for each offer is about 0.01€-0.02€. This is due to the fact that the added images are relatively expensive, as in they require a lot of tokens ([see here](https://platform.openai.com/docs/guides/vision)).

There are currently about $50 \cdot 25=1250$ offers for windsurfing equipment on the Kleinanzeigen website in the whole of Germany. This would mean that the cost for scraping all of the offers would be about $12.5€-25€$. In a 50km radius around Karlsruhe there are about $4 \cdot 25=100$ offers. This would mean that the cost for scraping all of the offers around Karlsruhe would be about $1€-2€$.

We do not reevaluate the offers that we have already scraped. This means that the cost for scraping the offers will be directly proportional to the number of new offers that are added to the website since the last scraping.

The rate of new offers being added to the website needs to be determined before we can estimate the cost of scraping the website over a longer period of time.
