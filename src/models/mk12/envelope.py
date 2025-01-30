from typing import Any, List, Tuple, TypeVar, Callable, Type, cast
from uuid import UUID

from src.models.common import (
    T,
    from_bool,
    from_datetime,
    from_dict,
    from_float,
    from_int,
    from_list,
    from_none,
    from_str,
    from_union,
    to_class,
    to_enum,
    to_float,
)


class SSCEnvelopeTransaction:
    raw_data: Any
    transaction_id: UUID
    hydra_events: List[Any]
    client_version: None
    client_platform: None

    def __init__(
        self,
        transaction_id: UUID,
        hydra_events: List[Any],
        client_version: None,
        client_platform: None,
    ) -> None:
        self.raw_data = None
        self.transaction_id = transaction_id
        self.hydra_events = hydra_events
        self.client_version = client_version
        self.client_platform = client_platform

    @staticmethod
    def from_dict(obj: Any, raw: bool = False) -> "SSCEnvelopeTransaction":
        assert isinstance(obj, dict)
        transaction_id = UUID(obj.get("transaction_id"))
        hydra_events = from_list(lambda x: x, obj.get("hydra_events"))
        client_version = from_none(obj.get("client_version"))
        client_platform = from_none(obj.get("client_platform"))
        instance = SSCEnvelopeTransaction(
            transaction_id, hydra_events, client_version, client_platform
        )
        if raw:
            instance.raw_data = obj
        return instance

    def to_dict(self) -> dict:
        result: dict = {}
        result["transaction_id"] = str(self.transaction_id)
        result["hydra_events"] = from_list(lambda x: x, self.hydra_events)
        result["client_version"] = from_none(self.client_version)
        result["client_platform"] = from_none(self.client_platform)
        return result


class SSCEnvelopeBody:
    raw_data: Any
    transaction: SSCEnvelopeTransaction
    account_id: None
    response: Any

    def __init__(
        self, transaction: SSCEnvelopeTransaction, account_id: None, response: Any
    ) -> None:
        self.raw_data = None
        self.transaction = transaction
        self.account_id = account_id
        self.response = response

    @staticmethod
    def from_dict(obj: Any, raw: bool = False) -> "SSCEnvelopeBody":
        assert isinstance(obj, dict)
        transaction = SSCEnvelopeTransaction.from_dict(obj.get("transaction"))
        account_id = from_none(obj.get("account_id"))
        response = obj.get("response")
        instance = SSCEnvelopeBody(transaction, account_id, response)
        if raw:
            instance.raw_data = obj
        return instance

    def to_dict(self) -> dict:
        result: dict = {}
        result["transaction"] = to_class(SSCEnvelopeTransaction, self.transaction)
        result["account_id"] = from_none(self.account_id)
        result["response"] = self.response.__class__.to_dict(self.response)
        return result


class SSCEnvelopeMetadata:
    raw_data: Any
    msg: str

    def __init__(self, msg: str) -> None:
        self.raw_data = None
        self.msg = msg

    @staticmethod
    def from_dict(obj: Any, raw: bool = False) -> "SSCEnvelopeMetadata":
        assert isinstance(obj, dict)
        msg = from_str(obj.get("msg"))
        instance = SSCEnvelopeMetadata(msg)
        if raw:
            instance.raw_data = obj
        return instance

    def to_dict(self) -> dict:
        result: dict = {}
        result["msg"] = from_str(self.msg)
        return result


class SSCEnvelope:
    raw_data: Any
    body: SSCEnvelopeBody
    metadata: SSCEnvelopeMetadata
    return_code: int

    def __init__(
        self, body: SSCEnvelopeBody, metadata: SSCEnvelopeMetadata, return_code: int
    ) -> None:
        self.raw_data = None
        self.body = body
        self.metadata = metadata
        self.return_code = return_code

    @staticmethod
    def from_dict(obj: Any, raw: bool = False) -> "SSCEnvelope":
        assert isinstance(obj, dict)
        body = SSCEnvelopeBody.from_dict(obj.get("body"))
        metadata = SSCEnvelopeMetadata.from_dict(obj.get("metadata"))
        return_code = from_int(obj.get("return_code"))
        instance = SSCEnvelope(body, metadata, return_code)
        if raw:
            instance.raw_data = obj
        return instance

    def to_dict(self) -> dict:
        result: dict = {}
        result["body"] = to_class(SSCEnvelopeBody, self.body)
        result["metadata"] = to_class(SSCEnvelopeMetadata, self.metadata)
        result["return_code"] = from_int(self.return_code)
        return result


def ssc_envelope_response_from_dict(s: Any, response_type: Type[T]) -> Tuple[SSCEnvelope, T]:
    envelope = SSCEnvelope.from_dict(s)
    return envelope, envelope.body.response


def ssc_envelope_player_module_to_dict(x: SSCEnvelope) -> Any:
    return to_class(SSCEnvelope, x)
