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
from sdv.vehicle_app import VehicleApp
from vehicle import Vehicle, vehicle  # type: ignore

# Configure the VehicleApp logger with the necessary log config and level.
logging.setLogRecordFactory(get_opentelemetry_log_factory())
logging.basicConfig(format=get_opentelemetry_log_format())
logging.getLogger().setLevel("DEBUG")
logger = logging.getLogger(__name__)


DATABROKER_SUBSCRIPTION_TEMPERATURE_TOPIC = "sampleapp/currentTemperature"


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

        # business processing
        if temperature >= 28:
            await self.Vehicle.Cabin.Door.Row1.Left.Window.Switch.set('OPEN')
        else:
            await self.Vehicle.Cabin.Door.Row1.Left.Window.Switch.set('CLOSE')
        if temperature >= 30:
            await self.Vehicle.Cabin.Sunroof.Switch.set('OPEN')
        else:
            await self.Vehicle.Cabin.Sunroof.Switch.set('CLOSE')
        if temperature >= 32:
            await self.Vehicle.Cabin.HVAC.Station.Row1.Left.FanSpeed.set(35)
        else:
            await self.Vehicle.Cabin.HVAC.Station.Row1.Left.FanSpeed.set(0)

        await self.publish_event(
            DATABROKER_SUBSCRIPTION_TEMPERATURE_TOPIC,
            json.dumps({"currentTemperature": temperature})
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
