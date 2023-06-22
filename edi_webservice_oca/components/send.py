# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from requests.exceptions import HTTPError

from odoo import _, exceptions

from odoo.addons.component.core import Component


class EDIWebserviceSend(Component):
    """Generic component for webservice requests.

    Configuration is expected to come from the work ctx key `webservice`.
    You can easily pass via exchange type advanced settings.
    """

    _name = "edi.webservice.send"
    _inherit = [
        "edi.component.mixin",
    ]
    _usage = "webservice.send"

    def __init__(self, work_context):
        super().__init__(work_context)
        self.ws_settings = getattr(work_context, "webservice", {})
        self.webservice_backend = self.backend.webservice_backend_id

    def send(self):
        method, pargs, kwargs = self._get_call_params()
        response_content = ""
        status_code = False
        try:
            response_content = self.webservice_backend.call(method, *pargs, **kwargs)
        except HTTPError as err:
            response_content = err.response.content
            status_code = err.response.status_code
            raise err from err
        except Exception as ex:
            response_content = ""
            raise ex from ex
        else:
            status_code = 200
        finally:
            self.exchange_record._set_file_content(
                response_content, field_name="ws_response_content"
            )
            self.exchange_record.ws_response_status_code = status_code
        return response_content

    def _get_call_params(self):
        try:
            method = self.ws_settings["method"].lower()
        except KeyError as err:
            raise exceptions.UserError(
                _("`method` is required in `webservice` type settings.")
            ) from err
        pargs = self.ws_settings.get("pargs", [])
        kwargs = self.ws_settings.get("kwargs", {})
        kwargs["data"] = self._get_data()
        return method, pargs, kwargs

    def _get_data(self):
        # By sending as bytes `requests` won't try to guess and/or alter the encoding.
        # TODO: add tests
        as_bytes = self.ws_settings.get("send_as_bytes")
        return self.exchange_record._get_file_content(as_bytes=as_bytes)
