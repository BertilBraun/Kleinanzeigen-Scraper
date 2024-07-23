from dataclasses import dataclass


@dataclass
class User:
    id: str
    name: str
    rating: str
    all_offers_link: str

    @staticmethod
    def from_json(json_data: dict) -> 'User':
        return User(**json_data)


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
    user: User

    @staticmethod
    def from_json(json_data: dict) -> 'Offer':
        user_data = json_data.pop('user')
        user = User.from_json(user_data)
        return Offer(user=user, **json_data)
