"""
Unit tests for the pxGrid client request methods (no broker required)
"""
import json
import unittest

from dxlclient.message import ErrorResponse, Request, Response
from mock import MagicMock

from dxlciscopxgridclient.client import CiscoPxGridClient


class CiscoPxGridClientTest(unittest.TestCase):
    def setUp(self):
        self.dxl_client = MagicMock()
        self.client = CiscoPxGridClient(self.dxl_client)

    def _respond_with(self, payload_dict):
        def sync_request(request, timeout=None): # pylint: disable=unused-argument
            self.request = request # pylint: disable=attribute-defined-outside-init
            response = Response(request)
            response.payload = json.dumps(payload_dict).encode("utf-8")
            return response
        self.dxl_client.sync_request.side_effect = sync_request

    def test_retrieve_all_policies(self):
        expected = {"ancStatus": "success", "ancpolicy": []}
        self._respond_with(expected)
        self.assertEqual(expected, self.client.anc.retrieve_all_policies())
        self.assertEqual("/mcafee/service/pxgrid/anc/retrieveallpolicies",
                         self.request.destination_topic)

    def test_apply_endpoint_policy_by_mac_sends_json_payload(self):
        self._respond_with({"status": "SUCCESS"})
        result = self.client.anc.apply_endpoint_policy_by_mac(
            "00:11:22:33:44:55", "ANC_Shut")
        self.assertEqual({"status": "SUCCESS"}, result)
        self.assertEqual("/mcafee/service/pxgrid/anc/applyendpointpolicybymac",
                         self.request.destination_topic)
        self.assertEqual(
            {"macAddress": "00:11:22:33:44:55", "policyName": "ANC_Shut"},
            json.loads(self.request.payload.decode("utf-8")))

    def test_error_response_raises(self):
        def sync_request(request, timeout=None): # pylint: disable=unused-argument
            response = ErrorResponse(request, error_code=404,
                                     error_message="unable to find service")
            return response
        self.dxl_client.sync_request.side_effect = sync_request
        with self.assertRaises(Exception) as context:
            self.client.anc.get_endpoints()
        self.assertIn("unable to find service", str(context.exception))

    def test_add_session_callback_registers_event_callback(self):
        callback = object()
        self.client.identity.add_session_callback(callback)
        self.dxl_client.add_event_callback.assert_called_once_with(
            "/mcafee/event/pxgrid/identity/session", callback)
