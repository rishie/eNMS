from sqlalchemy import Boolean, Column, ForeignKey, Integer, PickleType, String, Text
from sqlalchemy.ext.mutable import MutableDict
from typing import Optional
from wtforms import HiddenField, SelectField
from wtforms.widgets import TextArea

from eNMS.database import LARGE_STRING_LENGTH, SMALL_STRING_LENGTH
from eNMS.forms.automation import ServiceForm
from eNMS.forms.fields import SubstitutionField
from eNMS.forms.services import NapalmForm
from eNMS.models.automation import Job, Service
from eNMS.models.inventory import Device


class NapalmConfigurationService(Service):

    __tablename__ = "NapalmConfigurationService"

    id = Column(Integer, ForeignKey("Service.id"), primary_key=True)
    has_targets = True
    action = Column(String(SMALL_STRING_LENGTH), default="")
    content = Column(Text(LARGE_STRING_LENGTH), default="")
    driver = Column(String(SMALL_STRING_LENGTH), default="")
    use_device_driver = Column(Boolean, default=True)
    optional_args = Column(MutableDict.as_mutable(PickleType), default={})

    __mapper_args__ = {"polymorphic_identity": "NapalmConfigurationService"}

    def job(self, run: "Run", device: Device) -> dict:
        napalm_connection = self.napalm_connection(device, parent)
        run.log("info", f"Pushing configuration on {device.name} (Napalm)")
        config = "\n".join(self.sub(self.content, locals()).splitlines())
        getattr(napalm_connection, self.action)(config=config)
        napalm_connection.commit_config()
        return {"success": True, "result": f"Config push ({config})"}


class NapalmConfigurationForm(ServiceForm, NapalmForm):
    form_type = HiddenField(default="NapalmConfigurationService")
    action = SelectField(
        choices=(
            ("load_merge_candidate", "Load merge"),
            ("load_replace_candidate", "Load replace"),
        )
    )
    content = SubstitutionField(widget=TextArea(), render_kw={"rows": 5})
