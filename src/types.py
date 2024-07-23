
from dataclasses import dataclass


@dataclass
class Offer:
    id: str
    title: str
    description: str
    price: str
    location: str
    date: str
    link: str
    sold: bool


@dataclass
class User:
    id: str
    name: str
    rating: str
    all_offers_link: str
