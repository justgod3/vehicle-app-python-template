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

SET_SEATADJUSTER_REQUEST_TOPIC = "sampleapp/setPosition"
SET_SEATADJUSTER_RESPONSE_TOPIC = "sampleapp/setPosition/response"


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

    async def on_seat_position_changed(self, data: DataPointReply):
        response_topic = "sampleapp/currentPosition"
        await self.publish_event(
            response_topic,
            json.dumps(
                {"position": data.get(self.Vehicle.Cabin.Seat.Row1.Pos1.Position).value}
            ),
        )

    @subscribe_topic(SET_SEATADJUSTER_REQUEST_TOPIC)
    async def on_set_position_request_received(self, data_str: str) -> None:
        data = json.loads(data_str)
        # 此方法是设置座椅的位置，所以需要判断一个事情位置，
        # 移动座椅，记忆点目前只有两个位置1，2

        if 'position' not in data:
            await self.publish_mqtt_event(
                SET_SEATADJUSTER_RESPONSE_TOPIC,
                json.dumps(
                    {
                        "result": {
                            "status": 1,
                            "message": "error request parameters",
                        },
                    }
                ),
            )
        else:
            # 判断position的数字大小，不在（1，2）就报错
            position_num = int(data['position'])
            if position_num not in [1, 2]:
                await self.publish_mqtt_event(
                    SET_SEATADJUSTER_RESPONSE_TOPIC,
                    json.dumps(
                        {
                            "result": {
                                "status": 1,
                                "message": "Unexpected parameters",
                            },
                        }
                    ),
                )
            else:
                await self.Vehicle.Cabin.Seat.Row1.Pos1.Position.set(position_num)
                await self.publish_mqtt_event(
                    SET_SEATADJUSTER_RESPONSE_TOPIC,
                    json.dumps(
                        {
                            "result": {
                                "status": 0,
                                "message": f"Current Position = {position_num}",
                            },
                        }
                    ),
                )


async def main():

    """Main function"""
    logger.info("Starting seat adjuster app...")
    seat_adjuster_app = SeatAdjusterApp(vehicle)
    await seat_adjuster_app.run()


LOOP = asyncio.get_event_loop()
LOOP.add_signal_handler(signal.SIGTERM, LOOP.stop)
LOOP.run_until_complete(main())
LOOP.close()
