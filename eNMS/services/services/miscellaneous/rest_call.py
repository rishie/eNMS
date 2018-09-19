from re import search
from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String
from sqlalchemy.ext.mutable import MutableList

from eNMS.services.connections import napalm_connection
from eNMS.services.models import multiprocessing, Service, service_classes


class RestCallService(Service):

    __tablename__ = 'RestCallService'

    id = Column(Integer, ForeignKey('Service.id'), primary_key=True)
    call_type = Column(String)
    url = Column(String)
    payload = Column(MutableDict.as_mutable(PickleType), default={})
    content_match = Column(String)
    content_match_regex = Column(Boolean)
    username = Column(String)
    password = Column(String)
    device_multiprocessing = False
    request_dict = {
        'GET': rest_get,
        'POST': rest_post,
        'PUT': rest_put,
        'DELETE': rest_delete
    }

    __mapper_args__ = {
        'polymorphic_identity': 'rest_call_service',
    }

    def job(self, task, results, incoming_payload):
        try:
            if self.call_type in ('GET', 'DELETE'):
                result = self.request_dict[self.call_type](
                    self.url,
                    headers={'Accept': 'application/json'},
                    auth=HTTPBasicAuth(self.username, self.password)
                ).json()
            else:
                result = loads(self.request_dict[self.call_type](
                    self.url,
                    data=dumps(self.payload),
                    auth=HTTPBasicAuth(self.username, self.password)
                ).content)
            if self.content_match_regex:
                success = bool(search(self.content_match, str(result)))
            else:
                success = self.content_match in str(result)
            if isinstance(incoming_payload, dict):
                incoming_payload[self.name] = result
            else:
                incoming_payload = {self.name: result}
        except Exception as e:
            result, success = str(e), False
        return {
            'success': success,
            'payload': {
                'incoming_payload': incoming_payload,
                'outgoing_payload': result
            },
            'logs': result
        }


service_classes['Rest Call Service'] = RestCallService
