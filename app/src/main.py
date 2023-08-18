# Copyright (c) 2022-2023 Robert Bosch GmbH and Microsoft Corporation
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

"""A sample Velocitas vehicle app for adjusting seat position."""

import asyncio
import json
import logging
import signal

from vehicle import Vehicle, vehicle  # type: ignore

from sdv.util.log import (  # type: ignore
    get_opentelemetry_log_factory,
    get_opentelemetry_log_format,
)
from sdv.vdb.reply import DataPointReply
from sdv.vehicle_app import VehicleApp, subscribe_topic

logging.setLogRecordFactory(get_opentelemetry_log_factory())
logging.basicConfig(format=get_opentelemetry_log_format())
logging.getLogger().setLevel("DEBUG")
logger = logging.getLogger(__name__)

SET_ATMOSPHERELIGHT_REQUEST_TOPIC = ""
SET_ATMOSPHERELIGHT_RESPONSE_TOPIC = "sampleapp/setAtmospherelight/response"

# 七种基本色
seven_color_dic = {
    "#ff0000": 0,
    "#00ff00": 3,
    "#0000ff": 6
}


class SeatAdjusterApp(VehicleApp):
    """
    Sample Velocitas Vehicle App.

    The SeatAdjusterApp subscribes to a MQTT topic to listen for incoming
    requests to change the seat position and calls the SeatService to move the seat
    upon such a request, but only if Vehicle.Speed equals 0.

    It also subcribes to the VehicleDataBroker for updates of the
    Vehicle.Cabin.Seat.Row1.Pos1.Position signal and publishes this
    information via another specific MQTT topic
    """

    def __init__(self, vehicle_client: Vehicle):
        super().__init__()
        self.Vehicle = vehicle_client

    async def on_start(self):
        """Run when the vehicle app starts"""
        await self.Vehicle.Cabin.Seat.Row1.Pos1.Position.subscribe(
            self.on_seat_position_changed
        )
        await self.Vehicle.Cabin.Seat.Row1.Pos2.Position.subscribe(
            self.on_seat_pos2_position_changed
        )

    async def on_seat_position_changed(self, data: DataPointReply):
        response_topic = "sampleapp/currentPosition"
        await self.publish_event(
            response_topic,
            json.dumps(
                {"position": data.get(self.Vehicle.Cabin.Seat.Row1.Pos1.Position).value}
            ),
        )

    async def on_seat_pos2_position_changed(self, data: DataPointReply):
        response_topic = "sampleapp/pos2/currentPosition"
        await self.publish_event(
            response_topic,
            json.dumps(
                {"position": data.get(self.Vehicle.Cabin.Seat.Row1.Pos2.Position).value}
            ),
        )

    @subscribe_topic("sampleapp/setPosition")
    async def on_set_position_request_received(self, data_str: str) -> None:
        data = json.loads(data_str)
        response_topic = "sampleapp/setPosition/response"
        response_data = {"position": data["position"]}
        logger.info("this is position: %s", data["position"])
        position = data["position"]

        await self.Vehicle.Cabin.Seat.Row1.Pos1.Position.set(position)
        response_data["result"] = {
            "status": 0,
            "message": f"Set Seat position to: {position}",
        }

        await self.publish_event(response_topic, json.dumps(response_data))

    @subscribe_topic(SET_ATMOSPHERELIGHT_REQUEST_TOPIC)
    async def on_set_atmospherelight_request_received(self, data_str: str) -> None:
        data = json.loads(data_str)
        color = data["color"]
        action = data["action"]
        status = data["status"]
        logger.info('atmospherelight color: %', data)
        logger.info('atmospherelight action: %', action)
        logger.info('atmospherelight status: %', status)
        # 逻辑处理
        if status:
            color_int = seven_color_dic[color]
            result_int = color_int + action
            logger.info(result_int)
            try:
                await self.Vehicle.Cabin.Seat.Row1.Pos2.Position.set(result_int)
                response_data = {
                    "status": 0,
                    "message": f"Set color {color}, action {action}",
                }
            except ValueError as error:
                response_data = {
                    "status": 1,
                    "message": f"Failed to set color {color}, action {action},\
                      error: {error}",
                }
            except Exception:

                response_data = {
                    "status": 1,
                    "message": "Exception on set Seat position",
                }
            await self.publish_event(SET_ATMOSPHERELIGHT_RESPONSE_TOPIC,
                                     json.dumps(response_data))
        else:
            result_int = 0
            try:
                await self.Vehicle.Cabin.Seat.Row1.Pos2.Position.set(result_int)
                response_data = {
                    "status": 0,
                    "message": f"Set Seat color {color}, action {action}",
                }
            except ValueError as error:
                response_data = {
                    "status": 1,
                    "message": f"Failed to set color {color}, action {action}, \
                    error: {error}",
                }
            except Exception:

                response_data = {
                    "status": 1,
                    "message": "Exception on set Seat lights",
                }
            await self.publish_event(SET_ATMOSPHERELIGHT_RESPONSE_TOPIC,
                                     json.dumps(response_data))


async def main():

    """Main function"""
    logger.info("Starting seat adjuster app...")
    seat_adjuster_app = SeatAdjusterApp(vehicle)
    await seat_adjuster_app.run()


LOOP = asyncio.get_event_loop()
LOOP.add_signal_handler(signal.SIGTERM, LOOP.stop)
LOOP.run_until_complete(main())
LOOP.close()
