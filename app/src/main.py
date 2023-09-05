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


class SecondBoxApp(VehicleApp):
    """
    The Second Box Vehicle App
    - Receive the value and make corresponding logic based on the value
    """

    def __init__(self, vehicle_client: Vehicle):
        # SampleApp inherits from VehicleApp.
        super().__init__()
        self.Vehicle = vehicle_client

    async def on_start(self):
        """Run when the vehicle app starts"""
        # This method will be called by the SDK when the connection to the
        # Vehicle DataBroker is ready.
        # Here I subscribe for the Vehicle Signals update
        # (e.g. Vehicle Cabin HVAC AmbientAirTemperature).
        logger.info("begin on start function")
        await self.Vehicle.Cabin.HVAC.AmbientAirTemperature.subscribe(
            self.on_temperature_change)

    async def on_temperature_change(self, data: DataPointReply):
        """The on_temperature_change callback, this will be executed when receiving 
        a new vehicle signal updates."""
        # Get the current temperature value from the received DatapointReply.
        # The DatapointReply containes the values of all subscribed DataPoints of
        # the same callback.
        temperature = data.get(self.Vehicle.Cabin.HVAC.AmbientAirTemperature).value

        logger.info("temperature value is, %s" % temperature)
        response_data = {
            "status": 1,
            "messages": f"current temperature is {temperature}",
        }
        json_response_data = json.dumps(response_data)
        await self.publish_event(DATABROKER_SUBSCRIPTION_TEMPERATURE_TOPIC,
                                 json_response_data)

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
            if window_value != 'CLOSE' or window_value is not None:
                await self.Vehicle.Cabin.Door.Row1.Left.Window.Switch.set('CLOSE')
            if roof_value != 'CLOSE' or roof_value is not None:
                await self.Vehicle.Cabin.Sunroof.Switch.set('OPEN')
            if fanspeed_value != 0:
                await self.Vehicle.Cabin.HVAC.Station.Row1.Left.FanSpeed.set(0)
            # add AtmosphereLight close
        else:
            if temperature >= 28:
                if window_value != 'OPEN':
                    logger.info("window switch set open")
                    await self.Vehicle.Cabin.Door.Row1.Left.Window.Switch.set('OPEN')
            else:
                if window_value != 'CLOSE' or window_value is not None:
                    logger.info("window switch set close")
                    await self.Vehicle.Cabin.Door.Row1.Left.Window.Switch.set('CLOSE')
            if temperature >= 30:
                if roof_value != 'OPEN':
                    logger.info("sunroof switch set open")
                    await self.Vehicle.Cabin.Sunroof.Switch.set('OPEN')
            else:
                if roof_value != 'CLOSE' or roof_value is not None:
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

    @subscribe_topic(USER_ONLINE_REQUEST)
    async def user_online_request_received(self, data_str: str) -> None:
        data = json.loads(data_str)
        logger.info("user info is %s" % data)
        status = data.get("status", None)
        if status is None:
            response_data = {
                "status": 0,
                "messages": "no expected args"
            }
            await self.publish_event(USER_ONLINE_RESPONSE, json.dumps(response_data))
        if status == "on":
            LOOP.create_task(self.device_start("on"))
            response_data = {
                "status": 1,
                "messages": "device has start"
            }
        elif status == "off":
            LOOP.create_task(self.device_start("off"))
            response_data = {
                "status": 1,
                "messages": "device has stop"
            }
        else:
            response_data = {
                "status": 0,
                "messages": "unexpected args"
            }
            
        await self.publish_event(USER_ONLINE_RESPONSE, json.dumps(response_data))


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
