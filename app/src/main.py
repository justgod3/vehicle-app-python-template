# Copyright (c) 2022 Robert Bosch GmbH and Microsoft Corporation
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""A sample skeleton vehicle app."""

import asyncio
import json
import logging
import signal

from sdv.util.log import (  # type: ignore
    get_opentelemetry_log_factory,
    get_opentelemetry_log_format,
)
from sdv.vdb.reply import DataPointReply
from sdv.vehicle_app import VehicleApp, subscribe_topic
from vehicle import Vehicle, vehicle  # type: ignore


# Configure the VehicleApp logger with the necessary log config and level.
logging.setLogRecordFactory(get_opentelemetry_log_factory())
logging.basicConfig(format=get_opentelemetry_log_format())
logging.getLogger().setLevel("DEBUG")
logger = logging.getLogger(__name__)


DATABROKER_SUBSCRIPTION_TEMPERATURE_TOPIC = "secondbox/currentTemperature"
USER_ONLINE_REQUEST = "secondbox/userOnline/Request"
USER_ONLINE_RESPONSE = "secondbox/userOnline/Response"
SET_MIRRORS_DIRECTION_REQUEST = "secondbox/setMirrorsDirecion/request"
SET_MIRRORS_DIRECTION_RESPONSE = "secondbox/setMirrorsDirection/response"
SET_FOLD_REQUEST = "secondbox/setFold/request"
SET_FOLD_RESPONSE = "secondbox/setFold/response"
SET_HVAC_REQUEST = "secondbox/setHvac/request"
SET_HVAC_RESPONSE = "secondbox/setHvac/response"
SET_DOOR_WINDOW_SWITCH_REQUEST = "secondbox/setDoorWindowSwitch/request"
SET_DOOR_WINDOW_SWITCH_RESPONSE = "secondbox/ \
    setDoorWindowSwitch/response"
SET_SUNROOF_REQUEST = "secondbox/setSunroof/request"
SET_SUNFOOF_RESPONSE = "secondbox/setSunroof/response"

SET_SEATFAN_REQUEST = "secondbox/setSeatFan/request"
SET_SEATFAN_RESPONSE = "secondbox/setSeatFan/response"
SET_ISDOMEON_REQUEST = "secondbox/setDomeonLight/request"
SET_ISDOMEON_RESPONSE = "secondbox/setDomeonLight/response"
GET_TEMPERATURE_REQUEST = "secondbox/getTemperature/request"
GET_TEMPERATURE_RESPONSE = "second/getTemperature/response"
GET_RADAR_REQUEST = "secondbox/getRadar/request"
GET_RADAR_RESPONSE = "secondbox/getRadar/response"


class SecondBoxApp(VehicleApp):
    """
    The Second Box Vehicle App
    - Receive the value and make corresponding logic based on the value
    """

    def __init__(self, vehicle_client: Vehicle):
        # SampleApp inherits from VehicleApp.
        super().__init__()
        self.Vehicle = vehicle_client
        self.rule = None

    async def on_start(self):
        """Run when the vehicle app starts"""
        # This method will be called by the SDK when the connection to the
        # Vehicle DataBroker is ready.
        # Here I subscribe for the Vehicle Signals update
        # (e.g. Vehicle Cabin HVAC AmbientAirTemperature).
        logger.info("begin on start function")

    async def on_temperature_change(self, data: DataPointReply):
        """The on_temperature_change callback, this will be executed when receiving 
        a new vehicle signal updates."""
        # Get the current temperature value from the received DatapointReply.
        # The DatapointReply containes the values of all subscribed DataPoints of
        # the same callback.
        temperature = data.get(self.Vehicle.Cabin.HVAC.AmbientAirTemperature).value
        logger.info("current temperature value is, %s" % temperature)
        window_value = (await
                        self.Vehicle.Cabin.Door.Row1.Left.Window.Switch.get()).value
        logger.info("window value is %s" % window_value)
        roof_value = (await self.Vehicle.Cabin.Sunroof.Switch.get()).value
        logger.info("roof value is %s" % roof_value)
        fanspeed_value = (await
                          self.Vehicle.Cabin.HVAC.Station.Row1.Left.FanSpeed.get()
                          ).value
        logger.info("fanspeed_valueis %s" % fanspeed_value)
        if temperature >= 28:
            if window_value != 'OPEN':
                logger.info("window switch set open")
                await self.Vehicle.Cabin.Door.Row1.Left.Window.Switch.set('OPEN')
        else:
            if not (window_value == 'CLOSE' or window_value == ''):
                logger.info("window switch set close")
                await self.Vehicle.Cabin.Door.Row1.Left.Window.Switch.set('CLOSE')
        if temperature >= 30:
            if roof_value != 'OPEN':
                logger.info("sunroof switch set open")
                await self.Vehicle.Cabin.Sunroof.Switch.set('OPEN')
        else:
            if not (roof_value == 'CLOSE' or roof_value == ''):
                logger.info("sunroof switch set close")
                await self.Vehicle.Cabin.Sunroof.Switch.set('CLOSE')
        if temperature >= 32:
            if fanspeed_value != 35:
                logger.info("fanspeed set open")
                await self.Vehicle.Cabin.HVAC.Station.Row1.Left.FanSpeed.set(35)
        else:
            if fanspeed_value != 0:
                logger.info("fanspeed set close")
                await self.Vehicle.Cabin.HVAC.Station.Row1.Left.FanSpeed.set(0)

    async def device_start(self, status_str) -> None:
        # business processing
        temperature = (await
                       self.Vehicle.Cabin.HVAC.AmbientAirTemperature.get()
                       ).value
        logger.info("current temperature value is, %s" % temperature)
        window_value = (await
                        self.Vehicle.Cabin.Door.Row1.Left.Window.Switch.get()).value
        logger.info("window value is %s" % window_value)
        roof_value = (await self.Vehicle.Cabin.Sunroof.Switch.get()).value
        logger.info("roof value is %s" % roof_value)
        fanspeed_value = (await
                          self.Vehicle.Cabin.HVAC.Station.Row1.Left.FanSpeed.get()
                          ).value
        logger.info("fan speed value is %s" % fanspeed_value)
        if status_str == "off":
            if self.rule is not None:
                logger.info("rule is not None")
                await self.rule.unsubscribe()
                logger.info("unsubscribe")
            if not (window_value == 'CLOSE' or window_value == ''):
                logger.info("close window")
                await self.Vehicle.Cabin.Door.Row1.Left.Window.Switch.set('CLOSE')
            if not (roof_value == 'CLOSE' or roof_value == ''):
                logger.info("close roof")
                await self.Vehicle.Cabin.Sunroof.Switch.set('OPEN')
            if fanspeed_value != 0:
                logger.info("close fanspeed")
                await self.Vehicle.Cabin.HVAC.Station.Row1.Left.FanSpeed.set(0)
            # add AtmosphereLight close
        else:
            self.rule = (await self.Vehicle.Cabin.HVAC.AmbientAirTemperature.subscribe(
                self.on_temperature_change))
            logger.info("subscribe data point")

    @subscribe_topic(USER_ONLINE_REQUEST)
    async def user_online_request_received(self, data_str: str) -> None:
        data = json.loads(data_str)
        logger.info("user info is %s" % data)
        status = data.get("status", None)
        if status is None:
            response_data = {
                "status": 0,
                "message": "no expected args"
            }
            await self.publish_event(USER_ONLINE_RESPONSE, json.dumps(response_data))
        if status == "on":
            LOOP.create_task(self.device_start("on"))
            response_data = {
                "status": 1,
                "message": "device has start"
            }
        elif status == "off":
            LOOP.create_task(self.device_start("off"))
            response_data = {
                "status": 1,
                "message": "device has stop"
            }
        else:
            response_data = {
                "status": 0,
                "message": "unexpected args"
            }

        await self.publish_event(USER_ONLINE_RESPONSE, json.dumps(response_data))

    @subscribe_topic(SET_MIRRORS_DIRECTION_REQUEST)
    async def set_mirrors_direction_change(self, data_str: str) -> None:
        data = json.loads(data_str)
        direction_str = data.get("direction", None)
        direction = direction_str.lower()
        angle = data.get("angle", 0)
        if direction not in ["up", "down", "left", "right"]:
            response_data = {
                "status": 0,
                "message": "unknow direction"
            }
        else:
            if angle == 0:
                response_data = {
                    "status": 1,
                    "message": "angle is 0, do nothing"
                }
            else:
                if direction == "left":
                    pan_value = (await self.Vehicle.Body.Mirrors.Left.Pan.get()).value
                    if pan_value == 100:
                        response_data = {
                            "status": 1,
                            "message": "mirrors is already on the far left"
                        }
                    else:
                        total_value = pan_value + angle
                        if total_value >= 100:
                            await self.Vehicle.Body.Mirrors.Left.Pan.set(100)
                        else:
                            await self.Vehicle.Body.Mirrors.Left.Pan.set(total_value)
                        response_data = {
                            "status": 1,
                            "message": "mirrors has been turn left"
                        }
                elif direction == "right":
                    pan_value = (await self.Vehicle.Body.Mirrors.Left.Pan.get()).value
                    if pan_value == -100:
                        response_data = {
                            "status": 1,
                            "message": "mirrors is already on the far left"
                        }
                    else:
                        total_value = pan_value - angle
                        if total_value <= -100:
                            await self.Vehicle.Body.Mirrors.Left.Pan.set(-100)
                        else:
                            await self.Vehicle.Body.Mirrors.Left.Pan.set(total_value)
                        response_data = {
                            "status": 1,
                            "message": "mirrors has been turn right"
                        }
                elif direction == "up":
                    tilt_value = (await self.Vehicle.Body.Mirrors.Left.Tilt.get()).value
                    if tilt_value == 100:
                        response_data = {
                            "status": 1,
                            "message": "mirrors is already on the far up"
                        }
                    else:
                        total_value = tilt_value + angle
                        if total_value >= 100:
                            await self.Vehicle.Body.Mirrors.Left.Tilt.set(100)
                        else:
                            await self.Vehicle.Body.Mirrors.Left.Tilt.set(total_value)
                        response_data = {
                            "status": 1,
                            "message": "mirrors has been turn up"
                        }
                else:
                    tilt_value = (await self.Vehicle.Body.Mirrors.Left.Tilt.get()).value
                    if tilt_value == -100:
                        response_data = {
                            "status": 1,
                            "message": "mirrors is already on the far down"
                        }
                    else:
                        total_value = tilt_value - angle
                        if total_value <= -100:
                            await self.Vehicle.Body.Mirrors.Left.Tilt.set(-100)
                        else:
                            await self.Vehicle.Body.Mirrors.Left.Tilt.set(total_value)
                        response_data = {
                            "status": 1,
                            "message": "mirrors has been turn down"
                        }
        logger.info("mirrors turn %s,angle is %s" % (direction, angle))
        await self.publish_event(
            SET_MIRRORS_DIRECTION_RESPONSE,
            json.dumps(response_data)
        )

    @subscribe_topic(SET_FOLD_REQUEST)
    async def set_mirrors_fold_change(self, data_str: str) -> None:
        data = json.loads(data_str)
        logger.info("data: %s" % data)
        fold = data["fold"]
        fold_value = (await self.Vehicle.Body.Mirrors.Left.Fold.get()).value
        if fold in [0, 1]:
            fold_status = "expand" if fold == 1 else "fold"
            if fold == fold_value:
                response_data = {
                    "status": 1,
                    "message": f"current mirrors status is already {fold_status}"
                }
                logger.info("fold status current status is already %s" % fold_status)
            else:
                await self.Vehicle.Body.Mirrors.Left.Fold.set(fold)
                response_data = {
                    "status": 1,
                    "message": f"current mirror change {fold_status}"
                }
                logger.info("fold status has change %s" % fold_status)
        else:
            response_data = {
                "status": 0,
                "message": "unpected values"
            }
            logger.info("unpected value,do nothing")

        await self.publish_event(
            SET_FOLD_RESPONSE,
            json.dumps(response_data)
        )

    @subscribe_topic(SET_HVAC_REQUEST)
    async def set_mirrors_hvac_change(self, data_str: str) -> None:
        data = json.loads(data_str)
        logger.info("data is %s" % data)
        fanspeed = data["fanspeed"]
        fanspeed_val = (await
                        self.Vehicle.Cabin.HVAC.Station.Row1.Left.FanSpeed.get()).value
        if fanspeed < 0 or fanspeed > 100:
            response_data = {
                "status": 0,
                "message": "out of range value"
            }
            logger.info("out of range range")
        else:
            if fanspeed == fanspeed_val:
                response_data = {
                    "status": 1,
                    "message": f"""current fanspeed is already {fanspeed}"""
                }
                logger.info("current fanspeed is already %s" % fanspeed)
            else:
                await self.Vehicle.Cabin.HVAC.Station.Row1.Left.FanSpeed.set(fanspeed)
                response_data = {
                    "status": 1,
                    "message": f"""fanspeed is change {fanspeed}"""
                }
                logger.info("fanspeed is change %s" % fanspeed)
        await self.publish_event(
            SET_HVAC_RESPONSE,
            json.dumps(response_data)
        )

    @subscribe_topic(SET_DOOR_WINDOW_SWITCH_REQUEST)
    async def set_door_window_switch_change(self, data_str: str) -> None:
        data = json.loads(data_str)
        logger.info("data is %s" % data)
        door_windo_window = data["window_value"]
        door_window_value = (await
                             self.Vehicle.Cabin.Door.Row1.Left.Window.Switch.get()
                             ).value
        if door_window_value == door_windo_window:
            response_data = {
                "status": 1,
                "message": f"""door window current status is {door_windo_window},
                do nothing"""
            }
        else:
            await self.Vehicle.Cabin.Door.Row1.Left.Window.Switch.set(door_windo_window)
            response_data = {
                "status": 1,
                "message": f"""door window has change {door_windo_window}"""
            }

        await self.publish_event(
            SET_HVAC_RESPONSE,
            json.dumps(response_data)
        )

    @subscribe_topic(SET_SUNROOF_REQUEST)
    async def set_mirrors_sunroof_change(self, data_str: str) -> None:
        data = json.loads(data_str)
        logger.info("data is %s" % data)
        sunroof = data["sunroof"]
        sunroof_val = (await self.Vehicle.Cabin.Sunroof.Switch.get()).value
        if sunroof == sunroof_val:
            response_data = {
                "status": 1,
                "message": """sunroof current status is already {sunroof}"""
            }
        else:
            await self.Vehicle.Cabin.Sunroof.Switch.set(sunroof)
            response_data = {
                "status": 1,
                "message": f"""sunroof status has change {sunroof}"""
            }

        await self.publish_event(
            SET_SUNFOOF_RESPONSE,
            json.dumps(response_data)
        )

    @subscribe_topic(SET_SEATFAN_REQUEST)
    async def set_seatfan_change(self, data_str: str) -> None:
        data = json.loads(data_str)
        logger.info("data is %s" % data)
        seatfan = data["seatfan"]
        seatfan_val = (await self.Vehicle.Cabin.Seat.Row1.Pos1.IsSeatFan.get()).value
        seatfan_status = "open" if seatfan is True else "close"
        if seatfan == seatfan_val:
            response_data = {
                "status": 1,
                "message": f"""current seat fan is {seatfan_status}"""
            }
        else:
            await self.Vehicle.Cabin.Seat.Row1.Pos1.IsSeatFan.set(seatfan)
            response_data = {
                "status": 1,
                "message": "seat fan has change seatfan_status"
            }
        await self.publish_event(
            SET_SEATFAN_RESPONSE,
            json.dumps(response_data)
        )

    @subscribe_topic(SET_ISDOMEON_REQUEST)
    async def set_domeon_change(self, data_str: str) -> None:
        data = json.loads(data_str)
        logger.info("data is %s" % data)
        light_status = data["light_status"]
        domeon_value = (await self.Vehicle.Cabin.Lights.IsDomeOn.get()).value
        light_status_val = "on" if light_status is True else "off"
        if light_status == domeon_value:
            response_data = {
                "status": 1,
                "message": f"""current light status is {light_status_val}"""
            }
        else:
            await self.Vehicle.Cabin.Lights.IsDomeOn.set(light_status)
            response_data = {
                "status": 1,
                "message": f"""light status has chang {light_status_val}"""
            }
        await self.publish_event(
            SET_ISDOMEON_RESPONSE,
            json.dumps(response_data)
        )

    @subscribe_topic(GET_TEMPERATURE_REQUEST)
    async def get_temperature_request_received(self, data_str: str) -> None:
        logger.debug(
            "PubSub event for the Topic: %s -> is received with the data: %s",
            GET_TEMPERATURE_REQUEST,
            data_str,
        )
        temperature = (await self.Vehicle.Cabin.HVAC.AmbientAirTemperature.get()).value
        await self.publish_event(
            GET_TEMPERATURE_RESPONSE,
            json.dumps(
                {
                    "result": {
                        "status": 0,
                        "message": f"""Current temperature = {temperature}""",
                    },
                }
            ),
        )

    @subscribe_topic(GET_TEMPERATURE_REQUEST)
    async def get_radar_request_received(self, data_str: str) -> None:
        logger.debug(
            "PubSub event for the Topic: %s -> is received with the data: %s",
            GET_RADAR_REQUEST,
            data_str,
        )
        radar = (await self.Vehicle.Body.Radar.get()).value
        await self.publish_event(
            GET_RADAR_RESPONSE,
            json.dumps(
                {
                    "result": {
                        "status": 0,
                        "message": f"""Current radar  = {radar}""",
                    },
                }
            ),
        )


async def main():
    """Main function"""
    logger.info("Starting SecondBoxApp...")
    # Constructing SecondBoxApp and running it.
    vehicle_app = SecondBoxApp(vehicle)
    await vehicle_app.run()


LOOP = asyncio.get_event_loop()
LOOP.add_signal_handler(signal.SIGTERM, LOOP.stop)
LOOP.run_until_complete(main())
LOOP.close()
