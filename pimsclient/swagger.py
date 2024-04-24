"""Additional methods to handle swagger API responses that were not or could not be
auto-generated like swagger_models.py
"""
import json
from enum import Enum
from typing import Dict, Type

import requests
from pydantic import BaseModel

from pimsclient.logs import get_module_logger
from pimsclient.autogen.swagger_models_v0 import JsonDataHeader

logger = get_module_logger("swagger")


class HTTPMethod(str, Enum):
    """Used in SwaggerPagedResultsIterator

    In python >= 3.11 this is in http.HTTPMethod. But not in the
    pimsclient python version.
    """

    GET = "GET"
    POST = "POST"


class SwaggerPagedResultsIterator:
    def __init__(
        self,
        paged_result_class: Type[BaseModel],
        session: requests.Session,
        url: str,
        params: Dict[str, str],
        method: HTTPMethod = HTTPMethod.GET,
    ):
        """Iterates over items in paged swagger response. Fires new queries as
        needed

        Parameters
        ----------
        paged_result_class:
            The python class of PagedResult you expect to get back from call.
            Should be an instance of `pydantic.BaseModel`.
        session:
            Session to call urls on to retrieve items
        url:
            API call url, can include parameters. Subsequent calls will include
            these parameters as well, adding a `page` parameter to call different
            pages
        params:
            Pass these params to requests.get()
        method: HTTPMethod, optional
            Whether to get or post for each new page. Default to get


        Raises
        ------
        ValueError
            If params contains a non-zero parameter `page`. In this case it is
            unclear
            what you want: get all items or get a certain page?
        """
        self.paged_result_class = paged_result_class
        self.session = session
        self.url = url
        if params.get("page"):  # None or 0 are OK, rest is not.
            raise ValueError(
                'Parameter "page" was given with non-zero argument '
                f'({params.get("page")}). You cannot iterate over all'
                f"pages results while define a single page. Please remove"
            )

        self.params = params
        self.method = method
        self._current_paged_response = None

    def __iter__(self):
        """Will iterate over items returned in paged result. If there are more items
        will launch a new query and return those
        """
        if (
            not self._current_paged_response
        ):  # initial situation. Get first result
            self._current_paged_response = self.get_page_response(page=0)

        while self._current_paged_response.items:
            yield self._current_paged_response.items.pop()
        if self._current_paged_response.countComplete:
            return  # yield exhausted and count is complete. we're done
        else:  # yield exhausted but count not complete. Query again and yield
            current_page = int(self._current_paged_response.page)
            self._current_paged_response = self.get_page_response(
                current_page + 1
            )
            yield from self

    def get_page_response(self, page):
        params = {"page": str(page)}
        params.update(self.params)
        logger.debug(
            f"Sending {self.method} for {self.paged_result_class.__name__} "
            f"paged result #{page}"
        )
        response = self.session.request(
            method=self.method, url=self.url, params=params
        )
        return self.paged_result_class.parse_obj(json.loads(response.text))


class MyJsonDataHeader(JsonDataHeader):
    """Auto-generated JsonDataHeader does not serialize the contained enum correctly.
    Fix this with pydantic config option.

    Also adding additional description of `pseudonymisationAction` enum by PIMS dev.

    Description of `pseudonymisationAction` enum values
    # "Store"
    # sla waardes op in keyfile onder datakolom met zelfde naam, maak leeg in
    # antwoord.

    # "Pseudonym"
    # deze kolom bevat pseudonymen die je zelf bedacht hebt of al eerder gegenereerd.
    # pims zal deze gebruiken als de identity nog niet bestaat, of als er geen
    # identity
    # meegegeven wordt zal pims met dit pseudonym de geuploade rijen matchen aan
    # bestaande rijen in de keyfile. wordt geleegd in het antwoord


    # "Identifier"
    # deze kolom bevat de unieke identifiers. wordt geleegd in het antwoord,
    #opgeslagen in keyfile en eventueel pseudonym aan gehangen


    #"Identitysource"
    # deze kolom bevat de identity sources. overschrijft de waarde van
    ‘identitysource’ in het hoofdobject indien gegeven

    # "PseudonymFromOtherKeyfile"
    # deze kolom bevat pseudonymen van een andere keyfile (id daarvan moet opgegeven
    # worden in hoofdobject). hiermee kan je bijvoorbeeld een dataset van de ene naar
    # een andere keyfile overzetten zonder tussendoor te hoeven reidentificeren.

    # "PseudonymOutput"
    # wordt automatisch gegenereerd door pims als deze niet bestaat. in de retourfile,
    # zal deze kolom de pseudonymen bevatten die aan elke rij zijn toegekend.

    # "None"
    # kolom wordt niks mee gedaan (niet opgeslagen in keyfile, wel geretourneerd in
    # antwoord).


    # "Clear"
    # kolom wordt leeggemaakt (niet opgeslagen in keyfile, leeg gemaakt in antwoord).


    # "Return_masked"
    # indien kolom een datum, tel. nr of postcode bevat, retourneert deze een
    # gemaskeerde kolom (***) in het resultaat maar slaat het origineel op in de
    # keyfile (voor datums wordt **-maand-jaar teruggegeven)*


    # "Return_masked_yyyy"
    # idem aan bovenstaande, maar maskeert het jaartal niet (dus **-**-2024)*

    """

    class Config:
        use_enum_values = (
            True  # Make pydantic serialize enums by string value.
        )
