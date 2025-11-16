import os
from functools import lru_cache
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client
from zeep.transports import Transport

load_dotenv()

WSDL_DIR = Path(__file__).parent / "wsdl"


def _build_transport() -> Transport:
    """Create a zeep transport with optional basic auth from env."""
    session = Session()
    username = os.getenv("SOAP_USERNAME")
    password = os.getenv("SOAP_PASSWORD")
    if username and password:
        session.auth = HTTPBasicAuth(username, password)
    return Transport(session=session, timeout=30)


@lru_cache(maxsize=None)
def _load_client(wsdl_filename: str) -> Client:
    wsdl_path = WSDL_DIR / wsdl_filename
    if not wsdl_path.exists():
        raise FileNotFoundError(f"WSDL bestand '{wsdl_path}' niet gevonden.")
    return Client(wsdl=str(wsdl_path), transport=_build_transport())


def get_meta_service() -> Client:
    """Return a cached zeep client for the MetaService WSDL."""
    return _load_client("metaservice.xml")


def get_report_service() -> Client:
    """Return a cached zeep client for the ReportService WSDL."""
    return _load_client("reportservice.xml")


def list_operations(client: Client) -> List[str]:
    """Return the names of SOAP operations available for a client."""
    return sorted(client.service._binding._operations.keys())


def report_webcast_get(webcast_code: str):
    """Fetch detailed webcast info from the ReportService."""
    username = os.getenv("SOAP_USERNAME")
    password = os.getenv("SOAP_PASSWORD")
    if not username or not password:
        raise RuntimeError("SOAP_USERNAME en SOAP_PASSWORD moeten gezet zijn.")
    client = get_report_service()
    return client.service.WebcastGet(
        Username=username,
        Password=password,
        WebcastCode=webcast_code,
    )


if __name__ == "__main__":
    meta_client = get_meta_service()
    report_client = get_report_service()
    print("MetaService operations:")
    for name in list_operations(meta_client):
        print(f" - {name}")
    print("\nReportService operations:")
    for name in list_operations(report_client):
        print(f" - {name}")
