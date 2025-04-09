import re
from dataclasses import dataclass

from app.services.base import TransfermarktBase
from app.utils.utils import extract_from_url, safe_split
from app.utils.xpath import Players


@dataclass
class TransfermarktPlayerTransfers(TransfermarktBase):
    """
    A class for retrieving and parsing the player's transfer history and youth club details from Transfermarkt.

    Args:
        player_id (str): The unique identifier of the player.
        URL (str): The URL template for the player's transfers page on Transfermarkt.
    """

    player_id: str = None
    URL: str = "https://www.transfermarkt.com/-/transfers/spieler/{player_id}"
    URL_TRANSFERS: str = "https://www.transfermarkt.com/ceapi/transferHistory/list/{player_id}"

    def __post_init__(self) -> None:
        """Initialize the TransfermarktPlayerTransfers class."""
        self.URL = self.URL.format(player_id=self.player_id)
        self.page = self.request_url_page()
        self.raise_exception_if_not_found(xpath=Players.Profile.NAME)
        self.transfer_history = self.make_request(url=self.URL_TRANSFERS.format(player_id=self.player_id))

    def __map_transfer_fee(self, fee_string: str) -> str:
        """
        Extracts the fee value from a string. If the string contains '<', it processes
        the string to fetch the value. Otherwise, it returns the original string.

        Args:
            fee_string (str): The fee string to process.

        Returns:
            str: The extracted fee value or the original string if no '<' is found.
        """
        print(fee_string)
        value = fee_string
        if "<" in fee_string:
            # Use regex to extract the value inside the HTML tags
            match = re.search(r'>([^<]+)<', fee_string)
            value = match.group(1).strip() if match else ""
        print(value)
        return value

    def __parse_player_transfer_history(self) -> list:
        """
        Parse and retrieve the transfer history of the specified player from Transfermarkt,
        including the unique identifier of each transfer, source club information (ID and name),
        destination club information (ID and name), transfer date, upcoming status, season, market
        value at the time of transfer, and transfer fee.

        Returns:
            list: A list of dictionaries, each containing details of the player's transfer history,
        """
        transfers = self.transfer_history.json().get("transfers")

        return [
            {
                "id": extract_from_url(transfer["url"], "transfer_id"),
                "clubFrom": {
                    "id": extract_from_url(transfer["from"]["href"]),
                    "name": transfer["from"]["clubName"],
                },
                "clubTo": {
                    "id": extract_from_url(transfer["to"]["href"]),
                    "name": transfer["to"]["clubName"],
                },
                "date": transfer["date"],
                "upcoming": transfer["upcoming"],
                "season": transfer["season"],
                "marketValue": transfer["marketValue"],
                "fee": self.__map_transfer_fee(transfer["fee"]),
            }
            for transfer in transfers
        ]

    def get_player_transfers(self) -> dict:
        """
        Retrieve and parse the transfer history and youth clubs of the specified player from Transfermarkt.

        Returns:
            dict: A dictionary containing the player's unique identifier, parsed transfer history, youth clubs,
                  and the timestamp of when the data was last updated.
        """
        self.response["id"] = self.player_id
        self.response["transfers"] = self.__parse_player_transfer_history()
        self.response["youthClubs"] = safe_split(self.get_text_by_xpath(Players.Transfers.YOUTH_CLUBS), ",")

        return self.response
