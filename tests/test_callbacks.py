"""
Unit tests for the pxGrid event callbacks (no broker required)
"""
import base64
import json
import unittest

from dxlclient.message import Event

from dxlciscopxgridclient.callbacks import AncStatusCallback, \
    CallbackHelper, IdentitySessionCallback

ANC_CONTENT = {
    "macAddress": "00:11:22:33:44:55",
    "operationId": "cise.psarchlab.com:104",
    "policyName": "ANC_Shut",
    "status": "SUCCESS"
}


def _make_event(payload_dict):
    event = Event("/mcafee/event/pxgrid/anc/status")
    event.payload = json.dumps(payload_dict).encode("utf-8")
    return event


def _base64_json(value):
    return base64.b64encode(json.dumps(value).encode("utf-8")).decode("ascii")


class CallbackHelperTest(unittest.TestCase):
    def test_base64_json_content_is_decoded(self):
        encoded = _base64_json(ANC_CONTENT)
        result = CallbackHelper.append_base64_decoded_content(
            {"command": "MESSAGE", "content": encoded})
        self.assertEqual(ANC_CONTENT, result["content"])
        self.assertEqual(encoded, result["content_base64"])
        self.assertEqual("MESSAGE", result["command"])

    def test_missing_content_is_untouched(self):
        result = CallbackHelper.append_base64_decoded_content({"command": "MESSAGE"})
        self.assertEqual({"command": "MESSAGE"}, result)

    def test_non_string_content_is_untouched(self):
        result = CallbackHelper.append_base64_decoded_content(
            {"content": ANC_CONTENT})
        self.assertEqual(ANC_CONTENT, result["content"])
        self.assertEqual(ANC_CONTENT, result["content_base64"])

    def test_content_that_is_not_base64_json_is_untouched(self):
        # Regression: plain text / invalid base64 / base64 of non-JSON used
        # to raise UnicodeDecodeError or JSONDecodeError out of the callback.
        for content in ("not base64 json", "eyJhIjo=", "YWJj", "%%%",
                        base64.b64encode(b"\xff\xfe").decode("ascii")):
            result = CallbackHelper.append_base64_decoded_content(
                {"content": content})
            self.assertEqual(content, result["content"], content)
            self.assertEqual(content, result["content_base64"], content)


class EventCallbackTest(unittest.TestCase):
    def test_anc_status_callback_receives_decoded_dict(self):
        received = []

        class TestCallback(AncStatusCallback):
            def _on_status_notification(self, status_dict):
                received.append(status_dict)

        TestCallback().on_event(_make_event(
            {"command": "MESSAGE", "content": _base64_json(ANC_CONTENT)}))
        self.assertEqual(1, len(received))
        self.assertEqual(ANC_CONTENT, received[0]["content"])

    def test_identity_session_callback_receives_decoded_dict(self):
        received = []

        class TestCallback(IdentitySessionCallback):
            def on_session(self, session_dict):
                received.append(session_dict)

        session = {"state": "Started", "user": {"name": "root"}}
        TestCallback().on_event(_make_event(session))
        self.assertEqual([session], received)
